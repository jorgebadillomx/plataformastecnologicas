"""parse_cfdi.py — Lee un ZIP (o carpeta) con XMLs del SAT y emite JSON normalizado.

Soporta:
- CFDI 4.0 (y tolera 3.3): tipos I (ingreso), E (egreso), P (pago), N (nómina), T (traslado).
- Complemento de Pagos 2.0 (CFDI tipo P): mapa de IVA efectivamente pagado por
  UUID de documento relacionado (clave para facturas PPD).
- CFDI de Retenciones e información de pagos 2.0 (incluye el Complemento de
  Servicios Plataformas Tecnológicas que emite Airbnb cada mes).

Diseño:
- Parsing namespace-agnóstico (local-name), igual que el flujo legacy validado:
  tolera variaciones de prefijo y versiones de complementos.
- Tolerante a XMLs malformados: el archivo problemático se reporta en "errores"
  y el proceso continúa (regla del proyecto: reportar y seguir, no tronar).
- Montos como Decimal internamente; en el JSON de salida se serializan como
  string para no perder precisión (los consumidores hacen Decimal(valor)).

Uso:
    python parse_cfdi.py archivos.zip            # JSON a stdout
    python parse_cfdi.py carpeta/ -o salida.json # JSON a archivo, resumen a stderr

NOTA sobre el CFDI de retenciones: los nombres de atributos del complemento de
plataformas tecnológicas se capturan de forma genérica (dict crudo) además de
los campos normalizados, para tolerar variantes de versión. Validar contra un
CFDI real de Airbnb antes de publicar (los fixtures del repo son sintéticos).
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET

# Códigos de impuesto: CFDI usa 001/002/003; el CFDI de retenciones usa 01/02/03.
IMPUESTO_NOMBRE = {
    "001": "ISR", "01": "ISR",
    "002": "IVA", "02": "IVA",
    "003": "IEPS", "03": "IEPS",
}


def _local(tag: str) -> str:
    return tag.rpartition("}")[2]


def _children(node: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in node if _local(c.tag) == name]


def _child(node: ET.Element, name: str) -> ET.Element | None:
    hijos = _children(node, name)
    return hijos[0] if hijos else None


def _descendants(node: ET.Element, name: str) -> list[ET.Element]:
    return [e for e in node.iter() if _local(e.tag) == name]


def _dec(value: str | None) -> Decimal:
    if value is None or not str(value).strip():
        return Decimal("0")
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return Decimal("0")


def _attr(node: ET.Element | None, *names: str) -> str:
    """Primer atributo presente entre varios nombres candidatos (tolerancia de versión)."""
    if node is None:
        return ""
    for name in names:
        if name in node.attrib:
            return node.attrib[name]
    return ""


def _sum_iva_traslados(parent: ET.Element) -> Decimal:
    """Suma Importe de Traslado con Impuesto IVA bajo un nodo Impuestos directo."""
    total = Decimal("0")
    for impuestos in _children(parent, "Impuestos"):
        for traslados in _children(impuestos, "Traslados"):
            for traslado in _children(traslados, "Traslado"):
                if IMPUESTO_NOMBRE.get(traslado.get("Impuesto", "")) == "IVA":
                    total += _dec(traslado.get("Importe"))
    return total


def parse_comprobante(root: ET.Element, archivo: str) -> dict:
    """CFDI 3.3/4.0 → dict normalizado."""
    a = root.attrib
    emisor = _child(root, "Emisor")
    receptor = _child(root, "Receptor")

    conceptos = []
    nodo_conceptos = _child(root, "Conceptos")
    if nodo_conceptos is not None:
        for c in _children(nodo_conceptos, "Concepto"):
            conceptos.append({
                "clave_prod_serv": c.get("ClaveProdServ", ""),
                "descripcion": c.get("Descripcion", ""),
                "cantidad": _dec(c.get("Cantidad")),
                "valor_unitario": _dec(c.get("ValorUnitario")),
                "importe": _dec(c.get("Importe")),
                "descuento": _dec(c.get("Descuento")),
            })

    # IVA trasladado: primero el resumen a nivel comprobante; si no existe,
    # suma por concepto (mismo criterio que el flujo legacy).
    iva_trasladado = _sum_iva_traslados(root)
    if iva_trasladado == 0 and nodo_conceptos is not None:
        for c in _children(nodo_conceptos, "Concepto"):
            iva_trasladado += _sum_iva_traslados(c)

    # Retenciones a nivel comprobante (ISR/IVA retenidos en la factura).
    iva_retenido = Decimal("0")
    isr_retenido = Decimal("0")
    for impuestos in _children(root, "Impuestos"):
        for retenciones in _children(impuestos, "Retenciones"):
            for ret in _children(retenciones, "Retencion"):
                nombre = IMPUESTO_NOMBRE.get(ret.get("Impuesto", ""))
                if nombre == "IVA":
                    iva_retenido += _dec(ret.get("Importe"))
                elif nombre == "ISR":
                    isr_retenido += _dec(ret.get("Importe"))

    relacionados = []
    for rel_nodo in _children(root, "CfdiRelacionados"):
        relacionados.append({
            "tipo_relacion": rel_nodo.get("TipoRelacion", ""),
            "uuids": [
                r.get("UUID", "").upper()
                for r in _children(rel_nodo, "CfdiRelacionado")
                if r.get("UUID")
            ],
        })

    # Complementos: timbre (UUID) y pagos 2.0.
    uuid = ""
    pagos = []
    for complemento in _children(root, "Complemento"):
        tfd = _descendants(complemento, "TimbreFiscalDigital")
        if tfd:
            uuid = tfd[0].get("UUID", "").upper()
        for nodo_pagos in _descendants(complemento, "Pagos"):
            for pago in _children(nodo_pagos, "Pago"):
                doctos = []
                for docto in _children(pago, "DoctoRelacionado"):
                    iva_dr = Decimal("0")
                    for imp_dr in _children(docto, "ImpuestosDR"):
                        for tras_dr in _children(imp_dr, "TrasladosDR"):
                            for t in _children(tras_dr, "TrasladoDR"):
                                if IMPUESTO_NOMBRE.get(t.get("ImpuestoDR", "")) == "IVA":
                                    iva_dr += _dec(t.get("ImporteDR"))
                    doctos.append({
                        "uuid": docto.get("IdDocumento", "").upper(),
                        "importe_pagado": _dec(docto.get("ImpPagado")),
                        "iva_pagado": iva_dr,
                        "num_parcialidad": docto.get("NumParcialidad", ""),
                    })
                pagos.append({
                    "fecha_pago": pago.get("FechaPago", ""),
                    "forma_pago": pago.get("FormaDePagoP", ""),
                    "monto": _dec(pago.get("Monto")),
                    "doctos": doctos,
                })

    return {
        "tipo_doc": "cfdi",
        "archivo": archivo,
        "version": a.get("Version", a.get("version", "")),
        "uuid": uuid,
        "tipo": a.get("TipoDeComprobante", ""),
        "fecha": a.get("Fecha", ""),
        "serie": a.get("Serie", ""),
        "folio": a.get("Folio", ""),
        "moneda": a.get("Moneda", ""),
        "tipo_cambio": _dec(a.get("TipoCambio") or "1"),
        "forma_pago": a.get("FormaPago", ""),
        "metodo_pago": a.get("MetodoPago", ""),
        "subtotal": _dec(a.get("SubTotal")),
        "descuento": _dec(a.get("Descuento")),
        "total": _dec(a.get("Total")),
        "emisor": {
            "rfc": _attr(emisor, "Rfc").upper(),
            "nombre": _attr(emisor, "Nombre"),
            "regimen_fiscal": _attr(emisor, "RegimenFiscal"),
        },
        "receptor": {
            "rfc": _attr(receptor, "Rfc").upper(),
            "nombre": _attr(receptor, "Nombre"),
            "uso_cfdi": _attr(receptor, "UsoCFDI"),
            "regimen_fiscal": _attr(receptor, "RegimenFiscalReceptor"),
            "domicilio_fiscal": _attr(receptor, "DomicilioFiscalReceptor"),
        },
        "conceptos": conceptos,
        "iva_trasladado": iva_trasladado,
        "iva_retenido": iva_retenido,
        "isr_retenido": isr_retenido,
        "relacionados": relacionados,
        "pagos": pagos,
    }


def parse_retenciones(root: ET.Element, archivo: str) -> dict:
    """CFDI de Retenciones e información de pagos (1.0/2.0) → dict normalizado.

    Captura campos normalizados + atributos crudos del complemento de
    plataformas tecnológicas (tolerancia entre versiones del esquema).
    """
    a = root.attrib
    emisor = _child(root, "Emisor")
    receptor = _child(root, "Receptor")
    nacional = _child(receptor, "Nacional") if receptor is not None else None
    periodo = _child(root, "Periodo")
    totales = _child(root, "Totales")

    impuestos_retenidos = []
    isr_retenido = Decimal("0")
    iva_retenido = Decimal("0")
    if totales is not None:
        for imp in _children(totales, "ImpRetenidos"):
            nombre = IMPUESTO_NOMBRE.get(_attr(imp, "ImpuestoRet", "Impuesto"), "")
            monto = _dec(_attr(imp, "MontoRet", "montoRet"))
            impuestos_retenidos.append({
                "impuesto": nombre or _attr(imp, "ImpuestoRet", "Impuesto"),
                "base": _dec(_attr(imp, "BaseRet", "baseRet")),
                "monto": monto,
                "tipo_pago": _attr(imp, "TipoPagoRet"),
            })
            if nombre == "ISR":
                isr_retenido += monto
            elif nombre == "IVA":
                iva_retenido += monto

    plataformas_raw: dict = {}
    uuid = ""
    for complemento in _children(root, "Complemento"):
        tfd = _descendants(complemento, "TimbreFiscalDigital")
        if tfd:
            uuid = tfd[0].get("UUID", "").upper()
        for nodo in complemento.iter():
            if _local(nodo.tag) == "ServiciosPlataformasTecnologicas":
                plataformas_raw = dict(nodo.attrib)

    return {
        "tipo_doc": "retenciones",
        "archivo": archivo,
        "version": a.get("Version", ""),
        "uuid": uuid,
        "fecha_exp": _attr(root, "FechaExp", "fechaExp"),
        "cve_retencion": _attr(root, "CveRetenc", "cveRetenc"),
        "desc_retencion": _attr(root, "DescRetenc", "descRetenc"),
        "emisor": {
            "rfc": _attr(emisor, "RfcE", "RFCEmisor", "Rfc").upper(),
            "nombre": _attr(emisor, "NomDenRazSocE", "NomDenRazSocR", "Nombre"),
        },
        "receptor": {
            "rfc": _attr(nacional, "RfcR", "RFCRecep", "Rfc").upper(),
            "nombre": _attr(nacional, "NomDenRazSocR", "Nombre"),
        },
        "periodo": {
            "mes_inicial": _attr(periodo, "MesIni", "mesIni"),
            "mes_final": _attr(periodo, "MesFin", "mesFin"),
            "ejercicio": _attr(periodo, "Ejercicio", "Ejerc", "ejerc"),
        },
        "totales": {
            "monto_operacion": _dec(_attr(totales, "MontoTotOperacion", "montoTotOperacion")),
            "monto_gravado": _dec(_attr(totales, "MontoTotGrav", "montoTotGrav")),
            "monto_exento": _dec(_attr(totales, "MontoTotExent", "montoTotExent")),
            "monto_retenido": _dec(_attr(totales, "MontoTotRet", "montoTotRet")),
        },
        "impuestos_retenidos": impuestos_retenidos,
        "isr_retenido": isr_retenido,
        "iva_retenido": iva_retenido,
        "plataformas_tecnologicas": plataformas_raw,
    }


def parse_xml_bytes(data: bytes, archivo: str) -> dict:
    root = ET.fromstring(data)
    nombre_raiz = _local(root.tag)
    if nombre_raiz == "Comprobante":
        return parse_comprobante(root, archivo)
    if nombre_raiz == "Retenciones":
        return parse_retenciones(root, archivo)
    raise ValueError(f"Raíz XML no reconocida: {nombre_raiz}")


def _iter_xml_sources(ruta: Path):
    """Genera (nombre, bytes) desde un ZIP o una carpeta (recursivo)."""
    if ruta.is_dir():
        for p in sorted(ruta.rglob("*.xml")):
            yield str(p.relative_to(ruta)), p.read_bytes()
        return
    if zipfile.is_zipfile(ruta):
        with zipfile.ZipFile(ruta) as zf:
            for info in sorted(zf.infolist(), key=lambda i: i.filename):
                if info.is_dir() or not info.filename.lower().endswith(".xml"):
                    continue
                yield info.filename, zf.read(info)
        return
    if ruta.suffix.lower() == ".xml":
        yield ruta.name, ruta.read_bytes()
        return
    raise ValueError(f"Entrada no soportada (se espera ZIP, carpeta o XML): {ruta}")


def parse_entrada(ruta: str | Path) -> dict:
    """Punto de entrada programático: ZIP/carpeta/XML → estructura normalizada."""
    ruta = Path(ruta)
    comprobantes: list[dict] = []
    retenciones: list[dict] = []
    errores: list[dict] = []

    for nombre, data in _iter_xml_sources(ruta):
        try:
            registro = parse_xml_bytes(data, nombre)
        except (ET.ParseError, ValueError) as exc:
            errores.append({"archivo": nombre, "error": str(exc)})
            continue
        if registro["tipo_doc"] == "retenciones":
            retenciones.append(registro)
        else:
            comprobantes.append(registro)

    por_tipo: dict[str, int] = {}
    for c in comprobantes:
        por_tipo[c["tipo"] or "?"] = por_tipo.get(c["tipo"] or "?", 0) + 1

    return {
        "fuente": str(ruta),
        "comprobantes": comprobantes,
        "retenciones": retenciones,
        "errores": errores,
        "resumen": {
            "total_archivos": len(comprobantes) + len(retenciones) + len(errores),
            "comprobantes": len(comprobantes),
            "comprobantes_por_tipo": por_tipo,
            "docs_retenciones": len(retenciones),
            "errores": len(errores),
        },
    }


def mapa_iva_pagado(comprobantes: list[dict], anio: int, mes: int) -> dict[str, Decimal]:
    """UUID de factura → IVA efectivamente pagado vía complementos P en el periodo.

    Es la pieza que resuelve las facturas PPD: solo cuenta el IVA cuyo pago
    (FechaPago) cae en el periodo solicitado.
    """
    mapa: dict[str, Decimal] = {}
    for c in comprobantes:
        if c["tipo"] != "P":
            continue
        for pago in c["pagos"]:
            fecha = pago.get("fecha_pago", "")
            if len(fecha) < 7:
                continue
            try:
                f_anio, f_mes = int(fecha[0:4]), int(fecha[5:7])
            except ValueError:
                continue
            if (f_anio, f_mes) != (anio, mes):
                continue
            for docto in pago["doctos"]:
                if not docto["uuid"]:
                    continue
                mapa[docto["uuid"]] = mapa.get(docto["uuid"], Decimal("0")) + docto["iva_pagado"]
    return mapa


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"No serializable: {type(value)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parser de CFDI (ZIP/carpeta/XML) a JSON normalizado")
    parser.add_argument("entrada", help="ZIP con XMLs, carpeta o XML individual")
    parser.add_argument("-o", "--salida", help="Archivo JSON de salida (default: stdout)")
    args = parser.parse_args(argv)

    resultado = parse_entrada(args.entrada)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2, default=_json_default)

    if args.salida:
        Path(args.salida).write_text(texto, encoding="utf-8")
    else:
        print(texto)

    r = resultado["resumen"]
    print(
        f"[parse_cfdi] {r['comprobantes']} CFDI ({r['comprobantes_por_tipo']}), "
        f"{r['docs_retenciones']} doc(s) de retenciones, {r['errores']} error(es)",
        file=sys.stderr,
    )
    for e in resultado["errores"]:
        print(f"[parse_cfdi]   error en {e['archivo']}: {e['error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""clasificador.py — Clasifica CFDI como deducibles/no deducibles/dudosos según el régimen.

Cada veredicto cita la regla aplicada (IDs R-xx legales y H-xx heurísticas de
skill/references/reglas_deducibilidad.md) — regla dura del proyecto: todo
explicable, nada de números mágicos.

Estatus:
  DEDUCIBLE            gasto de la actividad con IVA acreditable
  NO_DEDUCIBLE         descartado (con regla y motivo)
  DUDOSA               requiere decisión del usuario (se persiste por UUID)
  DIFERIDA             PPD sin complemento de pago en el periodo (se difiere)
  AJUSTE               nota de crédito (E) que compensa una factura incluida
  EXCLUIDO_DOC         tipo P/N/T: no es gasto por sí mismo (R-01)
  DEDUCCION_PERSONAL   UsoCFDI D0x: candidata para la declaración ANUAL (R-22)
  INVERSION            UsoCFDI I0x: activo fijo, se reporta aparte (R-21)

Heurísticas H-xx: portadas del flujo legacy validado del autor (4 meses de
datos reales con paridad verificada). El orden de evaluación replica el flujo
legacy para conservar ese comportamiento.

Overrides: decisiones del usuario por UUID, persistentes. Acepta el formato
legacy (lista de {"UUID":..., "Decision": 100|0}) y el simple
({"<uuid>": "incluir"|"excluir"}).

Uso:
    python clasificador.py cfdis.zip --periodo 2026-05 [--regimen plataformas]
        [--overrides decisiones.json] [-o salida.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from decimal import Decimal
from pathlib import Path

from parse_cfdi import mapa_iva_pagado, parse_entrada
from referencias import parametros_deducibilidad

REGIMENES = ("plataformas", "plataformas_definitivo", "resico")

# --- Términos heurísticos (heredados del flujo legacy validado; ver H-xx) ---
TERMINOS_FINANCIEROS = [
    "hsbc", "santander", "banco", "casa de bolsa", "kuspit", "bursatil",
    "interes", "inversion", "prestam", "financ", "credito", "seguro",
    "anualidad", "comisiones", "estado de cuenta",
]
TERMINOS_PERSONALES = [
    "colegiatura", "medico", "nomina", "pantalon", "mezclilla", "ropa",
    "crema", "ojos", "leche", "supermerc", "farmacia",
]
TERMINOS_MARKETPLACE = ["amazon", "mercado libre", "walmart", "costco", "soriana", "chedraui"]
TERMINOS_INCLUIR_CLARO = [
    "plataformas digitales", "airbnb", "resico", "gas rem",
    "renta de servicios de internet", "infraestructura", "limpieza",
    "aromatizante", "mantenimiento", "reparacion", "inmueble",
    "insumos de operacion",
]
TERMINOS_DUDOSOS = [
    "workspace", "telecomunicaciones", " tv", "tv ", "mueble", "organizador",
    "perchero", "zapatera", "cocina", "ollas", "sartenes", "herramienta",
    "material", "pantalla", "echo", "equipo", "digital",
]


def _normaliza(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", (texto or "").lower())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-z0-9/\- ]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _contiene(texto: str, terminos: list[str]) -> bool:
    return any(t in texto for t in terminos)


def carga_overrides(ruta: str | Path | None) -> dict[str, bool]:
    """Archivo de decisiones por UUID → {uuid: incluir(bool)}. Tolera 2 formatos."""
    if not ruta:
        return {}
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    overrides: dict[str, bool] = {}
    if isinstance(datos, list):  # formato legacy
        for item in datos:
            uuid = str(item.get("UUID", "")).upper()
            if uuid:
                overrides[uuid] = int(item.get("Decision", 0)) == 100
    elif isinstance(datos, dict):
        for uuid, valor in datos.items():
            incluir = str(valor).strip().lower() in ("100", "1", "si", "sí", "true", "incluir")
            overrides[uuid.upper()] = incluir
    return overrides


def _heuristica(registro: dict) -> tuple[str, str, str]:
    """(estatus, regla, motivo) por términos de emisor+conceptos. Orden = legacy."""
    descripciones = " | ".join(c["descripcion"] for c in registro["conceptos"])
    texto = _normaliza(f"{registro['emisor']['nombre']} {descripciones}")
    emisor = _normaliza(registro["emisor"]["nombre"])

    if _contiene(texto, TERMINOS_FINANCIEROS):
        return "NO_DEDUCIBLE", "H-03", "Gasto financiero/bancario/seguro: no estrictamente indispensable para la operación"
    if "internet" in texto and "tv" in texto:
        return "DUDOSA", "H-06", "Internet con TV: posible uso mixto personal/actividad"
    if ("total play" in emisor or "total box" in emisor) and _contiene(texto, ["internet", "infraestructura", "telecomunicaciones"]):
        return "DEDUCIBLE", "H-02", "Servicio de conectividad del inmueble operado"
    if _contiene(texto, TERMINOS_INCLUIR_CLARO):
        return "DEDUCIBLE", "H-01", "Gasto claramente relacionado con la actividad (comisión de plataforma / servicio del inmueble)"
    if _contiene(texto, TERMINOS_MARKETPLACE) or _contiene(texto, TERMINOS_DUDOSOS):
        return "DUDOSA", "H-05", "Gasto plausible para la actividad pero no claramente exclusivo"
    if _contiene(texto, TERMINOS_PERSONALES):
        return "NO_DEDUCIBLE", "H-04", "Gasto personal o no relacionado con la actividad"
    if "telecomunicaciones" in texto or "radiomovil" in emisor:
        return "DUDOSA", "H-06", "Telefonía/telecom: posible uso mixto"
    return "DUDOSA", "H-08", "Sin coincidencia con patrones conocidos: requiere tu decisión (default conservador)"


def _evalua_ingreso(registro: dict, iva_disponible: Decimal, usa_iva_pagado: bool,
                    overrides: dict[str, bool], limite_efectivo: Decimal,
                    regimen: str) -> tuple[str, str, str]:
    """(estatus, regla, motivo) para CFDI tipo I. Precedencia: overrides > forma > uso > heurística."""
    uuid = registro["uuid"]
    uso = registro["receptor"]["uso_cfdi"]

    if uuid in overrides:
        if overrides[uuid]:
            return "DEDUCIBLE", "OVERRIDE", "Decisión manual previa del usuario (persistida por UUID)"
        return "NO_DEDUCIBLE", "OVERRIDE", "Decisión manual previa del usuario (persistida por UUID)"

    # Régimen con pagos definitivos: sin deducciones ni acreditamiento (R-14).
    if regimen == "plataformas_definitivo":
        return "NO_DEDUCIBLE", "R-14", "Con pagos definitivos no hay deducciones ni IVA acreditable (LISR 113-B-a; LIVA 18-M-II)"

    # UsoCFDI con tratamiento propio.
    if uso.startswith("D"):
        return "DEDUCCION_PERSONAL", "R-22", "UsoCFDI D0x: no es gasto de la actividad; candidata a deducción personal en la ANUAL (solo si presentas anual)"
    if uso.startswith("I"):
        return "INVERSION", "R-21", "UsoCFDI I0x: inversión/activo fijo; se deduce vía depreciación, se reporta aparte (MVP no la calcula)"
    if uso == "S01":
        return "DUDOSA", "R-23", "UsoCFDI S01 (sin efectos fiscales): si el gasto es de la actividad, pide refacturar con uso correcto"

    # Reglas de forma.
    if registro["forma_pago"] == "01":
        if registro["total"] > limite_efectivo:
            return "NO_DEDUCIBLE", "R-02", f"Pagado en efectivo y total > ${limite_efectivo}: no deducible (LISR 27-III)"
        return "DUDOSA", "R-03", "Pagado en efectivo (≤ límite legal): deducible solo si es estrictamente indispensable"

    if (registro["metodo_pago"] == "PPD" or registro["forma_pago"] == "99") and iva_disponible <= 0:
        return "DIFERIDA", "R-04", "PPD sin complemento de pago en el periodo: se acredita/deduce hasta el mes en que se pague"

    if iva_disponible <= 0 and not usa_iva_pagado and registro["iva_trasladado"] <= 0:
        # Sin IVA (exento/tasa 0): puede seguir siendo deducible para ISR.
        estatus, regla, motivo = _heuristica(registro)
        return estatus, regla, motivo + " (CFDI sin IVA trasladado: solo efecto ISR)"

    return _heuristica(registro)


def clasifica(parseo: dict, anio: int, mes: int, regimen: str = "plataformas",
              overrides: dict[str, bool] | None = None,
              rfc_usuario: str = "") -> dict:
    """Clasifica los comprobantes de un periodo. Entrada: salida de parse_cfdi.parse_entrada."""
    if regimen not in REGIMENES:
        raise ValueError(f"Régimen '{regimen}' no soportado. Opciones: {REGIMENES}")
    overrides = overrides or {}
    params = parametros_deducibilidad()
    limite_efectivo = params["limite_efectivo_deducible"]

    comprobantes = parseo["comprobantes"]
    clave_periodo = f"{anio:04d}-{mes:02d}"
    del_periodo = [c for c in comprobantes if c["fecha"].startswith(clave_periodo)]

    # RFC del usuario: explícito o el receptor más frecuente (es SU buzón de recibidas).
    if not rfc_usuario:
        conteo: dict[str, int] = {}
        for c in del_periodo:
            rfc = c["receptor"]["rfc"]
            if rfc:
                conteo[rfc] = conteo.get(rfc, 0) + 1
        rfc_usuario = max(conteo, key=conteo.get) if conteo else ""

    iva_pagado = mapa_iva_pagado(comprobantes, anio, mes)
    evaluaciones: list[dict] = []
    incluidas_por_uuid: dict[str, dict] = {}

    for c in del_periodo:
        descripciones = " | ".join(x["descripcion"] for x in c["conceptos"])
        base = {
            "uuid": c["uuid"], "fecha": c["fecha"], "tipo": c["tipo"],
            "emisor_rfc": c["emisor"]["rfc"], "emisor": c["emisor"]["nombre"],
            "descripcion": descripciones, "uso_cfdi": c["receptor"]["uso_cfdi"],
            "forma_pago": c["forma_pago"], "metodo_pago": c["metodo_pago"],
            "subtotal": c["subtotal"], "total": c["total"],
            "iva_detectado": Decimal("0"), "iva_acreditable": Decimal("0"),
            "base_deducible_isr": Decimal("0"),
            "estatus": "", "regla": "", "motivo": "",
            "referencia": "reglas_deducibilidad.md",
        }

        if c["tipo"] in ("P", "N", "T"):
            base.update(estatus="EXCLUIDO_DOC", regla="R-01",
                        motivo=f"CFDI tipo {c['tipo']}: no es un gasto por sí mismo")
            evaluaciones.append(base)
            continue

        if rfc_usuario and c["receptor"]["rfc"] and c["receptor"]["rfc"] != rfc_usuario:
            base.update(estatus="NO_DEDUCIBLE", regla="R-07",
                        motivo=f"El receptor no es tu RFC ({rfc_usuario}): no es tu comprobante")
            evaluaciones.append(base)
            continue

        if c["tipo"] == "E":
            evaluaciones.append(base)  # se resuelve al final (necesita las incluidas)
            continue

        # Tipo I: IVA disponible (PPD usa el efectivamente pagado del periodo).
        es_ppd = c["metodo_pago"] == "PPD" or c["forma_pago"] == "99"
        usa_iva_pagado = False
        if es_ppd:
            iva_disp = iva_pagado.get(c["uuid"], Decimal("0"))
            usa_iva_pagado = c["uuid"] in iva_pagado
        else:
            iva_disp = c["iva_trasladado"]
        base["iva_detectado"] = iva_disp

        estatus, regla, motivo = _evalua_ingreso(
            c, iva_disp, usa_iva_pagado, overrides, limite_efectivo, regimen)
        base.update(estatus=estatus, regla=regla, motivo=motivo)

        if estatus == "DEDUCIBLE":
            base["iva_acreditable"] = iva_disp
            if es_ppd and c["iva_trasladado"] > 0:
                # Efectivamente erogado: proporción pagada del subtotal (R-11).
                proporcion = iva_disp / c["iva_trasladado"]
                base["base_deducible_isr"] = (c["subtotal"] * proporcion).quantize(Decimal("0.01"))
            else:
                base["base_deducible_isr"] = c["subtotal"] - c["descuento"]
            base["usa_iva_pagado"] = usa_iva_pagado
            incluidas_por_uuid[c["uuid"]] = base
        evaluaciones.append(base)

    # Egresos (notas de crédito): compensan facturas incluidas (R-06, lógica legacy).
    for ev, c in [(e, c) for e in evaluaciones for c in del_periodo
                  if e["uuid"] == c["uuid"] and c["tipo"] == "E" and not e["estatus"]]:
        relacionadas = [u for rel in c["relacionados"] for u in rel["uuids"]]
        relacionada_incluida = next((incluidas_por_uuid[u] for u in relacionadas
                                     if u in incluidas_por_uuid), None)
        ev["iva_detectado"] = c["iva_trasladado"]
        if relacionada_incluida is None:
            ev.update(estatus="NO_DEDUCIBLE", regla="R-06",
                      motivo="Egreso no relacionado con una factura incluida")
        elif relacionada_incluida.get("usa_iva_pagado"):
            ev.update(estatus="NO_DEDUCIBLE", regla="R-06",
                      motivo="Egreso ya reflejado en el complemento de pago del CFDI relacionado")
        else:
            ev.update(estatus="AJUSTE", regla="R-06",
                      motivo="Nota de crédito que compensa una factura incluida (resta)")
            ev["iva_acreditable"] = -c["iva_trasladado"]
            ev["base_deducible_isr"] = -(c["subtotal"] - c["descuento"])

    incluidos = [e for e in evaluaciones if e["estatus"] in ("DEDUCIBLE", "AJUSTE")]
    total_iva = sum((e["iva_acreditable"] for e in incluidos), Decimal("0"))
    total_base = sum((e["base_deducible_isr"] for e in incluidos), Decimal("0"))

    def _lista(estatus: str) -> list[dict]:
        return [e for e in evaluaciones if e["estatus"] == estatus]

    return {
        "periodo": clave_periodo,
        "regimen": regimen,
        "rfc_usuario": rfc_usuario,
        "evaluaciones": sorted(evaluaciones, key=lambda e: (e["fecha"], e["uuid"])),
        "totales": {
            "iva_acreditable": total_iva.quantize(Decimal("0.01")),
            "base_deducible_isr": total_base.quantize(Decimal("0.01")),
            "deducibles": len(_lista("DEDUCIBLE")),
            "ajustes": len(_lista("AJUSTE")),
            "no_deducibles": len(_lista("NO_DEDUCIBLE")),
            "dudosas": len(_lista("DUDOSA")),
            "diferidas": len(_lista("DIFERIDA")),
            "deducciones_personales": len(_lista("DEDUCCION_PERSONAL")),
            "inversiones": len(_lista("INVERSION")),
            "excluidos_doc": len(_lista("EXCLUIDO_DOC")),
        },
        "dudosas": _lista("DUDOSA"),
        "deducciones_personales": _lista("DEDUCCION_PERSONAL"),
        "inversiones": _lista("INVERSION"),
        "errores_parseo": parseo.get("errores", []),
    }


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"No serializable: {type(value)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clasificador de CFDI por régimen con reglas citadas")
    parser.add_argument("entrada", help="ZIP/carpeta con XMLs (o JSON ya parseado de parse_cfdi)")
    parser.add_argument("--periodo", required=True, help="Periodo AAAA-MM, ej. 2026-05")
    parser.add_argument("--regimen", default="plataformas", choices=REGIMENES)
    parser.add_argument("--overrides", help="JSON de decisiones por UUID (formato legacy o simple)")
    parser.add_argument("--rfc", default="", help="RFC del usuario (default: autodetectado)")
    parser.add_argument("-o", "--salida", help="Archivo JSON de salida (default: stdout)")
    args = parser.parse_args(argv)

    anio, mes = (int(p) for p in args.periodo.split("-"))
    parseo = parse_entrada(args.entrada)
    resultado = clasifica(parseo, anio, mes, args.regimen,
                          carga_overrides(args.overrides), args.rfc.upper())

    texto = json.dumps(resultado, ensure_ascii=False, indent=2, default=_json_default)
    if args.salida:
        ruta_completa = Path(args.salida)
        ruta_completa.write_text(texto, encoding="utf-8")
        resumen = {k: v for k, v in resultado.items() if k != "evaluaciones"}
        ruta_resumen = ruta_completa.parent / (ruta_completa.stem + "_resumen" + ruta_completa.suffix)
        ruta_resumen.write_text(
            json.dumps(resumen, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
    else:
        print(texto)

    t = resultado["totales"]
    print(
        f"[clasificador] {resultado['periodo']} ({resultado['regimen']}): "
        f"IVA acreditable {t['iva_acreditable']}, base deducible ISR {t['base_deducible_isr']} | "
        f"{t['deducibles']} deducibles, {t['ajustes']} ajustes, {t['no_deducibles']} no deducibles, "
        f"{t['dudosas']} dudosas, {t['diferidas']} diferidas, "
        f"{t['deducciones_personales']} deducciones personales, {t['inversiones']} inversiones",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

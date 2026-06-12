"""calculo_impuestos.py — Pagos mensuales (ISR/IVA) y proyección para plataformas tecnológicas y RESICO PF.

Toda cifra fiscal (tarifas, tasas, límites) se lee en tiempo de ejecución desde
skill/references/*.md vía referencias.py — el código no contiene números
fiscales (regla dura del proyecto). Cada resultado cita su fundamento.

Funciones principales (importables):
- isr_por_tarifa(base, tarifa): aplica tarifa Art. 96/152 (cuota fija + % excedente)
- calcula_isr_plataformas(historial): pago provisional Art. 106 (acumulado)
- calcula_iva_mes(...): IVA mensual del régimen de plataformas
- concilia_plataforma(...): cruza retenciones del CSV vs tasas de ley vs CFDI de retenciones
- calcula_resico_mensual(ingresos): tabla Art. 113-E
- oportunidad_definitivos(...): detector de la opción de pagos definitivos (≤ límite legal)

CLI (orquesta un mes completo de plataformas):
    python calculo_impuestos.py --clasificacion clas.json --plataforma plat.json \
        --periodo 2026-05 [--actividad hospedaje] [--historial hist.json] [-o out.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from referencias import (
    carga_tabla_resico,
    carga_tarifa_isr,
    parametros_plataformas,
)

DISCLAIMER = (
    "Esta es una herramienta de apoyo con cálculos ESTIMADOS. No constituye "
    "asesoría fiscal ni sustituye a un contador público. Valida siempre contra "
    "el prellenado del portal del SAT antes de declarar."
)

TASAS_RETENCION_ISR = {
    "hospedaje": "retencion_isr_hospedaje",
    "transporte": "retencion_isr_transporte",
    "enajenacion": "retencion_isr_enajenacion",
}


def _q2(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _peso_sat(valor: Decimal) -> int:
    """Redondeo a peso como lo captura el SAT (mitades alejándose de cero)."""
    return int(valor.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def isr_por_tarifa(base: Decimal, tarifa: list[dict]) -> dict:
    """Aplica la tarifa ISR: cuota fija + % sobre excedente del límite inferior."""
    if base <= 0:
        return {"isr": Decimal("0.00"), "renglon": None}
    for i, r in enumerate(tarifa, start=1):
        if r["limite_inferior"] <= base <= r["limite_superior"]:
            excedente = base - r["limite_inferior"]
            isr = r["cuota_fija"] + excedente * r["porcentaje"] / Decimal("100")
            return {
                "isr": _q2(isr),
                "renglon": i,
                "limite_inferior": r["limite_inferior"],
                "cuota_fija": r["cuota_fija"],
                "porcentaje": r["porcentaje"],
            }
    raise ValueError(f"Base {base} fuera de la tarifa (¿tabla incompleta?)")


def tarifa_elevada(tarifa_mensual: list[dict], meses: int) -> list[dict]:
    """Tarifa mensual elevada al periodo (Art. 106 LISR: límites y cuotas × meses)."""
    n = Decimal(meses)
    return [
        {
            "limite_inferior": r["limite_inferior"] * n,
            "limite_superior": r["limite_superior"] * n,
            "cuota_fija": r["cuota_fija"] * n,
            "porcentaje": r["porcentaje"],
        }
        for r in tarifa_mensual
    ]


def calcula_isr_plataformas(historial: list[dict]) -> dict:
    """Pago provisional ISR del régimen de plataformas SIN opción definitiva.

    historial: meses transcurridos del ejercicio EN ORDEN, cada uno:
      {"mes": 1-12, "ingresos": base sin IVA, "deducciones": autorizadas,
       "isr_retenido": por la plataforma, "pago_provisional_pagado": opcional}
    El cálculo es acumulado (Art. 106 LISR): el último elemento es el mes a declarar.
    """
    if not historial:
        raise ValueError("historial vacío")
    tarifa_mensual = carga_tarifa_isr("mensual")
    n = len(historial)
    mes_actual = historial[-1]

    ingresos_acum = sum((Decimal(str(m["ingresos"])) for m in historial), Decimal("0"))
    deducciones_acum = sum((Decimal(str(m.get("deducciones", 0))) for m in historial), Decimal("0"))
    retenciones_acum = sum((Decimal(str(m.get("isr_retenido", 0))) for m in historial), Decimal("0"))
    pagos_previos = sum(
        (Decimal(str(m.get("pago_provisional_pagado", 0))) for m in historial[:-1]), Decimal("0"))

    base = max(ingresos_acum - deducciones_acum, Decimal("0"))
    aplicacion = isr_por_tarifa(base, tarifa_elevada(tarifa_mensual, n))
    isr_causado = aplicacion["isr"]
    pago = max(isr_causado - retenciones_acum - pagos_previos, Decimal("0"))

    advertencias = []
    if n != int(mes_actual.get("mes", n)):
        advertencias.append(
            f"Se recibieron {n} meses de historial pero el mes a declarar es "
            f"{mes_actual.get('mes')}: el cálculo acumulado (Art. 106 LISR) requiere TODOS "
            "los meses desde enero. El resultado es una estimación incompleta; "
            "el prellenado del SAT trae el acumulado correcto."
        )

    return {
        "fundamento": "LISR Arts. 106 (pago provisional acumulado) y 96 (tarifa) — ver tarifas_isr.md y regimen_plataformas.md",
        "meses_acumulados": n,
        "ingresos_acumulados": _q2(ingresos_acum),
        "deducciones_acumuladas": _q2(deducciones_acum),
        "base_gravable": _q2(base),
        "renglon_tarifa": aplicacion["renglon"],
        "isr_causado_acumulado": isr_causado,
        "retenciones_acumuladas": _q2(retenciones_acum),
        "pagos_provisionales_previos": _q2(pagos_previos),
        "pago_provisional_del_mes": pago,
        "pago_provisional_del_mes_sat": _peso_sat(pago),
        "advertencias": advertencias,
    }


def calcula_iva_mes(base_gravada: Decimal, iva_acreditable: Decimal,
                    iva_retenido_plataforma: Decimal,
                    saldo_favor_anterior: Decimal = Decimal("0")) -> dict:
    """IVA mensual definitivo del régimen de plataformas (sin opción definitiva).

    IVA causado − retenido por plataforma − acreditable de gastos
    − saldo a favor del mes anterior = a cargo (o a favor).
    LIVA Arts. 1o., 4o., 5o., 6o. (saldo a favor), 18-J; RMF 2026 12.3.14.
    """
    params = parametros_plataformas()
    tasa = params["tasa_iva_general"] / Decimal("100")
    trasladado = _q2(base_gravada * tasa)
    # Cantidad a cargo antes de aplicar saldo anterior (SAT field: "Cantidad a cargo")
    cantidad_a_cargo = trasladado - iva_retenido_plataforma - iva_acreditable
    # El saldo a favor solo se aplica hasta el tope de "cantidad a cargo" (regla SAT:
    # "*Acreditamiento de saldo a favor de periodos anteriores (sin exceder de cantidad a cargo)")
    saldo_aplicable = _q2(min(saldo_favor_anterior, max(cantidad_a_cargo, Decimal("0"))))
    saldo_no_aplicado = _q2(max(saldo_favor_anterior - saldo_aplicable, Decimal("0")))
    neto = cantidad_a_cargo - saldo_aplicable
    return {
        "fundamento": "LIVA Arts. 1o. (tasa), 4o./5o. (acreditamiento), 6o. (saldo a favor), 18-J (retención 50%); RMF 2026 12.3.14 — ver regimen_plataformas.md",
        "base_gravada": _q2(base_gravada),
        "iva_trasladado": trasladado,
        "iva_retenido_plataforma": _q2(iva_retenido_plataforma),
        "iva_acreditable_gastos": _q2(iva_acreditable),
        "cantidad_a_cargo_pre_saldo": _q2(max(cantidad_a_cargo, Decimal("0"))),
        "saldo_favor_iva_anterior": _q2(saldo_favor_anterior),
        "saldo_favor_aplicado": saldo_aplicable,
        "saldo_favor_no_aplicado": saldo_no_aplicado,
        "resultado": _q2(neto),
        "a_cargo": _q2(max(neto, Decimal("0"))),
        "a_favor": _q2(max(-neto, Decimal("0"))),
        "a_cargo_sat": _peso_sat(max(neto, Decimal("0"))),
    }


def concilia_plataforma(totales_plataforma: dict, actividad: str = "hospedaje",
                        doc_retenciones: dict | None = None) -> dict:
    """Deriva la base gravable desde las retenciones del CSV y la cruza contra ley y CFDI.

    base_por_isr = ISR retenido / tasa de retención de la actividad (LISR 113-A)
    base_por_iva = IVA retenido / (tasa IVA × % retención)        (LIVA 18-J)
    Si hay CFDI de retenciones de la plataforma, se compara también su base.
    """
    params = parametros_plataformas()
    if actividad not in TASAS_RETENCION_ISR:
        raise ValueError(f"Actividad '{actividad}' no soportada: {list(TASAS_RETENCION_ISR)}")
    tasa_isr = params[TASAS_RETENCION_ISR[actividad]] / Decimal("100")
    tasa_iva_ret = (params["tasa_iva_general"] / Decimal("100")) * (
        params["retencion_iva_con_rfc"] / Decimal("100"))

    isr_ret = Decimal(str(totales_plataforma.get("isr_retenido", 0)))
    iva_ret = Decimal(str(totales_plataforma.get("iva_retenido", 0)))
    ingresos_recibidos = Decimal(str(totales_plataforma.get("ingresos_recibidos", 0)))

    advertencias = []
    base_isr = _q2(isr_ret / tasa_isr) if isr_ret > 0 else None
    base_iva = _q2(iva_ret / tasa_iva_ret) if iva_ret > 0 else None

    if base_isr is None and base_iva is None:
        advertencias.append(
            "El reporte no trae filas de retención ISR/IVA: no se puede derivar la "
            "base gravable. Se usará 'ingresos recibidos' como aproximación (es el "
            "depósito neto, NO la base; el prellenado del SAT es la fuente correcta)."
        )
        base = ingresos_recibidos
    else:
        base = base_isr if base_isr is not None else base_iva
        if base_isr is not None and base_iva is not None and abs(base_isr - base_iva) > Decimal("1"):
            advertencias.append(
                f"La base derivada del ISR retenido ({base_isr}) y la del IVA retenido "
                f"({base_iva}) difieren más de $1: revisa el reporte (¿retenciones de "
                "otro periodo, RFC no proporcionado, o estancias exentas?)."
            )

    comparacion_cfdi = None
    if doc_retenciones:
        plat = doc_retenciones.get("plataformas_tecnologicas", {})
        base_cfdi = plat.get("MonTotServSIVA") or plat.get("MontoTotServSIVA")
        if base_cfdi is not None:
            base_cfdi = Decimal(str(base_cfdi))
            comparacion_cfdi = {
                "base_cfdi_retenciones": _q2(base_cfdi),
                "isr_cfdi": str(doc_retenciones.get("isr_retenido", "")),
                "iva_cfdi": str(doc_retenciones.get("iva_retenido", "")),
                "coincide_con_csv": abs(base_cfdi - base) <= Decimal("1"),
            }
            if not comparacion_cfdi["coincide_con_csv"]:
                advertencias.append(
                    f"La base del CFDI de retenciones ({base_cfdi}) no coincide con la "
                    f"derivada del CSV ({base}): concilia ambos documentos antes de declarar."
                )

    return {
        "fundamento": "LISR 113-A (tasa de retención por actividad); LIVA 18-J (retención de IVA) — ver regimen_plataformas.md",
        "actividad": actividad,
        "isr_retenido": _q2(isr_ret),
        "iva_retenido": _q2(iva_ret),
        "ingresos_recibidos_neto": _q2(ingresos_recibidos),
        "base_por_isr": base_isr,
        "base_por_iva": base_iva,
        "base_gravable_estimada": _q2(base),
        "comparacion_cfdi_retenciones": comparacion_cfdi,
        "advertencias": advertencias,
    }


def calcula_resico_mensual(ingresos: Decimal) -> dict:
    """ISR mensual RESICO PF: tasa de la tabla del Art. 113-E sobre el TOTAL cobrado."""
    tabla = carga_tabla_resico("mensual")
    ingresos = Decimal(str(ingresos))
    if ingresos < 0:
        raise ValueError("ingresos negativos")
    for r in tabla:
        if ingresos <= r["hasta"]:
            isr = _q2(ingresos * r["tasa"] / Decimal("100"))
            return {
                "fundamento": "LISR Art. 113-E (tabla mensual; tasa sobre el total cobrado, sin deducciones) — ver regimen_resico_pf.md",
                "ingresos": _q2(ingresos),
                "tasa": r["tasa"],
                "isr_mensual": isr,
                "isr_mensual_sat": _peso_sat(isr),
            }
    raise ValueError(
        f"Ingresos {ingresos} exceden el último renglón de la tabla RESICO: el "
        "contribuyente saldría del régimen (LISR 113-E)."
    )


def oportunidad_definitivos(ingresos_acumulados: Decimal, meses: int) -> dict:
    """Detecta si conviene evaluar la opción de pagos definitivos (LISR 113-B)."""
    params = parametros_plataformas()
    limite = params["limite_pagos_definitivos"]
    proyeccion = (Decimal(str(ingresos_acumulados)) / Decimal(meses) * Decimal("12")) if meses else Decimal("0")
    aplica = proyeccion <= limite
    return {
        "fundamento": "LISR 113-B (opción si ingresos ≤ límite legal; irrevocable 5 años) — ver regimen_plataformas.md",
        "ingresos_proyectados_anual": _q2(proyeccion),
        "limite_legal": limite,
        "podria_aplicar": aplica,
        "nota": (
            "Tus ingresos proyectados quedan dentro del límite: podrías evaluar la opción "
            "de pagos definitivos (la retención sería tu pago final, sin declaraciones "
            "mensuales de ISR por plataforma, pero PIERDES deducciones y acreditamiento "
            "de IVA, y es irrevocable 5 años). Decisión importante: valídala con un contador."
            if aplica else
            "Tus ingresos proyectados exceden el límite legal: la opción de pagos "
            "definitivos no aplicaría."
        ),
    }


def _carga_json(ruta: str) -> dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"No serializable: {type(value)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cálculo mensual ISR/IVA para plataformas tecnológicas")
    parser.add_argument("--clasificacion", required=True, help="JSON de clasificador.py")
    parser.add_argument("--plataforma", required=True, help="JSON de parse_plataforma.py")
    parser.add_argument("--periodo", required=True, help="AAAA-MM")
    parser.add_argument("--actividad", default="hospedaje", choices=list(TASAS_RETENCION_ISR))
    parser.add_argument("--historial", help="JSON con meses previos del ejercicio (ver calcula_isr_plataformas)")
    parser.add_argument("--saldo_favor_iva", default="0",
                        help="Saldo a favor de IVA del mes anterior (LIVA Art. 6o), en pesos")
    parser.add_argument("-o", "--salida", help="Archivo JSON de salida (default: stdout)")
    args = parser.parse_args(argv)

    clasificacion = _carga_json(args.clasificacion)
    plataforma = _carga_json(args.plataforma)
    anio, mes = (int(p) for p in args.periodo.split("-"))

    totales_mes = plataforma.get("por_mes", {}).get(args.periodo, plataforma["totales"])
    conciliacion = concilia_plataforma(totales_mes, args.actividad)
    base_mes = conciliacion["base_gravable_estimada"]
    iva_acreditable = Decimal(str(clasificacion["totales"]["iva_acreditable"]))
    base_deducible = Decimal(str(clasificacion["totales"]["base_deducible_isr"]))
    isr_retenido_mes = conciliacion["isr_retenido"]

    advertencias = list(conciliacion["advertencias"])
    if args.historial:
        historial = _carga_json(args.historial)
        historial.append({
            "mes": mes, "ingresos": base_mes, "deducciones": base_deducible,
            "isr_retenido": isr_retenido_mes,
        })
    else:
        historial = [{"mes": mes, "ingresos": base_mes, "deducciones": base_deducible,
                      "isr_retenido": isr_retenido_mes}]
        if mes != 1:
            advertencias.append(
                "Sin historial de meses previos: el ISR se calculó como mes aislado, "
                "pero el pago provisional real es ACUMULADO desde enero (Art. 106). "
                "Proporciona el historial o toma el acumulado del prellenado del SAT."
            )

    isr = calcula_isr_plataformas(historial)
    saldo_favor_iva = Decimal(args.saldo_favor_iva)
    iva = calcula_iva_mes(base_mes, iva_acreditable, conciliacion["iva_retenido"], saldo_favor_iva)
    ingresos_acum = isr["ingresos_acumulados"]
    oportunidad = oportunidad_definitivos(ingresos_acum, len(historial))

    resultado = {
        "periodo": args.periodo,
        "regimen": clasificacion.get("regimen", "plataformas"),
        "actividad": args.actividad,
        "conciliacion": conciliacion,
        "isr": isr,
        "iva": iva,
        "oportunidad_pagos_definitivos": oportunidad,
        "dudosas_pendientes": clasificacion["totales"]["dudosas"],
        "advertencias": advertencias + isr.pop("advertencias"),
        "disclaimer": DISCLAIMER,
    }

    texto = json.dumps(resultado, ensure_ascii=False, indent=2, default=_json_default)
    if args.salida:
        Path(args.salida).write_text(texto, encoding="utf-8")
    else:
        print(texto)

    print(
        f"[calculo] {args.periodo} ({args.actividad}): base {base_mes} | "
        f"ISR del mes {isr['pago_provisional_del_mes']} (SAT: {isr['pago_provisional_del_mes_sat']}) | "
        f"IVA a cargo {iva['a_cargo']} (SAT: {iva['a_cargo_sat']}) | "
        f"{resultado['dudosas_pendientes']} dudosas sin resolver",
        file=sys.stderr,
    )
    for a in resultado["advertencias"]:
        print(f"[calculo]   aviso: {a}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

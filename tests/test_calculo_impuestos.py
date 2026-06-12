"""Tests de calculo_impuestos.py con casos numéricos derivados a mano de las tarifas oficiales."""
import json
from decimal import Decimal
from pathlib import Path

import pytest

from calculo_impuestos import (
    calcula_isr_plataformas,
    calcula_iva_mes,
    calcula_resico_mensual,
    concilia_plataforma,
    isr_por_tarifa,
    oportunidad_definitivos,
    tarifa_elevada,
)
from referencias import carga_tarifa_isr

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_isr_por_tarifa_mensual_caso_conocido():
    # Base 10,000: renglón 3 (7,168.52–12,598.02): 420.95 + (10,000−7,168.52)×10.88%
    # = 420.95 + 2,831.48×0.1088 = 420.95 + 308.07 = 729.02
    r = isr_por_tarifa(Decimal("10000"), carga_tarifa_isr("mensual"))
    assert r["renglon"] == 3
    assert r["isr"] == Decimal("729.02")


def test_isr_por_tarifa_base_cero():
    assert isr_por_tarifa(Decimal("0"), carga_tarifa_isr("mensual"))["isr"] == Decimal("0.00")


def test_tarifa_elevada_duplica_limites():
    mensual = carga_tarifa_isr("mensual")
    doble = tarifa_elevada(mensual, 2)
    assert doble[0]["limite_inferior"] == mensual[0]["limite_inferior"] * 2
    assert doble[5]["cuota_fija"] == mensual[5]["cuota_fija"] * 2
    assert doble[5]["porcentaje"] == mensual[5]["porcentaje"]


def test_calcula_isr_plataformas_acumulado_dos_meses():
    # Acumulado: ingresos 60,000 − deducciones 10,000 = base 50,000 con tarifa ×2.
    # Renglón 6 ×2 (35,067.30–70,725.66, cuota 3,713.68, 21.36%):
    # 3,713.68 + (50,000−35,067.30)×0.2136 = 3,713.68 + 3,189.62 = 6,903.30
    # − retenciones acumuladas 2,400 − pago previo 1,500 = 3,003.30
    historial = [
        {"mes": 1, "ingresos": "30000", "deducciones": "5000",
         "isr_retenido": "1200", "pago_provisional_pagado": "1500"},
        {"mes": 2, "ingresos": "30000", "deducciones": "5000", "isr_retenido": "1200"},
    ]
    r = calcula_isr_plataformas(historial)
    assert r["meses_acumulados"] == 2
    assert r["base_gravable"] == Decimal("50000.00")
    assert r["isr_causado_acumulado"] == Decimal("6903.30")
    assert r["pago_provisional_del_mes"] == Decimal("3003.30")
    assert r["pago_provisional_del_mes_sat"] == 3003
    assert r["advertencias"] == []


def test_isr_plataformas_retencion_mayor_no_da_negativo():
    historial = [{"mes": 1, "ingresos": "1000", "deducciones": "0", "isr_retenido": "500"}]
    r = calcula_isr_plataformas(historial)
    assert r["pago_provisional_del_mes"] == Decimal("0.00")


def test_calcula_iva_mes():
    r = calcula_iva_mes(Decimal("10000"), Decimal("500"), Decimal("800"))
    assert r["iva_trasladado"] == Decimal("1600.00")
    assert r["a_cargo"] == Decimal("300.00")
    assert r["a_favor"] == Decimal("0.00")
    assert r["a_cargo_sat"] == 300
    assert r["saldo_favor_iva_anterior"] == Decimal("0.00")


def test_calcula_iva_mes_con_saldo_anterior():
    # 10,000 × 16% = 1,600 − 800 ret − 200 acred = cantidad_a_cargo 600
    # saldo 300 ≤ 600 → se aplica íntegro → impuesto a cargo 300
    r = calcula_iva_mes(Decimal("10000"), Decimal("200"), Decimal("800"), Decimal("300"))
    assert r["a_cargo"] == Decimal("300.00")
    assert r["saldo_favor_aplicado"] == Decimal("300.00")
    assert r["saldo_favor_no_aplicado"] == Decimal("0.00")
    assert r["a_cargo_sat"] == 300


def test_calcula_iva_mes_saldo_tope_cantidad_a_cargo():
    # 10,000 × 16% = 1,600 − 1,000 ret − 0 acred = cantidad_a_cargo 600
    # saldo 900 > 600 → solo se aplican 600 (tope SAT) → impuesto a cargo 0, no aplicado 300
    r = calcula_iva_mes(Decimal("10000"), Decimal("0"), Decimal("1000"), Decimal("900"))
    assert r["cantidad_a_cargo_pre_saldo"] == Decimal("600.00")
    assert r["saldo_favor_aplicado"] == Decimal("600.00")
    assert r["saldo_favor_no_aplicado"] == Decimal("300.00")
    assert r["a_cargo"] == Decimal("0.00")
    assert r["a_favor"] == Decimal("0.00")


def test_calcula_iva_mes_saldo_a_favor():
    r = calcula_iva_mes(Decimal("1000"), Decimal("500"), Decimal("80"))
    # 160 − 80 − 500 = −420
    assert r["a_cargo"] == Decimal("0.00")
    assert r["a_favor"] == Decimal("420.00")


def test_conciliacion_consistente():
    # ISR 400 / 4% = 10,000 ; IVA 800 / (16%×50%) = 10,000 → sin advertencias
    r = concilia_plataforma(
        {"isr_retenido": "400", "iva_retenido": "800", "ingresos_recibidos": "9250"},
        "hospedaje",
    )
    assert r["base_por_isr"] == Decimal("10000.00")
    assert r["base_por_iva"] == Decimal("10000.00")
    assert r["base_gravable_estimada"] == Decimal("10000.00")
    assert r["advertencias"] == []


def test_conciliacion_inconsistente_avisa():
    r = concilia_plataforma(
        {"isr_retenido": "400", "iva_retenido": "900", "ingresos_recibidos": "9000"},
        "hospedaje",
    )
    assert r["base_por_iva"] == Decimal("11250.00")
    assert any("difieren" in a for a in r["advertencias"])


def test_conciliacion_contra_cfdi_retenciones():
    doc = {
        "isr_retenido": Decimal("400.00"), "iva_retenido": Decimal("800.00"),
        "plataformas_tecnologicas": {"MonTotServSIVA": "10000.00"},
    }
    r = concilia_plataforma(
        {"isr_retenido": "400", "iva_retenido": "800", "ingresos_recibidos": "9250"},
        "hospedaje", doc_retenciones=doc,
    )
    assert r["comparacion_cfdi_retenciones"]["coincide_con_csv"] is True


def test_resico_mensual():
    r = calcula_resico_mensual(Decimal("20000"))
    assert r["tasa"] == Decimal("1.00")
    assert r["isr_mensual"] == Decimal("200.00")
    r2 = calcula_resico_mensual(Decimal("60000"))
    assert r2["tasa"] == Decimal("1.50")
    assert r2["isr_mensual"] == Decimal("900.00")


def test_resico_fuera_de_tabla():
    with pytest.raises(ValueError, match="exceden"):
        calcula_resico_mensual(Decimal("4000000"))


def test_oportunidad_definitivos():
    dentro = oportunidad_definitivos(Decimal("100000"), 5)   # proyección 240,000
    assert dentro["podria_aplicar"] is True
    fuera = oportunidad_definitivos(Decimal("200000"), 5)    # proyección 480,000
    assert fuera["podria_aplicar"] is False


def test_cli_e2e_mvp(tmp_path):
    """Flujo completo con fixtures: parse → clasifica → calcula (como lo correrá el skill)."""
    import calculo_impuestos
    import clasificador
    import parse_plataforma

    clas_json = tmp_path / "clas.json"
    plat_json = tmp_path / "plat.json"
    out_json = tmp_path / "calc.json"

    clasificador.main([str(FIXTURES / "cfdis.zip"), "--periodo", "2026-05", "-o", str(clas_json)])
    parse_plataforma.main([str(FIXTURES / "airbnb_ganancias_2026-05.csv"), "-o", str(plat_json)])
    calculo_impuestos.main([
        "--clasificacion", str(clas_json), "--plataforma", str(plat_json),
        "--periodo", "2026-05", "--actividad", "hospedaje", "-o", str(out_json),
    ])

    salida = json.loads(out_json.read_text(encoding="utf-8"))
    assert salida["conciliacion"]["base_gravable_estimada"] == "10000.00"
    assert salida["iva"]["iva_trasladado"] == "1600.00"
    # IVA: 1600 − 800 retenido − 224 acreditable = 576
    assert salida["iva"]["a_cargo"] == "576.00"
    assert salida["disclaimer"]
    assert any("acumulado" in a.lower() for a in salida["advertencias"])  # mayo sin historial

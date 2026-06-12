"""Tests del cargador de referencias: las cifras fiscales DEBEN venir de los .md."""
from decimal import Decimal

from referencias import (
    carga_tabla_resico,
    carga_tarifa_isr,
    parametros_deducibilidad,
    parametros_plataformas,
)


def test_tarifa_mensual_2026():
    tarifa = carga_tarifa_isr("mensual")
    assert len(tarifa) == 11
    assert tarifa[0]["limite_inferior"] == Decimal("0.01")
    assert tarifa[0]["porcentaje"] == Decimal("1.92")
    assert tarifa[2]["cuota_fija"] == Decimal("420.95")   # renglón 3 Anexo 8 RMF 2026
    assert tarifa[10]["limite_superior"] == Decimal("Infinity")
    assert tarifa[10]["cuota_fija"] == Decimal("133488.54")
    assert tarifa[10]["porcentaje"] == Decimal("35.00")


def test_tarifa_anual_2026():
    tarifa = carga_tarifa_isr("anual")
    assert len(tarifa) == 11
    assert tarifa[0]["limite_superior"] == Decimal("10135.11")
    assert tarifa[10]["cuota_fija"] == Decimal("1601862.46")


def test_tabla_resico_mensual():
    tabla = carga_tabla_resico("mensual")
    assert len(tabla) == 5
    assert tabla[0] == {"hasta": Decimal("25000.00"), "tasa": Decimal("1.00")}
    assert tabla[4] == {"hasta": Decimal("3500000.00"), "tasa": Decimal("2.50")}


def test_parametros_plataformas():
    p = parametros_plataformas()
    assert p["retencion_isr_hospedaje"] == Decimal("4.0")      # LISR 113-A-II
    assert p["retencion_iva_con_rfc"] == Decimal("50.0")       # LIVA 18-J
    assert p["limite_pagos_definitivos"] == Decimal("300000.00")
    assert p["tasa_iva_general"] == Decimal("16.0")


def test_parametros_deducibilidad():
    p = parametros_deducibilidad()
    assert p["limite_efectivo_deducible"] == Decimal("2000.00")  # LISR 27-III

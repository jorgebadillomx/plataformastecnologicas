"""Tests de parse_plataforma.py (adaptador Airbnb) contra el CSV sintético."""
from decimal import Decimal
from pathlib import Path

import pytest

from parse_plataforma import parse_money, parse_reporte

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CSV_AIRBNB = FIXTURES / "airbnb_ganancias_2026-05.csv"


@pytest.fixture(scope="module")
def resultado():
    return parse_reporte(CSV_AIRBNB)


def test_autodeteccion_airbnb(resultado):
    assert resultado["plataforma"] == "airbnb"
    assert resultado["columnas_usadas"]["ingreso"] == "Ingresos recibidos"


def test_totales(resultado):
    t = resultado["totales"]
    assert t["ingresos_recibidos"] == Decimal("9250.00")
    assert t["isr_retenido"] == Decimal("400.00")
    assert t["iva_retenido"] == Decimal("800.00")
    assert t["filas_ingreso"] == 3
    assert t["filas_retencion"] == 2


def test_desglose_mensual(resultado):
    assert list(resultado["por_mes"].keys()) == ["2026-05"]
    mes = resultado["por_mes"]["2026-05"]
    assert mes["ingresos_recibidos"] == Decimal("9250.00")
    assert mes["isr_retenido"] == Decimal("400.00")
    assert mes["iva_retenido"] == Decimal("800.00")


def test_advertencia_fecha_ambigua(resultado):
    # 05/02/2026 es ambiguo (¿2 de mayo o 5 de febrero?): debe avisarse.
    assert any("MM/DD" in a for a in resultado["advertencias"])


def test_columnas_faltantes(tmp_path):
    malo = tmp_path / "otro.csv"
    malo.write_text("Columna1,Columna2\na,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Ning[uú]n adaptador"):
        parse_reporte(malo)


def test_plataforma_desconocida():
    with pytest.raises(ValueError, match="no soportada"):
        parse_reporte(CSV_AIRBNB, plataforma="uber")


@pytest.mark.parametrize(
    ("crudo", "esperado"),
    [
        ("$1,234.56", Decimal("1234.56")),
        ("1.234,56", Decimal("1234.56")),
        ("(123.45)", Decimal("-123.45")),
        ("-400.00", Decimal("-400.00")),
        ("", None),
        ("N/A", None),
    ],
)
def test_parse_money(crudo, esperado):
    assert parse_money(crudo) == esperado

"""Tests del clasificador contra los fixtures sintéticos."""
from decimal import Decimal
from pathlib import Path

import pytest

from clasificador import carga_overrides, clasifica
from parse_cfdi import parse_entrada

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="module")
def parseo():
    return parse_entrada(FIXTURES / "cfdis.zip")


@pytest.fixture(scope="module")
def resultado(parseo):
    return clasifica(parseo, 2026, 5, "plataformas")


def _eval(resultado, sufijo):
    for e in resultado["evaluaciones"]:
        if e["uuid"].endswith(sufijo):
            return e
    raise AssertionError(f"Sin evaluación para ...{sufijo}")


def test_rfc_usuario_autodetectado(resultado):
    assert resultado["rfc_usuario"] == "CACX7605101P8"


def test_comision_plataforma_deducible(resultado):
    e = _eval(resultado, "0001")
    assert e["estatus"] == "DEDUCIBLE"
    assert e["regla"] == "H-01"
    assert e["iva_acreditable"] == Decimal("160.00")
    assert e["base_deducible_isr"] == Decimal("1000.00")


def test_ppd_con_pago_en_periodo_deducible(resultado):
    e = _eval(resultado, "0002")
    assert e["estatus"] == "DEDUCIBLE"
    assert e["iva_acreditable"] == Decimal("80.00")   # del complemento de pago
    assert e["base_deducible_isr"] == Decimal("500.00")


def test_efectivo_mayor_a_limite_no_deducible(resultado):
    e = _eval(resultado, "0004")
    assert e["estatus"] == "NO_DEDUCIBLE"
    assert e["regla"] == "R-02"
    assert e["iva_acreditable"] == Decimal("0")


def test_colegiatura_es_deduccion_personal(resultado):
    e = _eval(resultado, "0006")
    assert e["estatus"] == "DEDUCCION_PERSONAL"
    assert e["regla"] == "R-22"


def test_egreso_compensa_factura_incluida(resultado):
    e = _eval(resultado, "0005")
    assert e["estatus"] == "AJUSTE"
    assert e["regla"] == "R-06"
    assert e["iva_acreditable"] == Decimal("-16.00")


def test_pago_excluido_como_documento(resultado):
    e = _eval(resultado, "0003")
    assert e["estatus"] == "EXCLUIDO_DOC"
    assert e["regla"] == "R-01"


def test_totales(resultado):
    t = resultado["totales"]
    # 160 (comisión) + 80 (internet PPD pagado) − 16 (nota de crédito) = 224
    assert t["iva_acreditable"] == Decimal("224.00")
    # 1000 + 500 − 100 = 1400
    assert t["base_deducible_isr"] == Decimal("1400.00")
    assert t["deducibles"] == 2
    assert t["ajustes"] == 1
    assert t["deducciones_personales"] == 1


def test_override_incluye_dudosa_o_excluida(parseo, tmp_path):
    archivo = tmp_path / "overrides.json"
    archivo.write_text(
        '[{"UUID": "aaaaaaaa-0000-4000-8000-000000000004", "Decision": 100}]',
        encoding="utf-8",
    )
    overrides = carga_overrides(archivo)
    r = clasifica(parseo, 2026, 5, "plataformas", overrides)
    e = _eval(r, "0004")
    assert e["estatus"] == "DEDUCIBLE"
    assert e["regla"] == "OVERRIDE"
    assert r["totales"]["iva_acreditable"] == Decimal("704.00")  # 224 + 480


def test_regimen_definitivo_sin_deducciones(parseo):
    r = clasifica(parseo, 2026, 5, "plataformas_definitivo")
    assert r["totales"]["iva_acreditable"] == Decimal("0.00")
    assert all(e["regla"] in ("R-14", "R-01", "R-06") for e in r["evaluaciones"])


def test_ppd_sin_pago_se_difiere():
    """Factura PPD cuyo complemento de pago cae en otro mes → DIFERIDA (R-04)."""
    cfdi_ppd = {
        "tipo_doc": "cfdi", "archivo": "x.xml", "version": "4.0",
        "uuid": "BBBBBBBB-0000-4000-8000-000000000001", "tipo": "I",
        "fecha": "2026-06-02T10:00:00", "serie": "", "folio": "",
        "moneda": "MXN", "tipo_cambio": Decimal("1"),
        "forma_pago": "99", "metodo_pago": "PPD",
        "subtotal": Decimal("500.00"), "descuento": Decimal("0"),
        "total": Decimal("580.00"),
        "emisor": {"rfc": "IXS7607092R5", "nombre": "PROVEEDOR X", "regimen_fiscal": "601"},
        "receptor": {"rfc": "CACX7605101P8", "nombre": "U", "uso_cfdi": "G03",
                     "regimen_fiscal": "625", "domicilio_fiscal": "64000"},
        "conceptos": [{"clave_prod_serv": "", "descripcion": "Mantenimiento inmueble",
                       "cantidad": Decimal("1"), "valor_unitario": Decimal("500"),
                       "importe": Decimal("500"), "descuento": Decimal("0")}],
        "iva_trasladado": Decimal("80.00"), "iva_retenido": Decimal("0"),
        "isr_retenido": Decimal("0"), "relacionados": [], "pagos": [],
    }
    parseo = {"comprobantes": [cfdi_ppd], "retenciones": [], "errores": []}
    r = clasifica(parseo, 2026, 6, "plataformas")
    e = r["evaluaciones"][0]
    assert e["estatus"] == "DIFERIDA"
    assert e["regla"] == "R-04"
    assert r["totales"]["iva_acreditable"] == Decimal("0.00")


# --- Tests de validación de periodo entre ZIP y periodo declarado ---

def _cfdi_simple(uuid_sufijo: str, fecha: str, rfc_receptor: str = "CACX7605101P8") -> dict:
    return {
        "tipo_doc": "cfdi", "archivo": "x.xml", "version": "4.0",
        "uuid": f"CCCCCCCC-0000-4000-8000-{uuid_sufijo.zfill(12)}",
        "tipo": "I", "fecha": fecha, "serie": "", "folio": "",
        "moneda": "MXN", "tipo_cambio": Decimal("1"),
        "forma_pago": "03", "metodo_pago": "PUE",
        "subtotal": Decimal("1000.00"), "descuento": Decimal("0"),
        "total": Decimal("1160.00"),
        "emisor": {"rfc": "XAXX010101000", "nombre": "Proveedor", "regimen_fiscal": "601"},
        "receptor": {"rfc": rfc_receptor, "nombre": "Yo", "uso_cfdi": "G03",
                     "regimen_fiscal": "625", "domicilio_fiscal": "01000"},
        "conceptos": [{"descripcion": "limpieza", "clave_prod_serv": "85121602",
                       "cantidad": Decimal("1"), "valor_unitario": Decimal("1000"),
                       "importe": Decimal("1000"), "descuento": Decimal("0")}],
        "iva_trasladado": Decimal("160.00"), "iva_retenido": Decimal("0"),
        "isr_retenido": Decimal("0"), "relacionados": [], "pagos": [],
    }


def test_advertencia_zip_cfdi_de_otro_mes():
    """ZIP con CFDIs de mes distinto al declarado → advertencia con meses disponibles."""
    parseo = {
        "comprobantes": [_cfdi_simple("0001", "2026-04-15T10:00:00")],
        "retenciones": [], "errores": [],
    }
    r = clasifica(parseo, 2026, 5, "plataformas")
    assert r["advertencias"], "Esperaba advertencia al pedir 2026-05 con ZIP de 2026-04"
    adv = r["advertencias"][0]
    assert "2026-05" in adv
    assert "2026-04" in adv


def test_advertencia_zip_completamente_vacio():
    """ZIP sin ningún CFDI válido → advertencia explícita."""
    parseo = {"comprobantes": [], "retenciones": [], "errores": []}
    r = clasifica(parseo, 2026, 5, "plataformas")
    assert r["advertencias"], "Esperaba advertencia con ZIP vacío"
    assert "válidos" in r["advertencias"][0].lower()


def test_sin_advertencia_cuando_hay_cfdis_del_periodo(resultado):
    """Fixture del periodo correcto → campo advertencias vacío."""
    assert resultado["advertencias"] == []

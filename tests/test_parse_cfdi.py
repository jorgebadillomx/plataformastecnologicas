"""Tests de parse_cfdi.py contra los fixtures sintéticos (tests/fixtures/cfdis.zip)."""
from decimal import Decimal
from pathlib import Path

import pytest

from parse_cfdi import mapa_iva_pagado, parse_entrada

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="module")
def resultado():
    return parse_entrada(FIXTURES / "cfdis.zip")


def _por_uuid(resultado, sufijo):
    for c in resultado["comprobantes"]:
        if c["uuid"].endswith(sufijo):
            return c
    raise AssertionError(f"No se encontró comprobante con UUID terminación {sufijo}")


def test_resumen_global(resultado):
    r = resultado["resumen"]
    assert r["comprobantes"] == 6
    assert r["docs_retenciones"] == 1
    assert r["errores"] == 1
    assert r["comprobantes_por_tipo"] == {"I": 4, "P": 1, "E": 1}


def test_xml_corrupto_se_reporta_sin_tronar(resultado):
    assert len(resultado["errores"]) == 1
    assert resultado["errores"][0]["archivo"] == "08_corrupto.xml"
    assert resultado["errores"][0]["error"]


def test_factura_pue_basica(resultado):
    c = _por_uuid(resultado, "0001")
    assert c["tipo"] == "I"
    assert c["uuid"] == "AAAAAAAA-0000-4000-8000-000000000001"  # normalizado a mayúsculas
    assert c["forma_pago"] == "03"
    assert c["metodo_pago"] == "PUE"
    assert c["emisor"]["rfc"] == "EKU9003173C9"
    assert c["receptor"]["rfc"] == "CACX7605101P8"
    assert c["receptor"]["uso_cfdi"] == "G03"
    assert c["subtotal"] == Decimal("1000.00")
    assert c["total"] == Decimal("1160.00")
    assert c["iva_trasladado"] == Decimal("160.00")
    assert "Comision" in c["conceptos"][0]["descripcion"]


def test_factura_efectivo(resultado):
    c = _por_uuid(resultado, "0004")
    assert c["forma_pago"] == "01"
    assert c["total"] == Decimal("3480.00")
    assert c["iva_trasladado"] == Decimal("480.00")


def test_colegiatura_sin_iva(resultado):
    c = _por_uuid(resultado, "0006")
    assert c["receptor"]["uso_cfdi"] == "D10"
    assert c["iva_trasladado"] == Decimal("0")


def test_egreso_con_relacionados(resultado):
    c = _por_uuid(resultado, "0005")
    assert c["tipo"] == "E"
    assert c["relacionados"][0]["tipo_relacion"] == "01"
    assert c["relacionados"][0]["uuids"] == ["AAAAAAAA-0000-4000-8000-000000000001"]
    assert c["iva_trasladado"] == Decimal("16.00")


def test_complemento_pagos(resultado):
    c = _por_uuid(resultado, "0003")
    assert c["tipo"] == "P"
    pago = c["pagos"][0]
    assert pago["fecha_pago"].startswith("2026-05-20")
    assert pago["monto"] == Decimal("580.00")
    docto = pago["doctos"][0]
    assert docto["uuid"] == "AAAAAAAA-0000-4000-8000-000000000002"
    assert docto["iva_pagado"] == Decimal("80.00")


def test_mapa_iva_pagado_resuelve_ppd(resultado):
    mapa = mapa_iva_pagado(resultado["comprobantes"], 2026, 5)
    assert mapa == {"AAAAAAAA-0000-4000-8000-000000000002": Decimal("80.00")}
    # En otro periodo el pago no cuenta.
    assert mapa_iva_pagado(resultado["comprobantes"], 2026, 4) == {}


def test_doc_retenciones_plataforma(resultado):
    ret = resultado["retenciones"][0]
    assert ret["emisor"]["rfc"] == "EKU9003173C9"
    assert ret["receptor"]["rfc"] == "CACX7605101P8"
    assert ret["periodo"] == {"mes_inicial": "05", "mes_final": "05", "ejercicio": "2026"}
    assert ret["totales"]["monto_operacion"] == Decimal("10000.00")
    assert ret["isr_retenido"] == Decimal("400.00")   # 4% hospedaje (LISR 113-A-II)
    assert ret["iva_retenido"] == Decimal("800.00")   # 50% del IVA (LIVA 18-J)
    assert ret["plataformas_tecnologicas"]["TotalISRRetenido"] == "400.00"
    assert ret["uuid"] == "AAAAAAAA-0000-4000-8000-000000000007"


def test_acepta_carpeta_ademas_de_zip():
    resultado_dir = parse_entrada(FIXTURES / "cfdi_xml")
    assert resultado_dir["resumen"]["comprobantes"] == 6
    assert resultado_dir["resumen"]["errores"] == 1

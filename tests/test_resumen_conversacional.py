"""Tests de los archivos *_resumen.json (lectura conversacional, ahorro de contexto).

Garantizan que la optimización de tokens no se pierda en cambios futuros:
- parse_cfdi -o escribe también cfdis_resumen.json SIN los arrays de comprobantes,
  pero con la lista íntegra de errores (los corruptos se reportan por nombre).
- clasificador -o escribe también clas_resumen.json SIN evaluaciones y con
  facturas compactas (solo los campos que la conversación necesita).
"""
import json
from pathlib import Path

import clasificador
import parse_cfdi
from clasificador import CAMPOS_RESUMEN_FACTURA

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ZIP = str(FIXTURES / "cfdis.zip")


def test_parse_cfdi_escribe_resumen_sin_arrays(tmp_path):
    salida = tmp_path / "cfdis.json"
    assert parse_cfdi.main([ZIP, "-o", str(salida)]) == 0

    resumen = json.loads((tmp_path / "cfdis_resumen.json").read_text(encoding="utf-8"))
    assert set(resumen) == {"fuente", "resumen", "errores"}
    # Los errores se conservan íntegros: el modelo reporta corruptos por nombre.
    assert [e["archivo"] for e in resumen["errores"]] == ["08_corrupto.xml"]
    # El completo sigue trayendo todo (lo consumen los scripts, no el modelo).
    completo = json.loads(salida.read_text(encoding="utf-8"))
    assert "comprobantes" in completo and "retenciones" in completo


def test_clasificador_escribe_resumen_compacto(tmp_path):
    salida = tmp_path / "clas.json"
    assert clasificador.main(
        [ZIP, "--periodo", "2026-05", "-o", str(salida)]) == 0

    resumen = json.loads((tmp_path / "clas_resumen.json").read_text(encoding="utf-8"))
    assert "evaluaciones" not in resumen
    assert resumen["totales"]["deducciones_personales"] == 1

    factura = resumen["deducciones_personales"][0]
    # Solo los campos conversacionales, ni uno más (referencia, estatus,
    # montos siempre-cero, etc. viven en clas.json y en el Excel).
    assert set(factura) == set(CAMPOS_RESUMEN_FACTURA)
    assert factura["fecha"] == "2026-05-03"  # sin hora
    assert factura["regla"] == "R-22"
    assert factura["uuid"]  # decisiones.json se lleva por UUID

    # El completo conserva el registro entero para generar_reporte.py.
    completo = json.loads(salida.read_text(encoding="utf-8"))
    assert "evaluaciones" in completo
    entera = completo["deducciones_personales"][0]
    assert "referencia" in entera and "estatus" in entera

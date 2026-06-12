"""referencias.py — Carga datos fiscales desde skill/references/*.md en tiempo de ejecución.

Regla dura del proyecto: el código NO contiene cifras fiscales. Tarifas, tasas y
límites viven en los archivos de referencia (con vigencia y fuente oficial) y se
parsean aquí. Actualizar un ejercicio fiscal = editar un .md, no tocar código.
"""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal
from pathlib import Path

RUTA_REFERENCIAS = Path(__file__).resolve().parent.parent / "references"


def _normaliza(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


def _lineas(nombre_md: str) -> list[str]:
    ruta = RUTA_REFERENCIAS / nombre_md
    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo de referencia {ruta}. El skill requiere la "
            "carpeta references/ junto a scripts/."
        )
    return ruta.read_text(encoding="utf-8").splitlines()


def _tabla_bajo_seccion(nombre_md: str, titulo_contiene: str) -> list[list[str]]:
    """Primera tabla markdown dentro de la sección cuyo encabezado contiene el texto."""
    lineas = _lineas(nombre_md)
    objetivo = _normaliza(titulo_contiene)
    en_seccion = False
    filas: list[list[str]] = []
    for linea in lineas:
        if linea.startswith("#"):
            if filas:
                break
            en_seccion = objetivo in _normaliza(linea)
            continue
        if not en_seccion:
            continue
        if linea.strip().startswith("|"):
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in celdas):
                continue  # separador |---|---|
            filas.append(celdas)
        elif filas:
            break  # terminó la tabla
    if not filas:
        raise ValueError(
            f"No se encontró tabla en la sección '{titulo_contiene}' de {nombre_md}"
        )
    return filas


def _decimal(celda: str) -> Decimal:
    limpio = celda.replace(",", "").replace("$", "").strip()
    if _normaliza(limpio) in ("inf", "en adelante"):
        return Decimal("Infinity")
    return Decimal(limpio)


def carga_parametros(nombre_md: str) -> dict[str, Decimal]:
    """Sección '## Parámetros' → {clave: Decimal}."""
    filas = _tabla_bajo_seccion(nombre_md, "Parámetros")
    encabezado, datos = filas[0], filas[1:]
    if _normaliza(encabezado[0]) != "clave":
        datos = filas  # tabla sin encabezado reconocible: tomar todo
    return {fila[0]: _decimal(fila[1]) for fila in datos if len(fila) >= 2}


def carga_tarifa_isr(periodo: str = "mensual") -> list[dict]:
    """Tarifa ISR PF desde tarifas_isr.md.

    periodo: "mensual" o "anual". Devuelve renglones con limite_inferior,
    limite_superior, cuota_fija y porcentaje (Decimal; superior puede ser inf).
    """
    titulo = "Tarifa MENSUAL" if periodo == "mensual" else "Tarifa ANUAL"
    filas = _tabla_bajo_seccion("tarifas_isr.md", titulo)
    renglones = []
    for fila in filas[1:]:  # salta encabezado
        renglones.append({
            "limite_inferior": _decimal(fila[0]),
            "limite_superior": _decimal(fila[1]),
            "cuota_fija": _decimal(fila[2]),
            "porcentaje": _decimal(fila[3]),
        })
    if not renglones:
        raise ValueError(f"Tarifa {periodo} vacía en tarifas_isr.md")
    return renglones


def carga_tabla_resico(periodo: str = "mensual") -> list[dict]:
    """Tabla RESICO PF (hasta → tasa) desde regimen_resico_pf.md."""
    titulo = "Tabla MENSUAL" if periodo == "mensual" else "Tabla ANUAL"
    filas = _tabla_bajo_seccion("regimen_resico_pf.md", titulo)
    return [
        {"hasta": _decimal(fila[0]), "tasa": _decimal(fila[1])}
        for fila in filas[1:]
    ]


def parametros_plataformas() -> dict[str, Decimal]:
    return carga_parametros("regimen_plataformas.md")


def parametros_deducibilidad() -> dict[str, Decimal]:
    return carga_parametros("reglas_deducibilidad.md")

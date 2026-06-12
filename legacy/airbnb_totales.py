import argparse
import csv
import os
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

def normalize_text(value: str) -> str:
    value = (value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_month(month: str) -> str:
    m = normalize_text(month).replace(" ", "_")
    if not m:
        raise ValueError("El parámetro --mes no puede estar vacío.")
    return m


def parse_money(value: object) -> Optional[Decimal]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    cleaned = raw.replace("(", "-").replace(")", "")
    cleaned = re.sub(r"[^0-9,.-]", "", cleaned)
    if not cleaned or cleaned in {"-", ".", ","}:
        return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        elif len(parts) == 2 and len(parts[1]) in (1, 2):
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def find_col(fieldnames: List[str], options: List[str]) -> Optional[str]:
    norm_map = {col: normalize_text(col) for col in fieldnames}
    for opt in options:
        opt_n = normalize_text(opt)
        for col, ncol in norm_map.items():
            if opt_n == ncol:
                return col
    for opt in options:
        opt_n = normalize_text(opt)
        for col, ncol in norm_map.items():
            if opt_n in ncol:
                return col
    return None


def summarize_csv(input_path: str, output_path: str) -> int:
    totals = {"isr": Decimal("0"), "iva": Decimal("0"), "ingreso": Decimal("0")}

    with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print("Error: el archivo CSV no contiene encabezados.")
            return 1

        fieldnames = [c.strip() for c in reader.fieldnames if c and c.strip()]

        tipo_col = find_col(fieldnames, ["Tipo"])
        monto_col = find_col(fieldnames, ["Monto", "Amount"])
        ingreso_col = find_col(fieldnames, ["Ingresos recibidos", "Ingreso", "Earnings", "Payout"])

        missing = []
        if not tipo_col:
            missing.append("Tipo")
        if not monto_col:
            missing.append("Monto")
        if not ingreso_col:
            missing.append("Ingresos recibidos")

        if missing:
            print("No se pudieron identificar todas las columnas necesarias.")
            print("Faltan:")
            for m in missing:
                print(f"- {m}")
            print("\nColumnas disponibles:")
            for col in fieldnames:
                print(f"- {col}")
            return 2

        valid_rows = 0
        for row in reader:
            if row is None or all((v is None or str(v).strip() == "") for v in row.values()):
                continue

            tipo = normalize_text(str(row.get(tipo_col) or ""))
            monto = parse_money(row.get(monto_col))
            ingreso = parse_money(row.get(ingreso_col))

            if ingreso is not None:
                totals["ingreso"] += ingreso

            if monto is None:
                continue

            if "retencion del iva en mexico" in tipo or "retencion iva" in tipo:
                totals["iva"] += abs(monto)
                valid_rows += 1
            elif "retencion del impuesto sobre la renta para mexico" in tipo or "isr" in tipo:
                totals["isr"] += abs(monto)
                valid_rows += 1

    with open(output_path, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["concepto", "total"])
        writer.writerow(["Total ISR retenido", f"{totals['isr']:.2f}"])
        writer.writerow(["Total IVA retenido", f"{totals['iva']:.2f}"])
        writer.writerow(["Ingreso total", f"{totals['ingreso']:.2f}"])

    print("Resumen calculado correctamente:")
    print(f"- Total ISR retenido: {totals['isr']:.2f}")
    print(f"- Total IVA retenido: {totals['iva']:.2f}")
    print(f"- Ingreso total: {totals['ingreso']:.2f}")
    print(f"\nArchivo de salida (sobrescribe si existe): {output_path}")
    print(f"Filas de retención detectadas: {valid_rows}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", help="Ruta completa al CSV de entrada")
    parser.add_argument("--mes", required=True, help="Mes de ejecución, por ejemplo 2026-02")
    args = parser.parse_args()

    input_path = os.path.abspath(args.csv_path)
    mes = normalize_month(args.mes)
    output_dir = os.path.dirname(input_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"airbnb_resumen_{mes}.csv")

    try:
        code = summarize_csv(input_path, output_path)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{input_path}'.")
        code = 1
    except Exception as ex:
        print(f"Error al procesar el archivo: {ex}")
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()

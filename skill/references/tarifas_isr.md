# Tarifas ISR — Personas Físicas

```
vigencia: ejercicio fiscal 2026 (01-ene-2026 a 31-dic-2026)
fuente: Anexo 8 RMF 2026, DOF 28-dic-2025 — https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rmf/anexos/Anexo-8-RMF-2026_DOF-28122025.pdf
verificado: 2026-06-11 (oficial: extraído del PDF del SAT que reproduce el DOF; cotejado al centavo contra fuente secundaria)
```

Este archivo es la fuente de verdad para `calculo_impuestos.py`. Las tablas se leen
en tiempo de ejecución: para actualizar un ejercicio fiscal se edita este archivo,
no el código. No modificar los encabezados de columna ni el formato de tabla.

## Tarifa MENSUAL 2026 (pagos provisionales — Art. 96 LISR, Anexo 8 RMF 2026 apartado B, fracc. V)

Título oficial: "Tarifa aplicable durante 2026 para el cálculo de los pagos
provisionales mensuales a que se refieren los artículos 96 de la Ley del ISR y 175
de su Reglamento, así como la regla 3.12.2."

| Límite inferior | Límite superior | Cuota fija | % sobre excedente |
|---|---|---|---|
| 0.01 | 844.59 | 0.00 | 1.92 |
| 844.60 | 7168.51 | 16.22 | 6.40 |
| 7168.52 | 12598.02 | 420.95 | 10.88 |
| 12598.03 | 14644.64 | 1011.68 | 16.00 |
| 14644.65 | 17533.64 | 1339.14 | 17.92 |
| 17533.65 | 35362.83 | 1856.84 | 21.36 |
| 35362.84 | 55736.68 | 5665.16 | 23.52 |
| 55736.69 | 106410.50 | 10457.09 | 30.00 |
| 106410.51 | 141880.66 | 25659.23 | 32.00 |
| 141880.67 | 425641.99 | 37009.69 | 34.00 |
| 425642.00 | inf | 133488.54 | 35.00 |

## Tarifa ANUAL 2026 (Art. 152 LISR, Anexo 8 RMF 2026 apartado C, fracc. II)

Declaración anual del ejercicio 2026, a presentar en abril de 2027.

| Límite inferior | Límite superior | Cuota fija | % sobre excedente |
|---|---|---|---|
| 0.01 | 10135.11 | 0.00 | 1.92 |
| 10135.12 | 86022.11 | 194.59 | 6.40 |
| 86022.12 | 151176.19 | 5051.37 | 10.88 |
| 151176.20 | 175735.66 | 12140.13 | 16.00 |
| 175735.67 | 210403.69 | 16069.64 | 17.92 |
| 210403.70 | 424353.97 | 22282.14 | 21.36 |
| 424353.98 | 668840.14 | 67981.92 | 23.52 |
| 668840.15 | 1276925.98 | 125485.07 | 30.00 |
| 1276925.99 | 1702567.97 | 307910.81 | 32.00 |
| 1702567.98 | 5107703.92 | 444116.23 | 34.00 |
| 5107703.93 | inf | 1601862.46 | 35.00 |

## Mecánica de aplicación

ISR = cuota_fija + (base_gravable − límite_inferior) × (% sobre excedente / 100),
tomando el renglón donde la base gravable cae entre límite inferior y superior.
Para pagos provisionales de actividad empresarial la tarifa mensual se "acumula"
conforme al Art. 106 LISR (tarifa elevada al número de meses del periodo).

## Notas de vigencia

- Las tarifas 2026 SÍ cambiaron respecto a 2025: actualización por inflación
  acumulada >10% (Art. 152, último párrafo LISR), factor ≈ 1.1321 (inflación
  nov-2022 a nov-2025 de 13.21%). Las tasas marginales (1.92%–35%) no cambiaron;
  solo límites y cuotas fijas. El factor exacto 1.1321 está verificado solo con
  fuentes secundarias consistentes; las cifras de las tablas son oficiales.
- La tarifa anual del ejercicio 2025 (declaración presentada en abril 2026) es
  distinta (primer renglón termina en 8,952.49) y consta en el mismo Anexo 8 RMF
  2026, apartado C, fracc. I. No se transcribe aquí; si se necesita soportar el
  ejercicio 2025: PENDIENTE_VERIFICAR (transcribir del mismo PDF oficial).

# ETAPA 1 — Validación de parsers contra datos reales (anonimizado)

Fecha: 2026-06-11. Los parsers se corrieron localmente contra los archivos
reales de 4 meses (Enero–Abril 2026) en `C:\Declaraciones\` (fuera del repo,
regla del proyecto: jamás datos reales en el repo). Aquí solo hallazgos
estructurales sin RFCs ni montos identificables.

## Resultados

| Validación | Resultado |
|---|---|
| 173 CFDI reales parseados (4 ZIPs) | 0 errores |
| Versión CFDI | 100% 4.0 |
| IVA por UUID vs snapshots del flujo legacy (123 facturas tipo I) | 0 diferencias, 0 faltantes, 0 sobrantes (incluye lógica PPD → complemento de pago) |
| CSV Airbnb 4 meses (detección de columnas y totales ISR/IVA/ingresos) | idénticos al resumen del flujo legacy en los 3 meses con resumen disponible |
| Desglose mensual del CSV | cada archivo cae en exactamente 1 mes (la asunción MM/DD/AAAA de Airbnb se sostiene) |

## Hallazgos estructurales (alimentan Etapa 2)

1. **Tipos presentes en ZIPs reales**: I, P, E y también **N (nómina, 2/mes)**.
   El usuario real tiene CFDIs de nómina → ingresos mixtos sueldos+plataforma.
   Relevante: compatible con 113-B (sueldos+intereses) y para fase 2 (anual con
   sueldos). El clasificador debe excluir N sin marcarlo como error (R-01 ya lo
   cubre).
2. **Formas de pago observadas**: 01, 03, 04, 15, 31, 99 → el clasificador debe
   manejar 04 (tarjeta de crédito), 15 (condonación) y 31 (intermediarios), no
   solo 01/03/99.
3. **UsoCFDI observados**: G01, G02, G03, S01, CN01, CP01, D01, D05, D09 y
   **I04 (inversión, abril)** → confirma la necesidad de R-21 (inversiones se
   reportan aparte) y R-22 (D0x → candidatas a deducción personal: el usuario
   real tiene D01 médicos, D05 hipoteca, D09 retiro).
4. **Los ZIPs NO contienen el CFDI de retenciones de Airbnb** (0 docs de
   retenciones en 4 meses). La conciliación retenciones debe funcionar
   CSV-only, y el CFDI de retenciones queda como entrada OPCIONAL (el skill
   debe explicar al usuario cómo descargarlo del portal SAT — sección
   "retenciones" — para una conciliación más fuerte).
5. La semántica del legacy `IvaDetectado` (PPD → IVA del complemento de pago
   del periodo; resto → IVA trasladado) quedó replicada exactamente en
   `parse_cfdi.mapa_iva_pagado()` + `iva_trasladado`.

# ETAPA 2 — Validación del clasificador contra declaraciones reales

Fecha: 2026-06-11. `clasificador.py` (con los overrides legacy del usuario)
contra los snapshots de 4 declaraciones ya presentadas:

| Mes | IVA acreditable legacy | IVA acreditable nuevo | Diferencia | Facturas incluidas |
|---|---|---|---|---|
| Enero 2026 | 1625.11 | 1625.11 | 0.00 | conjuntos idénticos |
| Febrero 2026 | 461.60 | 461.60 | 0.00 | conjuntos idénticos |
| Marzo 2026 | 81.37 | 81.37 | 0.00 | conjuntos idénticos |
| Abril 2026 | 145.87 | 145.87 | 0.00 | conjuntos idénticos |

Valor nuevo detectado que el flujo legacy ignoraba:
- Deducciones personales (D01 médicos, D05 hipoteca, D09 retiro): 3/3/1/2
  CFDIs por mes → candidatas para la declaración ANUAL.
- Inversiones (I04): 1 CFDI en abril → reportada aparte (sin depreciación en MVP).

Nota de diseño pendiente de decidir en Etapa 3: el default conservador H-08
marca DUDOSA lo que el legacy auto-excluía (16–21 por mes). No afecta totales
(excluido en ambos flujos si el usuario no decide), pero el skill NO debe
preguntar una por una las 20: debe presentar solo las plausibles (H-05/H-06) y
listar las H-08 en el reporte como "revisables".

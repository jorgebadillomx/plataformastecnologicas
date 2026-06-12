# ETAPA 0 — Log de investigación y verificación fiscal

Fecha: 2026-06-11. Investigación hecha con 4 agentes en paralelo contra fuentes
primarias (texto extraído de los PDF oficiales). Este archivo es contexto de
trabajo del repo (NO se empaqueta en `skill/`). Los datos operativos viven en
`skill/references/*.md`; aquí queda el detalle de verificación, fuentes y
decisiones abiertas.

## Fuentes primarias usadas (todas leídas el 2026-06-11)

| Documento | URL |
|---|---|
| LISR vigente (última reforma DOF 01-abr-2024; SIN reformas 2025-2026) | https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf |
| Historial reformas LISR | https://www.diputados.gob.mx/LeyesBiblio/ref/lisr.htm |
| LIVA vigente (última reforma DOF 12-nov-2021) | https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf |
| LIF 2026 (DOF 07-nov-2025) — Art. 25 fraccs. VI y IX | https://www.diputados.gob.mx/LeyesBiblio/pdf/LIF_2026.pdf |
| RMF 2026 (DOF 28-dic-2025) | https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rmf/rmf/RMF_2026-DOF-28122025.pdf |
| Anexo 8 RMF 2026 (tarifas ISR, DOF 28-dic-2025) | https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rmf/anexos/Anexo-8-RMF-2026_DOF-28122025.pdf |
| UMA 2026 (DOF 09-ene-2026) | https://www.dof.gob.mx/nota_detalle.php?codigo=5778072&fecha=09/01/2026 |
| UMA 2025 (INEGI 1/25) | https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/uma/uma2025.pdf |
| RLISR (Art. 264, lentes/médicos) | https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LISR_060516.pdf |
| Decreto colegiaturas (DOF 26-dic-2013) | https://www.dof.gob.mx/nota_detalle.php?codigo=5328028&fecha=26/12/2013 |
| Decreto desindexación salario mínimo→UMA (DOF 27-ene-2016) | https://www.dof.gob.mx/nota_detalle.php?codigo=5423663&fecha=27/01/2016 |
| Decreto reforma CFF 30-B (DOF 07-nov-2025) | https://www.dof.gob.mx/nota_detalle.php?codigo=5772358&fecha=07/11/2025 |

Respaldo local: un agente dejó los PDF descargados en
`C:\Users\jorge\AppData\Local\Temp\fiscal2026\` (LISR, LIVA, LIF2026, RMF2026) —
carpeta temporal, copiar a otro lado si se quieren conservar.

## Hallazgos clave (resumen ejecutivo)

1. **Tarifas ISR 2026 actualizadas por inflación** (factor ≈1.1321, primera
   actualización desde 2023; detonada por inflación acumulada >10%, Art. 152
   último párrafo). Tablas mensual y anual 2026 transcritas al centavo desde el
   Anexo 8 → `skill/references/tarifas_isr.md`.
2. **Plataformas 2026 — retenciones ISR**: hospedaje 4% (sin cambio), transporte
   2.1% (sin cambio), enajenación/servicios genéricos **2.5% solo 2026 vía LIF
   Art. 25-VI** (el texto de LISR sigue diciendo 1%; revisar cada año). Sin RFC:
   20% (113-C). → `regimen_plataformas.md`.
3. **IVA plataformas**: retención 50% con RFC / 100% sin RFC; **nuevo 2026: 100%
   si los cobros se depositan en cuenta bancaria en el extranjero** (LIF Art.
   25-IX-c, RMF 12.2.10) — relevante para anfitriones que cobran en cuenta
   extranjera; aplicación operativa a PF con RFC: PENDIENTE_VERIFICAR.
4. **Airbnb NO puede tributar en RESICO** por ingresos de plataforma: el régimen
   113-A es obligatorio y la RMF 2026 regla 3.13.3 lo hace incompatible (y
   contamina el resto de actividades empresariales). Decisión de producto: el
   skill detecta la mezcla y lo explica. → `regimen_resico_pf.md`.
5. **RESICO PF**: tablas 1.00%–2.50% (mensual y anual) en ley, sin actualización
   inflacionaria; límite $3.5M; retención PM 1.25% (113-J); **regla 3.13.7 RMF
   2026 hace el pago mensual definitivo y releva de la anual**; sin deducciones;
   IVA normal 16% con acreditamiento condicionado a deducibilidad ISR (3.13.18).
6. **Pagos definitivos plataformas** (113-B / 18-L, 18-M): tope $300,000 del
   ejercicio anterior, compatible solo con sueldos+intereses, aviso ficha 4/PLT
   en 30 días, irrevocable 5 años, sin deducciones ni anual; cobros directos con
   IVA al 8% (18-M) y tasas 113-A como definitivo (RMF 12.3.7/12.3.8/12.3.15).
7. **UMA 2026**: 117.31 / 3,566.22 / 42,794.64 (vigente 01-feb-2026). UMA 2025:
   113.14 / 3,439.46 / 41,273.52. → `uma.md`.
8. **Deducciones personales**: tope global min(5 UMA anuales, 15% ingresos);
   fuera del tope: retiro (151-V), discapacidad y colegiaturas; donativos dentro
   del tope desde 2022; lentes $2,500/persona (RLISR 264); colegiaturas con
   montos 2013 sin actualizar; hipoteca ≤750,000 UDIS. Aplican a plataformas SIN
   opción definitiva; NO aplican a RESICO ni a definitivos. →
   `deducciones_personales.md`.
9. **Deducibilidad de forma**: efectivo >$2,000 no deducible (LISR 27-III, vía
   105); efectivamente erogado (105-I); PPD solo con complemento de pago; IVA
   acreditable solo si el gasto es deducible ISR. → `reglas_deducibilidad.md`.
10. **CFDI de la plataforma**: "CFDI de Retenciones e información de pagos" con
    Complemento de Servicios Plataformas Tecnológicas, mensual, dentro de los 5
    días tras el cierre de mes (113-C-II, 18-J-II-c, RMF 12.2.2) — este es el
    documento contra el que se concilia el reporte de ganancias de Airbnb.
11. **CFF 30-B (vigor 01-abr-2026)**: SAT con acceso en línea/tiempo real a info
    de plataformas y facultad de bloqueo. Contexto de mercado: el SAT va a tener
    más visibilidad → más fiscalización → más demanda del skill.

## PENDIENTE_VERIFICAR (inventario completo)

| # | Pendiente | Dónde está marcado | Impacto |
|---|---|---|---|
| 1 | Aplicación práctica del 100% IVA por depósito en cuenta extranjera a PF con RFC (hospedaje) | regimen_plataformas.md | Medio: afecta a anfitriones que cobran en cuenta US |
| 2 | Detalle fino del cálculo de provisionales ISR con deducciones en el aplicativo prellenado (mecánica estándar Cap. II, no regulada expresa en Sección III) | regimen_plataformas.md | Bajo: la mecánica general es consistente en fuentes |
| 3 | Posibles Resoluciones de Modificaciones a la RMF 2026 posteriores al 28-dic-2025 | regimen_plataformas.md | Monitorear minisitio SAT |
| 4 | Convención del aplicativo SAT para tope 151-V retiro (UMA anual INEGI vs diaria×365, dif. ~$113–118) | deducciones_personales.md | Mínimo |
| 5 | Tarifa anual ejercicio 2025 (si se decide soportar la anual 2025) | tarifas_isr.md | Decisión de alcance |
| 6 | Rutas y campos exactos del portal SAT 2026 (se hace en Etapa 3) | paso_a_paso_portal_sat.md | Alto para Etapa 3 |
| 7 | Código de nota DOF exacto de los Anexos del 28-dic-2025 (la fecha está confirmada en el documento mismo) | tarifas_isr.md (nota) | Cosmético |
| 8 | % de depreciación de inversiones (LISR 33–35) si fase 1 calcula activo fijo | reglas_deducibilidad.md | Decisión de alcance |
| 9 | Criterio de proporcionalidad para gastos de uso mixto (anfitrión que habita el inmueble) | reglas_deducibilidad.md | Decisión de producto (ver abajo) |

## Decisiones de producto (validadas por Jorge el 2026-06-11)

1. **Gastos de uso mixto**: en MVP siempre se marcan DUDOSA y el usuario decide
   (con texto explicativo); prorrateo por % en fase 2.
2. **Ejercicio soportado**: SOLO 2026 en MVP. La tabla anual 2025 se agrega
   después si se necesita (mismo PDF del Anexo 8).
3. **Inversiones (UsoCFDI I0x)**: se reportan sin calcular depreciación.
4. **Detector de oportunidad**: si los ingresos proyectados ≤ $300k, el reporte
   señala que existe la opción de pagos definitivos (con disclaimer reforzado).
5. **Alcance Etapa 1**: flujo Airbnb puro. Caso de uso real de Jorge: descarga
   el CSV de rentas del mes de Airbnb + el ZIP de facturas del SAT; el skill
   cruza ambos y entrega los valores a capturar en el SAT. El flujo actual de
   `legacy/` es la base y se puede mejorar.
6. **Dudosas (decidido 2026-06-11)**: el skill PREGUNTA al usuario al inicio
   del flujo de revisión si quiere decidir TODAS las dudosas (incluidas las
   H-08 default) o solo las plausibles (H-05/H-06); las no revisadas van al
   reporte como "excluidas por default, revisables". Nunca se resuelven solas.

## Activos heredados de `legacy/` (lógica a portar en Etapas 1-2)

- `cfdi_airbnb_iva.ps1`: parser CFDI 4.0 namespace-agnóstico, mapa de IVA pagado
  desde complementos P (DoctoRelacionado/ImpuestosDR), clasificación
  Include/Exclude/Doubtful con términos normalizados, overrides persistentes por
  UUID, notas de crédito (tipo E) como ajuste negativo si se relacionan con
  factura incluida, snapshots con diff entre corridas, redondeo SAT
  (AwayFromZero). Todo esto se porta a `parse_cfdi.py` + `clasificador.py`.
- `airbnb_totales.py`: parser tolerante de CSV de Airbnb; columnas reales del
  reporte: "Tipo", "Monto", "Ingresos recibidos"; tipos de fila de retención:
  "Retención del IVA en México", "Retención del impuesto sobre la renta para
  México"; parse_money que tolera formatos con coma/punto/paréntesis. Se porta a
  `parse_plataforma.py` (adaptador Airbnb).

# Reglas de deducibilidad y acreditamiento — clasificador de CFDI

```
vigencia: ejercicio fiscal 2026
fuente: LISR Arts. 27, 103, 105, 147 — https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf
        LIVA Arts. 4o., 5o. — https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf
        RMF 2026 regla 3.13.18 — https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rmf/rmf/RMF_2026-DOF-28122025.pdf
verificado: 2026-06-11 (reglas legales: oficial/secundarias consistentes según se indica; heurísticas: criterio propio del skill, marcadas como tales)
```

Este archivo es la fuente de verdad de `clasificador.py`. Cada regla tiene un ID
estable (R-xx / H-xx) que el clasificador cita en cada veredicto. Las reglas R
son legales (con fundamento); las H son heurísticas de clasificación del skill
(criterio operativo, siempre degradan a "dudosa", nunca deciden solas una
inclusión automática salvo que se indique).

Veredictos posibles: DEDUCIBLE / NO_DEDUCIBLE / DUDOSA (requiere decisión del
usuario; se persiste por UUID para no volver a preguntar).

## Parámetros (machine-readable — los scripts los leen en tiempo de ejecución; no cambiar claves ni formato)

| clave | valor | unidad | fundamento |
|---|---|---|---|
| limite_efectivo_deducible | 2000.00 | MXN | LISR 27 fracc. III (vía 105/147) |
| tasa_iva_general | 16.0 | % | LIVA Art. 1o. |

## Bloque 1 — Reglas duras de forma (descalifican sin importar el concepto)

| ID | Regla | Veredicto | Fundamento |
|---|---|---|---|
| R-01 | CFDI tipo P (pago) o N (nómina) no es gasto por sí mismo; tipo P solo alimenta el IVA pagado de facturas PPD relacionadas | excluir del listado de gastos | CFDI 4.0 Anexo 20 |
| R-02 | Forma de pago 01 (efectivo) con total > $2,000.00 | NO_DEDUCIBLE (ISR) y SIN IVA acreditable | LISR 27-III (aplicable a PF por remisión de 105/147); verificado con fuentes secundarias consistentes + página SAT |
| R-03 | Forma de pago 01 (efectivo) con total ≤ $2,000.00 | DUDOSA (deducible en ISR solo si es estrictamente indispensable; combustibles NUNCA en efectivo) | LISR 27-III |
| R-04 | Método PPD o forma 99 sin complemento de pago (CFDI tipo P) que lo cubra en el periodo | NO acreditable/deducible EN ESE PERIODO (efectivamente erogado: se difiere al mes del pago) | LISR 105 (efectivamente erogadas); LIVA 5o.-III (IVA efectivamente pagado) |
| R-05 | Método PPD cubierto por complemento de pago en el periodo | considerar SOLO el IVA/importe del DoctoRelacionado pagado en el periodo | LIVA 5o.; mecánica del complemento de pagos |
| R-06 | CFDI tipo E (egreso/nota de crédito) relacionado con una factura incluida | resta (ajuste negativo) | Anexo 20; simetría del acreditamiento |
| R-07 | Receptor ≠ RFC del usuario | NO_DEDUCIBLE (no es su comprobante) | LISR 27-I/105 |
| R-08 | CFDI cancelado (si el usuario aporta lista de vigencia o el ZIP trae solo vigentes se asume vigente) | NO_DEDUCIBLE | CFF 29-A |
| R-09 | Moneda extranjera | DUDOSA (requiere tipo de cambio del CFDI; revisar) | criterio operativo |

## Bloque 2 — Requisitos de fondo (ISR)

| ID | Regla | Fundamento |
|---|---|---|
| R-10 | El gasto debe ser ESTRICTAMENTE INDISPENSABLE para la actividad (hospedaje/transporte/venta según el caso) | LISR 27-I, 105-II |
| R-11 | Efectivamente erogado en el ejercicio (PF acumula por flujo) | LISR 105-I |
| R-12 | Amparado con CFDI vigente con RFC del usuario como receptor | LISR 27-III, CFF 29/29-A |
| R-13 | IVA acreditable solo si el gasto es deducible para ISR (aplica también en RESICO aunque RESICO no deduzca) | LIVA 5o.-I; RMF 2026 3.13.18 |
| R-14 | En plataformas con pagos DEFINITIVOS: NO hay deducciones ni IVA acreditable — el clasificador solo concilia retenciones | LISR 113-B-a; LIVA 18-M-II |
| R-15 | En RESICO: NO hay deducciones de ISR; el clasificador solo evalúa IVA acreditable (vía R-13) | LISR 113-E/113-F |

## Bloque 3 — UsoCFDI (señal, no veredicto único)

| ID | Regla | Efecto |
|---|---|---|
| R-20 | UsoCFDI G01 (adquisición de mercancías), G02 (devoluciones), G03 (gastos en general) con concepto relacionado con la actividad | señal a favor de DEDUCIBLE |
| R-21 | UsoCFDI I01–I08 (inversiones/activo fijo) | DUDOSA: deducible vía depreciación (% máximos LISR Arts. 33–35), no como gasto directo; fase 1 lo reporta como "inversión — consultar tratamiento" |
| R-22 | UsoCFDI D01–D10 | NO es gasto de la actividad: candidata a DEDUCCIÓN PERSONAL en la anual (ver `deducciones_personales.md`); solo si el régimen presenta anual |
| R-23 | UsoCFDI S01 (sin efectos fiscales) | señal fuerte en contra; DUDOSA si el concepto parece claramente de la actividad (el uso incorrecto puede corregirse refacturando) |
| R-24 | UsoCFDI CP01 (pagos) / CN01 (nómina) | excluir (va con R-01) |

## Bloque 4 — Heurísticas por concepto/emisor (criterio del skill, heredadas del flujo validado del autor; H-xx siempre citan este archivo)

| ID | Patrón (texto normalizado de emisor + conceptos) | Veredicto sugerido |
|---|---|---|
| H-01 | comisiones/servicios de la PLATAFORMA (Airbnb, Uber, etc.) | DEDUCIBLE (gasto directo de la actividad) |
| H-02 | servicios del inmueble en hospedaje: luz, agua, gas, internet, limpieza, mantenimiento, reparación, insumos de operación, aromatizantes | DEDUCIBLE si el domicilio coincide con el inmueble operado; DUDOSA si no es verificable |
| H-03 | financieros: bancos, casas de bolsa, intereses, seguros (no del inmueble), créditos, comisiones bancarias | NO_DEDUCIBLE (no estrictamente indispensable para la operación) |
| H-04 | claramente personales: colegiaturas*, médicos*, ropa, supermercado, farmacia (* pueden ser deducción personal: aplicar R-22) | NO_DEDUCIBLE como gasto de actividad |
| H-05 | marketplaces genéricos (Amazon, Mercado Libre, Walmart, Costco…): mobiliario, blancos, cocina, herramientas, pantallas, equipo | DUDOSA (plausible para el inmueble pero no exclusivo; preguntar y persistir decisión por UUID) |
| H-06 | internet + TV residencial, telefonía celular | DUDOSA (uso mixto personal/actividad) |
| H-07 | combustible pagado con medio electrónico, vehículo usado en la actividad (transporte/entrega) | DEDUCIBLE para transporte; DUDOSA para hospedaje |
| H-08 | sin coincidencia con ningún patrón | DUDOSA (default conservador: nunca incluir automáticamente lo desconocido) |

Regla de precedencia: Bloque 1 (forma) > overrides del usuario por UUID >
Bloque 3 (UsoCFDI) > Bloque 4 (heurísticas). Toda DUDOSA resuelta por el usuario
se persiste por UUID con fecha y motivo.

## Pendientes

- PENDIENTE_VERIFICAR: tratamiento fino de inversiones (R-21) — porcentajes de
  depreciación por tipo de bien (LISR 33-35) se documentarán si fase 1 lo
  requiere; por ahora el skill las reporta sin calcular depreciación.
- PENDIENTE_VERIFICAR: proporcionalidad de gastos de uso mixto (p. ej. % del
  inmueble destinado a hospedaje cuando el anfitrión vive ahí) — criterio no
  resuelto; el skill lo expone como decisión del usuario con advertencia.

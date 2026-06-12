# Régimen de Plataformas Tecnológicas — Personas Físicas (Sección III, Cap. II, Título IV LISR)

```
vigencia: ejercicio fiscal 2026
fuente: LISR Arts. 113-A a 113-D — https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf
        LIVA Arts. 18-B a 18-M — https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf
        LIF 2026 Art. 25, fraccs. VI y IX (DOF 07-nov-2025) — https://www.diputados.gob.mx/LeyesBiblio/pdf/LIF_2026.pdf
        RMF 2026 Título 12 (DOF 28-dic-2025) — https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rmf/rmf/RMF_2026-DOF-28122025.pdf
verificado: 2026-06-11 (oficial: texto literal de ley, LIF y RMF)
```

## Parámetros (machine-readable — los scripts los leen en tiempo de ejecución; no cambiar claves ni formato)

| clave | valor | unidad | fundamento |
|---|---|---|---|
| tasa_iva_general | 16.0 | % | LIVA Art. 1o. |
| retencion_isr_hospedaje | 4.0 | % | LISR 113-A fracc. II |
| retencion_isr_transporte | 2.1 | % | LISR 113-A fracc. I |
| retencion_isr_enajenacion | 2.5 | % | LIF 2026 Art. 25 fracc. VI (solo 2026; texto LISR: 1%) |
| retencion_isr_sin_rfc | 20.0 | % | LISR 113-C fracc. IV |
| retencion_iva_con_rfc | 50.0 | % del IVA | LIVA 18-J fracc. II inciso a |
| retencion_iva_sin_rfc | 100.0 | % del IVA | LIVA 18-J fracc. II inciso a |
| limite_pagos_definitivos | 300000.00 | MXN/año | LISR 113-B fracc. I |
| iva_cobros_directos_definitivo | 8.0 | % | LIVA 18-M segundo párrafo |

## ¿Quién tributa aquí? (Art. 113-A, primer párrafo)

OBLIGATORIO (no opcional) para personas físicas con actividades empresariales que
enajenen bienes o presten servicios a través de Internet mediante plataformas
tecnológicas, aplicaciones informáticas y similares. Incluye expresamente
servicios de hospedaje (Airbnb), transporte terrestre de pasajeros y entrega de
bienes (Uber, Didi, Rappi), y enajenación de bienes (Mercado Libre, Amazon).

INCOMPATIBLE con RESICO PF: quien está obligado por el 113-A no puede tributar en
RESICO por esos ingresos, y la opción RESICO debe ejercerse por la totalidad de
actividades (RMF 2026 regla 3.13.3). Ver `regimen_resico_pf.md`.

## Tasas de retención de ISR (Art. 113-A, tercer párrafo; tasa única sobre ingresos efectivamente percibidos vía plataforma, SIN IVA)

| Actividad | Tasa 2026 | Fundamento |
|---|---|---|
| Transporte terrestre de pasajeros y entrega de bienes | 2.1% | LISR 113-A fracc. I |
| Servicios de hospedaje (Airbnb) | 4.0% | LISR 113-A fracc. II |
| Enajenación de bienes y prestación de servicios (demás) | 2.5% | LIF 2026 Art. 25 fracc. VI (sustituye el 1% del texto de LISR 113-A fracc. III, SOLO ejercicio 2026) |
| Usuario que NO proporciona RFC a la plataforma | 20% | LISR 113-C fracc. IV, segundo párrafo |

OJO renovación anual: la tasa del 2.5% (fracc. III) vive en la Ley de Ingresos
2026; si la LIF 2027 no la repite, regresa al 1% de ley. Revisar cada ejercicio.
Hospedaje (4%) y transporte (2.1%) no fueron tocados por la LIF 2026.

Base de retención: total de ingresos efectivamente percibidos vía la plataforma,
sin incluir IVA; incluye lo que la propia plataforma pague al contribuyente y
excluye cobros directos al cliente (RMF 2026 regla 12.2.5).

## Retención de IVA por la plataforma (LIVA 18-J, fracc. II, inciso a)

| Caso | Retención |
|---|---|
| El usuario proporcionó RFC a la plataforma | 50% del IVA cobrado (8 de los 16 puntos) |
| Sin RFC | 100% del IVA cobrado |
| NUEVO 2026: cobros depositados en cuentas bancarias en el extranjero | 100% del IVA cobrado (LIF 2026 Art. 25 fracc. IX inciso c; RMF 12.2.10). Aplicación operativa exacta a PF con RFC: PENDIENTE_VERIFICAR (criterio nuevo sin guía SAT específica) |

El hospedaje tipo Airbnb SÍ causa IVA 16%: la exención de casa habitación NO
aplica a inmuebles amueblados ni destinados a hospedaje (LIVA Art. 20, fracc. II).

## Opción de PAGOS DEFINITIVOS (LISR 113-B; LIVA 18-L y 18-M)

- Requisito: ingresos del ejercicio inmediato anterior ≤ $300,000.00 (cifra de
  ley, no se actualiza por inflación). Compatible únicamente con ingresos
  adicionales por sueldos y salarios (Cap. I) e intereses (Cap. VI).
- Aviso al SAT dentro de los 30 días siguientes al primer ingreso: ficha de
  trámite 4/PLT (RMF 2026 regla 12.3.3).
- Irrevocable durante 5 años; si dejan de cumplirse los supuestos, cesa y NO
  puede volver a ejercerse.
- Consecuencias: la retención es pago definitivo; NO hay deducciones de la
  actividad (113-B inciso a) ni deducciones personales por esos ingresos
  (Art. 152: el cálculo anual no aplica a ingresos con pago definitivo); en IVA
  no hay acreditamiento (18-M fracc. II); se debe conservar el CFDI de
  retenciones; no se presenta declaración anual por esos ingresos.
- Cobros directos (parte cobrada fuera de la plataforma) con total anual ≤
  $300,000: puede aplicarse a esos cobros la tasa del 113-A como pago definitivo
  de ISR y 8% de IVA (LISR 113-A último párrafo; LIVA 18-M segundo párrafo; RMF
  2026 reglas 12.3.7, 12.3.8 y 12.3.15), declarando a más tardar el día 17 del
  mes siguiente.

## Si NO se opta por definitivos (esquema general)

- ISR: la retención tiene carácter de PAGO PROVISIONAL acreditable (113-A,
  tercer párrafo). El contribuyente presenta pagos provisionales mensuales
  ("Declaración de pago del ISR personas físicas plataformas tecnológicas", día
  17 del mes siguiente, RMF 2026 regla 12.3.13). Mecánica: ingresos acumulables
  menos deducciones autorizadas, tarifa del Art. 96 acumulada conforme al Art.
  106 (ver `tarifas_isr.md`), menos retenciones. Los ingresos van a la
  declaración anual (tarifa Art. 152) donde SÍ aplican deducciones personales
  (ver `deducciones_personales.md`). Nota: el detalle fino del cálculo con
  deducciones dentro del aplicativo prellenado del SAT deriva de la mecánica
  general del Cap. II (la Sección III no lo regula expresamente); confianza
  media-alta.
- IVA: pago mensual DEFINITIVO normal (LIVA 5o.-D) vía "Declaración de pago del
  IVA personas físicas plataformas tecnológicas" (RMF 2026 regla 12.3.14):
  traslada 16%, acredita el IVA de gastos conforme a reglas generales (LIVA 4o.
  y 5o.; ver `reglas_deducibilidad.md`) y resta el IVA retenido por la
  plataforma (50%).

## Documentos que el usuario recibe de la plataforma

- "CFDI de Retenciones e información de pagos" con el Complemento de Servicios
  Plataformas Tecnológicas: monto pagado + ISR e IVA retenidos. La plataforma
  debe emitirlo dentro de los 5 días siguientes al cierre del mes (LISR 113-C
  fracc. II; LIVA 18-J fracc. II inciso c; RMF 2026 regla 12.2.2). En la
  práctica: un CFDI mensual.
- CFDI por la comisión/servicio de intermediación que la plataforma cobra al
  anfitrión (gasto potencialmente deducible y con IVA acreditable).
- La plataforma reporta al SAT la dirección del inmueble en hospedaje (LIVA 18-J
  fracc. III inciso g).

## Obligaciones del contribuyente (resumen operativo)

1. Estar inscrito en el RFC con la obligación de plataformas (RMF 12.3.1, 12.3.2).
2. Proporcionar su RFC a la plataforma (si no: retenciones 20% ISR / 100% IVA).
3. Conservar los CFDI de retenciones mensuales.
4. Si NO optó por definitivos: declarar ISR provisional e IVA mensual (día 17).
5. Expedir CFDI por cobros directos a clientes (RMF 12.3.4).
6. Declaración anual en abril (solo si no optó por definitivos).

## Reformas recientes (contexto, vigente al 2026-06-11)

- 2021–2025: tasas 2.1% / 4% / 1% e IVA 50%-100% sin cambios.
- 2026 (Paquete Económico, DOF 07-nov-2025, vigor 01-ene-2026, todo vía LIF
  Art. 25): fracc. III PF sube a 2.5%; retención a personas morales 2.5% ISR
  (20% sin RFC); IVA 100% a depósitos en cuentas extranjeras y a residentes en
  el extranjero sin establecimiento; CFF Art. 30-B (acceso del SAT en línea y
  tiempo real a info de plataformas, con bloqueo por incumplimiento, vigor
  01-abr-2026).
- PENDIENTE_VERIFICAR: posibles Resoluciones de Modificaciones a la RMF 2026
  posteriores al 28-dic-2025 que toquen el Título 12 (monitorear minisitio SAT).

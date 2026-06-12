# Prompts de prueba — impuestos AIRBNB mx

Estos prompts representan conversaciones reales esperadas con el skill.
Para cada uno se documenta: qué debe hacer el skill, qué NO debe hacer,
y cómo verificar que la respuesta es correcta.

Fixtures de referencia: `tests/fixtures/cfdis.zip` + `tests/fixtures/airbnb_ganancias_2026-05.csv`
Resultado E2E base (fixtures sintéticos, mayo 2026):
- Ingresos recibidos: $9,250.00 | ISR retenido: $400.00 | IVA retenido: $800.00
- IVA acreditable de gastos: $224.00 | IVA a cargo: $576.00
- Deducibles: 2 | No deducibles: 1 | Deducciones personales: 1

---

## P-01 — Inicio de flujo con archivos listos

**Prompt del usuario:**
> Aquí están mis archivos del SAT de mayo y mi CSV de Airbnb. Quiero saber cuánto pago este mes.

**Comportamiento esperado:**
1. Da el disclaimer (herramienta de apoyo, no asesoría fiscal).
2. Confirma modalidad (provisional vs. definitivos) con una pregunta rápida; asume provisional si no lo ha indicado.
3. Corre los 4 scripts en orden: parse_cfdi → parse_plataforma → clasificador → calculo_impuestos.
4. Muestra resumen: ingresos, IVA a cargo, ISR a cargo.
5. Pregunta si hay dudosas para revisar antes de cerrar.

**Verifica:**
- Disclaimer presente antes de los números.
- No inventa tasas: cita LISR 113-A, LIVA Arts. 1o./4o./5o.
- Ingresos recibidos = depósito neto del CSV (no el bruto).

**NO debe:**
- Pedir e.firma, CIEC o contraseñas.
- Entregar el Excel antes de resolver las dudosas.

---

## P-02 — Factura dudosa de marketplace

**Prompt del usuario:**
> ¿Por qué mi factura de Amazon por $1,800 está en 'dudosas'? ¿La puedo incluir?

**Comportamiento esperado:**
1. Lee `references/reglas_deducibilidad.md` sección H-05.
2. Explica: marketplace → plausible pero no automáticamente exclusivo de Airbnb.
3. Pregunta: "¿el artículo que compraste (ej. blancos, artículos de cocina, herramientas) es para el departamento que rentas?"
4. Si el usuario dice sí → le indica agregar el UUID a `decisiones.json` como "incluir" y volver a correr el clasificador.
5. Si dice no → excluir.

**Verifica:**
- Cita regla H-05.
- Explica el mecanismo de `decisiones.json` para persistir la decisión.
- No incluye la factura sin confirmación explícita del usuario.

---

## P-03 — No encuentra sus XMLs en el SAT

**Prompt del usuario:**
> No sé cómo descargar mis facturas del SAT. ¿Dónde entro?

**Comportamiento esperado:**
1. Lee `references/paso_a_paso_portal_sat.md`, sección 1 "Descarga tus XMLs".
2. Da los pasos exactos: portalcfdi.facturaelectronica.sat.gob.mx → RFC + contraseña → Consultar facturas recibidas → rango de fechas del mes → Descargar seleccionados (XML).
3. Advierte: el skill JAMÁS pide ni recibe RFC, contraseña o e.firma.

**Verifica:**
- URL correcta del portal de descarga.
- Instrucción de filtrar por "vigentes" (no canceladas).
- No pide las credenciales al usuario.

---

## P-04 — Captura en el portal del SAT (paso a paso)

**Prompt del usuario:**
> Ya calculaste todo. ¿Cómo capturo esto en el SAT?

**Comportamiento esperado:**
1. Lee `references/paso_a_paso_portal_sat.md` sección 2 completa.
2. Guía paso a paso: URL ptscpteweb.clouda.sat.gob.mx/platec → RFC + CIEC → Presentar declaración → Configuración → ISR hospedaje.
3. Para ISR: da los 3 valores exactos del Excel (campo 1, campo 3; campo 2 = 0 preguntando cobros directos).
4. Para IVA: da los valores, enfatiza que el `IVA acreditable` es el valor clave que calculó el skill.
5. Recuerda: NO hay prellenado, el usuario captura todo manualmente.

**Verifica:**
- Valores coinciden con el Excel del skill (hoja Resumen).
- Menciona que el IVA acreditable = hoja Deducibles del Excel.
- Menciona el dropdown "¿Desea disminuir...?" = No.

---

## P-05 — Factura en efectivo

**Prompt del usuario:**
> Tengo una factura de limpieza por $3,500 pero la pagué en efectivo. ¿Puedo deducirla?

**Comportamiento esperado:**
1. Lee `references/reglas_deducibilidad.md` regla R-02.
2. Responde: NO deducible ni acreditable IVA. Fundamento: LISR Art. 27-III (pagos en efectivo > $2,000 no son deducibles).
3. Sugiere: para el futuro, pagar con tarjeta de débito/crédito o transferencia bancaria.
4. Aclara que NO tiene solución retroactiva.

**Verifica:**
- Cita LISR Art. 27-III.
- No inventa ninguna alternativa para "rescatar" la factura.
- Consejo forward-looking para el siguiente mes.

---

## P-06 — Consulta sobre RESICO

**Prompt del usuario:**
> Soy anfitrión de Airbnb. Me dijeron que puedo estar en RESICO. ¿Es cierto?

**Comportamiento esperado:**
1. Lee `references/regimen_resico_pf.md` sección de incompatibilidades.
2. Responde: en general, NO son compatibles. Los ingresos vía plataforma digital (Airbnb) están sujetos al régimen de Plataformas Tecnológicas (LISR 113-A), que es INCOMPATIBLE con RESICO (RMF 3.13.3).
3. Sugiere validar la situación con un contador, especialmente si también tiene otros ingresos o si ya está en RESICO.
4. Da el disclaimer.

**Verifica:**
- No afirma que son compatibles.
- Cita RMF 3.13.3 y LISR 113-A.
- Sugiere contador para el caso mixto.

---

## P-07 — Factura diferida (PPD sin complemento de pago)

**Prompt del usuario:**
> El skill puso una factura de mi proveedor de internet como "diferida". ¿Qué significa eso?

**Comportamiento esperado:**
1. Lee `references/reglas_deducibilidad.md` regla R-04.
2. Explica: el CFDI es PPD (Pago en Parcialidades o Diferido) y no encontró el complemento de pago en el ZIP. No es un rechazo — significa que aún no se puede acreditar en este mes.
3. Indica: se acreditará el mes en que pagaste y el proveedor emitió el CFDI de complemento de pago. Cuando tengas ese XML, vuelve a correr el skill con el ZIP de ese mes.

**Verifica:**
- Distingue DIFERIDA de NO_DEDUCIBLE.
- No dice que la factura "está mal" — es cuestión de timing.
- Menciona el complemento de pago (CFDI tipo P).

---

## P-08 — Conveniencia de pagos definitivos

**Prompt del usuario:**
> ¿Me conviene hacer pagos definitivos con el SAT para simplificar mi declaración?

**Comportamiento esperado:**
1. Lee `references/regimen_plataformas.md` sección "pagos definitivos".
2. Explica: en pagos definitivos las retenciones de la plataforma son el pago final — más simple, pero SIN deducciones ni IVA acreditable.
3. Da la fórmula de conveniencia aproximada: conviene cuando los gastos deducibles son pequeños vs. los ingresos (break-even depende del % de gastos deducibles).
4. Advierte: es IRREVOCABLE por 5 años (LISR 113-D) y se presenta vía ficha de trámite 4/PLT.
5. Recomienda consultar a un contador antes de decidir. No recomienda ni desaconseja — es decisión del usuario.

**Verifica:**
- Menciona irreversibilidad de 5 años.
- No decide por el usuario.
- Cita LISR 113-D.

---

## P-09 — Diferencia entre lo que calculó el skill y lo que mostró el SAT

**Prompt del usuario:**
> El SAT me calculó $650 de IVA pero tú me dices $576. ¿Quién tiene razón?

**Comportamiento esperado:**
1. Lee `references/paso_a_paso_portal_sat.md` sección 4 "Si lo precargado no cuadra".
2. El SAT es la fuente legal — el skill es una herramienta de estimación.
3. Lista las causas típicas de diferencia:
   - Corte de fechas distinto (reservas a caballo entre meses).
   - Ingresos directos al huésped que el usuario no capturó.
   - IVA acreditable que el usuario no capturó en el portal.
   - Facturas canceladas que siguen en el ZIP.
   - CFDI de retenciones emitido con retraso.
4. Ayuda a identificar cuál aplica con preguntas de diagnóstico.

**Verifica:**
- No descarta el cálculo del SAT.
- Ofrece diagnóstico, no discute con el SAT.
- Identifica el IVA acreditable como la causa más probable (el usuario puede haberlo omitido).

---

## P-10 — Saldo a favor de IVA del mes anterior

**Prompt del usuario:**
> El mes pasado me quedé con $300 de IVA a favor. ¿Cómo aplico ese saldo este mes?

**Comportamiento esperado:**
1. Cita LIVA Art. 6o. (acreditamiento de saldo a favor).
2. Explica: al correr el skill, usar el parámetro `--saldo_favor_iva 300` en `calculo_impuestos.py`.
3. En el Excel (hoja Resumen) aparecerá el campo "Acreditamiento saldo a favor periodos anteriores".
4. En el portal del SAT: ese campo solo se habilita cuando hay "Cantidad a cargo" > 0 (verificado por Jorge en pantalla). Si no hay IVA a cargo, el saldo se arrastra al mes siguiente.
5. El skill calcula el cap: no puede aplicarse más de lo que es la "Cantidad a cargo".

**Verifica:**
- Cita LIVA Art. 6o.
- Explica el cap (sin exceder de cantidad a cargo).
- Menciona que el campo en el SAT es condicional.
- Indica qué hacer con el saldo no aplicado (llevarlo al mes siguiente).

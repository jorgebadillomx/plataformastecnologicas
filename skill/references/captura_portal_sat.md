# Captura de declaración — Portal del SAT (plataformas tecnológicas, persona física)

```text
vigencia: 2026
fuente: https://www.sat.gob.mx/minisitio/PlataformasTecnologicas/PersonasFisicas/personasfisicas_declaraciones.html
        https://www.sat.gob.mx/portal/public/personas-fisicas/regimen-de-las-actividades-empresariales-con-ingresos-a-traves-de-plataformas-tecnologicas
        https://ptscpteweb.clouda.sat.gob.mx/platec
verificado: 2026-06-11 (URLs y flujo de acceso: confirmado directamente por usuario real;
            pantalla bienvenida + configuración + obligaciones a declarar: confirmadas;
            campos internos del formulario ISR/IVA: PENDIENTE_VERIFICAR, ver nota al final)
```

REGLA PERMANENTE: el usuario hace TODO esto él mismo con su RFC y contraseña.
El skill jamás pide ni recibe credenciales. Si el usuario las ofrece, recházalas
y comparte esta guía.

## 2. Declaración mensual de ISR e IVA (plataformas)

**Ruta de acceso verificada (2026-06-11):**

1. Punto de entrada oficial:
   `https://www.sat.gob.mx/portal/public/personas-fisicas/regimen-de-las-actividades-empresariales-con-ingresos-a-traves-de-plataformas-tecnologicas`
2. Desde ahí, o directamente, entra al aplicativo:
   `https://ptscpteweb.clouda.sat.gob.mx/platec`
3. Autentícate con tu **RFC + CIEC** (el usuario lo hace él mismo; el skill
   JAMÁS pide ni recibe estas credenciales).
4. La pantalla de bienvenida muestra "Declaraciones de Plataformas tecnológicas"
   con tu nombre y un botón **PRESENTAR DECLARACIÓN** (menú superior también
   tiene "Presentar declaración" y "Consultas"). Haz clic en ese botón.

### 2a. Configuración de la declaración (verificada 2026-06-11)

Aparece la pantalla **"Configuración de la declaración"** con estos campos:

| Campo              | Valor a seleccionar                              |
| ------------------ | ------------------------------------------------ |
| Ejercicio          | 2026                                             |
| Periodicidad       | Mensual                                          |
| Periodo            | El mes que vas a declarar (ej. Mayo)             |
| Tipo de declaración | Normal (si es tu primera presentación del mes)  |

Debajo aparece **"Obligaciones a declarar"** con 5 iconos. El sistema
pre-selecciona automáticamente las que te corresponden (se muestran en azul):

| Obligación | Seleccionar | Para quién |
| --- | :---: | --- |
| Impuesto al Valor Agregado por la prestación de servicios digitales | NO | Solo para las plataformas (Airbnb como empresa) |
| IVA retenciones por el uso de plataformas tecnológicas | NO | Para las plataformas retenedoras, no para ti |
| **ISR personas físicas plataformas tecnológicas** | **SÍ** (pre-seleccionada) | Tu ISR mensual |
| IVA personas físicas plataformas tecnológicas, pago definitivo | NO | Solo si presentaste aviso ficha 4/PLT |
| **IVA personas físicas plataformas tecnológicas** | **SÍ** (pre-seleccionada) | Tu IVA mensual |

Las dos pre-seleccionadas son exactamente las que corresponden al Excel del
skill: el ISR provisional y el IVA mensual. Verifica que solo esas dos estén
activas y haz clic en **Siguiente**.

### 2b. Administración de la declaración (verificada 2026-06-11)

Aparece la pantalla **"Administración de la declaración"** con:

- Un recuadro de instrucciones que explica el flujo:
  1. Ingresa a cada sección y captura la información del periodo.
  2. Para revisar: botón **Vista previa**.
  3. Para enviar: botón **Enviar**.
  4. Después del envío se genera el **acuse de recibo**.
- Dos iconos clickeables: **ISR personas físicas plataformas tecnológicas** y
  **IVA personas físicas plataformas tecnológicas**.
- Un recuadro **"Total a pagar:"** al fondo que se actualiza conforme llenas
  cada sección.

Haz clic primero en **ISR personas físicas plataformas tecnológicas**, llena su
formulario (sección 2c), regresa a esta pantalla y luego haz clic en
**IVA personas físicas plataformas tecnológicas** (sección 2d). Al terminar
ambas, revisa con **Vista previa** y envía.

### 2c. Formulario ISR — Tipo de ingreso (verificado 2026-06-11)

Pantalla: **"ISR personas físicas plataformas tecnológicas"**

Botones superiores: INSTRUCCIONES · ADMINISTRACIÓN DE LA DECLARACIÓN · GUARDAR

El formulario tiene tres pestañas en orden: **Tipo de ingreso → [actividad] → Pago**.

**Pestaña "Tipo de ingreso"** — tres checkboxes; selecciona el que aplica:

| Checkbox | Cuándo | Tasa ISR |
| --- | --- | --- |
| Ingresos por servicios terrestres de pasajeros y entrega de bienes | Uber, Didi, Rappi, etc. | 2.1% |
| **Ingresos por prestación de servicios de hospedaje** | **Airbnb** ← pre-seleccionado | **4%** |
| Ingresos por enajenación de bienes y prestación de servicios | Mercado Libre, etc. | 2.5% (2026) |

Para Airbnb: **"Ingresos por prestación de servicios de hospedaje"** ya viene
pre-seleccionado. Confirma que solo ese esté marcado y pasa a la siguiente
pestaña que aparece con ese nombre.

⚠ Si desactivas un checkbox, el SAT borra los datos capturados en esa sección.

### 2d. Formulario ISR — Prestación de servicios de hospedaje (verificado 2026-06-11)

La pestaña **"Prestación de servicios de hospedaje"** tiene estos campos
(los marcados con * son obligatorios; los demás se auto-calculan):

| # | Campo (nombre literal en el SAT) | Cómo llenarlo | Fuente en el Excel del skill |
| - | --- | --- | --- |
| 1 | `*Ingresos obtenidos mediante intermediarios` | Captura tú | "Depósitos netos recibidos" (sección Conciliación) |
| 2 | `*Ingresos obtenidos directamente del usuario` | Captura tú | Pregunta al usuario: cobros directos fuera de Airbnb — normalmente **0** |
| = | `Ingresos totales del mes` | **AUTO** | = campo 1 + campo 2 |
| × | `Tasa %` | **AUTO** (botón "VER TASAS") | Tarifa del SAT — no capturar |
| = | `ISR causado` | **AUTO** | = Ingresos totales × Tasa% |
| 3 | `*Retenciones por plataformas tecnológicas` | Captura tú | "ISR retenido por la plataforma" del CSV de Airbnb |
| = | `ISR a cargo` | **AUTO** (botón "VER RESUMEN") | = max(0, ISR causado − Retenciones) |

**Solo capturas los campos 1, 2 y 3.** El SAT calcula todo lo demás.

**⚠ NO HAY PRELLENADO (verificado 2026-06-11):** el formulario NO viene con datos
de Airbnb. Tú capturas todo manualmente a partir del CSV de Airbnb. El SAT
auto-calcula: Ingresos totales, Tasa % y ISR causado.

**Tasa % = 4.00 para hospedaje (verificado):** el SAT usa la tasa plana de
retención del Art. 113-A, NO la tarifa progresiva del Art. 96. Por eso:
ISR causado = ingresos × 4%. Para un anfitrión Airbnb cuya retención ya fue
del 4%, ISR a cargo = 0 (la retención cubre exactamente el ISR causado).

Flujo exacto para Airbnb (usando el CSV del mes):

- Campo 1 → columna "Ingresos recibidos" del CSV de Airbnb
- Campo 2 → 0 (salvo que hayas cobrado directamente a algún huésped — preguntarlo)
- Campo 3 → columna "Total ISR retenido" del CSV de Airbnb

⚠ **Deducciones**: el formulario ISR mensual de plataformas NO tiene campo de
deducciones. Tu análisis de facturas del skill aplica al IVA acreditable (en el
formulario IVA) y a la declaración ANUAL — no al ISR mensual.

### 2e. Formulario ISR — Pago (verificado 2026-06-11)

La pestaña **"Pago"** es de solo lectura — no se puede editar. Muestra el
resultado final del cálculo:

| Campo | Descripción |
| --- | --- |
| A cargo | ISR causado (ingresos × tasa) |
| Total de contribuciones | ISR total determinado |
| Total de aplicaciones | Retenciones aplicadas |
| Cantidad a cargo | ISR a cargo neto |
| **Cantidad a pagar** | **Importe final a pagar (pesos enteros)** |

**"Cantidad a pagar"** es el número que verifica contra el Excel del skill:
sección "VALORES PARA CAPTURAR EN EL SAT" → "ISR — pago provisional del mes
(entero)".

Flujo de cierre del ISR:

1. Revisa "Cantidad a pagar" — si cuadra con el estimado del skill, bien.
   Si difiere, ver sección "Si lo precargado no cuadra con tu cálculo".
2. Haz clic en **GUARDAR**.
3. Haz clic en **ADMINISTRACIÓN DE LA DECLARACIÓN** para regresar al menú
   con los dos iconos (ISR e IVA). El ícono ISR ya mostrará tu ISR guardado.
4. Ahora haz clic en **IVA personas físicas plataformas tecnológicas** para
   llenar el formulario IVA (sección 2f).

### 2f. Formulario IVA — Determinación (verificado 2026-06-11)

Pantalla: **"IVA personas físicas plataformas tecnológicas"**
Pestañas: **Determinación** (activa) → Pago

**⚠ NO HAY PRELLENADO (verificado 2026-06-11):** igual que en ISR, el formulario
IVA NO viene con datos de Airbnb. Tú capturas todo manualmente desde tu CSV.

| # | Campo (nombre literal en el SAT) | Cómo llenarlo | Fuente en el Excel del skill |
| - | --- | --- | --- |
| 1 | `*Ingresos obtenidos mediante intermediarios` | Captura tú | Mismo valor que pusiste en ISR (columna "Ingresos recibidos" del CSV) |
| 2 | `*Ingresos obtenidos directamente del usuario` | Captura tú | 0 normalmente — preguntar al usuario |
| = | `Ingresos totales del mes` | **AUTO** | = campo 1 + campo 2 |
| × | `Tasa %` | **AUTO** | 16% IVA general |
| = | `IVA a cargo a la tasa del 16%` | **AUTO** | = Ingresos totales × 16% |
| 3 | `IVA acreditable` | Captura tú | **Suma IVA hoja Deducibles** ← valor principal del skill |
| 4 | `*IVA retenido` | Captura tú | Columna "IVA retenido" del CSV de Airbnb |
| = | `Cantidad a cargo` | **AUTO** | = IVA 16% − IVA acreditable − IVA retenido |
| = | `Impuesto a cargo` | **AUTO** | = Cantidad a cargo (pesos enteros) |

**Regla condicional del saldo a favor anterior (LIVA Art. 6o, verificado):**
El campo "IVA pendiente de acreditar de periodos anteriores" solo se **habilita**
cuando "IVA a cargo a la tasa del 16%" > 0 después de las otras deducciones.
Debe ser exclusivamente de plataformas tecnológicas. El skill lo estima con
`--saldo_favor_iva`.

**El `IVA acreditable`** (campo 3, no obligatorio) es donde el skill aporta su
valor principal: la suma del IVA de tus facturas deducibles del mes. Sin el
skill, ese campo quedaría en 0 y pagarías de más IVA.

### 2g. Formulario IVA — Pago (verificado 2026-06-11)

La pestaña **"Pago"** consolida el resultado. Campos (todos solo lectura
excepto el dropdown):

| Campo | Descripción |
| --- | --- |
| A cargo | = Impuesto a cargo de la pestaña Determinación |
| Total de contribuciones | = A cargo |
| **¿Desea disminuir su total de contribuciones con algún concepto?** | Dropdown → selecciona **No** (para Airbnb normal) |
| Total de aplicaciones | 0 (cuando se responde No) |
| Cantidad a cargo | = Total de contribuciones − Total de aplicaciones |
| **Cantidad a pagar** | **Importe final a pagar** — verifica contra Excel del skill |

**"Cantidad a pagar"** es lo que verifica contra el Excel:
sección "FORMULARIO IVA" → "Impuesto a cargo IVA estimado".

Flujo de cierre completo:

1. Pestaña Pago → dropdown "¿Desea disminuir...?" → **No** → "Cantidad a pagar" se muestra.
2. Haz clic en **GUARDAR**.
3. Haz clic en **ADMINISTRACIÓN DE LA DECLARACIÓN** → pantalla hub muestra ISR + IVA guardados y el **Total a pagar** consolidado.
4. Haz clic en **Enviar** → confirma → se genera el **acuse de recibo** (guárdalo en PDF).

## 3. Aviso de opción de pagos definitivos (solo si decide ejercerla)

Ficha de trámite **4/PLT** "Aviso para ejercer la opción de considerar como
pagos definitivos las retenciones del IVA e ISR" (RMF 2026 regla 12.3.3,
Anexo 1-A): se presenta vía Mi portal (caso de aclaración) dentro de los 30
días siguientes al primer ingreso. Antes de sugerirlo, lee la letra chica en
`regimen_plataformas.md` (irrevocable 5 años, sin deducciones).

## 4. Si lo precargado no cuadra con tu cálculo

Causas típicas, en orden de frecuencia:

1. La plataforma reportó con corte distinto al mes calendario (reservas a
   caballo entre meses).
2. CFDI de retenciones emitido con retraso (hasta 5 días después del cierre).
3. Cobros directos al huésped fuera de la plataforma (no los reporta Airbnb).
4. Facturas canceladas que siguen en tu ZIP.
5. Devoluciones/reembolsos a huéspedes (notas de crédito).

El precargado del SAT es el punto de partida legal: el valor del skill es
detectar y explicar la diferencia, no sustituirlo.

## Nota de mantenimiento

Los nombres de menús/aplicativos cambian con cada versión del portal. Los
marcados PENDIENTE_VERIFICAR deben validarse en pantalla en la primera sesión
de cada ejercicio fiscal; si el usuario reporta una pantalla distinta, pídele
el nombre exacto que ve y adáptate (la mecánica legal no cambia: Arts. 106
LISR, 5o.-D LIVA, reglas RMF 12.3.13/12.3.14).

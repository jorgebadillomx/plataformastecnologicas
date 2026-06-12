# impuestos AIRBNB mx — Plataformas Tecnológicas · pagos provisionales (Airbnb)

## Tagline
Concilia lo que Airbnb te retuvo, calcula tu IVA acreditable y prepara tu declaración mensual en el SAT — en minutos, con la regla legal citada en cada número.

## Qué hace

Convierte tus archivos del SAT + tu reporte de Airbnb en un Excel listo para capturar en el portal del SAT, campo por campo:

1. **Lee tus facturas XML** del SAT (las que recibiste de proveedores ese mes) y las clasifica automáticamente: deducibles, dudosas y no deducibles, con la regla legal citada.
2. **Lee tu CSV de Airbnb** (reporte de ganancias del mes) y extrae ingresos, ISR retenido e IVA retenido.
3. **Calcula tu IVA acreditable** (el valor que el SAT no precalcula y que, si no lo capturas, pagas de más).
4. **Genera un Excel** con exactamente los valores que debes capturar en el portal del SAT, con los nombres literales de cada campo del formulario.
5. **Te guía campo por campo** en el portal del SAT, con pantallazos del flujo verificados en 2026.

## Para quién es

- Anfitriones de Airbnb en México que rentan propiedades y están en el **régimen de Plataformas Tecnológicas** (el régimen que aplica por defecto cuando cobras vía Airbnb).
- Personas físicas que quieren entender y verificar su declaración mensual sin depender completamente de un contador para los números de rutina.
- El skill complementa a tu contador — no lo reemplaza para decisiones fiscales complejas.

## Qué necesitas tener listo

| Archivo | Dónde lo consigues |
|---|---|
| ZIP con tus XMLs del mes (facturas recibidas) | Portal del SAT → portalcfdi.facturaelectronica.sat.gob.mx → Consultar facturas recibidas |
| CSV de ganancias de Airbnb | Airbnb → Menú → Cuenta → Pagos y cobros → Historial de transacciones → Exportar |

El skill nunca te pide contraseñas, e.firma ni CIEC. Tú descargas tus archivos y los subes aquí.

## Qué recibes

- **Excel mensual** con 6 hojas:
  - `Resumen` — los 6-8 valores exactos que captures en el SAT (ISR + IVA), con los nombres literales del formulario
  - `Deducibles` — facturas aceptadas con regla legal citada e IVA acreditable calculado
  - `Dudosas` — facturas para tu revisión con columna "¿Qué puedo hacer?" por tipo
  - `Rechazadas` — no deducibles con motivo y consejo de corrección para el futuro
  - `Deducciones personales` — candidatas para tu declaración anual
  - `Inversiones` — activo fijo detectado
- **Guía paso a paso** del portal del SAT campo por campo, verificada con el portal real.
- **Explicación de cada número**: regla citada, fundamento legal, qué significa en pesos.

## Qué NO hace (sé honesto con tus usuarios)

- No se conecta al SAT ni presenta la declaración por ti.
- No maneja e.firma, CIEC ni contraseñas.
- No cubre (aún): sueldos y salarios, arrendamiento directo, actividad empresarial/profesional general, personas morales, declaración anual completa.
- No calcula depreciación de activos fijos (los detecta y reporta).
- No es asesoría fiscal ni sustituye a un contador público.

## Régimen y cobertura actual (Fase 1)

| Régimen | Soportado | Notas |
|---|---|---|
| Plataformas Tecnológicas — provisionales | ✅ Completo | Solo Airbnb |
| Plataformas Tecnológicas — pagos definitivos | ✅ Conciliación | Sin deducciones (por diseño del régimen) |
| RESICO PF | ❌ No aplica | Incompatible con ingresos vía Airbnb (LISR 113-A / RMF 3.13.3) |
| Otras plataformas (Uber, Didi, Rappi, ML) | ❌ No soportado | Solo Airbnb en esta versión |
| Sueldos y salarios | ❌ Fase 2 | |
| Arrendamiento directo | ❌ Fase 2 | |
| Actividad profesional | ❌ Fase 2 | |

## Fuentes fiscales

Todas las tasas, tarifas y reglas se leen de archivos de referencia con vigencia y fuente oficial (DOF / SAT / RMF 2026). El skill nunca inventa cifras.

- LISR Arts. 113-A a 113-D (Plataformas Tecnológicas)
- LIVA Arts. 1o., 4o., 5o., 6o., 18-J
- RMF 2026 reglas 12.3.13, 12.3.14, 3.13.3
- Tarifa ISR mensual 2026 (DOF)
- Tabla RESICO mensual 2026 (DOF)

## Disclaimer

Esta herramienta entrega cálculos estimados con fundamento en la legislación fiscal vigente. No constituye asesoría fiscal ni sustituye a un contador público autorizado. Valida siempre los resultados contra el portal del SAT antes de pagar.

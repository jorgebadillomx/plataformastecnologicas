# BRIEF_PRODUCTO.md — impuestos AIRBNB mx

## Oportunidad

Marketplace Capafy: el creador conserva 80% por transacción (Capafy toma 20%),
tarifa única de certificación de $0.99 USD al publicar por primera vez. Tres modos
de venta: suscripción (diaria/semanal/mensual), alquiler por hora y descarga con
pago único. Benchmark publicado por Capafy: un skill de "asistente CPA" en
suscripción de $19 USD/mes alcanzó 32 suscriptores (~$408/mes) en 2 meses.

**Decisión de modo: SUSCRIPCIÓN.**
- En modo Download el comprador recibe el paquete completo (prompts, lógica, código
  fuente) → regala la IP.
- En modo Run on Capafy el skill corre en sandbox y el usuario solo interactúa por
  chat → protege la metodología.
- Las tablas fiscales cambian cada año → la actualización continua justifica la
  suscripción ("siempre al día con el SAT").

Precio objetivo Fase 1: $9–15 USD/mes (nicho Airbnb/plataformas).
Al escalar a asistente fiscal general: $19 USD/mes.

## Usuario objetivo (Fase 1)

Anfitrión de Airbnb / conductor o repartidor de app / vendedor de marketplace en
México, persona física, sin contador o con contador caro, que:
- Recibe un reporte de ganancias de la plataforma (Excel/CSV).
- Puede descargar sus XMLs del portal del SAT (o aprender con la guía del skill).
- Quiere saber: ¿qué facturas me sirven?, ¿cuánto voy a pagar?, ¿qué capturo en el
  portal?, ¿lo precargado está bien?

## Propuesta de valor (vs. lo que ya existe)

El SAT ya precarga la declaración. El valor del skill NO es llenar por el usuario,
sino:
1. **Explicar** su situación en español claro, por régimen.
2. **Detectar** deducciones que el precargado ignora y facturas mal emitidas
   (UsoCFDI incorrecto, método de pago que invalida deducción).
3. **Conciliar** retenciones de la plataforma vs. CFDIs de retenciones.
4. **Validar** el precargado con un paso a paso campo por campo.
5. Estar **actualizado** cada ejercicio fiscal (argumento de suscripción).

Competencia conocida: Satoko AI (SaaS independiente), simulador del propio SAT,
contadores tradicionales. Diferenciador: vive dentro del agente del usuario
(Claude/Codex), procesa SUS archivos sin pedir credenciales, y explica cada peso.

## Restricciones de seguridad y legales

- Cero manejo de e.firma/CIEC (riesgo legal y de confianza inaceptable).
- Disclaimer permanente: herramienta de apoyo, no asesoría fiscal, no relación con
  el SAT, cálculos estimados que el usuario debe validar (mismo patrón que usa la
  competencia para mitigar responsabilidad).
- Revisar la guía de revisión de Capafy antes de publicar:
  https://capafy.ai/es/review-guidelines y el acuerdo de creadores:
  https://capafy.ai/es/publisher-agreement

## Roadmap

- **F1 (este repo, MVP):** Plataformas Tecnológicas (Airbnb) + RESICO PF.
- **F2:** Sueldos y salarios → devolución de saldo a favor (mercado masivo, pico en
  abril). Campaña: "recupera tu saldo a favor".
- **F3:** Arrendamiento; actividad empresarial y profesional.
- **F4 (premium):** script LOCAL de descarga masiva vía web service del SAT v1.5
  (el usuario lo corre en SU máquina con SU e.firma; la FIEL nunca sale de su
  equipo). Librería candidata: @nodecfdi/sat-ws-descarga-masiva. Nota: el web
  service es asíncrono (hasta 72 h) y limita a los últimos 5 ejercicios.

## Métricas de éxito del MVP

- Flujo completo (ZIP + Excel → reporte + paso a paso) sin intervención manual.
- 0 cifras fiscales sin fuente verificada.
- 10/10 prompts de eval: dispara cuando debe, no dispara cuando no debe.
- Un usuario beta real (Jorge mismo con sus datos de Airbnb, fuera del repo)
  completa su pago provisional usando solo el skill.

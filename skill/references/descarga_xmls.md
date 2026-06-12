# Descarga de XMLs — Portal del SAT (plataformas tecnológicas)

```text
vigencia: 2026
fuente: https://www.sat.gob.mx/aplicacion/82471/consulta,-cancela-y-recupera-tus-facturas-electronicas
        https://portalcfdi.facturaelectronica.sat.gob.mx/
verificado: 2026-06-11 (URLs y flujo de descarga: confirmado directamente por usuario real)
```

REGLA PERMANENTE: el usuario hace TODO esto él mismo con su RFC y contraseña.
El skill jamás pide ni recibe credenciales. Si el usuario las ofrece, recházalas
y comparte esta guía.

## 1. Descarga tus XMLs (facturas recibidas del mes)

1. Entra a "Cancela y recupera tus facturas" en el portal del SAT
   (sat.gob.mx → Factura electrónica) o directo a
   `https://portalcfdi.facturaelectronica.sat.gob.mx/`.
2. Autentícate con RFC + contraseña (o e.firma) y el captcha.
3. Elige **Consultar facturas recibidas**.
4. Busca por rango de fechas: del día 1 al último día del mes a declarar.
   Puedes filtrar por estado del comprobante (descarga solo VIGENTES; si
   incluyes canceladas, sepáralas).
5. Selecciona todas y haz clic en **Descargar seleccionados** (XML). Guarda
   todos los XML en una carpeta o conserva el ZIP que entrega el portal.
6. Nota: la consulta clásica muestra hasta 500 resultados por búsqueda; si
   tienes más, acota el rango de fechas. Para volúmenes grandes existe
   "Consulta y recuperación de comprobantes (nuevo)" con paquetes ZIP que
   pueden tardar hasta 48 h en generarse.
7. Repite en **Consultar facturas emitidas** si también facturas directo a
   clientes.
8. CFDI de RETENCIONES de la plataforma (el que emite Airbnb cada mes): se
   consulta en la sección de retenciones del mismo portal de factura
   electrónica. PENDIENTE_VERIFICAR la ruta exacta del menú vigente
   ("Consultar retenciones"); si el usuario no lo encuentra, el flujo funciona
   con el CSV de la plataforma.

# CLAUDE.md — impuestos AIRBNB mx

## Qué es este proyecto

Agent Skill comercial para vender en Capafy (https://capafy.ai/es/earn), modo
**suscripción** (Run on Capafy: el código corre en sandbox y el comprador no ve el
fuente — por eso la lógica valiosa vive en `skill/scripts/` y `skill/references/`).
Ayuda a personas físicas en México a entender, calcular y preparar sus impuestos
(ISR/IVA) a partir de sus propios archivos: ZIP de XMLs CFDI 4.0 del SAT + reportes
de plataformas (Airbnb, etc.).

Fase 1: régimen de **Plataformas Tecnológicas** y **RESICO PF**.
Fases futuras: sueldos y salarios (devoluciones), arrendamiento, actividad
empresarial y profesional. La arquitectura debe permitir agregar un régimen
agregando un archivo en `references/` y reglas en el clasificador, sin reescribir.

## Reglas duras del proyecto

- **NUNCA** pedir, aceptar ni manejar e.firma, CIEC, .key, .cer o contraseñas del SAT.
- **NUNCA** inventar tasas, tarifas, UMAs o límites fiscales. Todo dato fiscal vive en
  `skill/references/*.md` con encabezado `vigencia / fuente (URL oficial) / verificado
  (fecha)`. Si no está verificado contra DOF / RMF / sat.gob.mx → `PENDIENTE_VERIFICAR`.
- Las tarifas se leen desde los archivos de referencia en tiempo de ejecución; el
  código no contiene cifras fiscales hardcodeadas.
- Todo cálculo y clasificación debe ser explicable: regla citada + referencia.
- Disclaimer en toda salida al usuario final: herramienta de apoyo, no asesoría
  fiscal, no sustituye a un contador.
- Datos de prueba: solo sintéticos en `tests/fixtures/`. Jamás RFCs ni montos reales.
- Lo que se empaqueta para Capafy es únicamente la carpeta `skill/`.

## Stack y convenciones

- Python 3.11+ para scripts (lxml/ElementTree para XML, pandas + openpyxl para
  Excel, pytest para tests). Sin dependencias exóticas: el skill debe correr en el
  sandbox de Capafy y en Claude Code sin instalación complicada.
- CFDI 4.0 usa namespaces (`http://www.sat.gob.mx/cfd/4`, complementos de
  retenciones y pagos): los parsers deben manejarlos explícitamente y tolerar XMLs
  malformados sin tronar (reportar y continuar).
- `SKILL.md` ≤ 500 líneas; detalle fino en `references/` con instrucciones claras de
  cuándo leer cada uno (progressive disclosure).
- Salidas al usuario final en español mexicano, tono claro y directo, sin jerga
  contable sin explicar.
- Commits: conventional commits en inglés.

## Comandos

- Tests: `python -m pytest tests/ -v`
- Flujo e2e con fixtures: `python skill/scripts/parse_cfdi.py tests/fixtures/cfdis.zip`
- Empaquetar para Capafy: zip de la carpeta `skill/` (verificar que no incluya tests
  ni fixtures).

## Criterio de "terminado" por etapa

Una etapa no está lista hasta que: tests pasan, los datos fiscales citados están
verificados o marcados PENDIENTE_VERIFICAR, y Jorge revisó el resumen de la etapa.

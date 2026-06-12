# CFDI Airbnb IVA

Script para revisar CFDI XML y calcular IVA acreditable mensual para Airbnb bajo el regimen de plataformas tecnologicas.

## Archivos

- `cfdi_airbnb_iva.ps1`
  Script principal.
- `history\uuid_overrides.json`
  Guarda overrides manuales por UUID en `100` o `0`.
- `history\AAAA-MM_FACTURAS.json`
  Snapshot completo de una corrida.
- `history\AAAA-MM_FACTURAS.csv`
  Resumen revisable en Excel.

## Que hace

- Lee todos los XML de una carpeta.
- Filtra por periodo `MM/YYYY`.
- Excluye automaticamente:
  - `P`
  - `N`
  - efectivo `01`
  - gastos bancarios, intereses, seguros, prestamos y personales claros
- Si el CFDI es `PPD/99`, toma el IVA realmente pagado desde complementos `P`.
- Detecta CFDI dudosos y pregunta solo `100` o `0`.
- Guarda cualquier decision manual por UUID para no volver a preguntarla.
- Genera historial de incluidos, excluidos, dudosos, ajustes y cambios contra la corrida anterior.

## Ubicacion esperada

La instalacion final queda en:

- `C:\Declaraciones\scripts\cfdi_airbnb_iva.ps1`
- `C:\Declaraciones\scripts\README.md`
- `C:\Declaraciones\scripts\history\`

## Ejercicio 1: corrida desde cero

Borra overrides guardados y corre el mes desde cero:

```powershell
& 'C:\Declaraciones\scripts\cfdi_airbnb_iva.ps1' `
  -FolderPath 'C:\Declaraciones\Enero\FACTURAS' `
  -Period '01/2026' `
  -ClearStoredDecisions
```

Que pasa:

- Te preguntara solo por CFDI dudosos.
- Respondes `100` para incluir o `0` para excluir.
- Guardara esas decisiones en `history\uuid_overrides.json`.
- Dejara el resultado del mes en JSON y CSV.

## Ejercicio 2: corrida normal reutilizando decisiones previas

```powershell
& 'C:\Declaraciones\scripts\cfdi_airbnb_iva.ps1' `
  -FolderPath 'C:\Declaraciones\Febrero\FACTURAS' `
  -Period '02/2026'
```

Que pasa:

- Si aparece un UUID ya decidido antes, lo reutiliza.
- Si aparece un dudoso nuevo, te lo pregunta al final.

## Ejercicio 3: forzar manualmente un UUID a incluir o excluir

Sirve para cambiar un CFDI que antes quedo incluido, excluido o dudoso.

Ejemplo para forzar exclusion:

```powershell
& 'C:\Declaraciones\scripts\cfdi_airbnb_iva.ps1' `
  -FolderPath 'C:\Declaraciones\Enero\FACTURAS' `
  -Period '01/2026' `
  -UuidOverrides @{
    'C476956A-EA0F-11F0-BDE6-D3D5EA647D62' = 0
  }
```

Ejemplo para forzar inclusion:

```powershell
& 'C:\Declaraciones\scripts\cfdi_airbnb_iva.ps1' `
  -FolderPath 'C:\Declaraciones\Enero\FACTURAS' `
  -Period '01/2026' `
  -UuidOverrides @{
    '035AD167-E718-11F0-94A4-E527C8FA39B9' = 100
  }
```

Que pasa:

- El override se guarda en `history\uuid_overrides.json`.
- En corridas futuras ese UUID ya no se clasifica automatico; se respeta el override.

## Ejercicio 4: quitar un override y volver a decidir

Si ya no quieres respetar una decision guardada:

```powershell
& 'C:\Declaraciones\scripts\cfdi_airbnb_iva.ps1' `
  -FolderPath 'C:\Declaraciones\Enero\FACTURAS' `
  -Period '01/2026' `
  -ForgetUuidOverrides 'C476956A-EA0F-11F0-BDE6-D3D5EA647D62'
```

Que pasa:

- El UUID se elimina del archivo de overrides.
- Si ese CFDI vuelve a caer en la zona dudosa, el script te lo preguntara otra vez.
- Si por reglas automaticas queda incluido o excluido, se ira por esa ruta.

## Ejercicio 5: revisar rapidamente incluidos, excluidos y cambios

Despues de cada corrida revisa:

- `history\AAAA-MM_FACTURAS.csv`
  para abrirlo en Excel.
- `history\AAAA-MM_FACTURAS.json`
  para revisar detalle completo.

Campos utiles:

- `IncludedCfdis`
- `ExcludedCfdis`
- `DoubtfulCfdis`
- `ChangesSincePrevious`

Si `ChangesSincePrevious` trae registros, hubo un cambio de criterio, estatus o IVA acreditado respecto de la corrida anterior del mismo periodo y carpeta.

## Ejercicio 6: volver a correr un mes completo desde cero

Si quieres rehacer totalmente un mes y no confiar en ningun override previo:

```powershell
& 'C:\Declaraciones\scripts\cfdi_airbnb_iva.ps1' `
  -FolderPath 'C:\Declaraciones\Enero\FACTURAS' `
  -Period '01/2026' `
  -ClearStoredDecisions
```

## Resultado principal

El dato importante para SAT es:

- `IvaAcreditableExact`
- `IvaAcreditableSatRounded`

## Nota de trabajo

El archivo `uuid_overrides.json` ya no es solo para dudosos.
Tambien sirve para corregir manualmente CFDI que originalmente hayan quedado incluidos o excluidos por clasificacion automatica.

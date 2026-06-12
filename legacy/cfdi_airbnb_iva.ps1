param(
    [Parameter(Mandatory = $true)]
    [string]$FolderPath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^(0[1-9]|1[0-2])/\d{4}$')]
    [string]$Period,

    [Alias('DoubtfulDecisions')]
    [hashtable]$UuidOverrides = @{},

    [string[]]$ForgetUuidOverrides = @{},

    [switch]$ClearStoredDecisions,

    [switch]$NoPrompt,

    [string]$HistoryFolder = 'C:\Declaraciones\scripts\history',

    [string]$DecisionStorePath = 'C:\Declaraciones\scripts\history\uuid_overrides.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$InvariantCulture = [System.Globalization.CultureInfo]::InvariantCulture

function Convert-ToDecimal {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return [decimal]0
    }

    return [decimal]::Parse($Value, $InvariantCulture)
}

function Get-XmlAttributeValue {
    param(
        [System.Xml.XmlNode]$Node,
        [string]$Name
    )

    if ($null -eq $Node) {
        return ''
    }

    $attribute = $Node.Attributes[$Name]
    if ($null -eq $attribute) {
        return ''
    }

    return [string]$attribute.Value
}

function Get-SafeFilePart {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return 'sin_nombre'
    }

    $safe = [regex]::Replace($Value, '[^A-Za-z0-9._-]+', '_')
    $safe = $safe.Trim('_')
    if ([string]::IsNullOrWhiteSpace($safe)) {
        return 'sin_nombre'
    }

    return $safe
}

function Read-DecisionStore {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return @{}
    }

    $raw = Get-Content -LiteralPath $Path -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return @{}
    }

    $parsed = $raw | ConvertFrom-Json
    $store = @{}
    foreach ($item in @($parsed)) {
        if ($null -eq $item) {
            continue
        }

        $uuid = [string]$item.UUID
        if ([string]::IsNullOrWhiteSpace($uuid)) {
            continue
        }

        $store[$uuid.ToUpperInvariant()] = [pscustomobject]@{
            UUID = $uuid.ToUpperInvariant()
            Decision = [int]$item.Decision
            UpdatedAt = [string]$item.UpdatedAt
            Emisor = [string]$item.Emisor
            Note = [string]$item.Note
        }
    }

    return $store
}

function Write-DecisionStore {
    param(
        [string]$Path,
        [hashtable]$Store
    )

    $parent = Split-Path -Path $Path -Parent
    if (-not (Test-Path -LiteralPath $parent)) {
        [void](New-Item -ItemType Directory -Path $parent -Force)
    }

    $items = foreach ($key in ($Store.Keys | Sort-Object)) {
        $Store[$key]
    }

    $items | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Normalize-Text {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return ''
    }

    $normalized = $Text.ToLowerInvariant()
    $normalized = [regex]::Replace($normalized, '[^a-z0-9/\- ]', ' ')
    $normalized = [regex]::Replace($normalized, '\s+', ' ')
    return $normalized.Trim()
}

function Test-ContainsAny {
    param(
        [string]$Text,
        [string[]]$Terms
    )

    foreach ($term in $Terms) {
        if ($Text.Contains($term)) {
            return $true
        }
    }

    return $false
}

function Get-IvaFromInvoice {
    param([xml]$Xml)

    $rootTraslados = $Xml.SelectNodes("/*[local-name()='Comprobante']/*[local-name()='Impuestos']/*[local-name()='Traslados']/*[local-name()='Traslado'][@Impuesto='002']")
    $sum = [decimal]0

    if ($rootTraslados.Count -gt 0) {
        foreach ($traslado in $rootTraslados) {
            $sum += Convert-ToDecimal (Get-XmlAttributeValue -Node $traslado -Name 'Importe')
        }
        return [decimal]::Round($sum, 2)
    }

    $conceptTraslados = $Xml.SelectNodes("/*[local-name()='Comprobante']/*[local-name()='Conceptos']/*[local-name()='Concepto']/*[local-name()='Impuestos']/*[local-name()='Traslados']/*[local-name()='Traslado'][@Impuesto='002']")
    foreach ($traslado in $conceptTraslados) {
        $sum += Convert-ToDecimal (Get-XmlAttributeValue -Node $traslado -Name 'Importe')
    }

    return [decimal]::Round($sum, 2)
}

function Parse-CfdiFile {
    param([string]$Path)

    [xml]$xml = Get-Content -LiteralPath $Path -Raw

    $comprobante = $xml.DocumentElement
    $emisor = $xml.SelectSingleNode("/*[local-name()='Comprobante']/*[local-name()='Emisor']")
    $receptor = $xml.SelectSingleNode("/*[local-name()='Comprobante']/*[local-name()='Receptor']")
    $tfd = $xml.SelectSingleNode("/*[local-name()='Comprobante']/*[local-name()='Complemento']/*[local-name()='TimbreFiscalDigital']")
    $conceptos = $xml.SelectNodes("/*[local-name()='Comprobante']/*[local-name()='Conceptos']/*[local-name()='Concepto']")
    $relacionados = $xml.SelectNodes("/*[local-name()='Comprobante']/*[local-name()='CfdiRelacionados']/*[local-name()='CfdiRelacionado']")

    $descriptions = New-Object System.Collections.Generic.List[string]
    foreach ($concepto in $conceptos) {
        $description = Get-XmlAttributeValue -Node $concepto -Name 'Descripcion'
        if (-not [string]::IsNullOrWhiteSpace($description)) {
            [void]$descriptions.Add($description)
        }
    }

    $relatedUuids = New-Object System.Collections.Generic.List[string]
    foreach ($rel in $relacionados) {
        $relatedUuid = Get-XmlAttributeValue -Node $rel -Name 'UUID'
        if (-not [string]::IsNullOrWhiteSpace($relatedUuid)) {
            [void]$relatedUuids.Add($relatedUuid.ToUpperInvariant())
        }
    }

    $uuid = ''
    $tfdUuid = Get-XmlAttributeValue -Node $tfd -Name 'UUID'
    if (-not [string]::IsNullOrWhiteSpace($tfdUuid)) {
        $uuid = $tfdUuid.ToUpperInvariant()
    }

    return [pscustomobject]@{
        Path = $Path
        FileName = [System.IO.Path]::GetFileName($Path)
        Fecha = [datetime](Get-XmlAttributeValue -Node $comprobante -Name 'Fecha')
        Tipo = Get-XmlAttributeValue -Node $comprobante -Name 'TipoDeComprobante'
        FormaPago = Get-XmlAttributeValue -Node $comprobante -Name 'FormaPago'
        MetodoPago = Get-XmlAttributeValue -Node $comprobante -Name 'MetodoPago'
        Moneda = Get-XmlAttributeValue -Node $comprobante -Name 'Moneda'
        Emisor = Get-XmlAttributeValue -Node $emisor -Name 'Nombre'
        EmisorRfc = Get-XmlAttributeValue -Node $emisor -Name 'Rfc'
        Receptor = Get-XmlAttributeValue -Node $receptor -Name 'Nombre'
        ReceptorRfc = Get-XmlAttributeValue -Node $receptor -Name 'Rfc'
        UsoCfdi = Get-XmlAttributeValue -Node $receptor -Name 'UsoCFDI'
        UUID = $uuid
        Iva = Get-IvaFromInvoice -Xml $xml
        Descriptions = @($descriptions)
        RelatedUuids = @($relatedUuids)
        Xml = $xml
    }
}

function Get-PaymentIvaMap {
    param(
        [object[]]$Records,
        [int]$Month,
        [int]$Year
    )

    $map = @{}

    foreach ($record in $Records | Where-Object { $_.Tipo -eq 'P' -and $_.Fecha.Month -eq $Month -and $_.Fecha.Year -eq $Year }) {
        $doctos = $record.Xml.SelectNodes("/*[local-name()='Comprobante']/*[local-name()='Complemento']/*[local-name()='Pagos']/*[local-name()='Pago']/*[local-name()='DoctoRelacionado']")

        foreach ($docto in $doctos) {
            $docUuid = Get-XmlAttributeValue -Node $docto -Name 'IdDocumento'
            if ([string]::IsNullOrWhiteSpace($docUuid)) {
                continue
            }

            $docUuid = $docUuid.ToUpperInvariant()
            $iva = [decimal]0

            $trasladosDr = $docto.SelectNodes("*[local-name()='ImpuestosDR']/*[local-name()='TrasladosDR']/*[local-name()='TrasladoDR'][@ImpuestoDR='002']")
            foreach ($traslado in $trasladosDr) {
                $iva += Convert-ToDecimal (Get-XmlAttributeValue -Node $traslado -Name 'ImporteDR')
            }

            if (-not $map.ContainsKey($docUuid)) {
                $map[$docUuid] = [decimal]0
            }

            $map[$docUuid] += [decimal]::Round($iva, 2)
        }
    }

    return $map
}

function Get-Classification {
    param(
        [object]$Record,
        [decimal]$AvailableIva
    )

    $text = Normalize-Text (($Record.Emisor + ' ' + (($Record.Descriptions -join ' | '))))
    $emisor = Normalize-Text $Record.Emisor

    $financeTerms = @(
        'hsbc', 'santander', 'banco', 'casa de bolsa', 'kuspit', 'bursatil',
        'interes', 'inversion', 'prestam', 'financ', 'credito', 'seguro',
        'anualidad', 'comisiones', 'estado de cuenta'
    )
    $personalTerms = @(
        'colegiatura', 'medico', 'nomina', 'pantalon', 'mezclilla', 'ropa',
        'crema', 'ojos', 'leche', 'supermerc', 'farmacia'
    )
    $marketplaceTerms = @('amazon', 'mercado libre', 'walmart', 'costco', 'soriana', 'chedraui')
    $clearIncludeTerms = @(
        'plataformas digitales', 'resico', 'gas rem', 'renta de servicios de internet',
        'infraestructura', 'limpieza', 'aromatizante', 'mantenimiento',
        'reparacion', 'inmueble', 'insumos de operacion'
    )
    $doubtfulTerms = @(
        'workspace', 'telecomunicaciones', ' tv', 'tv ', 'mueble', 'organizador',
        'perchero', 'zapatera', 'cocina', 'ollas', 'sartenes', 'herramienta',
        'material', 'pantalla', 'echo', 'equipo', 'digital'
    )

    if ($Record.FormaPago -eq '01') {
        return @{
            Status = 'Exclude'
            Reason = 'Forma de pago 01 efectivo'
        }
    }

    if ($AvailableIva -le 0) {
        if ($Record.MetodoPago -eq 'PPD' -or $Record.FormaPago -eq '99') {
            return @{
                Status = 'Exclude'
                Reason = 'CFDI PPD sin pago acreditable en el periodo'
            }
        }

        return @{
            Status = 'Exclude'
            Reason = 'No tiene IVA acreditable en el periodo'
        }
    }

    if (Test-ContainsAny -Text $text -Terms $financeTerms) {
        return @{
            Status = 'Exclude'
            Reason = 'Financiero, bancario, seguro o financiamiento'
        }
    }

    $isMarketplace = Test-ContainsAny -Text $text -Terms $marketplaceTerms
    $isPersonal = Test-ContainsAny -Text $text -Terms $personalTerms
    $isClearInclude = Test-ContainsAny -Text $text -Terms $clearIncludeTerms
    $isDoubtful = Test-ContainsAny -Text $text -Terms $doubtfulTerms

    if ($text.Contains('internet') -and $text.Contains('tv')) {
        return @{
            Status = 'Doubtful'
            Reason = 'Internet con TV; posible uso mixto'
        }
    }

    if (($emisor.Contains('total play') -or $emisor.Contains('total box')) -and ($text.Contains('internet') -or $text.Contains('infraestructura') -or $text.Contains('telecomunicaciones'))) {
        return @{
            Status = 'Include'
            Reason = 'Servicio del inmueble relacionado con conectividad'
        }
    }

    if ($isClearInclude) {
        return @{
            Status = 'Include'
            Reason = 'Gasto claramente relacionado con Airbnb'
        }
    }

    if ($isMarketplace -or $isDoubtful) {
        return @{
            Status = 'Doubtful'
            Reason = 'Gasto plausible para Airbnb, pero no claramente exclusivo'
        }
    }

    if ($isPersonal) {
        return @{
            Status = 'Exclude'
            Reason = 'Gasto personal o no relacionado'
        }
    }

    if ($text.Contains('telecomunicaciones') -or $emisor.Contains('radiomovil')) {
        return @{
            Status = 'Doubtful'
            Reason = 'Telefonia o telecom; posible uso mixto'
        }
    }

    return @{
        Status = 'Exclude'
        Reason = 'No se ve defendible como gasto de Airbnb'
    }
}

function Resolve-DoubtfulDecision {
    param([object]$Record)

    if ($NoPrompt) {
        return $null
    }

    Write-Host ''
    Write-Host 'CFDI dudoso detectado:'
    Write-Host ('Fecha: {0:yyyy-MM-dd}' -f $Record.Fecha)
    Write-Host ('Emisor: {0}' -f $Record.Emisor)
    Write-Host ('UUID: {0}' -f $Record.UUID)
    Write-Host ('IVA detectado: {0:N2}' -f $Record.IvaDetectado)
    Write-Host ('Conceptos: {0}' -f ($Record.Descriptions -join ' | '))
    Write-Host ('Motivo: {0}' -f $Record.Reason)

    while ($true) {
        $answer = (Read-Host 'Responde 100 para incluir o 0 para excluir').Trim()
        if ($answer -eq '100') { return 100 }
        if ($answer -eq '0') { return 0 }
    }
}

$decisionStore = Read-DecisionStore -Path $DecisionStorePath
if ($ClearStoredDecisions) {
    $decisionStore = @{}
}

foreach ($uuid in @($ForgetUuidOverrides)) {
    if ([string]::IsNullOrWhiteSpace($uuid)) {
        continue
    }

    [void]$decisionStore.Remove($uuid.ToUpperInvariant())
}

foreach ($key in @($UuidOverrides.Keys)) {
    $uuid = [string]$key
    if ([string]::IsNullOrWhiteSpace($uuid)) {
        continue
    }

    $normalizedUuid = $uuid.ToUpperInvariant()
    $value = [string]$UuidOverrides[$key]
    $decision = 0
    if ($value -eq '100' -or $value -eq '1' -or $value -eq 'SI' -or $value -eq 'si' -or $value -eq 'true') {
        $decision = 100
    }

    $decisionStore[$normalizedUuid] = [pscustomobject]@{
        UUID = $normalizedUuid
        Decision = $decision
        UpdatedAt = (Get-Date).ToString('s')
        Emisor = ''
        Note = 'Override recibido por parametro'
    }
}

$periodMonth = [int]$Period.Substring(0, 2)
$periodYear = [int]$Period.Substring(3, 4)

if (-not (Test-Path -LiteralPath $FolderPath)) {
    throw "La carpeta no existe: $FolderPath"
}

$files = Get-ChildItem -LiteralPath $FolderPath -File -Filter *.xml | Sort-Object FullName
$records = foreach ($file in $files) {
    Parse-CfdiFile -Path $file.FullName
}

$recordsInPeriod = $records | Where-Object { $_.Fecha.Month -eq $periodMonth -and $_.Fecha.Year -eq $periodYear }
$paymentIvaMap = Get-PaymentIvaMap -Records $records -Month $periodMonth -Year $periodYear

$invoiceEvaluations = New-Object System.Collections.Generic.List[object]
$doubtfulEvaluations = New-Object System.Collections.Generic.List[object]
$includedByUuid = @{}

foreach ($record in $recordsInPeriod | Where-Object { $_.Tipo -eq 'I' }) {
    $availableIva = $record.Iva
    $usesPaidIva = $false
    if ($record.MetodoPago -eq 'PPD' -or $record.FormaPago -eq '99') {
        if ($paymentIvaMap.ContainsKey($record.UUID)) {
            $availableIva = [decimal]::Round([decimal]$paymentIvaMap[$record.UUID], 2)
            $usesPaidIva = $true
        } else {
            $availableIva = [decimal]0
        }
    }

    $classification = $null
    if ($decisionStore.ContainsKey($record.UUID)) {
        $storedDecision = [int]$decisionStore[$record.UUID].Decision
        if ($storedDecision -eq 100) {
            $classification = @{
                Status = 'Include'
                Reason = 'Override manual guardado por UUID'
            }
        } else {
            $classification = @{
                Status = 'Exclude'
                Reason = 'Override manual guardado por UUID'
            }
        }
    } else {
        $classification = Get-Classification -Record $record -AvailableIva $availableIva
    }

    $evaluation = [pscustomobject]@{
        Fecha = $record.Fecha
        Emisor = $record.Emisor
        UUID = $record.UUID
        Tipo = $record.Tipo
        FormaPago = $record.FormaPago
        MetodoPago = $record.MetodoPago
        IvaDetectado = [decimal]::Round($availableIva, 2)
        IvaAcreditado = [decimal]0
        Status = $classification.Status
        Reason = $classification.Reason
        Descriptions = $record.Descriptions
        RelatedUuids = $record.RelatedUuids
        UsesPaidIva = $usesPaidIva
    }

    switch ($classification.Status) {
        'Include' {
            $evaluation.IvaAcreditado = $evaluation.IvaDetectado
            [void]$invoiceEvaluations.Add($evaluation)
            $includedByUuid[$evaluation.UUID] = $evaluation
        }
        'Doubtful' {
            [void]$doubtfulEvaluations.Add($evaluation)
        }
        default {
            [void]$invoiceEvaluations.Add($evaluation)
        }
    }
}

foreach ($doubtful in $doubtfulEvaluations | Sort-Object Fecha, UUID) {
    $decision = $null
    if ($decisionStore.ContainsKey($doubtful.UUID)) {
        $decision = [int]$decisionStore[$doubtful.UUID].Decision
    } else {
        $decision = Resolve-DoubtfulDecision -Record $doubtful
    }

    if ($null -eq $decision) {
        $doubtful.Status = 'PendingDecision'
        [void]$invoiceEvaluations.Add($doubtful)
        continue
    }

    if ($decision -eq 100) {
        $doubtful.Status = 'Include'
        $doubtful.IvaAcreditado = $doubtful.IvaDetectado
        $doubtful.Reason = $doubtful.Reason + '; decision final: incluir 100%'
        $includedByUuid[$doubtful.UUID] = $doubtful
    } else {
        $doubtful.Status = 'Exclude'
        $doubtful.IvaAcreditado = [decimal]0
        $doubtful.Reason = $doubtful.Reason + '; decision final: excluir'
    }

    $decisionStore[$doubtful.UUID] = [pscustomobject]@{
        UUID = $doubtful.UUID
        Decision = [int]$decision
        UpdatedAt = (Get-Date).ToString('s')
        Emisor = $doubtful.Emisor
        Note = 'Override tomado en flujo de dudosos'
    }

    [void]$invoiceEvaluations.Add($doubtful)
}

$egresoEvaluations = New-Object System.Collections.Generic.List[object]
foreach ($record in $recordsInPeriod | Where-Object { $_.Tipo -eq 'E' }) {
    $relatedIncluded = $false
    $relatedUsesPaidIva = $false
    foreach ($relatedUuid in $record.RelatedUuids) {
        if ($includedByUuid.ContainsKey($relatedUuid)) {
            $relatedIncluded = $true
            if ($includedByUuid[$relatedUuid].UsesPaidIva) {
                $relatedUsesPaidIva = $true
            }
            break
        }
    }

    $evaluation = [pscustomobject]@{
        Fecha = $record.Fecha
        Emisor = $record.Emisor
        UUID = $record.UUID
        Tipo = $record.Tipo
        FormaPago = $record.FormaPago
        MetodoPago = $record.MetodoPago
        IvaDetectado = $record.Iva
        IvaAcreditado = [decimal]0
        Status = 'Exclude'
        Reason = 'Egreso no relacionado con una factura incluida'
        Descriptions = $record.Descriptions
        RelatedUuids = $record.RelatedUuids
    }

    if ($relatedUsesPaidIva) {
        $evaluation.Reason = 'Egreso ya reflejado en el complemento de pago del CFDI relacionado'
    } elseif ($relatedIncluded -and $record.Iva -gt 0) {
        $evaluation.Status = 'Adjustment'
        $evaluation.IvaAcreditado = -1 * $record.Iva
        $evaluation.Reason = 'Egreso relacionado que compensa una factura incluida'
    }

    [void]$egresoEvaluations.Add($evaluation)
}

$allEvaluations = @($invoiceEvaluations.ToArray()) + @($egresoEvaluations.ToArray())
$pending = @($allEvaluations | Where-Object { $_.Status -eq 'PendingDecision' })

$includedForTotal = @($allEvaluations | Where-Object { $_.Status -in @('Include', 'Adjustment') })
$includedCount = @($includedForTotal).Count
$excludedCount = ($recordsInPeriod.Count - $includedCount)
$doubtfulCount = @($allEvaluations | Where-Object { $_.Reason -like '*decision final*' -or $_.Status -eq 'PendingDecision' }).Count
$total = [decimal]0
foreach ($item in $includedForTotal) {
    $total += $item.IvaAcreditado
}
$total = [decimal]::Round($total, 2)
$roundedTotal = [math]::Round([double]$total, 0, [System.MidpointRounding]::AwayFromZero)

$doubtfulList = @($allEvaluations |
    Where-Object { $_.Reason -like '*decision final*' -or $_.Status -eq 'PendingDecision' } |
    Sort-Object Fecha, UUID)

$doubtfulExport = @($doubtfulList | Select-Object Fecha, Emisor, UUID, @{Name='Descripcion';Expression={($_.Descriptions -join ' | ')}}, IvaDetectado, IvaAcreditado, Reason)

$includedList = @($allEvaluations |
    Where-Object { $_.Status -eq 'Include' } |
    Sort-Object Fecha, UUID |
    Select-Object Fecha, Emisor, UUID, @{Name='Descripcion';Expression={($_.Descriptions -join ' | ')}}, IvaDetectado, IvaAcreditado, Reason)

$excludedList = @($allEvaluations |
    Where-Object { $_.Status -eq 'Exclude' } |
    Sort-Object Fecha, UUID |
    Select-Object Fecha, Emisor, UUID, @{Name='Descripcion';Expression={($_.Descriptions -join ' | ')}}, IvaDetectado, IvaAcreditado, Reason)

$adjustmentList = @($allEvaluations |
    Where-Object { $_.Status -eq 'Adjustment' } |
    Sort-Object Fecha, UUID |
    Select-Object Fecha, Emisor, UUID, @{Name='Descripcion';Expression={($_.Descriptions -join ' | ')}}, IvaDetectado, IvaAcreditado, Reason)

$historyRoot = $HistoryFolder
if (-not (Test-Path -LiteralPath $historyRoot)) {
    [void](New-Item -ItemType Directory -Path $historyRoot -Force)
}

$folderLeaf = Split-Path -Path $FolderPath -Leaf
$periodKey = ('{0}-{1}' -f $periodYear, '{0:D2}' -f $periodMonth)
$baseName = '{0}_{1}' -f $periodKey, (Get-SafeFilePart $folderLeaf)
$snapshotPath = Join-Path $historyRoot ($baseName + '.json')
$csvPath = Join-Path $historyRoot ($baseName + '.csv')
$sourceParentPath = Split-Path -Path $FolderPath -Parent
$sourceParentCsvPath = Join-Path $sourceParentPath ($baseName + '.csv')
$previousSnapshot = $null

if (Test-Path -LiteralPath $snapshotPath) {
    $previousSnapshot = Get-Content -LiteralPath $snapshotPath -Raw | ConvertFrom-Json
}

$statusChanges = New-Object System.Collections.Generic.List[object]
if ($null -ne $previousSnapshot) {
    $previousMap = @{}
    foreach ($item in @($previousSnapshot.AllCfdis)) {
        $previousMap[[string]$item.UUID] = $item
    }

    foreach ($item in $allEvaluations) {
        if ($previousMap.ContainsKey($item.UUID)) {
            $old = $previousMap[$item.UUID]
            if ($old.Status -ne $item.Status -or [decimal]$old.IvaAcreditado -ne [decimal]$item.IvaAcreditado) {
                [void]$statusChanges.Add([pscustomobject]@{
                    UUID = $item.UUID
                    Fecha = $item.Fecha
                    Emisor = $item.Emisor
                    OldStatus = $old.Status
                    NewStatus = $item.Status
                    OldIvaAcreditado = [decimal]$old.IvaAcreditado
                    NewIvaAcreditado = [decimal]$item.IvaAcreditado
                })
            }
        } else {
            [void]$statusChanges.Add([pscustomobject]@{
                UUID = $item.UUID
                Fecha = $item.Fecha
                Emisor = $item.Emisor
                OldStatus = 'NoExistia'
                NewStatus = $item.Status
                OldIvaAcreditado = [decimal]0
                NewIvaAcreditado = [decimal]$item.IvaAcreditado
            })
        }
    }
}

$allCfdiExport = @($allEvaluations |
    Sort-Object Fecha, UUID |
    Select-Object Fecha, Emisor, UUID, Tipo, FormaPago, MetodoPago, @{Name='Descripcion';Expression={($_.Descriptions -join ' | ')}}, IvaDetectado, IvaAcreditado, Status, Reason)

$generatedAt = Get-Date

$snapshotMap = [ordered]@{}
$snapshotMap['GeneratedAt'] = $generatedAt
$snapshotMap['FolderPath'] = $FolderPath
$snapshotMap['Period'] = $Period
$snapshotMap['IvaAcreditableExact'] = $total
$snapshotMap['IvaAcreditableSatRounded'] = $roundedTotal
$snapshotMap['IncludedCfdiCount'] = $includedCount
$snapshotMap['ExcludedCfdiCount'] = $excludedCount
$snapshotMap['DoubtfulCfdiCount'] = $doubtfulCount
$snapshotMap['PendingDecisionCount'] = @($pending).Count
$snapshotMap['DecisionStorePath'] = $DecisionStorePath
$snapshotMap['IncludedCfdis'] = $includedList
$snapshotMap['ExcludedCfdis'] = $excludedList
$snapshotMap['AdjustmentCfdis'] = $adjustmentList
$snapshotMap['DoubtfulCfdis'] = $doubtfulExport
$snapshotMap['AllCfdis'] = $allCfdiExport
$snapshotMap['ChangesSincePrevious'] = $statusChanges.ToArray()
$snapshot = [pscustomobject]$snapshotMap

$snapshot | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $snapshotPath -Encoding UTF8
$effectiveCsvPath = $csvPath
try {
    $allCfdiExport | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8
} catch {
    $timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
    $fallbackCsvPath = Join-Path $historyRoot ($baseName + '_' + $timestamp + '.csv')
    $allCfdiExport | Export-Csv -LiteralPath $fallbackCsvPath -NoTypeInformation -Encoding UTF8
    $effectiveCsvPath = $fallbackCsvPath
}
Copy-Item -LiteralPath $effectiveCsvPath -Destination $sourceParentCsvPath -Force
Write-DecisionStore -Path $DecisionStorePath -Store $decisionStore

$resultMap = [ordered]@{}
$resultMap['FolderPath'] = $FolderPath
$resultMap['Period'] = $Period
$resultMap['IvaAcreditableExact'] = $total
$resultMap['IvaAcreditableSatRounded'] = $roundedTotal
$resultMap['IncludedCfdiCount'] = $includedCount
$resultMap['ExcludedCfdiCount'] = $excludedCount
$resultMap['DoubtfulCfdiCount'] = $doubtfulCount
$resultMap['PendingDecisionCount'] = @($pending).Count
$resultMap['HistoryJsonPath'] = $snapshotPath
$resultMap['HistoryCsvPath'] = $effectiveCsvPath
$resultMap['SourceParentCsvPath'] = $sourceParentCsvPath
$resultMap['DecisionStorePath'] = $DecisionStorePath
$resultMap['StoredOverrideCount'] = $decisionStore.Count
$resultMap['ChangeCountVsPrevious'] = $statusChanges.Count
$resultMap['ChangesSincePrevious'] = $statusChanges.ToArray()
$resultMap['IncludedCfdis'] = $includedList
$resultMap['ExcludedCfdis'] = $excludedList
$resultMap['DoubtfulCfdis'] = $doubtfulExport
[pscustomobject]$resultMap

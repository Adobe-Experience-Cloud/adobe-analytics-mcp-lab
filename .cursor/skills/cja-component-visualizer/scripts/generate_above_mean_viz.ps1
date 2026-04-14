# Generate visualization data for above-mean components
# Reads: synthetic_sample/*.json
# Outputs: synthetic_sample/visualization_data_above_mean.js

$SkillRoot = Split-Path $PSScriptRoot -Parent
$SampleDir = Join-Path $SkillRoot 'synthetic_sample'
function SamplePath($name) { Join-Path $SampleDir $name }

Write-Host "Generating visualization data for above-mean components..." -ForegroundColor Cyan

$componentIds = Get-Content (SamplePath 'above_mean_components.json') -Raw | ConvertFrom-Json
if ($componentIds -isnot [System.Array]) { $componentIds = @($componentIds) }
$connections = Get-Content (SamplePath 'network_mean_connections.json') -Raw | ConvertFrom-Json
if ($connections -isnot [System.Array]) { $connections = @($connections) }

Write-Host "Loaded $($componentIds.Count) components and $($connections.Count) connections" -ForegroundColor Green

Write-Host "Calculating usage from sample raw dataset..." -ForegroundColor Yellow
$rawConnections = Get-Content (SamplePath 'connections_sample_raw.json') -Raw | ConvertFrom-Json
if ($rawConnections -isnot [System.Array]) { $rawConnections = @($rawConnections) }

$realUsageMap = @{}
foreach ($conn in $rawConnections) {
    if ([string]::IsNullOrEmpty($conn.Source)) { continue }
    if ([string]::IsNullOrEmpty($conn.Target)) { continue }

    if (-not $realUsageMap.ContainsKey($conn.Source)) { $realUsageMap[$conn.Source] = 0 }
    $realUsageMap[$conn.Source] += $conn.Count

    if (-not $realUsageMap.ContainsKey($conn.Target)) { $realUsageMap[$conn.Target] = 0 }
    $realUsageMap[$conn.Target] += $conn.Count
}

Write-Host "Calculated usage for $($realUsageMap.Count) components from raw data" -ForegroundColor Green

$namesObj = Get-Content (SamplePath 'component_display_names.json') -Raw | ConvertFrom-Json
$componentNames = @{}
foreach ($p in $namesObj.PSObject.Properties) {
    $componentNames[$p.Name] = [string]$p.Value
}

function Get-ComponentType($id) {
    if ($id -match '^variables/') { return 'dimension' }
    elseif ($id -match '^metrics/') { return 'metric' }
    elseif ($id -match '^cm[A-F0-9]+@AdobeOrg') { return 'calculatedMetric' }
    elseif ($id -match '^s[A-F0-9]+@AdobeOrg') { return 'segment' }
    else { return 'other' }
}

$nodes = @()
$idMap = @{}
$counter = 1

Write-Host "`nBuilding nodes..." -ForegroundColor Yellow

foreach ($compId in $componentIds) {
    $simpleId = "n$counter"
    $type = Get-ComponentType $compId
    $name = $componentNames[$compId]
    $usage = if ($realUsageMap.ContainsKey($compId)) { $realUsageMap[$compId] } else { 1 }

    if (-not $name) {
        $name = "[Unknown: $($compId.Substring(0, [Math]::Min(30, $compId.Length)))]"
    }

    $nodes += @{
        id = $simpleId
        fullId = $compId
        name = $name
        type = $type
        usage = $usage
    }

    $idMap[$compId] = $simpleId
    $counter++
}

Write-Host "Created $($nodes.Count) nodes" -ForegroundColor Green

$links = @()
$unmapped = 0

foreach ($conn in $connections) {
    $sourceSimple = $idMap[$conn.Source]
    $targetSimple = $idMap[$conn.Target]

    if ($sourceSimple -and $targetSimple) {
        $links += @{
            source = $sourceSimple
            target = $targetSimple
            count = $conn.Count
        }
    } else {
        $unmapped++
    }
}

Write-Host "Mapped $($links.Count) connections ($unmapped unmapped)" -ForegroundColor Green

$dimCount = @($nodes | Where-Object { $_.type -eq 'dimension' }).Count
$metCount = @($nodes | Where-Object { $_.type -eq 'metric' }).Count
$calcCount = @($nodes | Where-Object { $_.type -eq 'calculatedMetric' }).Count
$segCount = @($nodes | Where-Object { $_.type -eq 'segment' }).Count

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$nodesJson = ConvertTo-Json -InputObject @($nodes) -Depth 10 -Compress
$linksJson = ConvertTo-Json -InputObject @($links) -Depth 10 -Compress

$js = @"
// CJA Component Network - synthetic lab sample (above mean)
// Generated: $timestamp
// Components: $($nodes.Count) ($metCount Metrics, $dimCount Dimensions, $calcCount Calc Metrics, $segCount Segments)
// Connections: $($links.Count)
// Selection: Components above mean usage within each category
// Usage: summed co-usage counts from connections_sample_raw.json (illustrative only)

const nodes = $nodesJson;
const apiConnections = $linksJson;
"@

$js | Out-File (SamplePath 'visualization_data_above_mean.js') -Encoding UTF8

Write-Host ""
Write-Host "Generated: synthetic_sample/visualization_data_above_mean.js" -ForegroundColor Green

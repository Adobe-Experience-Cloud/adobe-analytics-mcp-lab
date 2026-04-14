# Build network with components above mean usage per category
$SkillRoot = Split-Path $PSScriptRoot -Parent
$SampleDir = Join-Path $SkillRoot 'synthetic_sample'
function SamplePath($name) { Join-Path $SampleDir $name }

$connections = Get-Content (SamplePath 'connections_sample_raw.json') -Raw | ConvertFrom-Json
if ($connections -isnot [System.Array]) { $connections = @($connections) }

function Get-ComponentType($id) {
    if ($id -match '^variables/') { return 'dimension' }
    elseif ($id -match '^metrics/') { return 'metric' }
    elseif ($id -match '^cm[A-F0-9]+@AdobeOrg') { return 'calculatedMetric' }
    elseif ($id -match '^s[A-F0-9]+@AdobeOrg') { return 'segment' }
    else { return 'other' }
}

# Exclude standard fields
$excludePatterns = @(
    '^metrics/visits$',
    '^metrics/visitors$',
    '^metrics/occurrences$',
    '^metrics/bounces$',
    '^metrics/timespent',
    '^metrics/event',
    '^variables/daterange',
    '^variables/day$',
    '^variables/week$',
    '^variables/month$',
    '^variables/quarter$',
    '^variables/year$',
    '^variables/hour$',
    '^variables/minute$',
    '^variables/adobe_personid$',
    '^variables/personid',
    '^variables/timestamp'
)

function Should-Exclude($id) {
    foreach ($pattern in $excludePatterns) {
        if ($id -match $pattern) { return $true }
    }
    return $false
}

Write-Host "Building network with above-mean components per category..." -ForegroundColor Cyan

# Calculate total usage for each component
$realUsageMap = @{}
foreach ($conn in $connections) {
    if ([string]::IsNullOrEmpty($conn.Source) -or [string]::IsNullOrEmpty($conn.Target)) { continue }
    
    $sourceType = Get-ComponentType $conn.Source
    $targetType = Get-ComponentType $conn.Target
    $validTypes = @('dimension', 'metric', 'calculatedMetric', 'segment')
    
    if (($validTypes -contains $sourceType) -and (-not (Should-Exclude $conn.Source))) {
        if (-not $realUsageMap.ContainsKey($conn.Source)) {
            $realUsageMap[$conn.Source] = @{usage = 0; type = $sourceType}
        }
        $realUsageMap[$conn.Source].usage += $conn.Count
    }
    
    if (($validTypes -contains $targetType) -and (-not (Should-Exclude $conn.Target))) {
        if (-not $realUsageMap.ContainsKey($conn.Target)) {
            $realUsageMap[$conn.Target] = @{usage = 0; type = $targetType}
        }
        $realUsageMap[$conn.Target].usage += $conn.Count
    }
}

# Group by type and select above-mean components
$selectedComponents = @()

foreach ($type in @('dimension', 'metric', 'calculatedMetric', 'segment')) {
    $compsOfType = $realUsageMap.GetEnumerator() | 
        Where-Object { $_.Value.type -eq $type }
    
    if ($compsOfType.Count -eq 0) { continue }
    
    # Calculate mean for this type
    $usages = $compsOfType | ForEach-Object { $_.Value.usage }
    $mean = ($usages | Measure-Object -Average).Average
    
    # Select components above mean
    $selected = $compsOfType | Where-Object { $_.Value.usage -gt $mean } | Sort-Object {$_.Value.usage} -Descending
    
    Write-Host "  $type - Mean: $([Math]::Round($mean, 0)), Selected: $($selected.Count) of $($compsOfType.Count)" -ForegroundColor Yellow
    
    foreach ($comp in $selected) {
        $selectedComponents += $comp.Name
    }
}

Write-Host "`nTotal selected: $($selectedComponents.Count) above-mean components" -ForegroundColor Green

# Filter connections to only selected components
$networkConnections = @($connections | Where-Object {
    ($selectedComponents -contains $_.Source) -and ($selectedComponents -contains $_.Target)
})

Write-Host "Raw connections between selected: $($networkConnections.Count)" -ForegroundColor Yellow

# Deduplicate bidirectional connections
$deduped = @{}
foreach ($conn in $networkConnections) {
    $key1 = "$($conn.Source)|$($conn.Target)"
    $key2 = "$($conn.Target)|$($conn.Source)"
    
    if ($deduped.ContainsKey($key2)) {
        if ($conn.Count -gt $deduped[$key2].Count) {
            $deduped.Remove($key2)
            $deduped[$key1] = $conn
        }
    } else {
        $deduped[$key1] = $conn
    }
}

$uniqueConnections = @($deduped.Values)

# Calculate network density
$maxPossibleConnections = ($selectedComponents.Count * ($selectedComponents.Count - 1)) / 2
$density = if ($maxPossibleConnections -gt 0) { [Math]::Round(($uniqueConnections.Count / $maxPossibleConnections) * 100, 2) } else { 0 }

Write-Host "`nNetwork Statistics:" -ForegroundColor Cyan
Write-Host "  Components: $($selectedComponents.Count)"
Write-Host "  Connections: $($uniqueConnections.Count)"
Write-Host "  Density: $density%" -ForegroundColor Green

# Save results
$selectedComponents | ConvertTo-Json | Out-File (SamplePath 'above_mean_components.json') -Encoding UTF8
$uniqueConnections | ConvertTo-Json | Out-File (SamplePath 'network_mean_connections.json') -Encoding UTF8

Write-Host "`nSaved:" -ForegroundColor Green
Write-Host "  synthetic_sample/above_mean_components.json"
Write-Host "  synthetic_sample/network_mean_connections.json"

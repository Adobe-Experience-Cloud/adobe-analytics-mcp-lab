# Build network with statistical outliers (Mean + 1.5 SD per category)
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

Write-Host "Building network with statistical outliers (Mean + 1.5 SD)..." -ForegroundColor Cyan

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

# Group by type and select outliers
$selectedComponents = @()

foreach ($type in @('dimension', 'metric', 'calculatedMetric', 'segment')) {
    $compsOfType = $realUsageMap.GetEnumerator() | 
        Where-Object { $_.Value.type -eq $type }
    
    if ($compsOfType.Count -eq 0) { continue }
    
    # Calculate mean and std dev for this type
    $usages = $compsOfType | ForEach-Object { $_.Value.usage }
    $mean = ($usages | Measure-Object -Average).Average
    $variance = ($usages | ForEach-Object { [Math]::Pow($_ - $mean, 2) } | Measure-Object -Average).Average
    $stdDev = [Math]::Sqrt($variance)
    
    # Threshold: Mean + 1.5 * SD
    $threshold = $mean + (1.5 * $stdDev)
    
    # Select components above threshold
    $selected = $compsOfType | Where-Object { $_.Value.usage -gt $threshold } | Sort-Object {$_.Value.usage} -Descending
    
    Write-Host "  $type - Threshold: $([Math]::Round($threshold, 0)), Selected: $($selected.Count) of $($compsOfType.Count)" -ForegroundColor Yellow
    
    foreach ($comp in $selected) {
        Write-Host "    - usage: $($comp.Value.usage)" -ForegroundColor Gray
        $selectedComponents += $comp.Name
    }
}

Write-Host "`nTotal selected: $($selectedComponents.Count) statistical outliers" -ForegroundColor Green

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
$selectedComponents | ConvertTo-Json | Out-File (SamplePath 'statistical_outliers_components.json') -Encoding UTF8
$uniqueConnections | ConvertTo-Json | Out-File (SamplePath 'network_outliers_connections.json') -Encoding UTF8

Write-Host "`nSaved:" -ForegroundColor Green
Write-Host "  synthetic_sample/statistical_outliers_components.json"
Write-Host "  synthetic_sample/network_outliers_connections.json"

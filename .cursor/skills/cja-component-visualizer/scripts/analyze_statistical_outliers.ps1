# Analyze usage distribution and identify statistical outliers per category
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

Write-Host "Analyzing usage distributions per category..." -ForegroundColor Cyan

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

# Group by type
$byType = @{}
foreach ($comp in $realUsageMap.GetEnumerator()) {
    $type = $comp.Value.type
    if (-not $byType.ContainsKey($type)) {
        $byType[$type] = @()
    }
    $byType[$type] += @{id = $comp.Name; usage = $comp.Value.usage}
}

# Analyze each category
foreach ($type in @('dimension', 'metric', 'calculatedMetric', 'segment')) {
    if (-not $byType.ContainsKey($type)) { continue }
    
    $components = $byType[$type]
    $usages = $components | ForEach-Object { $_.usage }
    
    # Calculate statistics
    $count = $usages.Count
    $mean = ($usages | Measure-Object -Average).Average
    $sum = ($usages | Measure-Object -Sum).Sum
    $variance = ($usages | ForEach-Object { [Math]::Pow($_ - $mean, 2) } | Measure-Object -Average).Average
    $stdDev = [Math]::Sqrt($variance)
    $median = ($usages | Sort-Object)[[Math]::Floor($count / 2)]
    $q3 = ($usages | Sort-Object)[[Math]::Floor($count * 0.75)]
    
    # Different selection criteria
    $threshold2SD = $mean + (2 * $stdDev)
    $threshold15SD = $mean + (1.5 * $stdDev)
    $threshold1SD = $mean + (1 * $stdDev)
    $thresholdQ3 = $q3
    
    # Count how many meet each criteria
    $over2SD = ($components | Where-Object { $_.usage -gt $threshold2SD }).Count
    $over15SD = ($components | Where-Object { $_.usage -gt $threshold15SD }).Count
    $over1SD = ($components | Where-Object { $_.usage -gt $threshold1SD }).Count
    $overQ3 = ($components | Where-Object { $_.usage -gt $thresholdQ3 }).Count
    
    Write-Host "`n=== $type ($count components) ===" -ForegroundColor Yellow
    Write-Host "  Mean: $([Math]::Round($mean, 0))"
    Write-Host "  Median: $median"
    Write-Host "  Std Dev: $([Math]::Round($stdDev, 0))"
    Write-Host "  75th percentile (Q3): $q3"
    Write-Host ""
    Write-Host "  Selection Options:" -ForegroundColor Cyan
    Write-Host "    > Mean + 2.0 SD (>$([Math]::Round($threshold2SD, 0))): $over2SD components" -ForegroundColor $(if ($over2SD -eq 0) { 'Red' } else { 'White' })
    Write-Host "    > Mean + 1.5 SD (>$([Math]::Round($threshold15SD, 0))): $over15SD components" -ForegroundColor White
    Write-Host "    > Mean + 1.0 SD (>$([Math]::Round($threshold1SD, 0))): $over1SD components" -ForegroundColor White
    Write-Host "    > 75th percentile (>$q3): $overQ3 components" -ForegroundColor White
    
    # Show top 5 by usage
    Write-Host "  Top 5 by usage:" -ForegroundColor Gray
    $top5 = $components | Sort-Object usage -Descending | Select-Object -First 5
    foreach ($c in $top5) {
        Write-Host "    - usage: $($c.usage)" -ForegroundColor DarkGray
    }
}

Write-Host "`n=== RECOMMENDATION ===" -ForegroundColor Green
Write-Host "Using Mean + 1.5 SD tends to select the true standouts without being too restrictive."
Write-Host "This typically captures the top 5-15% that are genuinely high-usage, not just 'above average'."

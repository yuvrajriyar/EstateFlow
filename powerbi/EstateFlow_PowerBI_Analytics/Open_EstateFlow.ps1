[CmdletBinding()]
param([switch]$ResetOnly)
$ErrorActionPreference = 'Stop'
try {
    if (Get-Process -Name PBIDesktop -ErrorAction SilentlyContinue) {
        throw 'Close Power BI Desktop, then run Open EstateFlow again. Save first if you have edited the report.'
    }
    $project = $PSScriptRoot
    $report = Join-Path $project 'EstateFlow_Dashboard.Report'
    $definition = Join-Path $report 'definition'
    $pbip = Join-Path $project 'EstateFlow_Dashboard.pbip'
    if (!(Test-Path -LiteralPath $pbip)) { throw 'Keep this launcher inside the extracted EstateFlow project folder.' }
    $defaults = Get-Content -LiteralPath (Join-Path $project 'Open_Defaults.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $baseline = @{}
    foreach ($entry in $defaults.files) { $baseline[$entry.path] = $entry }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $changes = @()
    foreach ($file in Get-ChildItem -LiteralPath $definition -Recurse -File -Filter '*.json') {
        if ($file.Name -notin @('visual.json', 'page.json', 'report.json', 'pages.json')) { continue }
        $before = [System.IO.File]::ReadAllText($file.FullName)
        $data = $before | ConvertFrom-Json
        $relative = $file.FullName.Substring($report.Length + 1).Replace('\', '/')
        $entry = $baseline[$relative]
        if ($file.Name -eq 'pages.json') {
            if (!(Test-Path -LiteralPath (Join-Path $definition ('pages\' + $defaults.homePage + '\page.json')))) {
                throw 'The default Overview page is missing. No files have been changed.'
            }
            $data | Add-Member -NotePropertyName activePageName -NotePropertyValue $defaults.homePage -Force
        } else {
            if ($entry -and $entry.hasFilterConfig) {
                $data | Add-Member -NotePropertyName filterConfig -NotePropertyValue $entry.filterConfig -Force
            } else { $data.PSObject.Properties.Remove('filterConfig') }
            if ($file.Name -eq 'visual.json' -and $data.visual -and $data.visual.objects) {
                foreach ($general in @($data.visual.objects.general)) {
                    if ($general -and $general.properties) { $general.properties.PSObject.Properties.Remove('filter') }
                }
            }
            if ($file.Name -eq 'report.json') {
                if (!$data.settings) { $data | Add-Member -NotePropertyName settings -NotePropertyValue ([pscustomobject]@{}) -Force }
                $data.settings | Add-Member -NotePropertyName isPersistentUserStateDisabled -NotePropertyValue $true -Force
            }
        }
        $after = ($data | ConvertTo-Json -Depth 100) + [Environment]::NewLine
        # Compare parsed content to avoid changing untouched files merely for whitespace.
        $originalCompact = ($before | ConvertFrom-Json | ConvertTo-Json -Depth 100 -Compress)
        $afterCompact = ($data | ConvertTo-Json -Depth 100 -Compress)
        if ($originalCompact -cne $afterCompact) {
            $changes += [pscustomobject]@{ Path = $file.FullName; Relative = $relative; Before = $before; After = $after }
        }
    }
    # Flat backup filenames avoid adding the report's deep directory tree.
    $backup = Join-Path $project 'EF_Backups\R'
    $index = @()
    $number = 0
    foreach ($change in $changes) {
        $backupName = '{0:D3}.json' -f $number
        $backupPath = Join-Path $backup $backupName
        foreach ($path in @($change.Path, $backupPath)) {
            if ($path.Length -ge 260 -or [System.IO.Path]::GetDirectoryName($path).Length -ge 248) {
                throw 'Move the whole EstateFlow project folder to C:\EstateFlow, then open it with the launcher again.'
            }
        }
        $index += [pscustomobject]@{ Original = $change.Relative; Backup = $backupName }
        $number++
    }
    if ($changes.Count -gt 0) {
        [System.IO.Directory]::CreateDirectory($backup) | Out-Null
        $number = 0
        foreach ($change in $changes) {
            [System.IO.File]::WriteAllText((Join-Path $backup ('{0:D3}.json' -f $number)), $change.Before, $utf8)
            $number++
        }
        [System.IO.File]::WriteAllText((Join-Path $backup 'index.json'), (ConvertTo-Json -InputObject @($index) -Depth 4), $utf8)
    }
    try {
        foreach ($change in $changes) { [System.IO.File]::WriteAllText($change.Path, $change.After, $utf8) }
    } catch {
        foreach ($change in $changes) { [System.IO.File]::WriteAllText($change.Path, $change.Before, $utf8) }
        throw
    }
    Write-Host 'Filters cleared. Starting on National Overview.' -ForegroundColor Green
    if (!$ResetOnly) { Start-Process -FilePath $pbip }
    exit 0
} catch {
    Write-Host ('EstateFlow could not open: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}

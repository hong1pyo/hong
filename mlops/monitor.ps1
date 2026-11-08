param([int]$DurationSeconds = 90, [string]$LogPath = 'monitor.jsonl', [string]$TestImagePath = '')
$ErrorActionPreference = 'Continue'
$api = 'http://127.0.0.1:8765/api/analyze'
$statusUrl = 'http://127.0.0.1:8765/api/status'
$tmp = if ($TestImagePath) { $TestImagePath } else { Join-Path $env:TEMP 'animal-face-fixed-test.jpg' }
if (-not (Test-Path $tmp)) { throw "Fixed test image does not exist: $tmp" }
if (Test-Path $LogPath) { Remove-Item $LogPath -Force }
$end = (Get-Date).ToUniversalTime().AddSeconds($DurationSeconds)
while ((Get-Date).ToUniversalTime() -lt $end) {
  $start = (Get-Date).ToUniversalTime()
  $responseFile = Join-Path $env:TEMP 'animal-face-response.json'
  $http = & curl.exe -sS -o $responseFile -w '%{http_code}' -X POST -F "file=@$tmp;type=image/jpeg" $api
  $finish = (Get-Date).ToUniversalTime()
  $ok = $false; $version = 'unknown'; $status = [int]$http
  try {
    $body = Get-Content $responseFile -Raw | ConvertFrom-Json
    $hasWinner = $null -ne ($body.PSObject.Properties['winner'])
    $ok = ($status -eq 200 -and $hasWinner)
  } catch {}
  try { $versionResponse = Invoke-RestMethod -Uri $statusUrl -TimeoutSec 5; $version = [string]$versionResponse.version } catch {}
  $record = [ordered]@{ start=$start.ToString('o'); end=$finish.ToString('o'); latency_ms=[math]::Round(($finish-$start).TotalMilliseconds,1); status=$status; analysis_ok=[bool]$ok; version=$version }
  ($record | ConvertTo-Json -Compress) | Add-Content -LiteralPath $LogPath -Encoding utf8
  Start-Sleep -Seconds 1
}
if (-not $TestImagePath) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
Remove-Item $responseFile -Force -ErrorAction SilentlyContinue

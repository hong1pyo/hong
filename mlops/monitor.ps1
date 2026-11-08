param([int]$DurationSeconds = 90, [string]$LogPath = 'monitor.jsonl')
$ErrorActionPreference = 'Continue'
$api = 'http://127.0.0.1:8765/api/analyze'
$statusUrl = 'http://127.0.0.1:8765/api/status'
$tmp = Join-Path $env:TEMP 'animal-face-fixed-test.jpg'
$meta = (Invoke-WebRequest 'https://datasets-server.huggingface.co/first-rows?dataset=Pratheesh99%2Fanimal-faces-raw&config=default&split=val&offset=0&length=1' -UseBasicParsing).Content | ConvertFrom-Json
Invoke-WebRequest $meta.rows[0].row.image.src -OutFile $tmp -UseBasicParsing
if (Test-Path $LogPath) { Remove-Item $LogPath -Force }
$end = (Get-Date).ToUniversalTime().AddSeconds($DurationSeconds)
while ((Get-Date).ToUniversalTime() -lt $end) {
  $start = (Get-Date).ToUniversalTime()
  $responseFile = Join-Path $env:TEMP 'animal-face-response.json'
  $http = & curl.exe -sS -o $responseFile -w '%{http_code}' -X POST -F "file=@$tmp;type=image/jpeg" $api
  $finish = (Get-Date).ToUniversalTime()
  $ok = $false; $version = 'unknown'; $status = [int]$http
  try { $body = Get-Content $responseFile -Raw | ConvertFrom-Json; $ok = ($status -eq 200 -and $body.winner); $version = (Invoke-RestMethod $statusUrl).version } catch {}
  $record = [ordered]@{ start=$start.ToString('o'); end=$finish.ToString('o'); latency_ms=[math]::Round(($finish-$start).TotalMilliseconds,1); status=$status; analysis_ok=[bool]$ok; version=$version }
  ($record | ConvertTo-Json -Compress) | Add-Content -LiteralPath $LogPath -Encoding utf8
  Start-Sleep -Seconds 1
}
Remove-Item $tmp,$responseFile -Force -ErrorAction SilentlyContinue

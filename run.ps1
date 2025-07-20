# run.ps1

# 1) Read NLU_APIKEY from .env
$envLines = Get-Content .env | Where-Object { $_ -match '^NLU_APIKEY=' }
if (-not $envLines) {
    Write-Error "Could not find NLU_APIKEY in .env"; exit 1
}
$API_KEY = ($envLines -split '=', 2)[1].Trim()
Write-Host "Using API key: $API_KEY"

# 2) Params
$NOTEBOOK = 'semantic_feature_extraction.ipynb'
$FMT      = 'trimmed'
$OUT      = 'data/processed/extracted_features.json'

# 3) Start API and wait for /health
docker-compose up -d api

# wait up to 30s for the health endpoint to return 200
$attempts = 0
do {
    Start-Sleep -Seconds 1
    $attempts++
    try {
        $hc = Invoke-RestMethod -Uri "http://localhost:8000/health" -Headers @{ "X-API-Key" = $API_KEY }
        if ($hc.status -eq "ok") {
            Write-Host "API is healthy after $attempts second(s)."
            break
        }
    } catch {
        Write-Host "Waiting for API to be healthy ($attempts)..."
    }
} while ($attempts -lt 30)

if ($attempts -ge 30) {
    Write-Error "API did not become healthy in time."
    exit 1
}

# 4) Call the trimmed-run endpoint
$uri = "http://localhost:8000/run?notebook=$NOTEBOOK&fmt=$FMT"
Write-Host "Calling $uri"
try {
    Invoke-RestMethod `
      -Uri $uri `
      -Headers @{ "X-API-Key" = $API_KEY } `
      -OutFile $OUT -ErrorAction Stop
    Write-Host "✅ Wrote output to $OUT"
} catch {
    Write-Error "API call failed: $($_.Exception.Message)"
    exit 1
}

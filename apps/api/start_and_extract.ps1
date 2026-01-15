# Start backend process
$pythonPath = "D:\idea\jobpilot-ai\apps\api\venv\Scripts\python.exe"
$workdir = "D:\idea\jobpilot-ai\apps\api"

Write-Host "Starting backend..."
$backendProc = Start-Process -FilePath $pythonPath `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning" `
  -WorkingDirectory $workdir `
  -WindowStyle Hidden `
  -PassThru

Write-Host "Backend PID: $($backendProc.Id)"
Start-Sleep -Seconds 3

# Fetch OpenAPI schema
Write-Host "`nFetching OpenAPI schema..."
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/openapi.json" -UseBasicParsing
    $swagger = $response.Content | ConvertFrom-Json
    $paths = @($swagger.paths.PSObject.Properties.Name)
    
    Write-Host "`nRelevant endpoints found:"
    $relevant = $paths | Where-Object { $_ -match "auth|resume|resumes|job|jobs|match|matches|apply|applykit" } | Sort-Object
    $relevant | ForEach-Object { Write-Host "  $_" }
    
    Write-Host "`nAll endpoint methods:"
    foreach ($path in $relevant) {
        $methods = @($swagger.paths.$path.PSObject.Properties.Name)
        foreach ($method in $methods) {
            if ($method -match "^(get|post|put|delete|patch)$") {
                $op = $swagger.paths.$path.$method
                $summary = if ($op.summary) { " - $($op.summary)" } else { "" }
                Write-Host "  [$($method.ToUpper())] $path$summary"
            }
        }
    }
    
} catch {
    Write-Host "ERROR: Failed to fetch OpenAPI: $_"
    $backendProc | Stop-Process -Force
    exit 1
}

# Save for later use
$relevant | ConvertTo-Json | Out-File "endpoints.json"
Write-Host "`nEndpoints saved to endpoints.json"

Write-Host "`nBackend is running on http://127.0.0.1:8000"
Write-Host "Press Ctrl+C to stop the backend"

# Keep running
while ($backendProc.HasExited -eq $false) {
    Start-Sleep -Seconds 1
}

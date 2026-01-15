# Start backend and log output
$proc = Start-Process -FilePath "D:\idea\jobpilot-ai\apps\api\venv\Scripts\python.exe" `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "debug" `
  -WorkingDirectory "D:\idea\jobpilot-ai\apps\api" `
  -RedirectStandardOutput "backend_stdout.log" `
  -RedirectStandardError "backend_stderr.log" `
  -NoNewWindow `
  -PassThru

Write-Host "Backend started with PID $($proc.Id)"
Write-Host "Waiting 3 seconds for startup..."
Start-Sleep -Seconds 3

Write-Host "Requesting /api/v1/openapi.json..."
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/openapi.json" `
      -UseBasicParsing -TimeoutSec 5 -ErrorAction Continue
    Write-Host "Response status: $($response.StatusCode)"
} catch {
    Write-Host "Request failed: $_"
}

Write-Host "Waiting 2 seconds..."
Start-Sleep -Seconds 2

Write-Host "Checking if backend process still running..."
$proc = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Process still running!"
    $proc | Stop-Process -Force
} else {
    Write-Host "Process has exited."
}

Write-Host "`n=== STDOUT ==="
Get-Content backend_stdout.log

Write-Host "`n=== STDERR ==="
Get-Content backend_stderr.log

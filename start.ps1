# KosztorysAI - skrypt startowy dla PowerShell
# Uzycie:
#   .\start.ps1              # build + serwer
#   .\start.ps1 -SkipBuild   # tylko serwer

param(
    [switch]$SkipBuild,
    [int]$Port = 8000
)

Write-Host ""
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host "   KosztorysAI" -ForegroundColor Cyan
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host ""

# Build frontendu
if (-not $SkipBuild) {
    Write-Host "  [1/2] Budowanie frontendu React..." -ForegroundColor Yellow
    $frontendDir = "C:\Users\Gabriel\Desktop\MVP kosztorysy\buildai-app"

    Push-Location $frontendDir
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [!] Blad budowania frontendu!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "  Frontend gotowy." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "  [1/2] Pomijam build (-SkipBuild)" -ForegroundColor Gray
}

# Start serwera przez WSL
Write-Host "  [2/2] Uruchamianie serwera na porcie $Port..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Aplikacja: http://localhost:$Port" -ForegroundColor Green
Write-Host "  API docs:  http://localhost:$Port/api/docs" -ForegroundColor Green
Write-Host "  Zatrzymaj: Ctrl+C" -ForegroundColor Gray
Write-Host ""

wsl -e bash -c "cd /mnt/c/Users/Gabriel/clawd/kosztorysAI && python3 server.py --port $Port"

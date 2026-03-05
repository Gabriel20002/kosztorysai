@echo off
chcp 65001 >nul
echo.
echo  ================================================
echo   KosztorysAI - Uruchamianie serwera
echo  ================================================
echo.

set SKIP_BUILD=0
if "%1"=="--skip-build" set SKIP_BUILD=1

if "%SKIP_BUILD%"=="0" (
    echo  [1/2] Budowanie frontendu React...
    cd /d "C:\Users\Gabriel\Desktop\MVP kosztorysy\buildai-app"
    call npm run build
    if errorlevel 1 (
        echo.
        echo  [!] Blad budowania frontendu
        pause
        exit /b 1
    )
    echo  Frontend gotowy.
    echo.
) else (
    echo  [1/2] Pomijam build ^(--skip-build^)
)

echo  [2/2] Uruchamianie serwera ^(WSL^)...
echo.
echo  Aplikacja bedzie dostepna pod: http://localhost:8000
echo  Zamknij to okno aby zatrzymac serwer.
echo.

wsl -e bash -c "cd /mnt/c/Users/Gabriel/clawd/kosztorysAI && python3 server.py"

pause

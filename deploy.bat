@echo off
chcp 65001 >nul
echo.
echo  ╔══════════════════════════════════════╗
echo  ║   KosztorysAI - Deploy do Railway    ║
echo  ╚══════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM Sprawdz czy Railway CLI jest zainstalowany
where railway >nul 2>nul
if errorlevel 1 (
    echo  [!] Instalowanie Railway CLI...
    npm install -g @railway/cli
    if errorlevel 1 (
        echo  [!] Blad instalacji Railway CLI.
        echo      Zainstaluj recznie: npm install -g @railway/cli
        pause
        exit /b 1
    )
)

echo  [1/3] Logowanie do Railway...
railway login
if errorlevel 1 (
    echo  [!] Blad logowania.
    pause
    exit /b 1
)

echo.
echo  [2/3] Inicjalizacja projektu...
railway init
if errorlevel 1 (
    echo  [!] Blad inicjalizacji (lub projekt juz istnieje - kontynuuje).
)

echo.
echo  [3/3] Wgrywanie do chmury...
railway up --detach
if errorlevel 1 (
    echo  [!] Blad deployu.
    pause
    exit /b 1
)

echo.
echo  ══════════════════════════════════════
echo   Gotowe! Adres URL:
railway domain
echo  ══════════════════════════════════════
echo.
pause

@echo off
chcp 65001 >nul
title kosztorysAI v3.0
cls
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                                                  ║
echo  ║         🏗️  kosztorysAI v3.0                    ║
echo  ║                                                  ║
echo  ║    Profesjonalne kosztorysy budowlane           ║
echo  ║    PDF → Kosztorys PDF + ATH                    ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  Uruchamianie serwera...
echo.
cd /d "%~dp0"
start "" http://localhost:8503
python -m streamlit run main.py --server.port 8503
pause

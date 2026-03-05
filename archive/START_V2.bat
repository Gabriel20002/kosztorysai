@echo off
title kosztorysAI v2.0
echo.
echo ====================================
echo   kosztorysAI v2.0
echo   355+ pozycji KNR + eksport ATH
echo ====================================
echo.
cd /d "%~dp0"
python -m streamlit run app_v2.py --server.port 8501
pause

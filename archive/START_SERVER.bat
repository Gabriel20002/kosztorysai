@echo off
chcp 65001 >nul
title kosztorysAI Server
cls
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║         kosztorysAI Server                       ║
echo  ║         http://localhost:8503                    ║
echo  ╚══════════════════════════════════════════════════╝
echo.
cd /d "%~dp0"
python run_server.py

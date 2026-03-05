# -*- coding: utf-8 -*-
"""
kosztorysAI - Server runner
Uruchamia Streamlit jako daemon
"""

import subprocess
import sys
import time
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

def run_streamlit():
    """Uruchom Streamlit server"""
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(BASE_DIR / "app.py"),
        "--server.port", "8503",
        "--server.headless", "true",
        "--server.runOnSave", "false",
        "--browser.gatherUsageStats", "false",
    ]
    
    print("=" * 50)
    print("  kosztorysAI Server")
    print("  http://localhost:8503")
    print("=" * 50)
    print()
    
    while True:
        print(f"[{time.strftime('%H:%M:%S')}] Starting server...")
        process = subprocess.Popen(cmd, cwd=str(BASE_DIR))
        process.wait()
        print(f"[{time.strftime('%H:%M:%S')}] Server stopped. Restarting in 3s...")
        time.sleep(3)

if __name__ == "__main__":
    run_streamlit()

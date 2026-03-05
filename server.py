# -*- coding: utf-8 -*-
"""
KosztorysAI Server
Obsługuje API + React frontend — jeden proces, jeden port.

Lokalnie:
    python server.py

W chmurze (Railway/Render):
    PORT ustawiany automatycznie przez platformę.
"""

import os
import sys
import base64

# Załaduj .env jeśli istnieje (lokalnie)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import argparse
import tempfile
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import uvicorn

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from kosztorys_generator import KosztorysGenerator
from exceptions import PDFParsingError, NormaPROError

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="KosztorysAI", version="1.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

DIST_DIR = HERE / "dist"

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "frontend": (DIST_DIR / "index.html").exists()}


@app.post("/api/generate")
async def generate(
    file: UploadFile = File(...),
    nazwa: str = Form(""),
    inwestor: str = Form(""),
    wykonawca: str = Form(""),
    format: str = Form("both"),
    stawka_rg: float = Form(35.0),
    stawka_sprzetu: float = Form(100.0),
    kp: float = Form(70.0),
    zysk: float = Form(12.0),
    vat: float = Form(23.0),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Wymagany plik PDF")
    if format not in ("ath", "pdf", "both"):
        raise HTTPException(400, "format musi być: ath, pdf lub both")

    base_name = Path(file.filename).stem
    safe_name = "".join(c for c in base_name if c.isalnum() or c in "-_")[:40] or "kosztorys"

    dane_tytulowe = {
        "nazwa_inwestycji": nazwa or base_name,
        "adres_inwestycji": "",
        "inwestor": inwestor,
        "adres_inwestora": "",
        "wykonawca": wykonawca,
        "adres_wykonawcy": "",
        "branza": "budowlana",
        "sporzadzil": "",
        "data": datetime.now().strftime("%m.%Y"),
    }

    # Wszystko w pamięci — tymczasowy folder auto-czyszczony
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        pdf_path = tmpdir / "input.pdf"
        try:
            pdf_path.write_bytes(await file.read())
        except Exception as e:
            raise HTTPException(500, f"Błąd zapisu pliku: {e}")

        base_out = str(tmpdir / safe_name)
        output_ath = f"{base_out}.ath" if format in ("ath", "both") else None
        output_pdf = f"{base_out}.pdf" if format in ("pdf", "both") else None

        try:
            gen = KosztorysGenerator()
            gen.params.update({
                "stawka_rg": stawka_rg,
                "stawka_sprzetu": stawka_sprzetu,
                "kp_procent": kp,
                "z_procent": zysk,
                "vat_procent": vat,
            })
            results = gen.generate(
                str(pdf_path),
                dane_tytulowe=dane_tytulowe,
                output_ath=output_ath,
                output_pdf=output_pdf,
            )
        except PDFParsingError as e:
            raise HTTPException(422, f"Błąd parsowania PDF: {e}")
        except NormaPROError as e:
            raise HTTPException(500, f"Błąd generowania ATH: {e}")
        except Exception as e:
            raise HTTPException(500, str(e))

        if not results:
            raise HTTPException(422, "Nie znaleziono pozycji w PDF")

        # Odczytaj pliki jako base64 — potem tmpdir jest usuwany automatycznie
        files = {}
        for fmt_key, path in results.items():
            data = Path(path).read_bytes()
            files[fmt_key] = {
                "filename": f"{safe_name}_kosztorys.{fmt_key}",
                "content": base64.b64encode(data).decode(),
            }

    return {"files": files}


# ---------------------------------------------------------------------------
# Frontend statyczny
# ---------------------------------------------------------------------------

def mount_frontend():
    if not DIST_DIR.exists():
        print(f"[!] Brak dist/ — frontend niedostępny ({DIST_DIR})")
        return

    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    index_html = (DIST_DIR / "index.html").read_text(encoding="utf-8")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        static_file = DIST_DIR / full_path
        if static_file.is_file():
            return FileResponse(str(static_file))
        return HTMLResponse(index_html)

    print(f"[✓] Frontend: {DIST_DIR}")


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--dev", action="store_true")
    args = parser.parse_args()

    if not args.dev:
        mount_frontend()

    print(f"\nKosztorysAI → http://localhost:{args.port}")
    print(f"API docs    → http://localhost:{args.port}/api/docs\n")

    uvicorn.run(app, host=args.host, port=args.port)

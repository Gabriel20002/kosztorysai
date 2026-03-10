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

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import uvicorn

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from kosztorys_generator import KosztorysGenerator
from exceptions import PDFParsingError, NormaPROError
from database import engine, get_db
import models
import auth
from sqlalchemy.orm import Session

# Utwórz tabele przy starcie (jeśli nie istnieją)
models.Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="KosztorysAI", version="1.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

DIST_DIR = HERE / "dist"

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "frontend": (DIST_DIR / "index.html").exists()}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class RegisterBody(BaseModel):
    email: str
    password: str
    name: str

class LoginBody(BaseModel):
    email: str
    password: str

def _user_dict(user: models.User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "plan": user.plan,
        "is_admin": user.is_admin,
        "can_generate": user.can_generate,
    }


@app.post("/api/auth/register")
def register(body: RegisterBody, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(400, detail="Email już zarejestrowany")
    if len(body.password) < 8:
        raise HTTPException(400, detail="Hasło musi mieć min. 8 znaków")
    user = models.User(
        email=body.email,
        name=body.name,
        hashed_password=auth.hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": auth.create_token(user.id), "user": _user_dict(user)}


@app.post("/api/auth/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not auth.verify_password(body.password, user.hashed_password):
        raise HTTPException(401, detail="Nieprawidłowy email lub hasło")
    return {"token": auth.create_token(user.id), "user": _user_dict(user)}


@app.get("/api/auth/me")
def me(current_user: models.User = Depends(auth.get_current_user)):
    return _user_dict(current_user)


# ---------------------------------------------------------------------------
# Historia
# ---------------------------------------------------------------------------

@app.get("/api/history")
def history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(models.Kosztorys)
        .filter(models.Kosztorys.user_id == current_user.id)
        .order_by(models.Kosztorys.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": k.id,
            "name": k.name,
            "filename": k.filename,
            "positions_count": k.positions_count,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        }
        for k in items
    ]


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
    current_user: models.User = Depends(auth.get_optional_user),
    db: Session = Depends(get_db),
):
    # Sprawdź uprawnienie do generowania
    if not current_user:
        raise HTTPException(401, "Musisz być zalogowany aby generować kosztorysy")
    if not current_user.can_generate and not current_user.is_admin:
        raise HTTPException(403, "Brak uprawnień do generowania. Skontaktuj się z administratorem.")

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

    # Zapisz do historii jeśli użytkownik zalogowany
    if current_user:
        record = models.Kosztorys(
            user_id=current_user.id,
            name=nazwa or base_name,
            filename=file.filename,
        )
        db.add(record)
        db.commit()

    return {"files": files}


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@app.get("/api/admin/users")
def admin_list_users(
    admin: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db),
):
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return [_user_dict(u) for u in users]


class PatchUserBody(BaseModel):
    can_generate: bool = None
    is_admin: bool = None

@app.patch("/api/admin/users/{user_id}")
def admin_patch_user(
    user_id: int,
    body: PatchUserBody,
    admin: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Użytkownik nie istnieje")
    if body.can_generate is not None:
        user.can_generate = body.can_generate
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    db.commit()
    db.refresh(user)
    return _user_dict(user)


@app.get("/api/admin/feedback")
def admin_get_feedback(
    admin: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db),
):
    items = db.query(models.Feedback).order_by(models.Feedback.created_at.desc()).limit(500).all()
    return [
        {
            "id": f.id,
            "user_id": f.user_id,
            "rating": f.rating,
            "message": f.message,
            "context": f.context,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in items
    ]


@app.post("/api/admin/seed")
def admin_seed(
    email: str,
    db: Session = Depends(get_db),
):
    """Jednorazowe: nadaj uprawnienia admina użytkownikowi po emailu.
    Działa tylko gdy w bazie nie ma jeszcze żadnego admina (zabezpieczenie)."""
    existing_admin = db.query(models.User).filter(models.User.is_admin == True).first()
    if existing_admin:
        raise HTTPException(403, "Admin już istnieje — użyj panelu admin")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(404, "Nie znaleziono użytkownika o tym emailu")
    user.is_admin = True
    user.can_generate = True
    db.commit()
    return {"ok": True, "admin": user.email}


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackBody(BaseModel):
    rating: int        # 1–5
    message: str = ""
    context: str = "general"

@app.post("/api/feedback")
def submit_feedback(
    body: FeedbackBody,
    current_user: models.User = Depends(auth.get_optional_user),
    db: Session = Depends(get_db),
):
    if not (1 <= body.rating <= 5):
        raise HTTPException(400, "Ocena musi być w zakresie 1–5")
    fb = models.Feedback(
        user_id=current_user.id if current_user else None,
        rating=body.rating,
        message=body.message[:2000] if body.message else "",
        context=body.context,
    )
    db.add(fb)
    db.commit()
    return {"ok": True}

@app.get("/api/feedback")
def get_feedback(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Widok dla admina — wszystkie opinie."""
    items = db.query(models.Feedback).order_by(models.Feedback.created_at.desc()).limit(200).all()
    return [
        {
            "id": f.id,
            "user_id": f.user_id,
            "rating": f.rating,
            "message": f.message,
            "context": f.context,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in items
    ]


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

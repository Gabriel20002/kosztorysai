# -*- coding: utf-8 -*-
"""
KosztorysAI Server
Obsługuje API + React frontend — jeden proces, jeden port.

Lokalnie:
    python server.py

W chmurze (Railway/Render):
    PORT ustawiany automatycznie przez platformę.
"""

import asyncio
import os
import sys
import base64
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)

# Załaduj .env jeśli istnieje (lokalnie)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import argparse
import tempfile
from pathlib import Path
from datetime import datetime, timezone

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

# Migracja: dodaj nowe kolumny jeśli nie istnieją (bezpieczne — idempotentne)
def _run_migrations():
    from sqlalchemy import text
    with engine.connect() as conn:
        for sql in [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS can_generate BOOLEAN DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP DEFAULT NULL",
            "CREATE TABLE IF NOT EXISTS feedback (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), rating INTEGER NOT NULL, message TEXT, context VARCHAR, created_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS contact_messages (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), email VARCHAR NOT NULL, category VARCHAR NOT NULL, message TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW())",
        ]:
            try:
                conn.execute(text(sql))
            except Exception:
                pass
        conn.commit()

_run_migrations()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="KosztorysAI", version="1.0", docs_url="/api/docs")

# Mount frontend przy imporcie modułu (działa zarówno z gunicorn jak i bezpośrednio)
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

def _send_activation_email(to_email: str, name: str):
    """Wysyła email o aktywacji konta. Wymaga zmiennych SMTP_HOST, SMTP_USER, SMTP_PASS."""
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user:
        log.info("SMTP nie skonfigurowany — pomijam email aktywacji dla %s", to_email)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Twoje konto KosztorysAI zostało aktywowane"
    msg["From"] = smtp_from
    msg["To"] = to_email

    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#0b1015;color:#e2e8f0;border-radius:12px;">
      <h2 style="color:#38bdf8;margin-bottom:8px;">Konto aktywowane</h2>
      <p>Cześć {name},</p>
      <p>Twoje konto w <strong>KosztorysAI</strong> zostało aktywowane. Możesz już generować kosztorysy.</p>
      <a href="https://kosztorysai.com/dashboard"
         style="display:inline-block;margin-top:24px;padding:12px 28px;background:#0ea5e9;color:#fff;
                border-radius:8px;text-decoration:none;font-weight:bold;">
        Przejdź do generatora
      </a>
      <p style="margin-top:32px;color:#64748b;font-size:12px;">
        KosztorysAI &mdash; wersja beta &mdash; <a href="mailto:kosztorysyai@gmail.com" style="color:#64748b;">kosztorysyai@gmail.com</a>
      </p>
    </div>
    """
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, to_email, msg.as_string())
        log.info("Email aktywacji wysłany do %s", to_email)
    except Exception as e:
        log.warning("Błąd wysyłania emaila aktywacji do %s: %s", to_email, e)


# mount_frontend() wołane NA KOŃCU pliku — po wszystkich trasach /api/*
# Catch-all GET /{full_path:path} musi być zarejestrowany OSTATNI,
# żeby trasy API były dopasowywane przed nim.

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
        terms_accepted_at=datetime.now(timezone.utc),
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

    # Odczytaj plik async — potem ciężka praca idzie do thread pool
    try:
        pdf_content = await file.read()
    except Exception as e:
        raise HTTPException(500, f"Błąd odczytu pliku: {e}")

    params_gen = {
        "stawka_rg": stawka_rg,
        "stawka_sprzetu": stawka_sprzetu,
        "kp_procent": kp,
        "z_procent": zysk,
        "vat_procent": vat,
    }

    def _sync_generate():
        """Cała ciężka praca (CPU + AI API) w osobnym wątku — nie blokuje event loop."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            pdf_path = tmpdir_path / "input.pdf"
            pdf_path.write_bytes(pdf_content)

            base_out = str(tmpdir_path / safe_name)
            output_ath = f"{base_out}.ath" if format in ("ath", "both") else None
            output_pdf = f"{base_out}.pdf" if format in ("pdf", "both") else None

            gen = KosztorysGenerator()
            gen.params.update(params_gen)
            results = gen.generate(
                str(pdf_path),
                dane_tytulowe=dane_tytulowe,
                output_ath=output_ath,
                output_pdf=output_pdf,
            )

            if not results:
                raise ValueError("Nie znaleziono pozycji w PDF")

            files_out = {}
            ath_text = None
            for fmt_key, path in results.items():
                data = Path(path).read_bytes()
                files_out[fmt_key] = {
                    "filename": f"{safe_name}_kosztorys.{fmt_key}",
                    "content": base64.b64encode(data).decode(),
                }
                if fmt_key == "ath":
                    try:
                        ath_text = Path(path).read_text(encoding="cp1250", errors="replace")
                    except Exception:
                        ath_text = Path(path).read_text(encoding="utf-8", errors="replace")

            return gen, files_out, ath_text

    try:
        gen, files, ath_text = await asyncio.to_thread(_sync_generate)
    except PDFParsingError as e:
        raise HTTPException(422, f"Błąd parsowania PDF: {e}")
    except NormaPROError as e:
        raise HTTPException(500, f"Błąd generowania ATH: {e}")
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

    # Zapisz do historii jeśli użytkownik zalogowany
    if current_user:
        record = models.Kosztorys(
            user_id=current_user.id,
            name=nazwa or base_name,
            filename=file.filename,
            positions_count=len(getattr(gen, "_last_pozycje", None) or []),
        )
        db.add(record)
        db.commit()

    # Weryfikacja AI w osobnym wątku — nie blokuje event loop
    verification = None
    try:
        import ai_verifier
        pozycje = getattr(gen, "_last_pozycje", None)
        podsumowanie = getattr(gen, "_last_podsumowanie", None)
        if pozycje and podsumowanie:
            verification = await asyncio.to_thread(
                ai_verifier.verify_kosztorys, pozycje, podsumowanie, gen.params, ath_text
            )
    except Exception as e:
        log.warning("Weryfikacja AI nieudana: %s", e)

    return {"files": files, "verification": verification}


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
    was_active = user.can_generate
    if body.can_generate is not None:
        user.can_generate = body.can_generate
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    db.commit()
    db.refresh(user)
    if body.can_generate and not was_active:
        _send_activation_email(user.email, user.name)
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
    current_user: models.User = Depends(auth.get_admin_user),
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
# Contact
# ---------------------------------------------------------------------------

class ContactBody(BaseModel):
    email: str
    category: str
    message: str

@app.post("/api/contact")
def submit_contact(
    body: ContactBody,
    current_user: models.User = Depends(auth.get_optional_user),
    db: Session = Depends(get_db),
):
    if not body.email or not body.message.strip():
        raise HTTPException(400, "Email i wiadomość są wymagane")
    if len(body.message) > 5000:
        raise HTTPException(400, "Wiadomość nie może przekraczać 5000 znaków")
    allowed = {"opinia", "zapytanie", "blad", "inne"}
    if body.category not in allowed:
        raise HTTPException(400, "Nieprawidłowa kategoria")
    msg = models.ContactMessage(
        user_id=current_user.id if current_user else None,
        email=body.email,
        category=body.category,
        message=body.message.strip(),
    )
    db.add(msg)
    db.commit()
    return {"ok": True}

@app.get("/api/admin/contact")
def admin_get_contact(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(403, "Brak dostępu")
    items = db.query(models.ContactMessage).order_by(models.ContactMessage.created_at.desc()).limit(500).all()
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "email": m.email,
            "category": m.category,
            "message": m.message,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in items
    ]


# Catch-all SPA fallback — MUSI być ostatni, po wszystkich trasach /api/*
mount_frontend()

# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    print(f"\nKosztorysAI → http://localhost:{args.port}")
    print(f"API docs    → http://localhost:{args.port}/api/docs\n")

    uvicorn.run(app, host=args.host, port=args.port)

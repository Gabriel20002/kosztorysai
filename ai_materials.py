# -*- coding: utf-8 -*-
"""
ai_materials.py

Szacuje skład materiałowy per KNR przez AI (Claude Haiku) dla pozycji
bez danych w knr_materialy.json.

Wynik cache'owany w learned_kosztorysy/knr_materialy_ai.json.
Funkcja: estimate_materials_batch(items) -> {knr_norm: [{name, jm, nz, ce}]}
"""

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

_CACHE_PATH = Path(__file__).parent / "learned_kosztorysy" / "knr_materialy_ai.json"
_BATCH_SIZE = 25  # max KNR na jedno wywołanie API

SYSTEM_MATERIALS = """Jesteś doświadczonym kosztorysantem budowlanym w Polsce.
Podajesz realny skład materiałowy dla robót budowlanych wg katalogów KNR.

ZASADY:
- Dla każdej pozycji podaj listę materiałów: nazwa, jm (jednostka), nz (ilość na jm roboty), ce (cena PLN/jm)
- WAŻNE: suma(nz * ce) musi być ≈ wartości "m_per_jm" podanej w danych wejściowych
- Podaj realistyczne ceny materiałów budowlanych 2024/2025 w Polsce
- Nazwy materiałów po polsku, konkretne (np. "cement portlandzki CEM I 42.5" nie "cement")
- Jeśli robota jest czysto usługowa (brak materiałów) zwróć pustą listę []
- Odpowiadaj WYŁĄCZNIE jako poprawny JSON, bez tekstu przed/po"""


def _load_cache() -> dict:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}


def _save_cache(cache: dict):
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def _normalize(mats: list, target_m: float) -> list:
    """
    Skaluje nz tak aby sum(nz*ce) = target_m.
    Jeśli target_m=0 lub lista pusta — zwraca listę bez zmian.
    """
    if not mats or target_m <= 0:
        return mats
    total = sum(m['nz'] * m['ce'] for m in mats if m.get('ce', 0) > 0)
    if total <= 0:
        return mats
    factor = target_m / total
    return [
        {**m, 'nz': round(m['nz'] * factor, 6)}
        for m in mats
    ]


def _call_api(items: list, api_key: str) -> dict:
    """
    items: [{knr_norm, knr, opis, jm, m_per_jm}, ...]
    Zwraca: {knr_norm: [{name, jm, nz, ce}]}
    """
    import anthropic

    payload = [
        {
            "knr_norm": it['knr_norm'],
            "knr": it['knr'],
            "opis": it['opis'][:80],
            "jm": it['jm'],
            "m_per_jm": round(it['m_per_jm'], 4),
        }
        for it in items
    ]

    user_msg = (
        "Podaj skład materiałowy dla poniższych pozycji kosztorysowych.\n"
        "Dla każdej pozycji: lista materiałów gdzie suma(nz*ce) ≈ m_per_jm.\n\n"
        f"POZYCJE:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Format odpowiedzi (klucz = knr_norm):\n"
        '{"KNR2-010122-01": [{"name": "cement", "jm": "kg", "nz": 5.2, "ce": 0.65}, ...], ...}'
    )

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=SYSTEM_MATERIALS,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def estimate_materials_batch(items: list) -> dict:
    """
    items: [{knr_norm, knr, opis, jm, m_per_jm}, ...]
    Zwraca: {knr_norm: [{name, jm, nz, ce}]} — dla wszystkich items z M>0.
    Wyniki są cache'owane w knr_materialy_ai.json.
    Pozycje bez ANTHROPIC_API_KEY → zwraca {}.
    """
    if not items:
        return {}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {}

    cache = _load_cache()

    # Odfiltruj już scache'owane
    to_fetch = [it for it in items if it['knr_norm'] not in cache and it.get('m_per_jm', 0) > 0]

    if not to_fetch:
        # Wszystkie są w cache
        return {it['knr_norm']: cache[it['knr_norm']] for it in items if it['knr_norm'] in cache}

    log.info("AI materials: szacuję %d KNR (batch po %d)", len(to_fetch), _BATCH_SIZE)

    # Batch calls
    for start in range(0, len(to_fetch), _BATCH_SIZE):
        batch = to_fetch[start:start + _BATCH_SIZE]
        try:
            result = _call_api(batch, api_key)
            # Normalizuj i zapisz do cache
            for it in batch:
                norm_key = it['knr_norm']
                raw_mats = result.get(norm_key, [])
                if isinstance(raw_mats, list) and raw_mats:
                    normalized = _normalize(raw_mats, it['m_per_jm'])
                    # Filtruj materiały z ce <= 0
                    normalized = [m for m in normalized if m.get('ce', 0) > 0 and m.get('nz', 0) > 0]
                    cache[norm_key] = normalized
                else:
                    cache[norm_key] = []  # brak materiałów — zapamiętaj żeby nie pytać ponownie
            _save_cache(cache)
            log.info("AI materials: zapisano batch %d-%d do cache", start + 1, start + len(batch))
        except Exception as e:
            log.warning("AI materials błąd API (batch %d): %s", start, e)

    # Zwróć wyniki dla wszystkich items
    return {it['knr_norm']: cache.get(it['knr_norm'], []) for it in items}

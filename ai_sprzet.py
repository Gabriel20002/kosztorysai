# -*- coding: utf-8 -*-
"""
ai_sprzet.py

Szacuje sprzęt per KNR przez AI (Claude Haiku) dla pozycji
bez danych w knr_sprzet.json.

Wynik cache'owany w learned_kosztorysy/knr_sprzet_ai.json.
Funkcja: estimate_sprzet_batch(items) -> {knr_norm: [{name, jm, nz, ce}]}
"""

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

_CACHE_PATH = Path(__file__).parent / "learned_kosztorysy" / "knr_sprzet_ai.json"

SYSTEM_SPRZET = """Jesteś doświadczonym kosztorysantem budowlanym w Polsce.
Podajesz skład sprzętowy (maszyny i sprzęt) dla robót budowlanych wg katalogów KNR.

ZASADY:
- Podaj listę maszyn/sprzętu: nazwa, jm (zawsze "m-g"), nz (godziny maszynowe na jm roboty), ce (stawka PLN/m-g)
- Stawki realistyczne 2024/2025 wg Sekocenbud: koparka 150-200, spycharka 130-160, samochód skrzyniowy 80-120, samochód dostawczy 50-70, żuraw 200-300, betoniarka 20-40, wiertarka elektryczna 5-15, wyciąg 10-20, zagęszczarka 20-40, przecinarka 15-25 PLN/m-g
- Nazwy konkretne: "samochód skrzyniowy 5 t", "koparka gąsienicowa 0.25 m3", "zagęszczarka wibracyjna 150 kg" — nie "sprzęt budowlany"
- Jeśli "Wartość sprzętu" > 0, ZAWSZE podaj co najmniej jedną maszynę — suma(nz * ce) ≈ wartości podanej
- Jeśli robota jest ręczna i sprzęt zbędny LUB "Wartość sprzętu" = 0 — zwróć []
- ZAKAZ: nie wpisuj materiałów, robocizny ani czynności — tylko konkretne maszyny/urządzenia
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


def _normalize(machines: list, target_s: float) -> list:
    """Skaluje nz tak aby sum(nz*ce) = target_s."""
    if not machines or target_s <= 0:
        return machines
    total = sum(m['nz'] * m['ce'] for m in machines if m.get('ce', 0) > 0)
    if total <= 0:
        return machines
    factor = target_s / total
    return [{**m, 'nz': round(m['nz'] * factor, 6)} for m in machines]


# Próg poniżej którego wartość s_per_jm uznajemy za placeholder (S=1 z bazy).
# S=1.0 PLN/jm to stara wartość zastępcza — traktuj jako "nieznana".
_S_PLACEHOLDER_THRESHOLD = 1.0


def _call_api_one(item: dict, api_key: str) -> list:
    import anthropic

    s = item['s_per_jm']
    if s > _S_PLACEHOLDER_THRESHOLD:
        # Znana wartość S — AI normalizuje do tej kwoty
        s_line = (
            f"Wartość sprzętu: {s:.4f} PLN/{item['jm']}\n\n"
            "KRYTYCZNE: podaj co najmniej jedną maszynę — suma(nz*ce) ≈ wartości powyżej."
        )
    else:
        # s_per_jm = 1.0 to placeholder lub S nieznana — AI szacuje typowy sprzęt
        s_line = (
            "Wartość sprzętu: nieznana, ale robota WYMAGA maszyn (S > 0).\n\n"
            "KRYTYCZNE: ZAWSZE podaj co najmniej jedną maszynę z typowymi nakładami wg KNR.\n"
            "Podaj sprzęt jako JSON — nakłady wg norm branżowych."
        )

    user_msg = (
        f"KNR: {item['knr']}\n"
        f"Opis: {item['opis'][:80]}\n"
        f"Jednostka miary: {item['jm']}\n"
        f"{s_line}\n"
        'Format: [{"name": "samochód skrzyniowy 5 t", "jm": "m-g", "nz": 0.05, "ce": 100.0}, ...]'
    )

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_SPRZET,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def estimate_sprzet_batch(items: list) -> dict:
    """
    items: [{knr_norm, knr, opis, jm, s_per_jm}, ...]
    Zwraca: {knr_norm: [{name, jm, nz, ce}]}
    """
    if not items:
        return {}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {}

    cache = _load_cache()
    # Wywołuj AI dla KNRów bez cache — zarówno gdy s_per_jm>0 jak i gdy s<1 (placeholder)
    to_fetch = [it for it in items if it['knr_norm'] not in cache and it.get('s_per_jm', 0) > 0]

    if not to_fetch:
        return {it['knr_norm']: cache.get(it['knr_norm'], []) for it in items if it['knr_norm'] in cache}

    log.info("AI sprzęt: szacuję %d KNR", len(to_fetch))

    saved = 0
    for it in to_fetch:
        norm_key = it['knr_norm']
        try:
            raw = _call_api_one(it, api_key)
            if isinstance(raw, list) and raw:
                s = it['s_per_jm']
                if s > _S_PLACEHOLDER_THRESHOLD:
                    # Znana wartość S — normalizuj
                    normalized = _normalize(raw, s)
                else:
                    # Placeholder — zostaw nakłady AI bez skalowania
                    normalized = raw
                normalized = [m for m in normalized if m.get('ce', 0) > 0 and m.get('nz', 0) > 0]
                if normalized:
                    cache[norm_key] = normalized
                    saved += 1
                    continue
            # AI zwróciło [] — cachuj tylko gdy S była prawdziwą wartością (nie placeholderem)
            # Dla s <= threshold (placeholder): nie cachuj — spróbuj ponownie następnym razem
            s = it['s_per_jm']
            if s > _S_PLACEHOLDER_THRESHOLD:
                cache[norm_key] = []
                saved += 1
            else:
                log.warning("AI sprzęt zwrócił [] dla placeholder s=%s: %s", s, it['knr'])
        except Exception as e:
            log.warning("AI sprzęt błąd dla %s: %s", it['knr'], e)

    _save_cache(cache)
    log.info("AI sprzęt: zapisano %d/%d KNR do cache", saved, len(to_fetch))

    return {it['knr_norm']: cache.get(it['knr_norm'], []) for it in items}

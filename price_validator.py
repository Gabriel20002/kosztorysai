# -*- coding: utf-8 -*-
"""
price_validator.py

Waliduje i koryguje ceny materiałów budowlanych.
Jeśli cena jest podejrzanie niska → pyta Claude Haiku o aktualną cenę (cached).

Cache: learned_kosztorysy/price_corrections.json
"""

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

_CACHE_PATH = Path(__file__).parent / "learned_kosztorysy" / "price_corrections.json"

# ── Minimalne ceny realne 2024/2025 dla typów materiałów ─────────────────────
# (fragment nazwy lowercase, jm) → min_cena
# Jeśli ce < min_cena → podejrzana i wymaga korekty

_PRICE_FLOORS = [
    # Przewody i kable elektryczne
    (('kabelkow', 'przewód', 'przewod', 'kabel solar', 'kable solar',
      'kabel yky', 'kabel ykxs', 'kabel n2xh', 'kabel nh90', 'kabel aykyk',
      'kabel yfdy', 'ydy', 'ydyp', 'ytdy', 'utp kat'), 'm', 3.0),
    # Rury elektroinstalacyjne cienkie (akceptowalnie tanie)
    (('rura elektro', 'rura winidur', 'winidur', 'rura pvc elektro'), 'm', 1.0),
    # Bednarka, drut uziemiający
    (('bednarka', 'drut fezn', 'drut ocynk'), 'm', 5.0),
    # Kable solarne / fotowoltaiczne (NIE 'pv' — matchuje 'pvc')
    (('solar', 'fotowolt', 'panel pv', 'kabel pv'), 'm', 6.0),
    # Puszki instalacyjne
    (('puszka instal', 'puszka podtynk', 'puszka natynk'), 'szt', 3.0),
    # Oprawy oświetleniowe
    (('oprawa', 'oprava', 'oprawa oswietl'), 'szt', 20.0),
    # Gniazda, łączniki
    (('gniazdo', 'łącznik', 'lacznik', 'wyłącznik', 'wylacznik'), 'szt', 5.0),
]

# ── Maksymalne ceny realne (sufit) ───────────────────────────────────────────
# Jeśli ce > max_cena → AI ustawiło ce=m_per_jm zamiast ceny jednostkowej → wymagana korekta
_PRICE_CEILINGS = [
    # (fragmenty_nazwy, jm, max_ce)
    (('cement',),                       'kg',  5.0),
    (('zaprawa',),                      'kg',  8.0),
    (('klej',),                         'kg', 15.0),
    (('tynk',),                         'kg', 10.0),
    (('piasek',),                       'm3', 250.0),
    (('żwir', 'zwir', 'kruszywo'),      'm3', 400.0),
    (('beton',),                        'm3', 800.0),
    (('farba', 'lakier', 'emalia'),     'l',  100.0),
    (('grunt', 'primer', 'preparat'),   'l',   60.0),
    (('styropian', 'eps'),              'm2', 100.0),
    (('wełna', 'welna', 'rockwool'),    'm2', 150.0),
    (('papa',),                         'm2',  80.0),
    (('folia',),                        'm2',  20.0),
    (('stal zbrojeniowa', 'pręt', 'pret'), 'kg', 20.0),
    (('drewno', 'tarcica'),             'm3', 4000.0),
    (('woda',),                         'm3',  20.0),
    (('gips',),                         'kg',   8.0),
]


# ── Bezwzględne wykluczenia (tanie z natury, nie wymagają korekty) ────────────
_EXEMPT_FRAGMENTS = (
    'woda', 'tlen', 'piasek', 'żwir', 'zwir', 'gaz', 'śruba', 'sruba',
    'wkręt', 'wkret', 'nakrętka', 'nakretka', 'podkładka', 'podkladka',
    'opaska', 'kołek rozp', 'kolek rozp', 'uszczelka', 'klips', 'złączka',
    'podkładka', 'końcówka', 'koncowka',
)

SYSTEM_PRICE = """Jesteś doświadczonym kosztorysantem budowlanym w Polsce.
Podajesz aktualne ceny katalogowe materiałów budowlanych i instalacyjnych na rok 2024/2025.
Odpowiadaj WYŁĄCZNIE jako poprawny JSON bez tekstu przed/po."""


def _is_exempt(name_l: str) -> bool:
    return any(f in name_l for f in _EXEMPT_FRAGMENTS)


def _get_ceiling(name_l: str, jm: str) -> float:
    """Zwraca maksymalną akceptowalną cenę lub 0 jeśli brak warunku."""
    name_main = name_l.split('(')[0][:40].strip()
    jm_l = jm.lower().rstrip('.')
    for fragments, jm_pat, max_ce in _PRICE_CEILINGS:
        if jm_l.startswith(jm_pat) and any(f in name_main for f in fragments):
            return max_ce
    return 0.0


def _get_floor(name_l: str, jm: str) -> float:
    """Zwraca minimalną oczekiwaną cenę dla materiału lub 0 jeśli brak warunku.
    Sprawdza tylko pierwsze 40 znaków nazwy (unika fałszywych dopasowań z opisów)."""
    if _is_exempt(name_l):
        return 0.0
    # Sprawdzaj tylko główną część nazwy (przed nawiasem lub po pierwszych 40 zn.)
    name_main = name_l.split('(')[0][:40].strip()
    jm_l = jm.lower().rstrip('.')
    for fragments, jm_pat, min_ce in _PRICE_FLOORS:
        if jm_l.startswith(jm_pat) and any(f in name_main for f in fragments):
            return min_ce
    return 0.0


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


def _cache_key(name: str, jm: str) -> str:
    return f"{name.strip().lower()}|{jm.strip().lower()}"


def _ask_ai_price(items: list, api_key: str) -> dict:
    """
    items: [{'name': ..., 'jm': ..., 'ce_old': ..., 'floor': ...}, ...]
    Zwraca: {'name|jm': new_ce, ...}
    """
    import anthropic

    user_msg = (
        "Podaj realistyczne ceny detaliczne/hurtowe 2024/2025 (PLN/jm) dla poniższych "
        "materiałów budowlanych i instalacyjnych w Polsce.\n"
        "WAŻNE: stare_ce są przestarzałe i zaniżone — podaj AKTUALNĄ cenę rynkową.\n"
        "Przykłady referencyjne 2024/2025:\n"
        "- przewód YDY 3x1.5mm²: 6.50 zł/m\n"
        "- przewody kabelkowe 2x1.5mm²: 4.50 zł/m\n"
        "- puszka instalacyjna p/t śr.60mm: 3.50 zł/szt\n"
        "- rura instalacyjna PVC DN16: 1.80 zł/m\n"
        "- kabel solarny 6mm²: 12.00 zł/m\n\n"
        + json.dumps(
            [{'name': it['name'], 'jm': it['jm'], 'stara_ce': it['ce_old']}
             for it in items],
            ensure_ascii=False,
        )
        + '\n\nFormat: [{"name": "...", "jm": "...", "ce": 12.50}, ...]'
    )

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=512,
        system=SYSTEM_PRICE,
        messages=[{'role': 'user', 'content': user_msg}],
    )
    text = msg.content[0].text.strip()
    if text.startswith('```'):
        text = text.split('```', 2)[1]
        if text.startswith('json'):
            text = text[4:]
        text = text.strip()
    start, end = text.find('['), text.rfind(']')
    if start != -1 and end != -1:
        text = text[start:end + 1]
    results = json.loads(text)

    out = {}
    for r in results:
        key = _cache_key(r.get('name', ''), r.get('jm', ''))
        ce = float(r.get('ce', 0) or 0)
        if ce > 0:
            out[key] = ce
    return out


def validate_and_correct_prices(mats: list) -> list:
    """
    Sprawdza ceny listy materiałów [{name, jm, nz, ce, ...}].
    Dla podejrzanie niskich cen pobiera aktualną cenę z AI (cached).
    Zwraca listę z poprawionymi cenami.
    """
    if not mats:
        return mats

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    cache = _load_cache()

    # Sprawdz każdy materiał
    to_fix = []
    for mat in mats:
        name = mat.get('name', '')
        jm = mat.get('jm', 'szt')
        ce = float(mat.get('ce', 0) or 0)
        name_l = name.lower()

        key = _cache_key(name, jm)
        if key in cache:
            continue  # już znamy aktualną cenę

        floor = _get_floor(name_l, jm)
        if floor > 0 and ce < floor:
            log.info("Podejrzana cena (za niska): '%s' %s ce=%.2f (min=%.2f)", name, jm, ce, floor)
            to_fix.append({'name': name, 'jm': jm, 'ce_old': ce, 'floor': floor})
            continue

        ceiling = _get_ceiling(name_l, jm)
        if ceiling > 0 and ce > ceiling:
            log.warning("Podejrzana cena (za wysoka): '%s' %s ce=%.2f (max=%.2f) — prawdopodobnie ce=m_per_jm", name, jm, ce, ceiling)
            to_fix.append({'name': name, 'jm': jm, 'ce_old': ce, 'floor': floor})

    if to_fix and api_key:
        log.info("Walidacja cen: zapytanie AI o %d materiałów", len(to_fix))
        try:
            ai_prices = _ask_ai_price(to_fix, api_key)
            # Enforce: cena po korekcie nie może być niższa od floor
            floor_map = {_cache_key(it['name'], it['jm']): it['floor'] for it in to_fix}
            for key, ce in ai_prices.items():
                floor = floor_map.get(key, 0.0)
                cache[key] = max(ce, floor)
            _save_cache(cache)
            log.info("Walidacja cen: AI zwrócił %d poprawek", len(ai_prices))
        except Exception as e:
            log.warning("Walidacja cen AI błąd: %s", e)
    elif to_fix and not api_key:
        # Brak AI — użyj floor jako fallback
        for it in to_fix:
            key = _cache_key(it['name'], it['jm'])
            cache[key] = it['floor']
        log.info("Walidacja cen: brak API, użyto floor dla %d materiałów", len(to_fix))

    # Zastosuj korekty
    result = []
    for mat in mats:
        name = mat.get('name', '')
        jm = mat.get('jm', 'szt')
        key = _cache_key(name, jm)
        if key in cache:
            corrected_ce = cache[key]
            if corrected_ce != mat.get('ce'):
                log.debug("Korekta ceny: '%s' %.2f → %.2f", name, mat.get('ce', 0), corrected_ce)
            result.append({**mat, 'ce': corrected_ce})
        else:
            result.append(mat)

    return result

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
_BATCH_SIZE = 1  # 1 KNR na wywołanie — niezawodny JSON

SYSTEM_MATERIALS = """Jesteś doświadczonym kosztorysantem budowlanym w Polsce.
Podajesz realny skład materiałowy dla robót budowlanych wg katalogów KNR.

ZASADY:
- Dla każdej pozycji podaj listę materiałów: nazwa, jm (jednostka), nz (ilość na jm roboty), ce (cena PLN/jm)
- WAŻNE: suma(nz * ce) musi być ≈ wartości "m_per_jm" podanej w danych wejściowych
- Podaj realistyczne ceny materiałów budowlanych 2024/2025 w Polsce
- Nazwy materiałów po polsku, konkretne (np. "cement portlandzki CEM I 42.5" nie "cement")
- KRYTYCZNE: jeśli "Wartość materiałów" > 0, ZAWSZE podaj co najmniej jeden materiał — nigdy nie zwracaj []
  Jeśli praca polega na montażu gotowego elementu (kabina, bateria, wpust itp.), tym materiałem jest ten element
- Jeśli "Wartość materiałów" = 0, wtedy możesz zwrócić []
- BEZWZGLĘDNY ZAKAZ: w liście materiałów NIE może pojawić się czynność ani usługa.
  NIE wpisuj: demontaż, montaż (jako usługa), rozebranie, transport, wywóz, czyszczenie, malowanie itp.
  Materiał to fizyczny przedmiot kupowany na budowie: rura, kształtka, cement, klej, śruba, kabina, zawór itp.
  Jeśli robota to demontaż/rozbiórka i nie ma fizycznych materiałów — zwróć []
- Odpowiadaj WYŁĄCZNIE jako poprawny JSON, bez tekstu przed/po"""


# Czasowniki oznaczające czynności — materiał o takiej nazwie jest błędem
_ACTION_VERBS = {
    'demontaż', 'montaż', 'rozebranie', 'rozbiórka', 'wykonanie', 'układanie',
    'roboty', 'prace', 'instalacja', 'wymiana', 'naprawa', 'czyszczenie',
    'malowanie', 'oczyszczenie', 'załadunek', 'transport', 'wywóz', 'usunięcie',
    'odtłuszczenie', 'obróbka', 'wykucie', 'zamurowanie', 'tynkowanie',
    'betonowanie', 'zbrojenie', 'szpachlowanie', 'gruntowanie',
    'zeskrobanie', 'skucie', 'odbicie', 'kucie', 'ługowanie', 'przecieranie',
    'zasypanie', 'zagęszczenie', 'uzupełnienie', 'nawiercenie', 'przebicie',
    'likwidacja', 'demontowanie', 'rozbieranie', 'skuwanie',
}


def _filter_action_materials(mats: list) -> list:
    """Usuwa z listy wpisy których nazwa jest czynnością, nie materiałem."""
    result = []
    for m in mats:
        name = (m.get('name') or '').strip()
        first_word = name.split()[0].lower().rstrip(',') if name else ''
        if first_word in _ACTION_VERBS:
            log.warning("AI zwrócił czynność zamiast materiału — pomijam: '%s'", name)
            continue
        result.append(m)
    return result


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


def _call_api_one(item: dict, api_key: str) -> list:
    """
    Jeden KNR → lista materiałów [{name, jm, nz, ce}].
    """
    import anthropic

    user_msg = (
        f"KNR: {item['knr']}\n"
        f"Opis: {item['opis'][:80]}\n"
        f"Jednostka miary: {item['jm']}\n"
        f"Wartość materiałów: {item['m_per_jm']:.4f} PLN/{item['jm']}\n\n"
        "Podaj skład materiałowy jako JSON — lista materiałów, gdzie suma(nz*ce) ≈ wartości powyżej.\n"
        'Format: [{"name": "nazwa", "jm": "jm", "nz": 1.23, "ce": 4.56}, ...]'
    )

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_MATERIALS,
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

    # Wywołania jeden po jednym — niezawodne
    saved = 0
    for it in to_fetch:
        norm_key = it['knr_norm']
        try:
            raw_mats = _call_api_one(it, api_key)
            if isinstance(raw_mats, list) and raw_mats:
                raw_mats = _filter_action_materials(raw_mats)
                normalized = _normalize(raw_mats, it['m_per_jm'])
                normalized = [m for m in normalized if m.get('ce', 0) > 0 and m.get('nz', 0) > 0]
                cache[norm_key] = normalized
                saved += 1
            elif it.get('m_per_jm', 0) <= 0:
                # Brak materiałów i M=0 — poprawne, cachuj jako puste
                cache[norm_key] = []
                saved += 1
            # else: M>0 ale AI zwrócił [] — nie cachuj, spróbuj ponownie następnym razem
        except Exception as e:
            log.warning("AI materials błąd dla %s: %s", it['knr'], e)
            # Nie cachuj błędu jeśli M>0 — spróbuj ponownie następnym razem

    _save_cache(cache)
    log.info("AI materials: zapisano %d/%d KNR do cache", saved, len(to_fetch))

    # Zwróć wyniki dla wszystkich items
    return {it['knr_norm']: cache.get(it['knr_norm'], []) for it in items}

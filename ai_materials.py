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
- "ce" to REALNA CENA RYNKOWA materiału (PLN/jm), NIE koszt roboty na jednostkę pracy.
  NIGDY nie ustawiaj ce = wartości "m_per_jm". ce musi być rzeczywistą ceną zakupu.
- "nz" to fizyczna ilość materiału zużywana na 1 jednostkę roboty (nakład jednostkowy).
  Przykład: 1 m2 tynku = ~50 kg cementu (nz=50, jm=kg, ce=0.85)
- Suma (nz * ce) powinna być zbliżona do "Wartości materiałów", ale PRIORYTETEM są realne ceny ce.
- Nazwy materiałów po polsku, konkretne (np. "cement portlandzki CEM I 42.5" nie "cement")
- KRYTYCZNE: jeśli "Wartość materiałów" > 0, ZAWSZE podaj co najmniej jeden materiał — nigdy nie zwracaj []
  Jeśli praca polega na montażu gotowego elementu (kabina, bateria, wpust itp.), tym materiałem jest ten element
- Jeśli "Wartość materiałów" = 0, wtedy możesz zwrócić []
- BEZWZGLĘDNY ZAKAZ: w liście materiałów NIE może pojawić się czynność ani usługa.
  Materiał to fizyczny przedmiot kupowany na budowie: rura, kształtka, cement, klej, śruba, kabina, zawór itp.
  Jeśli robota to demontaż/rozbiórka i nie ma fizycznych materiałów — zwróć []

PRZYKŁADY REALISTYCZNYCH CEN 2024/2025 (ce):
- cement portlandzki CEM I 42.5: 0.85 PLN/kg
- piasek budowlany: 80 PLN/m3
- żwir / kruszywo: 100 PLN/m3
- beton gotowy B20/C16/20: 350 PLN/m3
- zaprawa murarska M10: 1.20 PLN/kg
- klej do płytek C1: 2.50 PLN/kg
- klej do styropianu: 2.00 PLN/kg
- farba lateksowa: 15 PLN/l
- gruntolateks / preparat gruntujący: 8 PLN/l
- styropian EPS100 gr.10cm: 12 PLN/m2
- wełna mineralna fasadowa 10cm: 25 PLN/m2
- folia paroizolacyjna: 2.50 PLN/m2
- papa termozgrzewalna: 25 PLN/m2
- tynk gipsowy maszynowy: 1.80 PLN/kg
- stal zbrojeniowa: 4.50 PLN/kg
- drewno tartaczne: 1200 PLN/m3

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


# Korekty jednostek miary dla typowych materiałów budowlanych
# klucz = fragment nazwy (lowercase), wartość = poprawna jm
_JM_CORRECTIONS = {
    'kabel': 'm', 'przewód': 'm', 'przewod': 'm', 'linka': 'm',
    'rura': 'm', 'rurka': 'm', 'rurociąg': 'm', 'rurociag': 'm',
    'bednarka': 'm', 'taśma': 'm', 'tasma': 'm',
    'listwa': 'm', 'profil': 'm', 'kątownik': 'm', 'katownik': 'm',
    'uszczelka': 'szt', 'złączka': 'szt', 'zlaczka': 'szt',
    'wspornik': 'szt', 'uchwyt': 'szt', 'obejma': 'szt',
    'śruba': 'szt', 'sruba': 'szt', 'wkręt': 'szt', 'wkret': 'szt',
    'nakrętka': 'szt', 'nakretka': 'szt', 'podkładka': 'szt', 'podkladka': 'szt',
    'puszka': 'szt', 'skrzynka': 'szt', 'rozdzielnica': 'szt',
    'wyłącznik': 'szt', 'wylacznik': 'szt', 'łącznik': 'szt', 'lacznik': 'szt',
    'gniazdo': 'szt', 'wtyk': 'szt', 'wtyczka': 'szt',
    'bezpiecznik': 'szt', 'wkładka': 'szt', 'zabezpieczenie': 'szt',
    'lampa': 'szt', 'oprawa': 'szt', 'świetlówka': 'szt', 'swietlowka': 'szt',
    'żarówka': 'szt', 'zarowka': 'szt', 'led': 'szt',
    'zawór': 'szt', 'zawor': 'szt', 'kurek': 'szt', 'zawór': 'szt',
    'blacha': 'kg',
    'klej': 'kg', 'masa': 'kg', 'pianka': 'szt', 'uszczelniacz': 'szt',
    'cement': 'kg', 'zaprawa': 'kg', 'beton': 'm3',
    'farba': 'l', 'lakier': 'l', 'grunt': 'l',
    'preparat': 'l', 'primer': 'l', 'żywica': 'l', 'zywica': 'l',
    'plastyfikator': 'l', 'emulsja': 'l',
    'papa': 'm2', 'folia': 'm2', 'siatka': 'm2',
    'płyta': 'm2', 'plyta': 'm2', 'panel': 'm2',
    'kostka': 'm2', 'płytka': 'm2', 'plytka': 'm2',
    'piasek': 'm3', 'żwir': 'm3', 'zwir': 'm3', 'gruz': 'm3',
}


def _correct_jm(name: str, jm: str) -> str:
    """Koryguje jednostkę miary materiału na podstawie słownika."""
    name_l = name.lower()
    for fragment, correct_jm in _JM_CORRECTIONS.items():
        if fragment in name_l:
            if jm != correct_jm:
                log.debug("Korekta JM: '%s' %s → %s", name, jm, correct_jm)
            return correct_jm
    return jm


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


def _is_lazy_response(mats: list, m_per_jm: float) -> bool:
    """
    Wykrywa wzorzec leniwej odpowiedzi AI: ce ≈ m_per_jm, nz ≈ 1.0.
    AI ustawiło ce = koszt roboczy zamiast ce = cena rynkowa materiału.
    """
    if not mats or m_per_jm <= 0:
        return False
    for mat in mats:
        ce = float(mat.get('ce', 0) or 0)
        nz = float(mat.get('nz', 0) or 0)
        # Jeśli nz ≈ 1 i ce ≈ m_per_jm → AI skopiowało koszt jako cenę
        if 0.8 <= nz <= 1.2 and 0.7 <= (ce / m_per_jm) <= 1.3:
            return True
    return False


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
    Gdy m_per_jm=0: szacuje typowe materiały bez celu wartościowego.
    """
    import anthropic

    m = item['m_per_jm']
    if m > 0:
        m_line = (
            f"Wartość materiałów: {m:.4f} PLN/{item['jm']}\n\n"
            "Podaj skład materiałowy jako JSON — lista materiałów, gdzie suma(nz*ce) ≈ wartości powyżej."
        )
    else:
        # M=0 w bazie, ale opis sugeruje materiały — AI szacuje od zera
        m_line = (
            "Wartość materiałów: nieznana (brak w bazie KNR).\n\n"
            "KRYTYCZNE: Robota wymaga fizycznych materiałów — ZAWSZE podaj co najmniej jeden.\n"
            "Podaj typowe materiały wg KNR z realistycznymi cenami 2024/2025 w Polsce.\n"
            "Nakłady nz = ilość materiału na 1 jednostkę roboty."
        )

    user_msg = (
        f"KNR: {item['knr']}\n"
        f"Opis: {item['opis'][:80]}\n"
        f"Jednostka miary: {item['jm']}\n"
        f"{m_line}\n"
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
                for mat in raw_mats:
                    mat['jm'] = _correct_jm(mat.get('name', ''), mat.get('jm', 'szt'))
                m = it.get('m_per_jm', 0)
                if m > 0:
                    # Sprawdź wzorzec leniwej odpowiedzi ce=m_per_jm, nz=1.0
                    if _is_lazy_response(raw_mats, m):
                        log.warning(
                            "AI materials: wykryto ce≈m_per_jm (lazy) dla %s — nie cachuj, spróbuj ponownie",
                            it['knr'],
                        )
                        continue
                    # Znana wartość M — normalizuj
                    normalized = _normalize(raw_mats, m)
                else:
                    # M=0 (nieznana) — zostaw ceny AI bez skalowania
                    normalized = raw_mats
                normalized = [mat for mat in normalized if mat.get('ce', 0) > 0 and mat.get('nz', 0) > 0]
                if normalized:
                    cache[norm_key] = normalized
                    saved += 1
                    continue
            # AI zwróciło [] — cachuj tylko gdy M=0 (genuinely no materials)
            # Gdy M>0 ale AI zwrócił []: nie cachuj — spróbuj ponownie następnym razem
            if it.get('m_per_jm', 0) <= 0:
                cache[norm_key] = []
                saved += 1
            else:
                log.warning("AI materials zwrócił [] dla M>0: %s", it['knr'])
        except Exception as e:
            log.warning("AI materials błąd dla %s: %s", it['knr'], e)

    _save_cache(cache)
    log.info("AI materials: zapisano %d/%d KNR do cache", saved, len(to_fetch))

    # Zwróć wyniki dla wszystkich items
    return {it['knr_norm']: cache.get(it['knr_norm'], []) for it in items}

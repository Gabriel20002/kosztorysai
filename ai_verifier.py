# -*- coding: utf-8 -*-
"""
AI Verifier — weryfikacja poprawności kosztorysu przez Claude Haiku.
Używa tool use API zamiast parsowania JSON — zero problemów z formatem.
"""

import logging
import os
import re

import anthropic

log = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 3000
_MAX_POZYCJE_IN_PROMPT = 80

_TOOL = {
    "name": "raport_weryfikacji",
    "description": "Zwróć ustrukturyzowany raport weryfikacji kosztorysu budowlanego.",
    "input_schema": {
        "type": "object",
        "properties": {
            "bledy": {
                "type": "array",
                "description": "Lista błędów wymagających korekty",
                "items": {
                    "type": "object",
                    "properties": {
                        "lp": {"type": ["integer", "null"], "description": "Numer pozycji lub null jeśli błąd ogólny"},
                        "opis": {"type": "string", "description": "Opis błędu"},
                        "sugestia": {"type": "string", "description": "Co poprawić"}
                    },
                    "required": ["lp", "opis", "sugestia"]
                }
            },
            "ostrzezenia": {
                "type": "array",
                "description": "Lista ostrzeżeń wymagających uwagi",
                "items": {
                    "type": "object",
                    "properties": {
                        "lp": {"type": ["integer", "null"], "description": "Numer pozycji lub null jeśli ostrzeżenie ogólne"},
                        "opis": {"type": "string", "description": "Opis ostrzeżenia"}
                    },
                    "required": ["lp", "opis"]
                }
            },
            "ocena": {
                "type": "string",
                "enum": ["dobry", "wymaga_uwagi", "wymaga_poprawy"],
                "description": "Ogólna ocena kosztorysu"
            },
            "komentarz": {
                "type": "string",
                "description": "Ogólne podsumowanie kosztorysu (2-3 zdania)"
            }
        },
        "required": ["bledy", "ostrzezenia", "ocena", "komentarz"]
    }
}


def verify_kosztorys(pozycje: list, podsumowanie: dict, params: dict, ath_text: str = None) -> dict:
    """
    Weryfikuje kosztorys i zwraca raport z błędami i ostrzeżeniami.
    Używa tool use — model zwraca natywny dict, zero parsowania JSON.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback("Brak klucza ANTHROPIC_API_KEY — weryfikacja AI niedostępna")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        pozycje_txt = _format_pozycje(pozycje)
        materialy_txt = _format_materials_from_ath(ath_text) if ath_text else ""

        prompt = f"""Jesteś niezależnym ekspertem weryfikacji kosztorysów budowlanych. Przeanalizuj poniższy kosztorys i wskaż błędy, nieprawidłowości oraz aspekty wymagające uwagi.

PARAMETRY KOSZTORYSU:
- Stawka robocizny: {params.get('stawka_rg', 35)} zł/r-g
- Koszty pośrednie: {params.get('kp_procent', 70)}%
- Zysk: {params.get('z_procent', 12)}%
- VAT: {params.get('vat_procent', 23)}%

PODSUMOWANIE FINANSOWE:
- Robocizna (R): {round(podsumowanie.get('suma_R', 0), 2)} PLN
- Materiały (M): {round(podsumowanie.get('suma_M', 0), 2)} PLN
- Sprzęt (S): {round(podsumowanie.get('suma_S', 0), 2)} PLN
- Koszty pośrednie: {round(podsumowanie.get('koszty_posrednie', 0), 2)} PLN
- Zysk: {round(podsumowanie.get('zysk', 0), 2)} PLN
- Wartość netto: {round(podsumowanie.get('wartosc_netto', 0), 2)} PLN
- Wartość brutto: {round(podsumowanie.get('wartosc_brutto', 0), 2)} PLN

POZYCJE KOSZTORYSU ({len(pozycje)} pozycji):
{pozycje_txt}

Sprawdź w szczególności:
- Pozycje gdzie M=0 a roboty wymagają materiałów (murowanie, betonowanie, malowanie, izolacje, okładziny) — POMIŃ pozycje demontażu/rozbiórki/rozebrania/wywozu/skucia: te z natury nie mają materiałów i M=0 jest tam poprawne
- Pozycje gdzie S=0 a roboty wymagają sprzętu (wykopy, transport, zagęszczanie, dźwig)
- Brakującą podstawę normatywną (pole podstawa puste lub "-")
- Podejrzanie niskie lub zerowe wartości robocizny przy pracochłonnych robotach
- Niespójności jednostek miary
- Pozycje z zerową ilością lub wartością
- Proporcje R:M:S dla danego rodzaju robót{materialy_txt}"""

        resp = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "raport_weryfikacji"},
            messages=[{"role": "user", "content": prompt}],
        )

        # tool_use zwraca gotowy dict — zero parsowania JSON
        for block in resp.content:
            if block.type == "tool_use" and block.name == "raport_weryfikacji":
                result = block.input
                _sanitize(result)
                log.info(
                    "AI Verifier: ocena=%s bledy=%d ostrzezenia=%d",
                    result.get("ocena"),
                    len(result.get("bledy", [])),
                    len(result.get("ostrzezenia", [])),
                )
                return result

        raise ValueError("Model nie zwrócił tool_use w odpowiedzi")

    except Exception as e:
        log.warning("AI Verifier error: %s", e)
        return _fallback(f"Błąd weryfikacji AI: {e}")


def _format_pozycje(pozycje: list) -> str:
    lines = []
    for i, p in enumerate(pozycje[:_MAX_POZYCJE_IN_PROMPT], 1):
        r = round(p.get("R", 0), 2)
        m = round(p.get("M", 0), 2)
        s = round(p.get("S", 0), 2)
        w = round(p.get("wartosc", 0), 2)
        podstawa = p.get("podstawa", "-") or "-"
        opis = (p.get("opis", "-") or "-")[:80]
        ilosc = p.get("ilosc", 0)
        jm = p.get("jm", "-")
        lines.append(
            f"{i}. [{podstawa}] {opis} | {ilosc} {jm} | R={r} M={m} S={s} | wartość={w} PLN"
        )
    if len(pozycje) > _MAX_POZYCJE_IN_PROMPT:
        lines.append(f"... (pominięto {len(pozycje) - _MAX_POZYCJE_IN_PROMPT} kolejnych pozycji)")
    return "\n".join(lines)


def _extract_materials_from_ath(ath_text: str) -> list:
    """
    Parsuje sekcje [RMS ZEST N] z pliku ATH (cp1250).
    Zwraca listę dict: {nazwa, jm, cena, typ}
    """
    materials = []
    # Znajdź wszystkie sekcje [RMS ZEST ...]
    sections = re.split(r'\[RMS ZEST \d+\]', ath_text)
    if len(sections) <= 1:
        return materials

    for section in sections[1:]:  # Pomiń część przed pierwszą sekcją
        # Wyciągnij pola z sekcji (do następnej sekcji [)
        lines = section.split('\n')
        entry = {}
        for line in lines:
            line = line.strip()
            if line.startswith('['):
                break  # Koniec sekcji
            if line.startswith('ty='):
                entry['typ'] = line[3:].split('\t')[0].strip()
            elif line.startswith('na='):
                entry['nazwa'] = line[3:].split('\t')[0].strip()
            elif line.startswith('jm='):
                entry['jm'] = line[3:].split('\t')[0].strip()
            elif line.startswith('ce='):
                ce_val = line[3:].split('\t')[0].strip()
                # Zamień przecinek na kropkę (format pl)
                ce_val = ce_val.replace(',', '.')
                try:
                    entry['cena'] = float(ce_val)
                except ValueError:
                    pass

        if entry.get('nazwa') and 'cena' in entry:
            materials.append(entry)

    return materials


_MAX_MATERIALS_IN_PROMPT = 60

# Typowe zakresy cen materiałów budowlanych (PLN/jm) do walidacji
_PRICE_RANGES = {
    # materiał: (min, max, typowe jm)
    'cement': (0.4, 3.0, 'kg'),
    'piasek': (30, 200, 'm3'),
    'żwir': (40, 250, 'm3'),
    'kruszywo': (30, 300, 'm3'),
    'beton': (200, 600, 'm3'),
    'cegła': (0.5, 5.0, 'szt'),
    'blachowkret': (0.1, 5.0, 'szt'),
    'stal': (3, 15, 'kg'),
    'pręt': (3, 15, 'kg'),
    'drewno': (400, 3000, 'm3'),
    'woda': (0.003, 0.02, 'l'),
    'farba': (5, 50, 'kg'),
    'klej': (1, 20, 'kg'),
    'zaprawa': (0.3, 5, 'kg'),
    'tynk': (0.3, 5, 'kg'),
    'izolacja': (5, 80, 'm2'),
    'styropian': (5, 80, 'm2'),
    'wełna': (5, 100, 'm2'),
    'rura': (5, 200, 'm'),
    'kabel': (2, 50, 'm'),
    'płyta': (10, 200, 'm2'),
}


def _format_materials_from_ath(ath_text: str) -> str:
    """Formatuje materiały z ATH jako sekcję do promptu."""
    if not ath_text:
        return ""

    materials = _extract_materials_from_ath(ath_text)
    if not materials:
        return ""

    lines = [
        f"\n\nMATERIAŁY Z PLIKU ATH ({len(materials)} pozycji) — sprawdź poprawność cen jednostkowych:",
        "Zwróć uwagę na: ceny absurdalnie wysokie lub niskie, błędne jednostki miary, brakujące materiały.",
        "Typowe ceny orientacyjne: cement ~0.5-1.5 PLN/kg, piasek ~50-150 PLN/m3, beton ~250-500 PLN/m3, stal ~5-12 PLN/kg\n",
    ]

    for i, m in enumerate(materials[:_MAX_MATERIALS_IN_PROMPT], 1):
        typ = m.get('typ', '?')
        nazwa = m.get('nazwa', '-')
        jm = m.get('jm', '-')
        cena = m.get('cena', 0)
        # Oznacz podejrzane ceny
        warning = _check_price_warning(nazwa, jm, cena)
        warn_str = f" ⚠ {warning}" if warning else ""
        lines.append(f"{i}. [{typ}] {nazwa} | {jm} | {cena:.4f} PLN/{jm}{warn_str}")

    if len(materials) > _MAX_MATERIALS_IN_PROMPT:
        lines.append(f"... (pominięto {len(materials) - _MAX_MATERIALS_IN_PROMPT} kolejnych materiałów)")

    return "\n".join(lines)


def _check_price_warning(nazwa: str, jm: str, cena: float) -> str:
    """Heurystyczna walidacja ceny — zwraca opis problemu lub pusty string."""
    if cena <= 0:
        return "cena zerowa lub ujemna"

    nazwa_lower = nazwa.lower()
    for keyword, (min_val, max_val, typical_jm) in _PRICE_RANGES.items():
        if keyword in nazwa_lower:
            # Sprawdź czy jednostka to typowa dla tego materiału
            jm_ok = typical_jm.lower() in jm.lower() or jm.lower() in typical_jm.lower()
            if jm_ok and cena > max_val * 20:
                return f"cena podejrzanie wysoka (oczekiwane {min_val}-{max_val} PLN/{typical_jm})"
            if jm_ok and cena < min_val / 20 and cena > 0:
                return f"cena podejrzanie niska (oczekiwane {min_val}-{max_val} PLN/{typical_jm})"
            break

    return ""


def _sanitize(result: dict):
    if "bledy" not in result or not isinstance(result["bledy"], list):
        result["bledy"] = []
    if "ostrzezenia" not in result or not isinstance(result["ostrzezenia"], list):
        result["ostrzezenia"] = []
    if result.get("ocena") not in ("dobry", "wymaga_uwagi", "wymaga_poprawy"):
        result["ocena"] = "wymaga_uwagi"
    if "komentarz" not in result:
        result["komentarz"] = ""


def _fallback(msg: str) -> dict:
    return {
        "bledy": [],
        "ostrzezenia": [{"lp": None, "opis": msg}],
        "ocena": "wymaga_uwagi",
        "komentarz": msg,
    }

# -*- coding: utf-8 -*-
"""
AI Verifier — weryfikacja poprawności kosztorysu przez Claude Haiku.
Działa niezależnie od głównego systemu generowania (osobny klient AI).
"""

import json
import logging
import os

import anthropic

log = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 2000
_MAX_POZYCJE_IN_PROMPT = 80  # limit żeby nie przekroczyć kontekstu


def verify_kosztorys(pozycje: list, podsumowanie: dict, params: dict) -> dict:
    """
    Weryfikuje kosztorys i zwraca raport z błędami i ostrzeżeniami.

    Returns:
        {
            "bledy": [{"lp": int|None, "opis": str, "sugestia": str}],
            "ostrzezenia": [{"lp": int|None, "opis": str}],
            "ocena": "dobry" | "wymaga_uwagi" | "wymaga_poprawy",
            "komentarz": str
        }
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback("Brak klucza ANTHROPIC_API_KEY — weryfikacja AI niedostępna")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        pozycje_txt = _format_pozycje(pozycje)

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
- Pozycje gdzie M=0 a roboty wymagają materiałów (np. murowanie, betonowanie, malowanie, izolacje, okładziny)
- Pozycje gdzie S=0 a roboty wymagają sprzętu (np. wykopy, transport, zagęszczanie, dźwig)
- Brakującą podstawę normatywną (pole podstawa puste lub "-")
- Podejrzanie niskie lub zerowe wartości robocizny przy pracochłonnych robotach
- Niespójności jednostek miary (np. roboty powierzchniowe w m zamiast m2)
- Pozycje z zerową ilością lub wartością
- Proporcje R:M:S dla danego rodzaju robót (czy są typowe dla branży)

Odpowiedz WYŁĄCZNIE jako JSON (bez żadnego tekstu poza JSON, wszystkie wartości stringowe w jednej linii bez znaków nowej linii):
{{"bledy":[{{"lp":<int_lub_null>,"opis":"<tekst>","sugestia":"<tekst>"}}],"ostrzezenia":[{{"lp":<int_lub_null>,"opis":"<tekst>"}}],"ocena":"<dobry|wymaga_uwagi|wymaga_poprawy>","komentarz":"<tekst>"}}"""

        resp = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        text = resp.content[0].text.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("Brak JSON w odpowiedzi AI")

        raw = text[start:end]
        result = _parse_json_robust(raw)
        _sanitize(result)
        log.info(
            "AI Verifier: ocena=%s bledy=%d ostrzezenia=%d",
            result.get("ocena"),
            len(result.get("bledy", [])),
            len(result.get("ostrzezenia", [])),
        )
        return result

    except Exception as e:
        log.warning("AI Verifier error: %s", e)
        return _fallback(f"Błąd weryfikacji AI: {e}")


def _parse_json_robust(raw: str) -> dict:
    """Parsuje JSON zwrócony przez AI — obsługuje typowe błędy (nowe linie w stringach, trailing commas)."""
    # Próba 1: bezpośredni parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Próba 2: usuń nowe linie i nadmiarowe spacje wewnątrz wartości stringowych
    import re
    # Zamień rzeczywiste nowe linie wewnątrz cudzysłowów na \n
    cleaned = re.sub(
        r'"((?:[^"\\]|\\.)*)"',
        lambda m: '"' + m.group(1).replace('\n', ' ').replace('\r', '') + '"',
        raw,
        flags=re.DOTALL,
    )
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Próba 3: usuń trailing commas przed ] i }
    cleaned2 = re.sub(r',\s*([\]}])', r'\1', cleaned)
    try:
        return json.loads(cleaned2)
    except json.JSONDecodeError as e:
        raise ValueError(f"Nie można sparsować JSON z odpowiedzi AI: {e}") from e


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


def _sanitize(result: dict):
    """Upewnij się że wymagane pola istnieją i mają właściwe typy."""
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

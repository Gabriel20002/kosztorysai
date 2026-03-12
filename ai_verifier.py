# -*- coding: utf-8 -*-
"""
AI Verifier — weryfikacja poprawności kosztorysu przez Claude Haiku.
Używa tool use API zamiast parsowania JSON — zero problemów z formatem.
"""

import logging
import os

import anthropic

log = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 2000
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


def verify_kosztorys(pozycje: list, podsumowanie: dict, params: dict) -> dict:
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
- Pozycje gdzie M=0 a roboty wymagają materiałów (murowanie, betonowanie, malowanie, izolacje, okładziny)
- Pozycje gdzie S=0 a roboty wymagają sprzętu (wykopy, transport, zagęszczanie, dźwig)
- Brakującą podstawę normatywną (pole podstawa puste lub "-")
- Podejrzanie niskie lub zerowe wartości robocizny przy pracochłonnych robotach
- Niespójności jednostek miary
- Pozycje z zerową ilością lub wartością
- Proporcje R:M:S dla danego rodzaju robót"""

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

# -*- coding: utf-8 -*-
import os, json, logging
import anthropic

log = logging.getLogger(__name__)

SYSTEM = """Jesteś ekspertem od polskich kosztorysów budowlanych.
Dopasowujesz opisy robót do kodów KNR z bazy nakładów.
Odpowiadaj WYŁĄCZNIE jako poprawny JSON bez żadnego tekstu przed ani po."""

def match_unmatched_positions(unmatched: list, baza: dict) -> dict:
    """
    unmatched: lista dict {'opis': ..., 'jm': ..., 'podstawa': ...}
    baza: self._naklady_index (klucz = normalized KNR, wartość = {'knr':..., 'opis':..., 'R':..., 'M':..., 'S':...})
    Zwraca: { "0": "KNR 2-02 0114-01", "1": null, ... }
    """
    if not unmatched:
        return {}
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {}

    # Top 300 rekordów z bazy (klucze + opis + jm)
    knr_sample = [
        {"kod": v.get('knr', k), "opis": v.get('opis', ''), "jm": v.get('jm', '')}
        for k, v in list(baza.items())[:300]
    ]

    user_msg = (
        f"Mam {len(unmatched)} pozycji bez dopasowania KNR.\n\n"
        f"POZYCJE DO DOPASOWANIA:\n{json.dumps(unmatched, ensure_ascii=False)}\n\n"
        f"DOSTĘPNE KODY KNR:\n{json.dumps(knr_sample, ensure_ascii=False)}\n\n"
        "Dla każdej pozycji zwróć najlepszy pasujący kod KNR lub null.\n"
        "Format: {\"0\": \"KNR X-XX XXXX-XX\", \"1\": null, ...}"
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM,
            messages=[{"role": "user", "content": user_msg}]
        )
        text = msg.content[0].text.strip()
        # usuń markdown code block jeśli model go dodał
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)
    except Exception as e:
        log.warning("AI KNR matcher error: %s", e)
        return {}

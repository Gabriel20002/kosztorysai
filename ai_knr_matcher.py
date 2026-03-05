# -*- coding: utf-8 -*-
import os, json, logging, random
import anthropic

log = logging.getLogger(__name__)

_BATCH_SIZE = 40  # max pozycji na 1 call API

SYSTEM_MATCH = """Jesteś ekspertem od polskich kosztorysów budowlanych.
Dopasowujesz opisy robót do kodów KNR z bazy nakładów.
Odpowiadaj WYŁĄCZNIE jako poprawny JSON bez żadnego tekstu przed ani po."""

SYSTEM_ESTIMATE = """Jesteś doświadczonym kosztorysantem budowlanym w Polsce.
Szacujesz koszty jednostkowe robocizny (R), materiałów (M) i sprzętu (S) dla pozycji kosztorysowych.

ZASADY:
- R = koszt robocizny w PLN na jednostkę miary (jm)
- M = koszt materiałów w PLN na jednostkę miary (jm)
- S = koszt sprzętu/maszyn w PLN na jednostkę miary (jm)
- stawka_rg = 35 zł/r-g (roboczogodzina)
- stawka_sprzetu = 100 zł/m-g (maszynogodzina)
- Podawaj wartości w PLN/jm, NIE wartości łączne
- Jeśli masz wątpliwości co do pozycji — zwróć null
- Odpowiadaj WYŁĄCZNIE jako poprawny JSON bez żadnego tekstu przed ani po."""


def _parse_json(text: str) -> dict:
    """Parsuje JSON z odpowiedzi modelu, obsługuje markdown code block."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def _pick_calibration(baza: dict, n: int = 20) -> list:
    """
    Wybiera n zróżnicowanych przykładów z bazy do kalibracji AI.
    Pokrywa: S>0, M=0, R małe, R duże, różne jm.
    """
    entries = list(baza.values())

    buckets = {
        'S>0':    [e for e in entries if e.get('S', 0) > 0],
        'M=0':    [e for e in entries if e.get('M', 0) == 0 and e.get('R', 0) > 0],
        'R_maly': [e for e in entries if 0 < e.get('R', 0) < 10],
        'R_duzy': [e for e in entries if e.get('R', 0) > 80],
        'reszta': entries,
    }

    seen = set()
    result = []
    per_bucket = max(1, n // len(buckets))

    for entries_b in buckets.values():
        candidates = [e for e in entries_b if id(e) not in seen]
        chosen = random.sample(candidates, min(per_bucket, len(candidates)))
        for e in chosen:
            seen.add(id(e))
            result.append({
                'knr': e.get('knr', ''),
                'opis': e.get('opis', '')[:60],
                'jm': e.get('jm', ''),
                'R': round(e.get('R', 0), 2),
                'M': round(e.get('M', 0), 2),
                'S': round(e.get('S', 0), 2),
            })
        if len(result) >= n:
            break

    return result[:n]


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
            system=SYSTEM_MATCH,
            messages=[{"role": "user", "content": user_msg}]
        )
        return _parse_json(msg.content[0].text)
    except Exception as e:
        log.warning("AI KNR matcher error: %s", e)
        return {}


def estimate_rms_direct(unmatched: list, baza: dict, stawki: dict = None) -> dict:
    """
    Bezpośrednie szacowanie R/M/S przez AI dla pozycji bez KNR w bazie.

    unmatched: lista dict {'opis': ..., 'jm': ..., 'podstawa': ...}
    baza: self._naklady_index — używane do generowania przykładów kalibracyjnych
    stawki: {'rg': 35.0, 'sprzet': 100.0}

    Zwraca: {
        "0": {"R": 45.5, "M": 120.0, "S": 0.0},
        "1": null,
        ...
    }
    """
    if not unmatched:
        return {}
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {}

    if stawki is None:
        stawki = {'rg': 35.0, 'sprzet': 100.0}

    calibration = _pick_calibration(baza, n=20)

    # Limity sensowności (PLN/jm) — powyżej → wynik odrzucany
    LIMITS = {'R': 5000.0, 'M': 50000.0, 'S': 10000.0}

    results = {}

    # Przetwarzaj partiami
    for batch_start in range(0, len(unmatched), _BATCH_SIZE):
        batch = unmatched[batch_start:batch_start + _BATCH_SIZE]
        batch_indices = list(range(batch_start, batch_start + len(batch)))

        user_msg = (
            f"stawka_rg={stawki['rg']} zł/r-g, stawka_sprzetu={stawki['sprzet']} zł/m-g\n\n"
            f"PRZYKŁADY KALIBRACYJNE (znane R/M/S z bazy):\n"
            f"{json.dumps(calibration, ensure_ascii=False)}\n\n"
            f"POZYCJE DO WYCENY ({len(batch)} szt.):\n"
            f"{json.dumps([{'i': i - batch_start, 'opis': p['opis'], 'jm': p['jm'], 'knr': p.get('podstawa', '')} for i, p in zip(batch_indices, batch)], ensure_ascii=False)}\n\n"
            "Dla każdej pozycji oszacuj R, M, S w PLN/jm.\n"
            "Jeśli nie możesz oszacować — zwróć null.\n"
            'Format: {"0": {"R": 4.5, "M": 0.0, "S": 12.0}, "1": null, ...}'
        )

        try:
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                system=SYSTEM_ESTIMATE,
                messages=[{"role": "user", "content": user_msg}]
            )
            batch_result = _parse_json(msg.content[0].text)
        except Exception as e:
            log.warning("AI estimate_rms_direct error (batch %d): %s", batch_start, e)
            batch_result = {}

        # Mapuj lokalne indeksy batcha → globalne, waliduj limity
        for local_i_str, val in batch_result.items():
            try:
                local_i = int(local_i_str)
            except ValueError:
                continue
            global_i = batch_start + local_i
            if val is None:
                results[str(global_i)] = None
                continue
            if not isinstance(val, dict):
                continue
            r = float(val.get('R', 0) or 0)
            m = float(val.get('M', 0) or 0)
            s = float(val.get('S', 0) or 0)
            # Odrzuć nierealistyczne wartości
            if r > LIMITS['R'] or m > LIMITS['M'] or s > LIMITS['S']:
                log.warning("AI estimate poza limitem dla poz %d: R=%s M=%s S=%s", global_i, r, m, s)
                results[str(global_i)] = None
                continue
            if r < 0 or m < 0 or s < 0:
                results[str(global_i)] = None
                continue
            results[str(global_i)] = {'R': r, 'M': m, 'S': s}

    return results

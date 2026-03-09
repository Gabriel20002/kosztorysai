# -*- coding: utf-8 -*-
import os, json, logging, random
import anthropic

log = logging.getLogger(__name__)

_BATCH_SIZE = 40  # max pozycji na 1 call API

SYSTEM_MATCH = """Jesteś ekspertem od polskich kosztorysów budowlanych.
Dopasowujesz opisy robót do kodów KNR z bazy nakładów.
Odpowiadaj WYŁĄCZNIE jako poprawny JSON bez żadnego tekstu przed ani po."""

SYSTEM_ESTIMATE = """Jesteś doświadczonym kosztorysantem budowlanym w Polsce z 20-letnim doświadczeniem.
Szacujesz koszty jednostkowe robocizny (R), materiałów (M) i sprzętu (S) dla pozycji kosztorysowych.

ZASADY:
- R = koszt robocizny w PLN na jednostkę miary (jm)
- M = koszt materiałów w PLN na jednostkę miary (jm)
- S = koszt sprzętu/maszyn w PLN na jednostkę miary (jm)
- stawka_rg = 35 zł/r-g (roboczogodzina)
- stawka_sprzetu = 100 zł/m-g (maszynogodzina)
- Podawaj wartości w PLN/jm, NIE wartości łączne
- KRYTYCZNE: ZAWSZE podaj wartości R/M/S — nigdy nie zwracaj null.
  Nawet dla pozycji "kalk. własna", "KNP", "KNR AL" czy urządzeń specjalistycznych —
  oszacuj na podstawie opisu, doświadczenia i analogii do podobnych robót.
  Minimalnie: jeśli robota wymaga montażu, R > 0. Jeśli są materiały, M > 0.
- Ceny materiałów 2024/2025 Polska (przykłady referencyjne):
  kabel YKY 4x16mm² ≈ 28 zł/m, rura PVC Ø110 ≈ 12 zł/m, bednarka FeZn 30x4 ≈ 8 zł/m,
  rozdzielnica natynkowa ≈ 200-800 zł/szt, wyłącznik p.poż ≈ 150 zł/szt,
  falownik 1-fazowy ≈ 500-1500 zł/szt, pomiar elektryczny ≈ 80-150 zł/punkt
- Odpowiadaj WYŁĄCZNIE jako poprawny JSON bez żadnego tekstu przed ani po."""

# Słownik urządzeń egzotycznych → analogiczne KNR standardowe
_EXOTIC_DEVICE_KNR = {
    'falownik': 'KNNR 5 0407-02',
    'falowniki': 'KNNR 5 0407-02',
    'bms': 'KNNR 5 0404-01',
    'sterownik': 'KNNR 5 0404-01',
    'optymalizator': 'KNNR 5 0407-02',
    'ups': 'KNNR 5 0408-01',
    'zasilacz ups': 'KNNR 5 0408-01',
    'pomiar': 'KNNR 5 0501-01',
    'pomiary': 'KNNR 5 0501-01',
    'bateria akumulatorów': 'KNNR 5 0408-02',
    'uszczelnienie przejść': 'KNR 2-02 2601-01',
    'lampka sygnalizacyjna': 'KNNR 5 0406-03',
    'sygnalizator': 'KNNR 5 0406-03',
    'czujnik': 'KNNR 5 0406-01',
    'detektor': 'KNNR 5 0406-01',
}


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


def _match_exotic(opis: str) -> str | None:
    """Dopasowuje opis do egzotycznego urządzenia i zwraca zastępczy KNR."""
    opis_l = opis.lower()
    for keyword, knr in _EXOTIC_DEVICE_KNR.items():
        if keyword in opis_l:
            return knr
    return None


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

    # Pre-matching egzotycznych urządzeń bez wywołania AI
    pre_results = {}
    still_unmatched = []
    for i, pos in enumerate(unmatched):
        exotic_knr = _match_exotic(pos.get('opis', ''))
        if exotic_knr:
            pre_results[str(i)] = exotic_knr
            log.info("Exotic device match: '%s' → %s", pos['opis'][:40], exotic_knr)
        else:
            still_unmatched.append((i, pos))

    if not still_unmatched:
        return pre_results

    # Top 300 rekordów z bazy (klucze + opis + jm)
    knr_sample = [
        {"kod": v.get('knr', k), "opis": v.get('opis', ''), "jm": v.get('jm', '')}
        for k, v in list(baza.items())[:300]
    ]

    only_positions = [pos for _, pos in still_unmatched]
    only_indices = [i for i, _ in still_unmatched]

    user_msg = (
        f"Mam {len(only_positions)} pozycji bez dopasowania KNR.\n\n"
        f"POZYCJE DO DOPASOWANIA:\n{json.dumps(only_positions, ensure_ascii=False)}\n\n"
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
        ai_results = _parse_json(msg.content[0].text)
        # Remapuj lokalne indeksy → globalne
        for local_i_str, val in ai_results.items():
            try:
                local_i = int(local_i_str)
                global_i = only_indices[local_i]
                pre_results[str(global_i)] = val
            except (ValueError, IndexError):
                pass
        return pre_results
    except Exception as e:
        log.warning("AI KNR matcher error: %s", e)
        return pre_results


def _heuristic_rms(pos: dict, stawki: dict) -> dict:
    """
    Heurystyczny fallback R/M/S gdy AI nie może oszacować.
    Opiera się na jm i słowach kluczowych z opisu.
    """
    opis = (pos.get('opis') or '').lower()
    jm = (pos.get('jm') or 'szt').lower()
    rg = stawki.get('rg', 35.0)

    # Pomiary elektryczne — tylko robocizna
    if any(w in opis for w in ['pomiar', 'próba', 'sprawdzenie', 'badanie']):
        return {'R': rg * 2.0, 'M': 0.0, 'S': 0.0}

    # Uszczelnienia, przejścia — robocizna + mały materiał
    if any(w in opis for w in ['uszczelni', 'przejście', 'masa ognioodporna']):
        return {'R': rg * 1.5, 'M': 30.0, 'S': 0.0}

    # Montaż urządzeń (lampka, sygnalizator, detektor) — robocizna + urządzenie
    if any(w in opis for w in ['lampk', 'sygnaliz', 'detektor', 'czujnik', 'montaż']):
        return {'R': rg * 1.0, 'M': 150.0, 'S': 0.0}

    # Domyślny fallback wg jm
    if jm in ('szt', 'szt.', 'kpl', 'kpl.'):
        return {'R': rg * 1.5, 'M': 100.0, 'S': 0.0}
    elif jm in ('m', 'mb', 'm.b.'):
        return {'R': rg * 0.3, 'M': 20.0, 'S': 0.0}
    elif jm in ('m2', 'm²'):
        return {'R': rg * 0.5, 'M': 30.0, 'S': 0.0}
    else:
        return {'R': rg * 1.0, 'M': 50.0, 'S': 0.0}


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
            if val is None or not isinstance(val, dict):
                # Heurystyczny fallback zamiast null — nigdy nie pomijamy pozycji
                pos = batch[local_i]
                results[str(global_i)] = _heuristic_rms(pos, stawki)
                continue
            r = float(val.get('R', 0) or 0)
            m = float(val.get('M', 0) or 0)
            s = float(val.get('S', 0) or 0)
            if r > LIMITS['R'] or m > LIMITS['M'] or s > LIMITS['S']:
                log.warning("AI estimate poza limitem dla poz %d: R=%s M=%s S=%s", global_i, r, m, s)
                results[str(global_i)] = _heuristic_rms(batch[local_i], stawki)
                continue
            if r < 0 or m < 0 or s < 0:
                results[str(global_i)] = _heuristic_rms(batch[local_i], stawki)
                continue
            results[str(global_i)] = {'R': r, 'M': m, 'S': s}

    # Dla pozycji nieobecnych w wynikach AI — dodaj heurystykę
    for i, pos in enumerate(unmatched):
        if str(i) not in results:
            results[str(i)] = _heuristic_rms(pos, stawki)

    return results

# -*- coding: utf-8 -*-
"""
extract_naklady_from_ath.py

Parsuje pliki ATH z Normy PRO i wyciąga z nich nakłady jednostkowe R/M/S
(wartość per jm w PLN) z linii kj= każdej pozycji.

Wynik: merged do learned_kosztorysy/naklady_merged.json
"""

import json
import re
import sys
from pathlib import Path


# ── Ścieżki do skanowania ────────────────────────────────────────────────────
ATH_SOURCES = [
    "/mnt/c/Users/Gabriel/Downloads/Kosztorys - usunięcie skutków zalania - przykładowy.ath",
    "/mnt/c/Users/Gabriel/Desktop/przedmiary",
    "/mnt/c/Users/Gabriel/Downloads/kosztorysy",
    "/mnt/c/Users/Gabriel/Desktop/kosztorysy",
    "/mnt/c/Users/Gabriel/Downloads",
]

DB_PATH = Path(__file__).parent / "learned_kosztorysy" / "naklady_merged.json"


# ── Parser ───────────────────────────────────────────────────────────────────

def _pl_float(s: str) -> float:
    """Konwertuje polską liczbę (przecinek jako separator) na float."""
    try:
        return float(s.strip().replace(',', '.').replace(' ', ''))
    except (ValueError, AttributeError):
        return 0.0


def _parse_kj(line: str):
    """
    Parsuje linię kj= → (R_per_jm, M_per_jm, S_per_jm).

    Format: kj=R\tM\tS  lub  kj=R\t0\t0
    Wartości mogą być 0, liczby z przecinkiem, lub puste.
    """
    val = line[3:]  # usuń "kj="
    parts = val.split('\t')
    r = _pl_float(parts[0]) if len(parts) > 0 else 0.0
    m = _pl_float(parts[1]) if len(parts) > 1 else 0.0
    s = _pl_float(parts[2]) if len(parts) > 2 else 0.0
    return r, m, s


def _parse_knr_from_pd(line: str) -> str:
    """
    Wyciąga KNR z linii pd=.

    Formaty pd=:
      pd=BOOK_TITLE\tKNR_TYPE\tFULL\tSHORT\tNUM\t...\t0
      pd=\tKNR_TYPE\tFULL\tSHORT\tNUM\t\t1
    Zwraca: "KNR_TYPE SHORT NUM" np. "KNR-W 2-02 1022-01"
    """
    val = line[3:]  # usuń "pd="
    parts = val.split('\t')
    if len(parts) < 4:
        return ''
    knr_type = parts[1].strip()
    knr_short = parts[3].strip()
    knr_num = parts[4].strip() if len(parts) > 4 else ''
    if not knr_type or not knr_short:
        return ''
    if knr_num:
        return f"{knr_type} {knr_short} {knr_num}"
    return f"{knr_type} {knr_short}"


def parse_ath_file(path: Path) -> list:
    """
    Parsuje jeden plik ATH i zwraca listę słowników:
    {knr, opis, jm, R, M, S}

    Tylko pozycje z niezerowym kj= (prawdziwe ceny, nie nasze generowane).
    """
    try:
        text = path.read_text(encoding='cp1250', errors='replace')
    except Exception as e:
        print(f"  SKIP {path.name}: {e}")
        return []

    results = []
    in_pozycja = False
    cur_knr = ''
    cur_opis = ''
    cur_jm = ''
    cur_kj = (0.0, 0.0, 0.0)

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if line == '[POZYCJA]':
            # Zapisz poprzednią pozycję jeśli miała ceny
            if in_pozycja:
                _maybe_append(results, cur_knr, cur_opis, cur_jm, cur_kj)
            # Reset dla nowej pozycji
            in_pozycja = True
            cur_knr = ''
            cur_opis = ''
            cur_jm = ''
            cur_kj = (0.0, 0.0, 0.0)

        elif line.startswith('[') and line != '[POZYCJA]':
            # Wyjście z sekcji pozycji — zapisz i zakończ
            if in_pozycja:
                _maybe_append(results, cur_knr, cur_opis, cur_jm, cur_kj)
            in_pozycja = False

        elif in_pozycja:
            if line.startswith('pd='):
                cur_knr = _parse_knr_from_pd(line)
            elif line.startswith('na='):
                cur_opis = line[3:].strip()[:200]
            elif line.startswith('jm='):
                jm_parts = line[3:].split('\t')
                cur_jm = jm_parts[0].strip()
            elif line.startswith('kj='):
                cur_kj = _parse_kj(line)

    # Ostatnia pozycja w pliku
    if in_pozycja and any(v > 0 for v in cur_kj):
        _maybe_append(results, cur_knr, cur_opis, cur_jm, cur_kj)

    return results


def _maybe_append(results, knr, opis, jm, kj):
    """Dodaje wpis do wyników jeśli ma KNR lub opis."""
    if not any(v > 0 for v in kj):
        return
    if knr:
        results.append({
            'knr': knr,
            'opis': opis,
            'jm': jm,
            'R': round(kj[0], 4),
            'M': round(kj[1], 4),
            'S': round(kj[2], 4),
        })
    elif opis:
        # Pozycja bez KNR — używamy opis jako pseudo-klucz
        opis_key = 'OPIS:' + re.sub(r'\s+', ' ', opis.upper().strip())
        results.append({
            'knr': opis_key,
            'opis': opis,
            'jm': jm,
            'R': round(kj[0], 4),
            'M': round(kj[1], 4),
            'S': round(kj[2], 4),
        })


def collect_ath_files(sources: list) -> list:
    """Zbiera pliki ATH ze wszystkich wskazanych ścieżek."""
    files = []
    for src in sources:
        p = Path(src)
        if p.is_file() and p.suffix.lower() == '.ath':
            files.append(p)
        elif p.is_dir():
            files.extend(p.glob('*.ATH'))
            files.extend(p.glob('*.ath'))
    return list(dict.fromkeys(files))  # usuń duplikaty zachowując kolejność


def merge_into_db(new_entries: list, db_path: Path) -> tuple:
    """
    Merguje nowe wpisy do istniejącej bazy.
    Nadpisuje wpis jeśli KNR już istnieje (nowe dane mają pierwszeństwo).

    Returns: (added, updated, total)
    """
    if db_path.exists():
        existing = json.loads(db_path.read_text(encoding='utf-8'))
    else:
        existing = []

    # Indeks istniejących wg znormalizowanego KNR
    ws_re = re.compile(r'\s+')
    idx = {}
    for i, entry in enumerate(existing):
        knr_norm = ws_re.sub('', entry.get('knr', '').upper())
        if knr_norm:
            idx[knr_norm] = i

    added = 0
    updated = 0

    for entry in new_entries:
        knr_norm = ws_re.sub('', entry.get('knr', '').upper())
        if not knr_norm:
            continue
        if knr_norm in idx:
            old = existing[idx[knr_norm]]
            # Aktualizuj tylko jeśli nowe wartości są lepsze (niezerowe)
            changed = False
            for field in ('R', 'M', 'S'):
                if entry[field] > 0 and old.get(field, 0) == 0:
                    old[field] = entry[field]
                    changed = True
            if changed:
                updated += 1
        else:
            existing.append(entry)
            idx[knr_norm] = len(existing) - 1
            added += 1

    db_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return added, updated, len(existing)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    files = collect_ath_files(ATH_SOURCES)
    print(f"Znaleziono {len(files)} plików ATH")

    all_entries = []
    for f in files:
        entries = parse_ath_file(f)
        print(f"  {f.name}: {len(entries)} pozycji z cenami")
        all_entries.extend(entries)

    print(f"\nŁącznie wyekstrahowano: {len(all_entries)} pozycji")

    added, updated, total = merge_into_db(all_entries, DB_PATH)
    print(f"Baza: +{added} nowych, ~{updated} zaktualizowanych, {total} łącznie")
    print(f"Zapisano: {DB_PATH}")


if __name__ == '__main__':
    main()

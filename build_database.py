# -*- coding: utf-8 -*-
"""
build_database.py — Buduje główną bazę nakładów KNR.

Źródła (w kolejności priorytetu):
  1. learned_kosztorysy/naklady_rms.json       (689 ręcznie sprawdzonych)
  2. learned_kosztorysy/naklady_extracted.json  (wyekstrahowane z plików ATH)
  3. learned_kosztorysy/*.txt                   (kosztorysy Norma PRO - ten skrypt)
  4. archive/knr_base.json                      (51 pozycji archiwalne)

Wynik: learned_kosztorysy/naklady_merged.json

Użycie:
    python build_database.py            # tryb normalny
    python build_database.py --verbose  # szczegółowe logi
    python build_database.py --stats    # tylko statystyki bez zapisu
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent / "learned_kosztorysy"
ARCHIVE = Path(__file__).parent / "archive"
OUTPUT = BASE / "naklady_merged.json"

VERBOSE = "--verbose" in sys.argv
STATS_ONLY = "--stats" in sys.argv


# ---------------------------------------------------------------------------
# Normalizacja
# ---------------------------------------------------------------------------

def norm_knr(knr: str) -> str:
    """Normalizuje kod KNR do postaci bez spacji (klucz słownika)."""
    return re.sub(r'[\s\-]+', '', knr.upper().strip())


def to_float(val) -> float:
    """Bezpieczna konwersja do float (obsługuje string z przecinkiem)."""
    if val is None:
        return 0.0
    try:
        return float(str(val).replace(',', '.').strip())
    except (ValueError, TypeError):
        return 0.0


_GARBAGE_PATTERNS = re.compile(r'^(DUALNA|NNRNKB)\b', re.I)

def is_valid_knr(knr: str) -> bool:
    """Sprawdza czy to prawidłowy kod katalogowy (KNR i warianty).

    Akceptuje: KNR, KNR-W, KNNR, KNK, KSNR, AT, AL, KNR AT, i inne
    wariacje używane w polskich katalogach budowlanych.
    Odrzuca: oczywiste śmieci OCR (DUALNA, NNRNKB, itp.)
    """
    if not knr or len(knr.strip()) < 4:
        return False
    knr = knr.strip()
    if _GARBAGE_PATTERNS.match(knr):
        return False
    # Musi zaczynać się od liter i zawierać cyfry
    return bool(re.match(r'^[A-Z]{1,6}[\-\s]?[A-Z0-9]', knr, re.I))


# ---------------------------------------------------------------------------
# Ładowanie istniejących baz JSON
# ---------------------------------------------------------------------------

def load_json_base(path: Path) -> list:
    """Ładuje bazę z pliku JSON — obsługuje format rms i extracted."""
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    result = []
    for n in (data if isinstance(data, list) else list(data.values())):
        knr = str(n.get('knr', n.get('KNR', ''))).strip()
        if not is_valid_knr(knr):
            continue
        r = to_float(n.get('R', 0))
        m = to_float(n.get('M', 0))
        s = to_float(n.get('S', 0))
        if r == 0 and m == 0 and s == 0:
            continue
        result.append({
            'knr': knr,
            'opis': str(n.get('opis', n.get('name', ''))).strip(),
            'jm': str(n.get('jm', n.get('unit', 'szt.'))).strip(),
            'R': r,
            'M': m,
            'S': s,
        })
    return result


def load_knr_base_archive(path: Path) -> list:
    """Ładuje archive/knr_base.json (format: {id, knr, name, unit, price_unit, category})."""
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    positions = data.get('positions', [])
    result = []
    for p in positions:
        knr = str(p.get('knr', '')).strip()
        if not is_valid_knr(knr):
            continue
        price = to_float(p.get('price_unit', 0))
        if price == 0:
            continue
        # Bez podziału R/M/S — wstaw całość do M (materiały + robocizna łącznie)
        result.append({
            'knr': knr,
            'opis': str(p.get('name', '')).strip(),
            'jm': str(p.get('unit', 'szt.')).strip(),
            'R': 0.0,
            'M': price,
            'S': 0.0,
        })
    return result


# ---------------------------------------------------------------------------
# Ekstraktor plików .txt (format Norma PRO)
# ---------------------------------------------------------------------------

# Wzorzec nagłówka pozycji:
# "2 KNR 2-01 Usunięcie warstwy ziemi m2 409,886 0,272"
_HEADER = re.compile(
    r'^(\d+)\s+(KNR[A-Z\-W]*\s+[\d]+(?:-[\d]+)?)\s+(.+?)\s+'
    r'(m2|m3|m\b|szt\.?|kpl\.?|kg|t|mb|m-g|r-g)\s+[\d,\. ]+$',
    re.IGNORECASE
)
# Detail code np. "d.2 0126-01 opis dalszy..."
_DETAIL = re.compile(r'^d\.\d+\s+([\d]+-[\d]+)')
# "Jednostkowe koszty bezpośrednie 6,800 3,920 2,880"
_JEDN = re.compile(r'^Jednostkowe koszty bezpo[śs]rednie\s+([\d,\.]+)\s+([\d,\.]+)(?:\s+([\d,\.]+))?(?:\s+([\d,\.]+))?')


def parse_txt_kosztorys(path: Path) -> list:
    """Parsuje plik .txt eksportu Norma PRO i wyciąga nakłady R/M/S."""
    try:
        content = path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return []

    lines = content.splitlines()
    results = []

    current = None

    for line in lines:
        stripped = line.strip()

        # Nagłówek pozycji
        m = _HEADER.match(stripped)
        if m:
            current = {
                'knr_base': m.group(2).strip(),
                'detail': None,
                'opis': m.group(3).strip(),
                'jm': m.group(4),
            }
            continue

        if current is None:
            continue

        # Kod szczegółowy (np. "d.2 0126-01")
        if current['detail'] is None:
            dm = _DETAIL.match(stripped)
            if dm:
                current['detail'] = dm.group(1)
                continue

        # Szukaj nakładów jednostkowych
        jm = _JEDN.match(stripped)
        if jm:
            vals = [to_float(jm.group(i)) for i in range(1, 5) if jm.group(i)]
            # vals = [total, val1, val2?, val3?]
            # Norma PRO: total R [M] [S] lub total R+S (bez M)
            if len(vals) == 2:
                r, s = vals[1], 0.0
                m_val = 0.0
            elif len(vals) == 3:
                r, s = vals[1], vals[2]
                m_val = 0.0
            elif len(vals) >= 4:
                r, m_val, s = vals[1], vals[2], vals[3]
            else:
                current = None
                continue

            if r == 0 and m_val == 0 and s == 0:
                current = None
                continue

            # Złóż pełny kod KNR
            if current['detail']:
                knr_full = f"{current['knr_base']} {current['detail']}"
            else:
                knr_full = current['knr_base']

            results.append({
                'knr': knr_full,
                'opis': current['opis'][:200],
                'jm': current['jm'],
                'R': round(r, 4),
                'M': round(m_val, 4),
                'S': round(s, 4),
                'source': path.stem,
            })
            current = None

    if VERBOSE:
        print(f"  {path.name}: wyciągnięto {len(results)} pozycji")

    return results


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def merge_sources(sources: list[list]) -> list:
    """
    Scala wiele list nakładów w jedną.
    Priorytety: pierwsza lista ma najwyższy priorytet.
    Duplikaty po znormalizowanym KNR są odrzucane (zachowujemy pierwszy).
    """
    index = {}
    for source_list in sources:
        for entry in source_list:
            key = norm_knr(entry['knr'])
            if not key:
                continue
            if key not in index:
                index[key] = entry
            else:
                # Aktualizuj tylko jeśli nowy rekord ma więcej danych
                old = index[key]
                old_sum = old.get('R', 0) + old.get('M', 0) + old.get('S', 0)
                new_sum = entry.get('R', 0) + entry.get('M', 0) + entry.get('S', 0)
                if new_sum > old_sum:
                    index[key] = entry

    return list(index.values())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  build_database.py — budowanie bazy nakładów KNR")
    print("=" * 60)

    # 1. Istniejące bazy JSON
    print("\n[1/4] Ładowanie baz JSON...")
    rms = load_json_base(BASE / "naklady_rms.json")
    ext = load_json_base(BASE / "naklady_extracted.json")
    arch = load_knr_base_archive(ARCHIVE / "knr_base.json")
    print(f"  naklady_rms.json:       {len(rms):>4} rekordów")
    print(f"  naklady_extracted.json: {len(ext):>4} rekordów")
    print(f"  archive/knr_base.json:  {len(arch):>4} rekordów")

    # 2. Ekstrakcja z .txt
    print("\n[2/4] Ekstrakcja z plików .txt...")
    txt_files = list(BASE.glob("*.txt"))
    txt_all = []
    for f in txt_files:
        txt_all.extend(parse_txt_kosztorys(f))
    print(f"  Znaleziono {len(txt_files)} plików .txt → {len(txt_all)} pozycji")

    # 3. Merge (priorytety: rms > extracted > txt > archive)
    print("\n[3/4] Scalanie...")
    merged = merge_sources([rms, ext, txt_all, arch])

    # Statystyki katalogów
    cats = {}
    for n in merged:
        m = re.match(r'(KNR[A-Z\-W]*\s*\d+)', n['knr'], re.I)
        if m:
            cat = m.group(1).upper()
            cats[cat] = cats.get(cat, 0) + 1

    print(f"\n  Łącznie po scaleniu: {len(merged)} unikalnych pozycji")
    print(f"  Katalogi ({len(cats)}):")
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1])[:12]:
        print(f"    {cat}: {cnt}")

    # Przyrost vs poprzednia baza
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            prev = json.load(f)
        delta = len(merged) - len(prev)
        sign = "+" if delta >= 0 else ""
        print(f"\n  Zmiana vs poprzednia baza: {sign}{delta} rekordów ({len(prev)} → {len(merged)})")

    if STATS_ONLY:
        print("\n[--stats] Tryb tylko statystyki — plik nie zostanie nadpisany.")
        return

    # 4. Zapis
    print("\n[4/4] Zapis...")
    # Sortuj po KNR dla czytelności
    merged.sort(key=lambda x: x['knr'])
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"  Zapisano: {OUTPUT}")
    print(f"  Rozmiar: {OUTPUT.stat().st_size / 1024:.1f} KB")

    print("\nGotowe!")


if __name__ == "__main__":
    main()

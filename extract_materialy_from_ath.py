# -*- coding: utf-8 -*-
"""
extract_materialy_from_ath.py

Parsuje pliki ATH i wyciąga skład materiałowy per KNR:
- dla każdej [POZYCJA] zbiera [RMS N] odnoszące się do [RMS ZEST N] z ty=M i ce>1 PLN
- wynik: {knr_norm: [{name, jm, nz, ce}, ...]}

Zapis: learned_kosztorysy/knr_materialy.json
"""

import json
import re
from pathlib import Path


ATH_SOURCES = [
    "/mnt/c/Users/Gabriel/Downloads/Kosztorys - usunięcie skutków zalania - przykładowy.ath",
    "/mnt/c/Users/Gabriel/Desktop/przedmiary",
    "/mnt/c/Users/Gabriel/Downloads/kosztorysy",
    "/mnt/c/Users/Gabriel/Desktop/kosztorysy",
    "/mnt/c/Users/Gabriel/Downloads",
]

DB_PATH = Path(__file__).parent / "learned_kosztorysy" / "knr_materialy.json"

# Jednostki "względne" lub zbiorcze — pomijamy (nie są fizycznymi materiałami)
SKIP_JM = {'%', 'kpl', 'kpl.', 'komplet'}


# ── Pomocnicze ───────────────────────────────────────────────────────────────

def _pl_float(s: str) -> float:
    """Polska liczba (przecinek / taby) → float. Bierze pierwszą wartość po tab."""
    try:
        return float(s.strip().split('\t')[0].replace(',', '.').replace(' ', ''))
    except Exception:
        return 0.0


def _knr_norm(pd_line: str) -> str:
    """Wyciąga i normalizuje KNR z linii pd= → 'KNR2-020290-02'."""
    val = pd_line[3:]  # usuń 'pd='
    parts = val.split('\t')
    if len(parts) < 4:
        return ''
    knr_type = parts[1].strip()
    knr_short = parts[3].strip()
    knr_num = parts[4].strip() if len(parts) > 4 else ''
    if not knr_type or not knr_short:
        return ''
    return re.sub(r'\s+', '', f"{knr_type}{knr_short}{knr_num}".upper())


# ── Parser ───────────────────────────────────────────────────────────────────

def parse_ath_for_materialy(path: Path) -> dict:
    """
    Parsuje jeden plik ATH.
    Returns: {knr_norm: [{name, jm, nz, ce}, ...]}
    Tylko materiały ty=M z ce>1 PLN (realne ceny, nie zbiorcze ce=1).
    """
    try:
        text = path.read_text(encoding='cp1250', errors='replace')
    except Exception as e:
        print(f"  SKIP {path.name}: {e}")
        return {}

    # 1. Zbierz [RMS ZEST N] z ty=M i realną ceną
    zest_m = {}  # N -> {name, jm, ce}
    for m in re.finditer(r'\[RMS ZEST (\d+)\](.*?)(?=\n\[)', text, re.DOTALL):
        n = int(m.group(1))
        body = m.group(2)
        ty_m = re.search(r'^ty=([^\t\n]+)', body, re.MULTILINE)
        if not ty_m or not ty_m.group(1).strip().startswith('M'):
            continue
        ce_m = re.search(r'^ce=(.+)', body, re.MULTILINE)
        if not ce_m:
            continue
        ce = _pl_float(ce_m.group(1))
        if ce <= 1.0:
            continue  # zbiorczy lub procentowy — pomiń
        jm_m = re.search(r'^jm=([^\t\n]+)', body, re.MULTILINE)
        jm = jm_m.group(1).strip().split('\t')[0] if jm_m else ''
        if jm.lower() in SKIP_JM:
            continue
        na_m = re.search(r'^na=([^\t\n]+)', body, re.MULTILINE)
        name = na_m.group(1).strip() if na_m else ''
        zest_m[n] = {'name': name, 'jm': jm, 'ce': ce}

    if not zest_m:
        return {}

    # 2. Parsuj pozycje — każda sekcja to jeden blok
    # Sekcje w obrębie [POZYCJA]: [PODSUMOWANIE], [OBMIAR NEX], [PRZEDMIAR], [RMS N]
    POZYCJA_END = {
        '[POZYCJA]', '[ELEMENT', '[KOSZTORYS', '[STRONA', '[NARZUTY', '[RMS ZEST',
    }

    sections = re.split(r'\n(?=\[)', text)
    result = {}

    i = 0
    while i < len(sections):
        s = sections[i]
        if not s.startswith('[POZYCJA]'):
            i += 1
            continue

        # KNR
        pd_m = re.search(r'^pd=(.+)', s, re.MULTILINE)
        knr = _knr_norm(pd_m.group(0)) if pd_m else ''

        # Zbierz [RMS N] z kolejnych sekcji (aż do granicy pozycji)
        materials = []
        j = i + 1
        while j < len(sections):
            sj = sections[j]
            header = sj.splitlines()[0] if sj else ''
            if any(header.startswith(e) for e in POZYCJA_END):
                break
            rms_m = re.match(r'\[RMS (\d+)\]', header)
            if rms_m:
                n = int(rms_m.group(1))
                if n in zest_m:
                    nz_m = re.search(r'^nz=(.+)', sj, re.MULTILINE)
                    nz = _pl_float(nz_m.group(1)) if nz_m else 0.0
                    if nz > 0:
                        mat = zest_m[n]
                        materials.append({
                            'name': mat['name'],
                            'jm': mat['jm'],
                            'nz': round(nz, 6),
                            'ce': round(mat['ce'], 4),
                        })
            j += 1

        if knr and materials:
            if knr not in result:
                result[knr] = materials

        i += 1

    return result


def collect_ath_files(sources: list) -> list:
    files = []
    for src in sources:
        p = Path(src)
        if p.is_file() and p.suffix.lower() == '.ath':
            files.append(p)
        elif p.is_dir():
            files.extend(p.glob('*.ATH'))
            files.extend(p.glob('*.ath'))
    return list(dict.fromkeys(files))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    files = collect_ath_files(ATH_SOURCES)
    print(f"Znaleziono {len(files)} plików ATH")

    all_data = {}
    for f in files:
        data = parse_ath_for_materialy(f)
        added = 0
        for knr, mats in data.items():
            if knr not in all_data:
                all_data[knr] = mats
                added += 1
        if added:
            print(f"  {f.name}: +{added} KNR z danymi materiałowymi")

    print(f"\nŁącznie KNR z danymi materiałowymi: {len(all_data)}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(
        json.dumps(all_data, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(f"Zapisano: {DB_PATH}")


if __name__ == '__main__':
    main()

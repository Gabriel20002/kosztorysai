# -*- coding: utf-8 -*-
"""
Testy regresyjne kosztorysAI.
Uruchom: python test_regression.py

Weryfikuje:
  - parser PDF → liczba pozycji (> 0)
  - poprawny format KNR w wyjściu ATH
  - brak podwojonych KNR (błąd sprzed naprawy)
  - skany PDF → czytelny komunikat błędu
  - parsery Zuzia, norma_standard_d, regex działają poprawnie
"""

import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

BASE_DIR = "/mnt/c/Users/Gabriel/Desktop/przedmiary"

# (plik, min_pozycji)
TEST_PDFS = [
    ("przedmiar budowlany.pdf",                           50),
    ("przedmiar sanitarny.pdf",                           50),
    ("przedmiar elektryka.pdf",                           100),
    ("przedmiar_robot_zalacznik_nr_3.pdf",                20),
    ("BTBS_bud_wielorodzinny_przedmiar_budowlanka.pdf",   100),
    ("BTBS_bud_wielorodzinny_przedmiar_instal_elektr.pdf",100),
    ("BTBS_bud_wielorodzinny_przedmiar_instal_sanit.pdf", 100),
    ("06_Fojutowo_-_Przedmiar.pdf",                       200),
    ("Przedmiar szkoła specjalna ELEKTRYKA.pdf",          100),
    ("PRZEDMIAR elektryczny.pdf",                         20),
    ("Biblioteka_Osiek_Przedmiar_robót.pdf",              20),
]

SCAN_PDFS = [
    "Szkoła Brzeg budowlany przedmiar.pdf",
    "PRZEDMIAR BRANŻA DROGOWA.pdf",
]

_PD_LINE = re.compile(
    r'^pd=\t'
    r'(KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)\t'
    r'([^\t]+)\t'
    r'([^\t]+)\t'
    r'([^\t]*)\t\t1$'
)


def check_ath_pd_lines(ath_path):
    errors = []
    with open(ath_path, encoding='cp1250', errors='replace') as f:
        content = f.read()
    for i, line in enumerate(content.split('\n'), 1):
        line = line.rstrip('\r')
        if not line.startswith('pd=\t'):
            continue
        if line == 'pd=\t\t\t\t\t\t0':
            continue
        m = _PD_LINE.match(line)
        if not m:
            errors.append(f"  Linia {i}: nieprawidłowy format: {line!r}")
            continue
        typ, full, short, num = m.group(1), m.group(2), m.group(3), m.group(4)
        # Błąd Zuzia: full i short identyczne ze slash-notacją (np. "45/1/2" "45/1/2")
        # Po naprawie: full="45/1/2", short="45/1", num="2"
        if '/' in full and full == short:
            errors.append(f"  Linia {i}: Zuzia — full==short bez podziału: {line!r}")
        if '/' in full and short not in full:
            errors.append(f"  Linia {i}: Zuzia — short nie jest prefixem full: {line!r}")
    return errors


def run_tests():
    from kosztorys_generator import KosztorysGenerator
    from exceptions import PDFParsingError

    gen = KosztorysGenerator()
    passed = failed = 0
    errors_total = []

    print("=" * 70)
    print("TESTY REGRESYJNE kosztorysAI")
    print("=" * 70)

    # [1] Parser PDF → pozycje
    print("\n[1] Parser PDF → pozycje")
    for fname, min_poz in TEST_PDFS:
        path = os.path.join(BASE_DIR, fname)
        if not os.path.exists(path):
            print(f"  SKIP  {fname}")
            continue
        try:
            poz = gen.parse_przedmiar_pdf(path, use_cache=False)
            if len(poz) < min_poz:
                msg = f"Za mało: {len(poz)} < {min_poz}"
                print(f"  FAIL  {fname}: {msg}")
                errors_total.append((fname, msg)); failed += 1
            else:
                print(f"  OK    {len(poz):3d} poz  {fname}")
                passed += 1
        except Exception as e:
            print(f"  FAIL  {fname}: {e}")
            errors_total.append((fname, str(e))); failed += 1

    # [2] Skany → auto-OCR (sukces) lub czytelny błąd gdy OCR niedostępny
    print("\n[2] Skany → auto-OCR lub czytelny błąd")
    for fname in SCAN_PDFS:
        path = os.path.join(BASE_DIR, fname)
        if not os.path.exists(path):
            print(f"  SKIP  {fname}")
            continue
        try:
            poz = gen.parse_przedmiar_pdf(path, use_cache=False)
            if poz:
                print(f"  OK    {fname}: auto-OCR → {len(poz)} pozycji")
                passed += 1
            else:
                print(f"  FAIL  {fname}: auto-OCR nie znalazł pozycji")
                errors_total.append((fname, "0 pozycji po OCR")); failed += 1
        except PDFParsingError as e:
            # Akceptowalny wynik gdy ocrmypdf niedostępny
            if any(w in str(e).lower() for w in ('skan', 'obraz', 'ocr')):
                print(f"  OK    {fname}: poprawny błąd skan (ocrmypdf niedostępny)")
                passed += 1
            else:
                print(f"  FAIL  {fname}: {e}")
                errors_total.append((fname, str(e))); failed += 1
        except Exception as e:
            print(f"  FAIL  {fname}: {e}")
            errors_total.append((fname, str(e))); failed += 1

    # [3] Format ATH — pd= linie
    print("\n[3] Format ATH — pd= linie (brak podwojeń, poprawny Zuzia)")
    with tempfile.TemporaryDirectory() as tmpdir:
        for fname, _ in TEST_PDFS:
            path = os.path.join(BASE_DIR, fname)
            if not os.path.exists(path):
                continue
            ath_out = os.path.join(tmpdir, re.sub(r'\.pdf$', '.ath', fname, flags=re.I))
            try:
                g = KosztorysGenerator()
                res = g.generate(path, dane_tytulowe={'nazwa_inwestycji': 'Test'},
                                 output_ath=ath_out, output_pdf=None)
                if res and 'ath' in res:
                    errs = check_ath_pd_lines(res['ath'])
                    if errs:
                        print(f"  FAIL  {fname}:"); [print(e) for e in errs[:3]]
                        errors_total.append((fname, f"{len(errs)} błędów pd=")); failed += 1
                    else:
                        print(f"  OK    {fname}"); passed += 1
            except Exception as e:
                print(f"  FAIL  {fname}: {e}")
                errors_total.append((fname, str(e))); failed += 1

    # [4] Unit: _parse_podstawa
    print("\n[4] Unit: _parse_podstawa()")
    from ath_generator import _parse_podstawa
    cases = [
        ("KNR 4-01 0354-09",   ("KNR",   "4-01",    "0354-09")),
        ("KNR-W 2-18 0434-02", ("KNR-W", "2-18",    "0434-02")),
        ("KNNR 1 0111-01",     ("KNNR",  "1",       "0111-01")),
        ("KNR 45/1/2",         ("KNR",   "45/1",    "2")),
        ("KNR 401/350/1",      ("KNR",   "401/350", "1")),
        ("KNR 401/310/2 (2)",  ("KNR",   "401/310", "2 (2)")),
    ]
    for val, expected in cases:
        result = _parse_podstawa(val)
        if result == expected:
            print(f"  OK    {val!r} → {result}")
            passed += 1
        else:
            msg = f"oczekiwano {expected}, dostano {result}"
            print(f"  FAIL  {val!r}: {msg}")
            errors_total.append((f"_parse_podstawa({val!r})", msg)); failed += 1

    # [5] Unit: fix_podstawa — Zuzia slash zachowany
    print("\n[5] Unit: fix_podstawa() — zachowanie formatu Zuzia")
    from validators import TextFixer
    tf = TextFixer()
    for val, expected in [("KNR 45/1/2", "KNR 45/1/2"), ("KNR 401/350/1", "KNR 401/350/1")]:
        result = tf.fix_podstawa(val)
        if result == expected:
            print(f"  OK    {val!r} → {result!r}")
            passed += 1
        else:
            msg = f"oczekiwano {expected!r}, dostano {result!r}"
            print(f"  FAIL  {val!r}: {msg}")
            errors_total.append((f"fix_podstawa({val!r})", msg)); failed += 1

    # Podsumowanie
    total = passed + failed
    print(f"\n{'='*70}")
    print(f"WYNIK: {passed}/{total} OK  |  {failed} błędów")
    if errors_total:
        print("\nBŁĘDY:")
        for f, msg in errors_total:
            print(f"  {f}: {msg}")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)

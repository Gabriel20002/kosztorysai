# -*- coding: utf-8 -*-
"""
Deterministyczny walidator ATH v2.
Sprawdza format ATH wygenerowany przez ATHGenerator v5.

Format v5 (zgodny z Norma PRO):
- kj=0, cj=0, wn= puste (Norma oblicza z RMS)
- [RMS N] per pozycja: N = numer ZEST, nz = nakład jednostkowy (kropka)
- [RMS ZEST N] z cenami

Uruchomienie:
    python validate_ath.py
    exit code 0 = OK, 1 = FAIL
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from ath_generator import ATHGenerator


PARAMS = {
    'stawka_rg': 35.0,
    'stawka_sprzetu': 100.0,
    'kp_procent': 70.0,
    'z_procent': 12.0,
    'vat_procent': 23.0,
}

POZYCJE = [
    {
        'lp': 1,
        'podstawa': 'KNR 4-01 0354-09',
        'opis': 'Rozbiórka elementów',
        'jm': 'szt',
        'ilosc': 10,
        'R': 1000.0,
        'M': 500.0,
        'S': 200.0,
    },
    {
        'lp': 2,
        'podstawa': 'KNR 2-02 0123-01',
        'opis': 'Murowanie ścian',
        'jm': 'm2',
        'ilosc': 50,
        'R': 5000.0,
        'M': 8000.0,
        'S': 0.0,
    },
]

PODSUMOWANIE = {'suma_R': 6000.0, 'suma_M': 8500.0, 'suma_S': 200.0}
DANE_TYTULOWE = {'nazwa_inwestycji': 'Test walidacji ATH'}
OUTPUT_PATH = '/tmp/validate_ath_test.ath'


def parse_ath(filepath):
    """
    Parsuje plik ATH.
    Zwraca:
      zest: dict {nr_str -> {ty, il, ce}}
      pozycje: list [{'fields': dict, 'rms': {nr_str: dict}}, ...]
    """
    with open(filepath, 'r', encoding='cp1250') as f:
        raw_lines = f.readlines()

    sections = []
    current_name = None
    current_fields = {}

    for line in raw_lines:
        line = line.rstrip('\n').rstrip('\r')
        if line.startswith('[') and line.endswith(']'):
            if current_name is not None:
                sections.append((current_name, current_fields))
            current_name = line[1:-1]
            current_fields = {}
        elif '=' in line and current_name is not None:
            key, _, val = line.partition('=')
            current_fields[key.strip()] = val

    if current_name is not None:
        sections.append((current_name, current_fields))

    # Zbierz ZEST — mapowanie nr → {ty, ce, il}
    zest = {}
    for name, fields in sections:
        if name.startswith('RMS ZEST '):
            nr = name.split()[-1]
            ty_raw = fields.get('ty', '')
            ty = ty_raw.split('\t')[0].strip()
            ce_raw = fields.get('ce', '0').split('\t')[0].replace(',', '.')
            il_raw = fields.get('il', '0').replace(',', '.')
            try:
                ce_val = float(ce_raw)
            except ValueError:
                ce_val = 0.0
            try:
                il_val = float(il_raw)
            except ValueError:
                il_val = 0.0
            zest[nr] = {'ty': ty, 'ce': ce_val, 'il': il_val}

    # Zbierz pozycje z sekcjami RMS
    # [RMS N] gdzie N = nr ZEST, nz = nakład jednostkowy
    pozycje = []
    i = 0
    while i < len(sections):
        name, fields = sections[i]
        if name == 'POZYCJA':
            pos = {'fields': dict(fields), 'rms': {}}
            i += 1
            while i < len(sections):
                sub_name, sub_fields = sections[i]
                if sub_name == 'PRZEDMIAR':
                    i += 1
                elif sub_name.startswith('RMS ') and not sub_name.startswith('RMS ZEST'):
                    nr = sub_name.split()[-1]
                    pos['rms'][nr] = dict(sub_fields)
                    i += 1
                else:
                    break
            pozycje.append(pos)
        else:
            i += 1

    return zest, pozycje


def check(label, actual, expected, errors, ok_list, tol=None):
    if tol is not None:
        try:
            a, e = float(str(actual).replace(',', '.')), float(str(expected).replace(',', '.'))
            if abs(a - e) < tol:
                ok_list.append(label)
                return True
        except (ValueError, TypeError):
            pass
        errors.append((label, actual, expected))
        return False
    if str(actual) == str(expected):
        ok_list.append(label)
        return True
    errors.append((label, actual, expected))
    return False


def run_validation():
    gen = ATHGenerator(PARAMS)
    gen.generate(POZYCJE, PODSUMOWANIE, DANE_TYTULOWE, OUTPUT_PATH)

    zest, pozycje = parse_ath(OUTPUT_PATH)
    errors = []
    ok_list = []

    if len(pozycje) < 2:
        print('BLAD: Sparsowano mniej niż 2 pozycje!')
        return False

    sr = PARAMS['stawka_rg']
    ss = PARAMS['stawka_sprzetu']
    TOL = 0.001

    # ── ZEST — ceny ────────────────────────────────────────────────────────
    if '1' in zest:
        check('ZEST 1 ce=', zest['1']['ce'], sr, errors, ok_list, tol=TOL)
        check('ZEST 1 ty=', zest['1']['ty'], 'R', errors, ok_list)
    else:
        errors.append(('ZEST 1', 'BRAK', 'wymagany'))

    if '2' in zest:
        check('ZEST 2 ce=', zest['2']['ce'], 1.0, errors, ok_list, tol=TOL)
        check('ZEST 2 ty=', zest['2']['ty'], 'M', errors, ok_list)
    else:
        errors.append(('ZEST 2', 'BRAK', 'wymagany'))

    if '3' in zest:
        check('ZEST 3 ce=', zest['3']['ce'], ss, errors, ok_list, tol=TOL)
        check('ZEST 3 ty=', zest['3']['ty'], 'S', errors, ok_list)
    else:
        errors.append(('ZEST 3', 'BRAK', 'wymagany'))

    # ── Pozycja 1 (R=1000, M=500, S=200, ilosc=10) ─────────────────────────
    p1 = pozycje[0]

    # kj=0, cj=0, wn= puste (Norma oblicza)
    check('Poz1 kj=', p1['fields'].get('kj', ''), '0\t0\t0', errors, ok_list)
    check('Poz1 cj=', p1['fields'].get('cj', ''), '0', errors, ok_list)

    # RMS 1 (R)
    if '1' in p1['rms']:
        ok_list.append('Poz1 [RMS 1] obecny')
        nz_raw = p1['rms']['1'].get('nz', '0').split('\t')[0].replace(',', '.')
        il_raw = p1['rms']['1'].get('il', '0').replace(',', '.')
        nz_exp = 1000.0 / sr / 10.0  # r-g/szt
        il_exp = 1000.0 / sr          # total r-g
        check('Poz1 RMS1 nz=', float(nz_raw), nz_exp, errors, ok_list, tol=TOL)
        check('Poz1 RMS1 il=', float(il_raw), il_exp, errors, ok_list, tol=TOL)
    else:
        errors.append(('Poz1 [RMS 1]', 'BRAK', f'nz≈{1000/sr/10:.4f}, il≈{1000/sr:.4f}'))

    # RMS 2 (M)
    if '2' in p1['rms']:
        ok_list.append('Poz1 [RMS 2] obecny')
        nz_raw = p1['rms']['2'].get('nz', '0').split('\t')[0].replace(',', '.')
        il_raw = p1['rms']['2'].get('il', '0').replace(',', '.')
        check('Poz1 RMS2 nz=', float(nz_raw), 500.0 / 10.0, errors, ok_list, tol=TOL)
        check('Poz1 RMS2 il=', float(il_raw), 500.0, errors, ok_list, tol=TOL)
    else:
        errors.append(('Poz1 [RMS 2]', 'BRAK', 'nz=50, il=500'))

    # ── Pozycja 2 (R=5000, M=8000, S=0, ilosc=50) ──────────────────────────
    p2 = pozycje[1]

    if '1' in p2['rms']:
        ok_list.append('Poz2 [RMS 1] obecny')
        nz_raw = p2['rms']['1'].get('nz', '0').split('\t')[0].replace(',', '.')
        il_raw = p2['rms']['1'].get('il', '0').replace(',', '.')
        check('Poz2 RMS1 nz=', float(nz_raw), 5000.0 / sr / 50.0, errors, ok_list, tol=TOL)
        check('Poz2 RMS1 il=', float(il_raw), 5000.0 / sr, errors, ok_list, tol=TOL)
    else:
        errors.append(('Poz2 [RMS 1]', 'BRAK', f'nz≈{5000/sr/50:.4f}'))

    if '3' not in p2['rms']:
        ok_list.append('Poz2 brak [RMS 3] (S=0) - OK')
    else:
        errors.append(('Poz2 [RMS 3]', 'OBECNY', 'powinien być BRAK gdy S=0'))

    # ── Matematyka narzutów ────────────────────────────────────────────────
    suma_R, suma_M, suma_S = 6000.0, 8500.0, 200.0
    kp_p = PARAMS['kp_procent'] / 100
    z_p  = PARAMS['z_procent'] / 100
    vat_p = PARAMS['vat_procent'] / 100

    kp_val = kp_p * (suma_R + suma_S)
    z_val  = z_p  * (suma_R + suma_S + kp_val)
    netto  = suma_R + suma_M + suma_S + kp_val + z_val
    vat_val = vat_p * netto
    brutto  = netto + vat_val

    def check_math(label, actual, expected):
        if abs(actual - expected) < 0.005:
            ok_list.append(label)
        else:
            errors.append((label, f'{actual:.2f}', f'{expected:.2f}'))

    check_math('Matematyka: Kp',     kp_val,   4340.0)
    check_math('Matematyka: Z',      z_val,    1264.8)
    check_math('Matematyka: NETTO',  netto,    20304.8)
    check_math('Matematyka: VAT',    vat_val,  4670.104)
    check_math('Matematyka: BRUTTO', brutto,   24974.904)

    # ── Raport ───────────────────────────────────────────────────────────────
    total = len(ok_list) + len(errors)
    print('=' * 47)
    print('  Walidacja ATH v5')
    print('=' * 47)

    if errors:
        for label, actual, expected in errors:
            print(f'  FAIL [{label}]')
            print(f"    oczekiwane: '{expected}'")
            print(f"    faktyczne:  '{actual}'")
        print('-' * 47)
        print(f'  FAIL: {len(errors)}/{total} sprawdzeń nie przeszło')
        print('=' * 47)
        return False

    print(f'  OK: Wszystkie {total} sprawdzeń przeszło pomyślnie')
    print('=' * 47)
    return True


if __name__ == '__main__':
    ok = run_validation()
    sys.exit(0 if ok else 1)

# -*- coding: utf-8 -*-
"""
Generator plików ATH (Norma PRO) z przedmiarów
"""

import json
import re
from datetime import datetime
from pathlib import Path
from table_parser import parse_przedmiar_table

BASE = Path(__file__).parent

# Załaduj bazę
with open(BASE / "learned_kosztorysy/naklady_merged.json", 'r', encoding='utf-8') as f:
    NAKLADY = json.load(f)

# Indeks KNR
KNR_INDEX = {}
for n in NAKLADY:
    knr = n.get('knr', '')
    if knr:
        KNR_INDEX[knr] = n
        KNR_INDEX[knr.upper().replace(' ', '')] = n


def find_naklady(podstawa, opis):
    """Szuka nakładów dla pozycji"""
    variants = [podstawa, podstawa.upper(), podstawa.replace(' ', ''), podstawa.upper().replace(' ', '')]
    
    for v in variants:
        if v in KNR_INDEX:
            n = KNR_INDEX[v]
            return n.get('R', 0), n.get('M', 0), n.get('S', 0)
    
    for n in NAKLADY:
        knr = n.get('knr', '').upper().replace(' ', '')
        if knr == podstawa.upper().replace(' ', ''):
            return n.get('R', 0), n.get('M', 0), n.get('S', 0)
    
    return 0, 0, 0


def generate_ath(pdf_path, output_path=None, params=None):
    """Generuje plik ATH z przedmiaru PDF"""
    
    # Parsuj przedmiar
    result = parse_przedmiar_table(pdf_path)
    
    # Domyślne parametry
    if params is None:
        params = {
            'stawka_rg': 35.00,
            'kp': 70.0,
            'z': 12.0,
            'vat': 23.0
        }
    
    # Metadane
    nazwa = result['metadata'].get('nazwa', 'Kosztorys')
    adres = result['metadata'].get('adres', '')
    inwestor = result['metadata'].get('inwestor', '')
    data = datetime.now().strftime('%d.%m.%Y')
    
    # Oblicz wartości
    pozycje_ath = []
    suma_r = 0
    suma_m = 0
    suma_s = 0
    
    for poz in result['pozycje']:
        r, m, s = find_naklady(poz['podstawa'], poz['opis'])
        
        r_val = r * poz['ilosc']
        m_val = m * poz['ilosc']
        s_val = s * poz['ilosc']
        
        suma_r += r_val
        suma_m += m_val
        suma_s += s_val
        
        pozycje_ath.append({
            'lp': poz['lp'],
            'podstawa': poz['podstawa'],
            'opis': poz['opis'],
            'jm': poz['jm'],
            'ilosc': poz['ilosc'],
            'R': r,
            'M': m,
            'S': s,
            'R_total': r_val,
            'M_total': m_val,
            'S_total': s_val,
        })
    
    # Narzuty
    R_koszt = suma_r * params['stawka_rg']
    netto = R_koszt + suma_m + suma_s
    kp = netto * params['kp'] / 100
    zysk = (netto + kp) * params['z'] / 100
    netto_z_narzutami = netto + kp + zysk
    vat = netto_z_narzutami * params['vat'] / 100
    brutto = netto_z_narzutami + vat
    
    # Generuj ATH
    ath_lines = []
    
    # Nagłówek
    ath_lines.append('[KOSZTORYS ATHENASOFT]')
    ath_lines.append('co=Copyright Athenasoft Sp. z o.o.')
    ath_lines.append('wf=5')
    ath_lines.append('pr=NORMA\t4.60')
    ath_lines.append(f'nan={nazwa}')
    
    # Strona tytułowa
    ath_lines.append('')
    ath_lines.append('[STRONA TYT]')
    ath_lines.append('na=KOSZTORYS INWESTORSKI\tPRZEDMIAR')
    ath_lines.append(f'nb={nazwa}')
    ath_lines.append(f'ab={adres}')
    ath_lines.append(f'ni={inwestor}')
    ath_lines.append(f'dt={data}\t0\t0')
    
    # Narzuty
    ath_lines.append('')
    ath_lines.append('[NARZUTY NORMA 2]')
    ath_lines.append('na=Koszty pośrednie\tKp')
    ath_lines.append(f'wa={params["kp"]}\t1\t0')
    ath_lines.append('nr=1')
    ath_lines.append('ns=1')
    
    ath_lines.append('')
    ath_lines.append('[NARZUTY NORMA 2]')
    ath_lines.append('na=Zysk\tZ')
    ath_lines.append(f'wa={params["z"]}\t1\t0')
    ath_lines.append('nr=1')
    ath_lines.append('ns=1')
    
    ath_lines.append('')
    ath_lines.append('[NARZUTY NORMA 1]')
    ath_lines.append('na=VAT\tV')
    ath_lines.append(f'wa={params["vat"]}\t1\t0')
    ath_lines.append('nc=1')
    
    # Pozycje
    for idx, poz in enumerate(pozycje_ath, 1):
        ath_lines.append('')
        ath_lines.append('[POZYCJA]')
        ath_lines.append(f'id={idx}')
        
        # Podstawa
        podstawa = poz['podstawa']
        match = re.match(r'(K[NS]?N?R(?:-[A-Z])?)\s*([\d]+-[\d]+)?\s*(\d{4}-\d{2})?', podstawa, re.I)
        if match:
            rodzaj = match.group(1).upper()
            katalog = match.group(2) or ''
            tablica = match.group(3) or ''
            ath_lines.append(f'pd=Generator\t{rodzaj}\t{katalog} {tablica}\t{katalog}\t{tablica}\t\t0')
        else:
            ath_lines.append(f'pd=Generator\tKALK\t{podstawa}\t\t\t\t0')
        
        ath_lines.append(f'na={poz["opis"]}')
        ath_lines.append(f'ob={poz["ilosc"]:.3f}\t{poz["ilosc"]:.3f}\t\t1')
        
        # Jednostka z kodem
        jm = poz['jm'].replace('.', '')
        jm_codes = {'m2': '061', 'm3': '062', 'm': '060', 'szt': '011', 'kpl': '012', 'kg': '030'}
        jm_code = jm_codes.get(jm, '000')
        ath_lines.append(f'jm={jm}\t{jm_code}')
        
        # Ceny jednostkowe
        cj_total = poz['R'] + poz['M'] + poz['S']
        ath_lines.append(f'cj={cj_total:.2f}\t\t{poz["R"]:.2f}\t{poz["M"]:.2f}\t{poz["S"]:.2f}')
    
    # Podsumowanie
    ath_lines.append('')
    ath_lines.append('[PODSUMOWANIE]')
    ath_lines.append('wa=')
    ath_lines.append(f'kb={netto:.2f}\t{R_koszt:.2f}\t{suma_m:.2f}\t{suma_s:.2f}\t0\t0\t0')
    ath_lines.append(f'wc={brutto:.2f}\t{R_koszt:.2f}\t{suma_m:.2f}\t{suma_s:.2f}\t0\t{kp + zysk:.2f}\t{vat:.2f}')
    
    # Zapisz plik
    if output_path is None:
        output_path = Path(pdf_path).with_suffix('.ath')
    
    content = '\n'.join(ath_lines)
    with open(output_path, 'w', encoding='cp1250') as f:
        f.write(content)
    
    print(f'Wygenerowano: {output_path}')
    print(f'Pozycji: {len(pozycje_ath)}')
    print(f'Brutto: {brutto:,.2f} zł')
    
    return output_path


if __name__ == '__main__':
    import sys
    
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else r"E:\przedmiary\Zał. nr 2 - przedmiar.pdf"
    output_path = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\Gabriel\Desktop\kosztorys_wygenerowany.ath"
    
    generate_ath(pdf_path, output_path)

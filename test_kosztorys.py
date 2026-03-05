# -*- coding: utf-8 -*-
"""
Test generowania kosztorysu z bazy KNR
"""

import json
import re
from pathlib import Path
from table_parser import parse_przedmiar_table

# Załaduj bazy
BASE = Path(__file__).parent

with open(BASE / "learned_kosztorysy/naklady_merged.json", 'r', encoding='utf-8') as f:
    NAKLADY = json.load(f)

print(f"Załadowano {len(NAKLADY)} nakładów")

# Utwórz indeks po KNR (różne formaty)
KNR_INDEX = {}
for n in NAKLADY:
    knr = n.get('knr', '')
    if knr:
        # Zapisz oryginał
        KNR_INDEX[knr] = n
        # Zapisz bez spacji
        KNR_INDEX[knr.replace(' ', '')] = n
        # Zapisz uppercase bez spacji
        KNR_INDEX[knr.upper().replace(' ', '')] = n

print(f"Indeks KNR: {len(KNR_INDEX)} pozycji (z wariantami)")

def normalize_knr(knr):
    """Normalizuje podstawę KNR do porównania"""
    knr = knr.upper()
    knr = re.sub(r'\s+', ' ', knr).strip()  # pojedyncze spacje
    return knr

def find_naklady(podstawa, opis):
    """Szuka nakładów dla pozycji"""
    
    # Warianty podstawy do sprawdzenia
    variants = [
        podstawa,
        podstawa.upper(),
        podstawa.replace(' ', ''),
        podstawa.upper().replace(' ', ''),
    ]
    
    # Szukaj exact match
    for v in variants:
        if v in KNR_INDEX:
            n = KNR_INDEX[v]
            return n.get('R', 0), n.get('M', 0), n.get('S', 0), 'EXACT'
    
    # Szukaj w oryginalnych nakładach (porównanie case-insensitive)
    podstawa_upper = podstawa.upper().replace(' ', '')
    for n in NAKLADY:
        knr = n.get('knr', '').upper().replace(' ', '')
        if knr == podstawa_upper:
            return n.get('R', 0), n.get('M', 0), n.get('S', 0), 'EXACT'
    
    # Szukaj partial (np. KNR 4-01 pasuje do KNR 4-01 0354-03)
    # Wyciągnij katalog i tablicę
    m = re.match(r'(K[NS]?N?R(?:-[A-Z])?\s*[\d]+-[\d]+)\s*(\d{4}-\d{2})?', podstawa, re.I)
    if m:
        katalog = m.group(1).upper().replace(' ', '')
        tablica = m.group(2) or ''
        
        for n in NAKLADY:
            knr = n.get('knr', '').upper().replace(' ', '')
            # Dopasuj po katalogu i tablicy
            if tablica and tablica in knr and katalog.replace('-', '') in knr.replace('-', ''):
                return n.get('R', 0), n.get('M', 0), n.get('S', 0), 'PARTIAL'
    
    # Kalkulacja własna - nie szukaj
    if 'KALK' in podstawa.upper():
        return 0, 0, 0, 'KALK'
    
    # Szukaj po opisie (fuzzy) - tylko dla pozycji z tego samego katalogu
    if m:
        katalog = m.group(1).upper()
        opis_lower = opis.lower()
        best_match = None
        best_score = 0
        
        for n in NAKLADY:
            n_knr = n.get('knr', '').upper()
            # Tylko z tego samego katalogu!
            if katalog.replace(' ', '').replace('-', '') not in n_knr.replace(' ', '').replace('-', ''):
                continue
            
            n_opis = n.get('opis', '').lower()
            # Proste podobieństwo - liczba wspólnych słów
            words1 = set(w for w in opis_lower.split() if len(w) > 3)
            words2 = set(w for w in n_opis.split() if len(w) > 3)
            common = len(words1 & words2)
            if common > best_score:
                best_score = common
                best_match = n
        
        if best_match and best_score >= 2:
            return best_match.get('R', 0), best_match.get('M', 0), best_match.get('S', 0), 'FUZZY'
    
    return 0, 0, 0, 'NONE'


def main():
    # Parsuj przedmiar
    pdf_path = r"E:\przedmiary\Zał. nr 2 - przedmiar.pdf"
    result = parse_przedmiar_table(pdf_path)
    
    print(f"\n=== KOSZTORYS ===")
    print(f"Inwestycja: {result['metadata']['nazwa']}")
    print(f"Adres: {result['metadata']['adres']}")
    print(f"Pozycji: {len(result['pozycje'])}")
    
    # Parametry
    STAWKA_RG = 35.00  # zł/r-g
    KP = 0.70  # 70%
    Z = 0.12  # 12%
    VAT = 0.23
    
    suma_R = 0
    suma_M = 0
    suma_S = 0
    matched = 0
    
    print(f"\n{'Lp':>3} {'Podstawa':<22} {'JM':>5} {'Ilość':>8} {'R':>8} {'M':>8} {'Match':<6}")
    print("-" * 80)
    
    for poz in result['pozycje']:
        R, M, S, match_type = find_naklady(poz['podstawa'], poz['opis'])
        
        # Oblicz wartości
        r_val = R * poz['ilosc']
        m_val = M * poz['ilosc']
        s_val = S * poz['ilosc']
        
        suma_R += r_val
        suma_M += m_val
        suma_S += s_val
        
        if match_type != 'NONE':
            matched += 1
        
        print(f"{poz['lp']:3} {poz['podstawa']:<22} {poz['jm']:>5} {poz['ilosc']:8.2f} {r_val:8.2f} {m_val:8.2f} {match_type:<6}")
    
    # Podsumowanie
    print("-" * 80)
    print(f"\nDOPASOWANO: {matched}/{len(result['pozycje'])} ({100*matched/len(result['pozycje']):.0f}%)")
    
    # Robocizna
    R_koszt = suma_R * STAWKA_RG
    
    # Netto
    netto = R_koszt + suma_M + suma_S
    koszty_posrednie = netto * KP
    zysk = (netto + koszty_posrednie) * Z
    netto_z_narzutami = netto + koszty_posrednie + zysk
    vat_kwota = netto_z_narzutami * VAT
    brutto = netto_z_narzutami + vat_kwota
    
    print(f"\n=== PODSUMOWANIE ===")
    print(f"Robocizna (r-g):     {suma_R:12.2f}")
    print(f"Robocizna (zł):      {R_koszt:12.2f} zł (@ {STAWKA_RG} zł/r-g)")
    print(f"Materiały:           {suma_M:12.2f} zł")
    print(f"Sprzęt:              {suma_S:12.2f} zł")
    print(f"----")
    print(f"RAZEM bezpośrednie:  {netto:12.2f} zł")
    print(f"Kp ({KP*100:.0f}%):             {koszty_posrednie:12.2f} zł")
    print(f"Zysk ({Z*100:.0f}%):            {zysk:12.2f} zł")
    print(f"----")
    print(f"NETTO:               {netto_z_narzutami:12.2f} zł")
    print(f"VAT ({VAT*100:.0f}%):            {vat_kwota:12.2f} zł")
    print(f"====")
    print(f"BRUTTO:              {brutto:12.2f} zł")


if __name__ == '__main__':
    main()

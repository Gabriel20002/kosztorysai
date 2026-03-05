# -*- coding: utf-8 -*-
"""
Parser przedmiarów w formacie tabelarycznym Norma PRO

Format tabeli:
| Lp. | Podstawa | Opis i wyliczenia | j.m. | Poszcz | Razem |
"""

import pdfplumber
import re
from pathlib import Path


def parse_przedmiar_table(pdf_path):
    """
    Parsuje przedmiar z tabel PDF (format Norma PRO)
    
    Returns:
        dict: {
            'metadata': {...},
            'dzialy': [...],
            'pozycje': [...]
        }
    """
    
    result = {
        'metadata': {
            'nazwa': '',
            'inwestor': '',
            'adres': '',
            'data': ''
        },
        'dzialy': [],
        'pozycje': []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        # 1. Metadane z pierwszej strony
        first_page = pdf.pages[0].extract_text() or ""
        
        # Szukaj metadanych
        nazwa_match = re.search(r'NAZWA INWESTYCJI\s*:\s*(.+)', first_page)
        if nazwa_match:
            result['metadata']['nazwa'] = nazwa_match.group(1).strip()
        
        adres_match = re.search(r'ADRES INWESTYCJI\s*:\s*(.+)', first_page)
        if adres_match:
            result['metadata']['adres'] = adres_match.group(1).strip()
        
        inwestor_match = re.search(r'INWESTOR\s*:\s*(.+)', first_page)
        if inwestor_match:
            result['metadata']['inwestor'] = inwestor_match.group(1).strip()
        
        data_match = re.search(r'DATA OPRACOWANIA\s*:\s*(.+)', first_page)
        if data_match:
            result['metadata']['data'] = data_match.group(1).strip()
        
        # 2. Parsuj tabele ze wszystkich stron
        all_rows = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                all_rows.extend(table)
        
        # 3. Parsuj pozycje z wierszy tabeli
        current_dzial = "Kosztorys"
        i = 0
        
        while i < len(all_rows):
            row = all_rows[i]
            
            # Pomiń nagłówki
            if row and row[0] == 'Lp.':
                i += 1
                continue
            
            # Pomiń puste wiersze
            if not row or all(cell is None or cell == '' for cell in row):
                i += 1
                continue
            
            # Sprawdź czy to dział (Lp w pierwszej kolumnie = numer, trzecia kolumna = nazwa działu bez KNR)
            # Zabezpiecz dostęp do kolumn
            def get_cell(r, idx):
                if r and len(r) > idx:
                    return str(r[idx] or '').strip()
                return ''
            
            lp_cell = get_cell(row, 0)
            podstawa_cell = get_cell(row, 1)
            opis_cell = get_cell(row, 2)
            
            # Dział: numer w Lp, pusta podstawa (lub tylko numer działowy), nazwa działu w opisie
            if lp_cell.isdigit() and not podstawa_cell and opis_cell and not re.search(r'KNR|KNNR|KSNR|ZKNR', opis_cell):
                # To może być nagłówek działu
                dzial_name = opis_cell
                
                # Sprawdź czy następny wiersz nie jest kontynuacją (d.X)
                if i + 1 < len(all_rows):
                    next_row = all_rows[i + 1]
                    next_lp = str(next_row[0] or '').strip() if next_row else ''
                    if not next_lp.startswith('d.'):
                        current_dzial = dzial_name
                        if current_dzial not in result['dzialy']:
                            result['dzialy'].append(current_dzial)
                        i += 1
                        continue
            
            # Pozycja: numer w Lp, KNR/KNNR/kalk w Podstawie
            if lp_cell.isdigit() and (re.search(r'KNR|KNNR|KSNR|ZKNR|kalk', podstawa_cell, re.I) or 
                                       (i + 1 < len(all_rows) and 
                                        re.search(r'KNR|KNNR|KSNR|ZKNR|kalk', str(all_rows[i+1][1] or ''), re.I))):
                
                pozycja = _parse_pozycja(all_rows, i, current_dzial)
                if pozycja:
                    result['pozycje'].append(pozycja)
                    # Przeskocz przetworzone wiersze
                    i = pozycja.get('_end_idx', i + 1)
                    continue
            
            i += 1
    
    return result


def _parse_pozycja(rows, start_idx, dzial):
    """Parsuje pojedynczą pozycję z wierszy tabeli"""
    
    def get_cell(r, idx):
        if r and len(r) > idx:
            return str(r[idx] or '').strip()
        return ''
    
    row = rows[start_idx]
    lp = int(get_cell(row, 0) or 0)
    
    # Zbierz podstawę (katalog + tablica)
    podstawa_parts = []
    opis_parts = []
    jm = ''
    ilosc = 0.0
    
    # Pierwsza linia
    cell1 = get_cell(row, 1)
    cell2 = get_cell(row, 2)
    cell3 = get_cell(row, 3)
    cell4 = get_cell(row, 4)
    
    if cell1:
        podstawa_parts.append(cell1)
    if cell2:
        opis_parts.append(cell2)
    if cell3:
        jm = cell3
        # Czasem jednostka jest rozdzielona (m | 2 -> m2)
        if cell4 and cell4.isdigit():
            jm = jm + cell4
    
    # Przeglądaj kolejne wiersze aż do RAZEM
    i = start_idx + 1
    found_razem = False
    
    while i < len(rows) and not found_razem:
        r = rows[i]
        
        # Pomiń puste
        if not r or all(cell is None or cell == '' for cell in r):
            i += 1
            continue
        
        # Sprawdź czy nowa pozycja (numer w pierwszej kolumnie)
        first_cell = get_cell(r, 0)
        if first_cell.isdigit() and int(first_cell) != lp:
            # Nowa pozycja - koniec bieżącej
            break
        
        cell1 = get_cell(r, 1)
        cell2 = get_cell(r, 2)
        cell5 = get_cell(r, 5)
        cell6 = get_cell(r, 6)
        
        # Wiersz "d.X" z tablicą KNR
        if first_cell.startswith('d.'):
            if cell1:
                podstawa_parts.append(cell1)
            if cell2:
                opis_parts.append(cell2)
        
        # Wiersz z "analiza indywidualna"
        elif cell1 and 'analiza' in cell1.lower():
            podstawa_parts.append('ANALIZA')
        elif cell1 and 'widualna' in cell1.lower():
            pass  # kontynuacja "indy-widualna"
        elif cell1 and 'kalk' in cell1.lower():
            podstawa_parts.append('KALKULACJA')
        
        # Szukaj RAZEM w dowolnej kolumnie
        for col_idx in range(len(r) if r else 0):
            cell_val = get_cell(r, col_idx)
            if 'RAZEM' in cell_val:
                # Wartość może być w tej samej komórce lub następnej
                razem_val = cell_val.replace('RAZEM', '').strip()
                if not razem_val:
                    # Sprawdź następną kolumnę
                    razem_val = get_cell(r, col_idx + 1)
                if razem_val:
                    try:
                        ilosc = float(razem_val.replace(',', '.').replace(' ', ''))
                    except:
                        pass
                found_razem = True
                break
        
        # Wartość w ostatniej kolumnie (fallback)
        if not found_razem and r:
            last_cell = get_cell(r, len(r) - 1)
            if last_cell and last_cell.replace('.', '').replace(',', '').isdigit():
                try:
                    ilosc = float(last_cell.replace(',', '.'))
                except:
                    pass
        
        i += 1
    
    # Złóż podstawę KNR
    podstawa = ' '.join([p for p in podstawa_parts if p and p not in ['ANALIZA', 'KALKULACJA', 'analiza indy-', 'widualna']])
    podstawa = re.sub(r'\s+', ' ', podstawa).strip()
    
    # Normalizuj KNR: "KNR 4-01 0354-03" -> "KNR 4-01 0354-03"
    knr_match = re.search(r'(K[NS]?N?R(?:-[A-Z])?\s*[\d]+-[\d]+)\s*(\d{4}-\d{2})?', podstawa, re.I)
    if knr_match:
        katalog = knr_match.group(1).upper().replace(' ', ' ')
        tablica = knr_match.group(2) or ''
        podstawa = f"{katalog} {tablica}".strip()
    elif 'ANALIZA' in podstawa_parts or 'KALKULACJA' in podstawa_parts:
        podstawa = 'KALKULACJA WŁASNA'
    
    # Złóż opis
    opis = ' '.join([o for o in opis_parts if o])
    opis = re.sub(r'\s+', ' ', opis).strip()
    opis = re.sub(r'-\s+', '', opis)  # usuń dzielenie wyrazów
    
    # Popraw jednostkę
    if not jm:
        jm = 'szt.'
    jm = jm.replace('.', '').strip()
    if jm in ['m', 'm2', 'm3']:
        pass
    elif jm in ['szt', 'kpl', 'kg', 'mb', 't']:
        jm = jm + '.'
    
    return {
        'lp': lp,
        'dzial': dzial,
        'podstawa': podstawa,
        'opis': opis,
        'jm': jm,
        'ilosc': ilosc,
        '_end_idx': i
    }


if __name__ == '__main__':
    import sys
    import json
    
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else r"E:\przedmiary\Zał. nr 2 - przedmiar.pdf"
    
    result = parse_przedmiar_table(pdf_path)
    
    print(f"=== METADANE ===")
    print(f"Nazwa: {result['metadata']['nazwa']}")
    print(f"Inwestor: {result['metadata']['inwestor']}")
    print(f"Adres: {result['metadata']['adres']}")
    
    print(f"\n=== DZIAŁY ({len(result['dzialy'])}) ===")
    for d in result['dzialy']:
        print(f"  - {d}")
    
    print(f"\n=== POZYCJE ({len(result['pozycje'])}) ===")
    print(f"{'Lp':>3} {'Podstawa':<25} {'JM':>6} {'Ilość':>10}  Opis")
    print("-" * 100)
    
    for poz in result['pozycje']:
        print(f"{poz['lp']:3} {poz['podstawa']:<25} {poz['jm']:>6} {poz['ilosc']:10.3f}  {poz['opis'][:40]}...")

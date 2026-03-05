# -*- coding: utf-8 -*-
"""Test parser dla formatu przedmiaru z KNR na 2 liniach"""

import pdfplumber
import re
import sys

def parse_przedmiar_v2(pdf_path):
    """Parser dla formatu:
    Linia 1: NrSST-B- KNR X-XX Opis...
    Linia 2: d.1. 01 XXXX-XX [jm]
    ...
    RAZEM XX.XXX
    """
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ''
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + '\n'

    lines = full_text.split('\n')
    positions = []

    # Wzorzec dla linii z KNR
    # Format: NrSST-B- KNR X-XX Opis... [jednostka]
    first_line_pattern = r'^(\d+)\s*SST-[A-Z]-\s*(KNR\s*\d+-\d+)\s+(.+?)\s*(m2|m3|m|szt\.?|kpl\.?|kg|t|mb|r-g)?\.?\s*$'

    # Format linii 2: d.1. 01 XXXX-XX [opcjonalnie reszta opisu]
    # Numer tablicy to ZAWSZE 4 cyfry-2 cyfry, np. 0354-09
    second_line_pattern = r'^d\.\d+\.\s*\d+\s+(\d{4}-\d{2})'

    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Szukaj pierwszej linii pozycji
        match1 = re.match(first_line_pattern, line, re.IGNORECASE)
        if match1:
            lp = int(match1.group(1))
            knr_base = match1.group(2)  # np. KNR 4-01
            opis = match1.group(3)
            jm = match1.group(4) if match1.group(4) else None
            
            # Sprawdź następną linię - powinna mieć numer tablicy (format XXXX-XX)
            knr_full = knr_base
            if i + 1 < len(lines):
                match2 = re.match(second_line_pattern, lines[i+1], re.IGNORECASE)
                if match2:
                    table_num = match2.group(1)  # np. 0354-09
                    knr_full = f'{knr_base} {table_num}'
                    # Jednostka może być na końcu tej linii
                    jm_match = re.search(r'(m2|m3|szt\.?|kpl\.?|kg|mb|r-g)\s*$', lines[i+1], re.IGNORECASE)
                    if not jm and jm_match:
                        jm = jm_match.group(1)
                    i += 1
            
            # Zbierz opis z kolejnych linii aż do RAZEM
            opis_lines = [opis]
            j = i + 1
            ilosc = 0
            while j < len(lines) and j < i + 20:
                next_line = lines[j].strip()
                if 'RAZEM' in next_line:
                    # Pobierz ilość
                    razem_match = re.search(r'RAZEM\s+([\d\s,\.]+)', next_line)
                    if razem_match:
                        ilosc_str = razem_match.group(1).replace(' ', '').replace(',', '.')
                        try:
                            ilosc = float(ilosc_str)
                        except:
                            pass
                    break
                # Pomiń wyliczenia (same cyfry, *, +, -, .)
                if re.match(r'^[\d\s,\.\*\+\-=]+\s*(m2|m3|m|szt\.?)?$', next_line):
                    j += 1
                    continue
                # Pomiń nagłówki
                if any(x in next_line for x in ['Lp.', 'spec.', 'techn.']):
                    j += 1
                    continue
                # Nowa pozycja?
                if re.match(r'^\d+\s*SST-[A-Z]-', next_line):
                    break
                # To część opisu
                if len(next_line) > 3 and not re.match(r'^d\.\d+\.', next_line):
                    opis_lines.append(next_line)
                j += 1
            
            full_opis = ' '.join(opis_lines)
            positions.append({
                'lp': lp,
                'knr': knr_full,
                'opis': full_opis[:200],
                'jm': jm or 'szt.',
                'ilosc': ilosc
            })
            
            i = j
        else:
            i += 1

    return positions


if __name__ == '__main__':
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Gabriel\Downloads\06. Zał. nr 2 do SWZ - Przedmiar robót.pdf'
    
    positions = parse_przedmiar_v2(pdf_path)
    
    print(f'Znaleziono {len(positions)} pozycji\n')
    print(f"{'Lp':>3} {'KNR':<25} {'JM':>6} {'Ilosc':>10}  Opis")
    print("-" * 100)
    for pos in positions[:15]:
        print(f"{pos['lp']:3} {pos['knr']:<25} {pos['jm']:>6} {pos['ilosc']:10.3f}  {pos['opis'][:50]}...")
    
    if len(positions) > 15:
        print(f"... i {len(positions) - 15} więcej")

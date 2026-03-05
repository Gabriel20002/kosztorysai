# -*- coding: utf-8 -*-
"""
Uniwersalny parser przedmiarów - obsługuje różne formaty Norma PRO
"""

import pdfplumber
import re
import sys


def parse_przedmiar_universal(pdf_path):
    """
    Parser obsługujący różne formaty przedmiarów:
    
    Format A (SST):
        1SST-B- KNR 4-01 Opis...
        d.1. 01 0354-09 2 m2
    
    Format B (bezpośredni):
        1KNNR 4 Opis... jm
        d.1.10507-10
        
        3KNR 0-35 Opis... jm
        d.1.10121-09
    """
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ''
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + '\n'

    lines = full_text.split('\n')
    positions = []
    
    # Wzorce dla różnych formatów
    
    # Format A: NrSST-B- KNR X-XX Opis...
    format_a_pattern = r'^(\d+)\s*SST-[A-Z]-\s*(KNR\s*\d+-\d+)\s+(.+?)\s*(m2|m3|m|szt\.?|kpl\.?|kg|t|mb|r-g)?\.?\s*$'
    format_a_line2 = r'^d\.\d+\.\s*\d+\s+(\d{4}-\d{2})'
    
    # Format B: NrKNR/KNNR X-XX Opis... jm  lub  NrKNR-W X-XX Opis... jm
    # Obsługuje: KNR, KNNR, KNR-W, KNR-INS, KNNR 4, KNR 0-35, etc.
    # Uwaga: KNNR 4 (bez myślnika!) też jest poprawne
    format_b_pattern = r'^(\d+)\s*(K(?:N+R|NR-[A-Z]+)\s*[\d]+(?:-[\d]+)?)\s+(.+?)\s+(m2|m3|m|szt\.?|kpl\.?|kg|t|mb|r-g)?\s*$'
    format_b_line2 = r'^d\.\d+\.?\d*(\d{4}-\d{2})'
    
    # Format C: Nr analiza indywidualna / kalkulacja własna (bez KNR)
    format_c_pattern = r'^(\d+)\s+(.+?)\s+(m2|m3|m|szt\.?|kpl\.?|kg|t|mb|r-g)\s*$'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Pomiń linie klasyfikacji CPV (np. 45330000-9)
        if re.match(r'^\d{8}-\d', line):
            i += 1
            continue
        
        # Pomiń nagłówki działów (np. 145330000-9 D.I KOTŁOWNIA)
        if re.match(r'^\d+\s*\d{8}-\d', line):
            i += 1
            continue
        
        # === Format A (SST) ===
        match_a = re.match(format_a_pattern, line, re.IGNORECASE)
        if match_a:
            lp = int(match_a.group(1))
            knr_base = match_a.group(2)
            opis = match_a.group(3)
            jm = match_a.group(4)
            
            # Szukaj numeru tablicy w następnej linii
            knr_full = knr_base
            if i + 1 < len(lines):
                match_a2 = re.match(format_a_line2, lines[i+1], re.IGNORECASE)
                if match_a2:
                    knr_full = f'{knr_base} {match_a2.group(1)}'
                    i += 1
            
            # Zbierz ilość z RAZEM
            ilosc = _find_razem(lines, i+1)
            
            positions.append({
                'lp': lp,
                'knr': knr_full,
                'opis': _clean_opis(opis),
                'jm': jm or 'szt.',
                'ilosc': ilosc
            })
            i += 1
            continue
        
        # === Format B (bezpośredni KNR/KNNR) ===
        match_b = re.match(format_b_pattern, line, re.IGNORECASE)
        if match_b:
            lp = int(match_b.group(1))
            knr_base = match_b.group(2)  # np. "KNR 0-35" lub "KNNR 4" lub "KNR-W 2-15"
            opis = match_b.group(3)
            jm = match_b.group(4)
            
            # Szukaj numeru tablicy w następnej linii (format: d.1.1XXXX-XX)
            knr_full = knr_base
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                match_b2 = re.match(format_b_line2, next_line)
                if match_b2:
                    knr_full = f'{knr_base} {match_b2.group(1)}'
                    i += 1
                else:
                    # Alternatywny format: d.1.1 XXXX-XX (ze spacją)
                    match_b2_alt = re.match(r'^d\.\d+\.\d+\s+(\d{4}-\d{2})', next_line)
                    if match_b2_alt:
                        knr_full = f'{knr_base} {match_b2_alt.group(1)}'
                        i += 1
            
            # Zbierz ilość z RAZEM
            ilosc = _find_razem(lines, i+1)
            
            positions.append({
                'lp': lp,
                'knr': knr_full,
                'opis': _clean_opis(opis),
                'jm': jm or 'szt.',
                'ilosc': ilosc
            })
            i += 1
            continue
        
        # === Format C (pozycja bez KNR - np. "2 Prace związane...") ===
        # Format: Nr Opis... jm (bez KNR na początku)
        format_c_match = re.match(r'^(\d+)\s+([A-ZĄĆĘŁŃÓŚŹŻ][^0-9].{10,}?)\s+(m2|m3|m|szt\.?|kpl\.?|kg|t|mb)\.?\s*$', line, re.IGNORECASE)
        if format_c_match:
            lp = int(format_c_match.group(1))
            opis = format_c_match.group(2)
            jm = format_c_match.group(3)
            
            # Sprawdź czy następna linia to "analiza indywidualna" lub kontynuacja opisu
            knr = 'KALKULACJA'
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if 'analiza' in next_line.lower() or 'kalkulacja' in next_line.lower():
                    knr = 'ANALIZA'
                    # Zbierz resztę opisu
                    opis_parts = [opis]
                    j = i + 1
                    while j < min(i + 5, len(lines)):
                        nl = lines[j].strip()
                        if 'RAZEM' in nl or re.match(r'^\d+\s', nl):
                            break
                        if nl and not nl.startswith('d.'):
                            opis_parts.append(nl)
                        j += 1
                    opis = ' '.join(opis_parts)
            
            ilosc = _find_razem(lines, i+1)
            
            positions.append({
                'lp': lp,
                'knr': knr,
                'opis': _clean_opis(opis),
                'jm': jm,
                'ilosc': ilosc
            })
            i += 1
            continue
        
        i += 1
    
    return positions


def _find_razem(lines, start_idx, max_lines=15):
    """Znajduje wartość RAZEM w kolejnych liniach"""
    for j in range(start_idx, min(start_idx + max_lines, len(lines))):
        line = lines[j]
        razem_match = re.search(r'RAZEM\s+([\d\s,\.]+)', line)
        if razem_match:
            ilosc_str = razem_match.group(1).replace(' ', '').replace(',', '.')
            try:
                return float(ilosc_str)
            except:
                return 0.0
        # Stop jeśli nowa pozycja
        if re.match(r'^\d+\s*(?:SST|KNR|KNNR)', line):
            break
    return 0.0


def _clean_opis(opis):
    """Czyści opis z nadmiarowych znaków"""
    opis = re.sub(r'\s+', ' ', opis)  # wielokrotne spacje
    opis = opis.strip()
    return opis[:250]


if __name__ == '__main__':
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else r'E:\przedmiary\Lipki_Przedszkole _Przedmiar_kotłownia+PC.pdf'
    
    positions = parse_przedmiar_universal(pdf_path)
    
    print(f'Znaleziono {len(positions)} pozycji\n')
    print(f"{'Lp':>3} {'KNR':<25} {'JM':>6} {'Ilosc':>10}  Opis")
    print("-" * 100)
    for pos in positions[:20]:
        print(f"{pos['lp']:3} {pos['knr']:<25} {pos['jm']:>6} {pos['ilosc']:10.3f}  {pos['opis'][:45]}...")
    
    if len(positions) > 20:
        print(f"\n... i {len(positions) - 20} wiecej")

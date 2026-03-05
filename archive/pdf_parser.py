# -*- coding: utf-8 -*-
"""
Parser przedmiarów PDF v2.0
Uniwersalny - działa z różnymi formatami
"""

import re
import pdfplumber
from typing import List, Dict, Tuple, Optional
from io import BytesIO


def parse_przedmiar(pdf_file) -> Dict:
    """
    Parsuje PDF z przedmiarem.
    Obsługuje różne formaty: Norma, WINBUD, Zuzia, inne.
    """
    
    if isinstance(pdf_file, bytes):
        pdf_file = BytesIO(pdf_file)
    
    positions = []
    full_text = []
    all_tables = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Wyciągnij tekst
            text = page.extract_text() or ""
            full_text.append(text)
            
            # Wyciągnij tabele
            tables = page.extract_tables() or []
            all_tables.extend(tables)
    
    combined_text = '\n'.join(full_text)
    
    # Próbuj różne metody parsowania
    
    # Metoda 1: Szukaj KNR
    positions = extract_by_knr(combined_text)
    
    # Metoda 2: Jeśli brak KNR, parsuj tabele
    if not positions and all_tables:
        positions = extract_from_tables(all_tables)
    
    # Metoda 3: Parsuj linie z ilościami
    if not positions:
        positions = extract_by_lines(combined_text)
    
    # Metoda 4: Fallback - każda linia z liczbą to pozycja
    if not positions:
        positions = extract_fallback(combined_text)
    
    # Metadane
    metadata = extract_metadata(combined_text)
    
    return {
        "metadata": metadata,
        "positions": positions,
        "pages_count": len(full_text),
        "raw_text": combined_text[:3000]
    }


def extract_by_knr(text: str) -> List[Dict]:
    """Wyciąga pozycje szukając numerów KNR/KNNR"""
    
    positions = []
    
    # Wzorce KNR
    knr_patterns = [
        r'(KNR|KNNR|KSNR|KNR-W|KNBK|NNRNKB)[\s\-]*(\d[\w\-]+)[\s\-]*([\d\-]+)',
        r'(\d{1,2})-(\d{2})\s+(\d{4})-(\d{2})',  # 2-02 0501-02
    ]
    
    for pattern in knr_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            knr = match.group(0).strip()
            
            # Znajdź kontekst (100 znaków po KNR)
            start = match.end()
            context = text[start:start+300]
            
            # Wyciągnij opis
            desc_match = re.search(r'^[^\d]{10,150}', context)
            description = desc_match.group(0).strip() if desc_match else "Pozycja kosztorysowa"
            
            # Wyciągnij ilość i jednostkę
            qty, unit = extract_quantity_unit(context)
            
            positions.append({
                'knr': knr.upper(),
                'description': clean_text(description),
                'quantity': qty or 1.0,
                'unit': unit or 'm2'
            })
    
    return positions


def extract_from_tables(tables: List) -> List[Dict]:
    """Wyciąga pozycje z tabel PDF"""
    
    positions = []
    
    for table in tables:
        if not table or len(table) < 2:
            continue
        
        # Znajdź kolumny (opis, ilość, jednostka)
        header = table[0] if table[0] else []
        
        for row in table[1:]:
            if not row or len(row) < 2:
                continue
            
            # Szukaj kolumny z opisem (najdłuższy tekst)
            desc = ''
            qty = 1.0
            unit = 'm2'
            knr = ''
            
            for cell in row:
                if not cell:
                    continue
                cell = str(cell).strip()
                
                # KNR?
                if re.search(r'KNR|KNNR|\d-\d{2}\s+\d{4}', cell, re.IGNORECASE):
                    knr = cell[:30]
                
                # Ilość? (liczba)
                qty_match = re.search(r'^([\d\s,\.]+)$', cell)
                if qty_match:
                    try:
                        val = float(cell.replace(',', '.').replace(' ', ''))
                        if 0.01 < val < 100000:
                            qty = val
                    except:
                        pass
                
                # Jednostka?
                if re.match(r'^(m2|m3|mb|szt|kpl|kg|t|r-g)\.?$', cell, re.IGNORECASE):
                    unit = cell.lower().replace('.', '')
                
                # Opis? (długi tekst)
                if len(cell) > len(desc) and len(cell) > 10:
                    if not re.match(r'^[\d\s,\.]+$', cell):  # nie sama liczba
                        desc = cell
            
            if desc:
                positions.append({
                    'knr': knr,
                    'description': clean_text(desc)[:200],
                    'quantity': qty,
                    'unit': unit
                })
    
    return positions


def extract_by_lines(text: str) -> List[Dict]:
    """Wyciąga pozycje analizując linie tekstu"""
    
    positions = []
    lines = text.split('\n')
    
    # Wzorce linii z pozycjami
    patterns = [
        # "1. Opis pozycji 123,45 m2"
        r'^(\d+)[\.\)]\s*(.{10,150}?)\s+([\d,\.]+)\s*(m2|m3|mb|szt|kpl|kg)',
        # "Opis pozycji m2 123,45"
        r'^(.{10,100}?)\s+(m2|m3|mb|szt|kpl|kg)\s+([\d,\.]+)',
        # Linia z numerem na początku i liczbą na końcu
        r'^(\d+)[\.\)]\s*(.{10,150}?)\s+([\d,\.]+)\s*$',
    ]
    
    for line in lines:
        line = line.strip()
        if len(line) < 15:
            continue
        
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Parsuj w zależności od wzorca
                if len(groups) >= 3:
                    desc = groups[1] if len(groups[0]) < 5 else groups[0]
                    
                    # Znajdź ilość
                    qty = 1.0
                    for g in groups:
                        if re.match(r'^[\d,\.]+$', str(g)):
                            try:
                                val = float(str(g).replace(',', '.'))
                                if 0.01 < val < 100000:
                                    qty = val
                                    break
                            except:
                                pass
                    
                    # Znajdź jednostkę
                    unit = 'm2'
                    for g in groups:
                        if re.match(r'^(m2|m3|mb|szt|kpl|kg)$', str(g), re.IGNORECASE):
                            unit = str(g).lower()
                            break
                    
                    positions.append({
                        'knr': '',
                        'description': clean_text(str(desc)),
                        'quantity': qty,
                        'unit': unit
                    })
                    break
    
    return positions


def extract_fallback(text: str) -> List[Dict]:
    """
    Fallback - tworzy pozycje z każdej sensownej linii
    """
    
    positions = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Pomijaj krótkie linie
        if len(line) < 20:
            continue
        
        # Pomijaj nagłówki
        if re.match(r'^(strona|page|kosztorys|przedmiar|inwestor|obiekt|data)', line, re.IGNORECASE):
            continue
        
        # Szukaj linii które wyglądają jak pozycje (mają liczby)
        numbers = re.findall(r'[\d,\.]+', line)
        if not numbers:
            continue
        
        # Weź największą liczbę jako ilość
        qty = 1.0
        for num in numbers:
            try:
                val = float(num.replace(',', '.'))
                if 0.1 < val < 100000 and val > qty:
                    qty = val
            except:
                pass
        
        # Wyciągnij opis (tekst bez liczb na końcu)
        desc = re.sub(r'[\d,\.\s]+$', '', line).strip()
        if len(desc) < 10:
            desc = line
        
        # Jednostka
        unit_match = re.search(r'(m2|m3|mb|szt|kpl|kg)', line, re.IGNORECASE)
        unit = unit_match.group(1).lower() if unit_match else 'm2'
        
        positions.append({
            'knr': '',
            'description': clean_text(desc)[:200],
            'quantity': qty,
            'unit': unit
        })
    
    # Usuń duplikaty
    seen = set()
    unique = []
    for p in positions:
        key = p['description'][:50]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    
    return unique[:100]  # Max 100 pozycji


def extract_quantity_unit(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Wyciąga ilość i jednostkę z tekstu"""
    
    patterns = [
        r'([\d\s,\.]+)\s*(m2|m3|mb|szt|kpl|kg|m²|m³)',
        r'(m2|m3|mb|szt|kpl|kg)\s*([\d,\.]+)',
        r'=\s*([\d,\.]+)',
        r'([\d]+[,\.]\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            qty = None
            unit = None
            
            for g in groups:
                if not g:
                    continue
                g = str(g).strip()
                
                # Liczba?
                if re.match(r'^[\d\s,\.]+$', g):
                    try:
                        qty = float(g.replace(',', '.').replace(' ', ''))
                    except:
                        pass
                
                # Jednostka?
                if re.match(r'^(m2|m3|mb|szt|kpl|kg|m²|m³)$', g, re.IGNORECASE):
                    unit = g.lower().replace('²', '2').replace('³', '3')
            
            if qty and qty > 0.01:
                return qty, unit or 'm2'
    
    return None, None


def extract_metadata(text: str) -> Dict:
    """Wyciąga metadane z przedmiaru"""
    
    metadata = {"title": None, "investor": None, "location": None}
    
    # Tytuł
    patterns = [
        r'NAZWA\s*INWESTYCJI[:\s]*(.+)',
        r'OBIEKT[:\s]*(.+)',
        r'PRZEDMIAR\s+ROBÓT?[:\s]*(.+)',
        r'KOSZTORYS[:\s]*(.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text[:2000], re.IGNORECASE)
        if match:
            metadata["title"] = clean_text(match.group(1))[:150]
            break
    
    if not metadata["title"]:
        # Weź pierwszą sensowną linię
        for line in text.split('\n')[:10]:
            line = line.strip()
            if 20 < len(line) < 100 and not re.match(r'^[\d\s,\.]+$', line):
                metadata["title"] = clean_text(line)
                break
    
    return metadata


def clean_text(text: str) -> str:
    """Czyści tekst"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip('.,;:-_ \t\n')
    return text


# Test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            result = parse_przedmiar(f.read())
        
        print(f"Tytuł: {result['metadata'].get('title', '-')}")
        print(f"Pozycji: {len(result['positions'])}")
        print()
        for i, p in enumerate(result['positions'][:10], 1):
            print(f"{i}. [{p['knr'] or '-':15}] {p['description'][:50]:50} | {p['quantity']:.2f} {p['unit']}")

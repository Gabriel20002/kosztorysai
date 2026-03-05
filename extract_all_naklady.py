# -*- coding: utf-8 -*-
"""
Ekstraktor nakładów R/M/S ze wszystkich kosztorysów ATH
Format Norma PRO: ceny jednostkowe w linii cj=
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# Foldery źródłowe
KOSZTORYSY_DIR = r"C:\Users\Gabriel\Desktop\kosztorysy"
OUTPUT_FILE = Path(__file__).parent / "learned_kosztorysy" / "naklady_extracted.json"
PROGRESS_FILE = Path(__file__).parent / "extraction_progress.json"

def parse_ath_file(filepath):
    """Parsuje plik ATH i wyciąga pozycje z cenami jednostkowymi"""
    
    pozycje = []
    
    # Próbuj różne kodowania
    content = None
    for encoding in ['cp1250', 'utf-8', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            break
        except:
            continue
    
    if not content:
        return []
    
    lines = content.split('\n')
    
    current_pos = {}
    in_pozycja = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Początek nowej pozycji
        if line_stripped == '[POZYCJA]':
            # Zapisz poprzednią pozycję jeśli kompletna
            if current_pos and current_pos.get('knr') and (current_pos.get('R', 0) > 0 or current_pos.get('M', 0) > 0 or current_pos.get('S', 0) > 0):
                pozycje.append(current_pos.copy())
            current_pos = {}
            in_pozycja = True
            continue
        
        # Koniec sekcji pozycji
        if line_stripped.startswith('[') and line_stripped != '[POZYCJA]':
            if current_pos and current_pos.get('knr') and (current_pos.get('R', 0) > 0 or current_pos.get('M', 0) > 0 or current_pos.get('S', 0) > 0):
                pozycje.append(current_pos.copy())
            current_pos = {}
            in_pozycja = False
            continue
        
        if not in_pozycja:
            continue
        
        # Podstawa (pd=)
        # Format: pd=Wydawca\tRodzaj\tPełny_KNR\tKatalog\tTablica\t\tCOŚ
        if line_stripped.startswith('pd=') and '\t' in line_stripped:
            parts = line_stripped[3:].split('\t')
            if len(parts) >= 3:
                rodzaj = parts[1].strip() if len(parts) > 1 else ''  # KNR, KNNR, etc.
                pelny_knr = parts[2].strip() if len(parts) > 2 else ''  # np. "2-02 0202-01"
                katalog = parts[3].strip() if len(parts) > 3 else ''  # np. "2-02"
                tablica = parts[4].strip() if len(parts) > 4 else ''  # np. "0202-01"
                
                # Złóż KNR
                if rodzaj and (katalog or pelny_knr):
                    if katalog and tablica:
                        current_pos['knr'] = f"{rodzaj} {katalog} {tablica}"
                    elif pelny_knr:
                        current_pos['knr'] = f"{rodzaj} {pelny_knr}"
                    
                    # Normalizuj: "KNNR 1 0202-08" -> "KNNR 1-01 0202-08" lub "KNR 2-02 0202-01"
                    knr = current_pos.get('knr', '')
                    # Dodaj myślnik jeśli brak: "KNNR 1 0202" -> "KNNR 1-01 0202"
                    knr = re.sub(r'(K[NS]?N?R(?:-[A-Z])?)\s+(\d+)\s+(\d{4})', r'\1 \2-01 \3', knr)
                    current_pos['knr'] = knr
        
        # Opis (na=)
        elif line_stripped.startswith('na=') and not current_pos.get('opis'):
            current_pos['opis'] = line_stripped[3:].strip()
        
        # Jednostka (jm=)
        elif line_stripped.startswith('jm='):
            parts = line_stripped[3:].split('\t')
            current_pos['jm'] = parts[0].strip() if parts else ''
        
        # Ilość (ob=)
        elif line_stripped.startswith('ob='):
            parts = line_stripped[3:].split('\t')
            try:
                current_pos['ilosc'] = float(parts[0].replace(',', '.'))
            except:
                current_pos['ilosc'] = 0
        
        # Ceny jednostkowe (cj=)
        # Format: cj=całość\t?\tR\tM\tS  lub  cj=całość\t\tR\t?\tS
        elif line_stripped.startswith('cj='):
            parts = line_stripped[3:].split('\t')
            # Parsuj wartości - różne formaty
            values = []
            for p in parts:
                try:
                    values.append(float(p.replace(',', '.')))
                except:
                    values.append(0)
            
            # Format typowy: [całość, ?, R, M?, S] lub [całość, ?, R, ?, S]
            if len(values) >= 3:
                current_pos['cj_total'] = values[0]
                current_pos['R'] = values[2] if len(values) > 2 else 0  # Robocizna jednostkowa
                current_pos['M'] = values[3] if len(values) > 3 else 0  # Materiały jednostkowe  
                current_pos['S'] = values[4] if len(values) > 4 else 0  # Sprzęt jednostkowy
    
    # Zapisz ostatnią pozycję
    if current_pos and current_pos.get('knr') and (current_pos.get('R', 0) > 0 or current_pos.get('M', 0) > 0 or current_pos.get('S', 0) > 0):
        pozycje.append(current_pos)
    
    return pozycje


def main():
    print("=" * 60)
    print("EKSTRAKCJA CEN JEDNOSTKOWYCH Z KOSZTORYSÓW ATH")
    print("=" * 60)
    
    # Znajdź wszystkie pliki ATH (bez ATHSZ - to szablony)
    ath_files = []
    for ext in ['*.ath', '*.ATH']:
        ath_files.extend(Path(KOSZTORYSY_DIR).rglob(ext))
    
    # Filtruj - tylko prawdziwe kosztorysy (bez szablonów)
    ath_files = [f for f in ath_files if not f.name.endswith('.ATHSZ')]
    
    print(f"\nZnaleziono {len(ath_files)} plików ATH")
    
    # Progress tracking
    progress = {
        'started': datetime.now().isoformat(),
        'files_total': len(ath_files),
        'files_processed': 0,
        'files_with_data': 0,
        'files_failed': [],
        'pozycje_extracted': 0,
    }
    
    all_naklady = []
    
    # Przetwórz każdy plik
    for idx, ath_file in enumerate(ath_files, 1):
        filename = ath_file.name
        print(f"\n[{idx}/{len(ath_files)}] {filename}...", end=" ")
        
        try:
            pozycje = parse_ath_file(str(ath_file))
            
            if pozycje:
                print(f"OK ({len(pozycje)} pozycji)")
                progress['files_with_data'] += 1
                
                for p in pozycje:
                    p['source'] = filename
                
                all_naklady.extend(pozycje)
                progress['pozycje_extracted'] += len(pozycje)
            else:
                print("(brak pozycji)")
            
            progress['files_processed'] += 1
            
        except Exception as e:
            print(f"BŁĄD: {e}")
            progress['files_failed'].append(filename)
    
    # Deduplikacja - zachowaj unikalne KNR
    print("\n\nDeduplikacja...")
    knr_dict = {}
    for n in all_naklady:
        knr = n.get('knr', '').upper().replace(' ', '')
        if knr:
            existing = knr_dict.get(knr)
            if not existing:
                knr_dict[knr] = n
            else:
                # Zachowaj ten z większymi danymi
                new_sum = n.get('R', 0) + n.get('M', 0) + n.get('S', 0)
                old_sum = existing.get('R', 0) + existing.get('M', 0) + existing.get('S', 0)
                if new_sum > old_sum:
                    knr_dict[knr] = n
    
    unique_naklady = list(knr_dict.values())
    
    # Zapisz wyniki
    print(f"\nZapisywanie {len(unique_naklady)} unikalnych pozycji...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_naklady, f, ensure_ascii=False, indent=2)
    
    # Zapisz progress
    progress['finished'] = datetime.now().isoformat()
    progress['unique_pozycje'] = len(unique_naklady)
    
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    
    # Podsumowanie
    print("\n" + "=" * 60)
    print("PODSUMOWANIE")
    print("=" * 60)
    print(f"Plików przetworzonych: {progress['files_processed']}/{progress['files_total']}")
    print(f"Plików z danymi: {progress['files_with_data']}")
    print(f"Plików z błędami: {len(progress['files_failed'])}")
    print(f"Pozycji wyekstrahowanych: {progress['pozycje_extracted']}")
    print(f"Unikalnych pozycji: {len(unique_naklady)}")
    print(f"\nWynik zapisany do: {OUTPUT_FILE}")
    
    # Statystyki katalogów
    catalogs = {}
    for n in unique_naklady:
        knr = n.get('knr', '')
        match = re.match(r'(K[NS]?N?R(?:-[A-Z])?\s*[\d]+(?:-[\d]+)?)', knr, re.I)
        if match:
            cat = match.group(1).upper().replace(' ', ' ')
            catalogs[cat] = catalogs.get(cat, 0) + 1
    
    print(f"\nKatalogi ({len(catalogs)}):")
    for cat, count in sorted(catalogs.items(), key=lambda x: -x[1])[:20]:
        print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()

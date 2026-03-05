# -*- coding: utf-8 -*-
"""
Nauka z prawdziwych kosztorysów PDF
Wyciąga strukturę i zapisuje jako wzorce
"""

import pdfplumber
import json
import re
from pathlib import Path
from datetime import datetime

PDF_FILES = [
    r"C:\Users\Gabriel\Downloads\1. kosztorys budowlany Małujowice.pdf",
    r"C:\Users\Gabriel\Downloads\2. Małujowice koszorys sanitarny.pdf",
    r"C:\Users\Gabriel\Downloads\3.KOSZTRYS OFERTOWY elektryczny.pdf",
    r"C:\Users\Gabriel\Downloads\2. SIECIEBOROWICE KOSZTORYS SANITARNY.pdf",
    r"C:\Users\Gabriel\Downloads\1. SIECIEBOROWICE BUDOWLANY DOPASOWA.pdf",
    r"C:\Users\Gabriel\Downloads\3. SIECIEBOROWICE KOSZTORYS ELEKTRYCZNY.pdf",
]

def extract_text_from_pdf(pdf_path):
    """Wyciągnij tekst z PDF"""
    text_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text_parts.append(text)
    
    return "\n".join(text_parts)

def analyze_kosztorys(text, filename):
    """Analizuj strukturę kosztorysu"""
    
    lines = text.split('\n')
    
    analysis = {
        'filename': filename,
        'total_lines': len(lines),
        'sections': [],
        'positions': [],
        'summary': {},
        'sample_lines': []
    }
    
    # Szukaj sekcji/działów
    for i, line in enumerate(lines[:100]):  # Pierwsze 100 linii
        line = line.strip()
        if len(line) > 5:
            analysis['sample_lines'].append(f"{i+1}: {line[:100]}")
    
    # Szukaj pozycji KNR
    knr_pattern = r'(KNR|KNNR|KSNR|KNBK)[\s\-]*[\d\w-]+[\s\-]*[\d-]+'
    knr_matches = re.findall(knr_pattern, text, re.IGNORECASE)
    analysis['knr_count'] = len(knr_matches)
    
    # Szukaj sum
    sum_patterns = [
        r'RAZEM[:\s]+([\d\s,\.]+)',
        r'NETTO[:\s]+([\d\s,\.]+)',
        r'BRUTTO[:\s]+([\d\s,\.]+)',
        r'SUMA[:\s]+([\d\s,\.]+)',
        r'OGÓŁEM[:\s]+([\d\s,\.]+)',
    ]
    
    for pattern in sum_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            analysis['summary'][pattern.split('[')[0]] = matches[:3]
    
    return analysis

def main():
    print("=" * 60)
    print("NAUKA Z PRAWDZIWYCH KOSZTORYSÓW")
    print("=" * 60)
    print()
    
    all_analysis = []
    
    for pdf_path in PDF_FILES:
        path = Path(pdf_path)
        
        if not path.exists():
            print(f"[SKIP] Nie znaleziono: {path.name}")
            continue
        
        print(f"[READ] {path.name}")
        
        try:
            text = extract_text_from_pdf(pdf_path)
            analysis = analyze_kosztorys(text, path.name)
            all_analysis.append(analysis)
            
            print(f"       Linii: {analysis['total_lines']}")
            print(f"       KNR: {analysis['knr_count']}")
            print(f"       Sumy: {list(analysis['summary'].keys())}")
            print()
            
            # Zapisz pełny tekst
            output_dir = Path(__file__).parent / "learned_kosztorysy"
            output_dir.mkdir(exist_ok=True)
            
            txt_path = output_dir / f"{path.stem}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"       Zapisano: {txt_path.name}")
            
        except Exception as e:
            print(f"[ERROR] {path.name}: {e}")
        
        print()
    
    # Zapisz analizę
    if all_analysis:
        analysis_path = Path(__file__).parent / "learned_kosztorysy" / "analysis.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(all_analysis, f, indent=2, ensure_ascii=False)
        print(f"Zapisano analizę: {analysis_path}")
    
    print()
    print("=" * 60)
    print("SAMPLE - pierwsze linie z każdego kosztorysu:")
    print("=" * 60)
    
    for a in all_analysis:
        print(f"\n--- {a['filename']} ---")
        for line in a['sample_lines'][:20]:
            print(line)

if __name__ == "__main__":
    main()

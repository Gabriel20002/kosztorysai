"""Analiza formatu pozycji w katalogach KNR"""
import pdfplumber
import re
import sys

def analyze_pdf(path, pages_to_check=None):
    pdf = pdfplumber.open(path)
    print(f"Plik: {path}")
    print(f"Stron: {len(pdf.pages)}")
    
    if pages_to_check is None:
        pages_to_check = [10, 20, 30, 40]
    
    for i in pages_to_check:
        if i >= len(pdf.pages):
            continue
        text = pdf.pages[i].extract_text() or ''
        
        print(f"\n{'='*60}")
        print(f"STRONA {i+1}")
        print('='*60)
        
        # Pokaż tekst (bezpieczny encoding)
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text[:2000])
        
        # Szukaj wzorców pozycji
        print(f"\n--- WYKRYTE WZORCE ---")
        
        # Różne wzorce
        patterns = [
            (r'\d{4}[-/]\d{2}', 'Kod pozycji (0101-01)'),
            (r'[Tt]ablica\s+\d+', 'Tablica'),
            (r'm[23]|szt|kg|mb|kpl', 'Jednostki'),
            (r'KNR[\s\-]*[\w\-]+', 'Referencja KNR'),
            (r'\d+[,\.]\d+\s*(r-g|m-g)', 'Nakłady R/S'),
        ]
        
        for pattern, name in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                unique = list(set(matches))[:5]
                print(f"  {name}: {unique}")
    
    pdf.close()

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Gabriel\Desktop\knr_sources\KNR_AT-38_Systemy_ocieplen_Atlas.pdf'
    analyze_pdf(path)

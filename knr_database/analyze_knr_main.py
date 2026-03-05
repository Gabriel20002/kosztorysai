"""Analiza głównych katalogów KNR 2-01 i 2-02"""
import fitz
import pdfplumber
import os
os.environ['TESSDATA_PREFIX'] = r'C:\Users\Gabriel\clawd\tessdata'
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

files = [
    r'C:\Users\Gabriel\Downloads\692467125-KNR-2-02-tom1.pdf',
    r'C:\Users\Gabriel\Downloads\505013623-KNR-2-01-Budowle-i-Roboty-Ziemne.pdf'
]

for f in files:
    name = f.split('\\')[-1]
    print(f'\n{"="*60}')
    print(f'=== {name} ===')
    print("="*60)
    
    # PyMuPDF
    doc = fitz.open(f)
    pages = len(doc)
    print(f'Strony: {pages}')
    
    # Sprawdź czy ma tekst
    with pdfplumber.open(f) as pdf:
        text_total = 0
        for i in range(min(5, len(pdf.pages))):
            t = pdf.pages[i].extract_text() or ''
            text_total += len(t)
        scan_type = "TEXT" if text_total > 500 else "SCAN"
        print(f'Tekst (5 stron): {text_total} zn -> {scan_type}')
    
    # Test OCR na kilku stronach
    print(f'\nTest OCR (strony 10, 30, 50):')
    for page_num in [10, 30, 50]:
        if page_num >= pages:
            continue
        page = doc[page_num]
        pix = page.get_pixmap(dpi=200)
        img_path = '_temp_test.png'
        pix.save(img_path)
        
        # OCR
        text = pytesseract.image_to_string(img_path, lang='pol')
        
        # Jakość - ile słów rozpoznano
        words = len([w for w in text.split() if len(w) > 2])
        
        # Sample tekstu
        safe_text = text[:200].encode('ascii', 'replace').decode('ascii')
        print(f'  Strona {page_num+1}: {words} slow, {pix.width}x{pix.height}')
        print(f'    Sample: {safe_text[:100]}...')
    
    os.remove('_temp_test.png')
    doc.close()

"""
Dedykowany ekstraktor dla KNR 2-01 i KNR 2-02
Obsługuje rotację, preprocessing, szczegółowy OCR
"""
import os
import re
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from PIL import Image
import io

import fitz  # PyMuPDF

os.environ['TESSDATA_PREFIX'] = r'C:\Users\Gabriel\clawd\tessdata'
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

DB_PATH = Path(__file__).parent / 'knr.db'


@dataclass
class TablePosition:
    """Pozycja/tablica KNR"""
    number: str              # "0114"
    description: str         # Opis robót
    unit: str               # "m2", "m3"
    chapter: str = ""       # "01"
    chapter_name: str = ""  # "Ściany budynków..."
    page: int = 0
    raw_content: str = ""   # Pełna treść tablicy


@dataclass
class ExtractedKNR:
    """Wyekstrahowany katalog"""
    id: str                 # "KNR 2-01"
    name: str
    pages: int
    tables: List[TablePosition] = field(default_factory=list)
    chapters: Dict[str, str] = field(default_factory=dict)


class KNRMainExtractor:
    """Ekstraktor dla głównych katalogów KNR"""
    
    # Konfiguracja katalogów
    CATALOG_CONFIG = {
        'KNR 2-01': {
            'rotation': 90,  # Stopnie rotacji (clockwise)
            'dpi': 200,
            'name': 'Budowle i roboty ziemne'
        },
        'KNR 2-02': {
            'rotation': 0,
            'dpi': 200,
            'name': 'Konstrukcje budowlane'
        }
    }
    
    # Regex patterns
    TABLE_PATTERN = r'[Tt]ablica\s+(\d{4})'
    CHAPTER_PATTERN = r'ROZDZIA[ŁL]\s+(\d+)'
    UNIT_PATTERN = r'[Nn]ak[łl]ady\s+na\s+(?:1\s*)?(m[23²³]|szt\.?|100\s*m[23]?|mb)'
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def detect_catalog(self, filename: str) -> Tuple[str, dict]:
        """Wykryj katalog po nazwie pliku"""
        if '2-02' in filename or '202' in filename:
            return 'KNR 2-02', self.CATALOG_CONFIG['KNR 2-02']
        elif '2-01' in filename or '201' in filename:
            return 'KNR 2-01', self.CATALOG_CONFIG['KNR 2-01']
        return 'UNKNOWN', {'rotation': 0, 'dpi': 200, 'name': 'Unknown'}
    
    def process_page(self, doc, page_num: int, config: dict) -> str:
        """Przetwórz stronę z rotacją i OCR"""
        page = doc[page_num]
        
        # Renderuj z odpowiednim DPI
        pix = page.get_pixmap(dpi=config['dpi'])
        
        # Konwertuj do PIL Image
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        # Rotacja jeśli potrzebna
        if config['rotation']:
            img = img.rotate(-config['rotation'], expand=True)
        
        # OCR
        text = pytesseract.image_to_string(img, lang='pol', config='--psm 6')
        
        return text
    
    def extract_tables_from_text(self, pages_text: Dict[int, str]) -> List[TablePosition]:
        """Wyciągnij tablice z przetworzonego tekstu"""
        tables = []
        current_chapter = ""
        current_chapter_name = ""
        seen_tables = set()
        
        for page_num, text in sorted(pages_text.items()):
            # Sprawdź rozdział
            ch_match = re.search(self.CHAPTER_PATTERN, text)
            if ch_match:
                current_chapter = ch_match.group(1)
                # Szukaj nazwy rozdziału
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if f'ROZDZIA' in line.upper() and current_chapter in line:
                        # Następna linia to nazwa
                        if i + 1 < len(lines):
                            name = lines[i + 1].strip()
                            if len(name) > 10:
                                current_chapter_name = name[:100]
                        break
            
            # Znajdź tablice
            for match in re.finditer(self.TABLE_PATTERN, text):
                table_num = match.group(1)
                
                if table_num in seen_tables:
                    continue
                seen_tables.add(table_num)
                
                # Kontekst: 300 przed, 1000 po
                start = max(0, match.start() - 300)
                end = min(len(text), match.end() + 1000)
                context = text[start:end]
                
                # Wyciągnij opis
                desc = self._extract_description(context, text, match.start() - start)
                
                # Jednostka
                unit = ""
                unit_match = re.search(self.UNIT_PATTERN, context)
                if unit_match:
                    unit = unit_match.group(1).replace('²', '2').replace('³', '3')
                
                tables.append(TablePosition(
                    number=table_num,
                    description=desc,
                    unit=unit,
                    chapter=current_chapter,
                    chapter_name=current_chapter_name,
                    page=page_num,
                    raw_content=context[:500]
                ))
        
        return tables
    
    def _extract_description(self, context: str, full_text: str, table_pos: int) -> str:
        """Wyciągnij opis tablicy"""
        # Szukaj "Wyszczególnienie robót:" przed Tablica
        before = context[:table_pos]
        
        # Pattern dla opisu
        wys_match = re.search(r'[Ww]yszczeg[óo]lnienie\s+rob[óo]t[:\s]+(.+?)(?=[Nn]ak[łl]ady|Tablica|\n\n)', 
                              before, re.DOTALL)
        if wys_match:
            desc = wys_match.group(1).strip()
            desc = re.sub(r'\s+', ' ', desc)
            return desc[:300]
        
        # Alternatywnie - szukaj nagłówka przed tablicą
        lines = before.split('\n')
        for line in reversed(lines[-10:]):
            line = line.strip()
            if len(line) > 20 and not re.match(r'^[\d\s\.,\-]+$', line):
                if 'Tablica' not in line and 'Nakłady' not in line:
                    return line[:200]
        
        return f"Tablica {context[table_pos:table_pos+4]}"
    
    def process_catalog(self, pdf_path: Path, progress_callback=None) -> ExtractedKNR:
        """Przetwórz cały katalog"""
        catalog_id, config = self.detect_catalog(pdf_path.name)
        
        print(f"\n{'='*60}")
        print(f"[KNR] {catalog_id}: {config['name']}")
        print(f"[FILE] {pdf_path.name}")
        print(f"[CONFIG] Rotacja: {config['rotation']}°, DPI: {config['dpi']}")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"[INFO] Stron: {total_pages}")
        
        # OCR wszystkich stron
        pages_text = {}
        
        for i in range(total_pages):
            if i % 20 == 0:
                print(f"  [OCR] Strona {i+1}/{total_pages}")
                if progress_callback:
                    progress_callback(i, total_pages)
            
            try:
                text = self.process_page(doc, i, config)
                pages_text[i] = text
            except Exception as e:
                print(f"  [WARN] Strona {i+1}: {e}")
        
        doc.close()
        
        # Wyciągnij tablice
        tables = self.extract_tables_from_text(pages_text)
        print(f"[RESULT] Wyekstrahowano tablic: {len(tables)}")
        
        if tables:
            print(f"[SAMPLE] Pierwsze tablice:")
            for t in tables[:5]:
                print(f"  [{t.number}] R{t.chapter}: {t.description[:50]}... [{t.unit}]")
        
        return ExtractedKNR(
            id=catalog_id,
            name=config['name'],
            pages=total_pages,
            tables=tables
        )
    
    def save_to_db(self, catalog: ExtractedKNR):
        """Zapisz do bazy"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Usuń stare dane tego katalogu
        cur.execute('DELETE FROM positions WHERE catalog_id = ?', (catalog.id,))
        cur.execute('DELETE FROM catalogs WHERE id = ?', (catalog.id,))
        
        # Dodaj katalog
        cur.execute('''
            INSERT INTO catalogs (id, name, pages_count, extraction_date, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (catalog.id, catalog.name, catalog.pages, datetime.now().isoformat(), 0.85))
        
        # Dodaj tablice
        for t in catalog.tables:
            position_id = f"{catalog.id} {t.number}"
            cur.execute('''
                INSERT OR REPLACE INTO positions
                (id, catalog_id, full_code, description, unit, source, raw_text, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position_id,
                catalog.id,
                position_id,
                t.description,
                t.unit or 'm2',
                'ocr-dedicated',
                t.raw_content,
                0.85
            ))
            
            # Dodaj rozdział jeśli jest
            if t.chapter:
                chapter_id = f"{catalog.id}/R{t.chapter}"
                cur.execute('''
                    INSERT OR IGNORE INTO chapters (id, catalog_id, number, name)
                    VALUES (?, ?, ?, ?)
                ''', (chapter_id, catalog.id, t.chapter, t.chapter_name or f"Rozdział {t.chapter}"))
        
        conn.commit()
        conn.close()
        print(f"[DB] Zapisano: {catalog.id} ({len(catalog.tables)} tablic)")


def main():
    import sys
    
    files = [
        Path(r'C:\Users\Gabriel\Downloads\692467125-KNR-2-02-tom1.pdf'),
        Path(r'C:\Users\Gabriel\Downloads\505013623-KNR-2-01-Budowle-i-Roboty-Ziemne.pdf'),
    ]
    
    # Opcjonalnie tylko jeden
    if len(sys.argv) > 1:
        if '2-02' in sys.argv[1]:
            files = [files[0]]
        elif '2-01' in sys.argv[1]:
            files = [files[1]]
    
    extractor = KNRMainExtractor()
    
    for pdf_path in files:
        if not pdf_path.exists():
            print(f"[ERROR] Nie znaleziono: {pdf_path}")
            continue
        
        catalog = extractor.process_catalog(pdf_path)
        extractor.save_to_db(catalog)
    
    print("\n" + "="*60)
    print("GOTOWE!")


if __name__ == '__main__':
    main()

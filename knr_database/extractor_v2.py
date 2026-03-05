"""
KNR Catalog Extractor v2.0
Podejście: wyłap Tablice i opisy, nakłady R/M/S z kontekstu
"""
import os
import re
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

import pdfplumber
import fitz  # PyMuPDF

# Konfiguracja OCR
os.environ['TESSDATA_PREFIX'] = r'C:\Users\Gabriel\clawd\tessdata'
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    HAS_TESSERACT = True
except:
    HAS_TESSERACT = False

# Ścieżki
DB_PATH = Path(__file__).parent / 'knr.db'
SOURCES_PATH = Path(r'C:\Users\Gabriel\Desktop\knr_sources')


@dataclass
class TableEntry:
    """Tablica KNR"""
    number: str           # "0101"
    name: str             # Opis tablicy
    unit: str = ""        # Jednostka miary
    chapter: str = ""     # Numer rozdziału
    raw_text: str = ""    # Kontekst


@dataclass  
class ExtractedCatalog:
    """Wyekstrahowany katalog"""
    id: str
    name: str
    source_file: str = ""
    pages_count: int = 0
    tables: List[TableEntry] = field(default_factory=list)
    raw_text: str = ""


class KNRExtractorV2:
    """Ekstraktor v2 - focus na Tablice"""
    
    # Wzorce dla ID katalogu
    CATALOG_PATTERNS = [
        (r'KNR\s*(\d+[-/]\d+)', 'KNR'),           # KNR 2-01
        (r'KNR\s+AT[-/]?\s*(\d+)', 'KNR AT'),     # KNR AT-31
        (r'KNR\s+K[-/]?\s*(\d+)', 'KNR K'),       # KNR K-10
        (r'KNR\s+SEK\s*(\d+[-/]?\d*)', 'KNR SEK'),# KNR SEK 02-04
        (r'KNR\s+BC[-/]?\s*(\d+)', 'KNR BC'),     # KNR BC-06
        (r'KNNR\s*(\d+)', 'KNNR'),                # KNNR 5
    ]
    
    # Wzorzec dla Tablicy
    TABLE_PATTERN = r'[Tt]ablica\s+(\d{4})\b'
    
    # Wzorce dla jednostek
    UNIT_PATTERN = r'\b(m[23²³]|szt\.?|km|mb|kg|[tT]|kpl\.?|r-g|m-g)\b'
    
    # Wzorzec dla rozdziału
    CHAPTER_PATTERN = r'[Rr]ozdzia[łl]\s+(\d+)'
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicjalizacja bazy"""
        schema_path = self.db_path.parent / 'schema.sql'
        conn = sqlite3.connect(self.db_path)
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
        conn.commit()
        conn.close()
        print(f"[DB] Baza: {self.db_path}")
    
    def extract_text(self, pdf_path: Path) -> Tuple[str, str, int]:
        """Ekstrakcja tekstu. Zwraca (text, method, pages)"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = len(pdf.pages)
                texts = []
                for page in pdf.pages:
                    t = page.extract_text() or ''
                    texts.append(t)
                full_text = '\n\n--- PAGE ---\n\n'.join(texts)
                
                if len(full_text.strip()) > 1000:
                    return full_text, 'text', pages
        except Exception as e:
            print(f"  [WARN] pdfplumber: {e}")
        
        # Fallback: OCR
        if not HAS_TESSERACT:
            print("  [WARN] Brak Tesseract, pomijam skan")
            return "", "skip", 0
        
        print(f"  [OCR] Przetwarzam skan...")
        return self._ocr_pdf(pdf_path)
    
    def _ocr_pdf(self, pdf_path: Path) -> Tuple[str, str, int]:
        """OCR dla skanów"""
        doc = fitz.open(pdf_path)
        pages = len(doc)
        texts = []
        
        # Limit dla skanów (pierwsze 50 stron wystarczy na strukturę)
        max_pages = min(pages, 50)
        
        for i in range(max_pages):
            if i % 10 == 0:
                print(f"    OCR: {i+1}/{max_pages}")
            
            pix = doc[i].get_pixmap(dpi=150)
            img_path = Path(__file__).parent / '_temp_ocr.png'
            pix.save(str(img_path))
            
            try:
                text = pytesseract.image_to_string(str(img_path), lang='pol')
                texts.append(text)
            except Exception as e:
                print(f"    [WARN] OCR page {i}: {e}")
            
            if img_path.exists():
                img_path.unlink()
        
        doc.close()
        return '\n\n--- PAGE ---\n\n'.join(texts), 'ocr', pages
    
    def detect_catalog(self, text: str, filename: str) -> Tuple[str, str]:
        """Wykryj ID i nazwę katalogu"""
        for pattern, prefix in self.CATALOG_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num = match.group(1).replace('/', '-')
                catalog_id = f"{prefix}-{num}" if prefix != 'KNR' else f"KNR {num}"
                catalog_id = catalog_id.replace('--', '-').strip()
                
                # Szukaj nazwy po ID
                name = self._find_catalog_name(text, match.end())
                return catalog_id, name
        
        # Z nazwy pliku
        for pattern, prefix in self.CATALOG_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                num = match.group(1).replace('/', '-')
                catalog_id = f"{prefix}-{num}" if prefix != 'KNR' else f"KNR {num}"
                return catalog_id.strip(), filename[:60]
        
        return f"UNKNOWN-{filename[:20]}", filename[:60]
    
    def _find_catalog_name(self, text: str, start_pos: int) -> str:
        """Znajdź nazwę katalogu po jego ID"""
        context = text[start_pos:start_pos+500]
        lines = context.split('\n')
        
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 15 and not re.match(r'^[\d\s\-\.]+$', line):
                # Wyczyść
                line = re.sub(r'\s+', ' ', line)
                return line[:100]
        
        return "Katalog nakładów rzeczowych"
    
    def extract_tables(self, text: str, catalog_id: str) -> List[TableEntry]:
        """Wyciągnij tablice z tekstu"""
        tables = []
        seen = set()
        
        # Aktualny rozdział
        current_chapter = ""
        
        # Podziel na strony dla kontekstu
        pages = text.split('--- PAGE ---')
        
        for page_text in pages:
            # Sprawdź rozdział
            ch_match = re.search(self.CHAPTER_PATTERN, page_text)
            if ch_match:
                current_chapter = ch_match.group(1)
            
            # Znajdź tablice
            for match in re.finditer(self.TABLE_PATTERN, page_text):
                table_num = match.group(1)
                
                if table_num in seen:
                    continue
                seen.add(table_num)
                
                # Kontekst: 200 znaków przed i 500 po
                start = max(0, match.start() - 200)
                end = min(len(page_text), match.end() + 500)
                context = page_text[start:end]
                
                # Wyciągnij opis (zazwyczaj przed "Tablica")
                desc = self._extract_table_description(context, match.start() - start)
                
                # Jednostka
                unit_match = re.search(r'[Nn]ak[łl]ady\s+na\s+(\d+\s*)?(m[23²³]|szt\.?|km|mb|kg)', context)
                unit = unit_match.group(2) if unit_match else ""
                
                tables.append(TableEntry(
                    number=table_num,
                    name=desc,
                    unit=unit,
                    chapter=current_chapter,
                    raw_text=context[:300]
                ))
        
        return tables
    
    def _extract_table_description(self, context: str, table_pos: int) -> str:
        """Wyciągnij opis tablicy"""
        # Tekst przed "Tablica"
        before = context[:table_pos]
        lines = before.split('\n')
        
        # Szukaj linii z opisem (ostatnie 3 niepuste linie przed Tablica)
        desc_lines = []
        for line in reversed(lines):
            line = line.strip()
            if line and len(line) > 10:
                # Pomiń linie z samymi liczbami
                if not re.match(r'^[\d\s\.,\-]+$', line):
                    desc_lines.insert(0, line)
                    if len(desc_lines) >= 2:
                        break
        
        if desc_lines:
            desc = ' '.join(desc_lines)
            # Wyczyść
            desc = re.sub(r'\s+', ' ', desc)
            desc = re.sub(r'[Ww]yszczeg[óo]lnienie\s+rob[óo]t:?\s*', '', desc)
            return desc[:200].strip()
        
        return "Tablica " + context[table_pos:table_pos+50].split('\n')[0]
    
    def process_pdf(self, pdf_path: Path) -> Optional[ExtractedCatalog]:
        """Przetwórz PDF"""
        print(f"\n{'='*60}")
        print(f"[FILE] {pdf_path.name}")
        
        text, method, pages = self.extract_text(pdf_path)
        print(f"  Metoda: {method}, Strony: {pages}, Tekst: {len(text)} zn")
        
        if len(text) < 500:
            print("  [SKIP] Za mało tekstu")
            return None
        
        catalog_id, name = self.detect_catalog(text, pdf_path.name)
        print(f"  Katalog: {catalog_id}")
        print(f"  Nazwa: {name[:50]}...")
        
        tables = self.extract_tables(text, catalog_id)
        print(f"  Tablice: {len(tables)}")
        
        if tables:
            print(f"  Sample:")
            for t in tables[:3]:
                print(f"    [{t.number}] {t.name[:50]}... [{t.unit}]")
        
        return ExtractedCatalog(
            id=catalog_id,
            name=name,
            source_file=pdf_path.name,
            pages_count=pages,
            tables=tables,
            raw_text=text[:5000]
        )
    
    def save_catalog(self, catalog: ExtractedCatalog):
        """Zapisz do bazy"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Katalog
        cur.execute('''
            INSERT OR REPLACE INTO catalogs 
            (id, name, source_file, pages_count, extraction_date, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            catalog.id,
            catalog.name,
            catalog.source_file,
            catalog.pages_count,
            datetime.now().isoformat(),
            0.9 if catalog.tables else 0.5
        ))
        
        # Tablice jako pozycje
        for table in catalog.tables:
            position_id = f"{catalog.id} {table.number}"
            cur.execute('''
                INSERT OR REPLACE INTO positions
                (id, catalog_id, full_code, description, unit, source, raw_text, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position_id,
                catalog.id,
                position_id,
                table.name,
                table.unit or 'jm',
                'pdf',
                table.raw_text,
                0.8
            ))
        
        conn.commit()
        conn.close()
        print(f"  [DB] Zapisano: {catalog.id} ({len(catalog.tables)} tablic)")
    
    def process_all(self, source_dir: Path = SOURCES_PATH, limit: int = None):
        """Przetwórz wszystkie PDF"""
        pdfs = sorted(source_dir.glob('*.pdf'))
        if limit:
            pdfs = pdfs[:limit]
        
        print(f"Plików PDF: {len(pdfs)}")
        
        stats = {'ok': 0, 'tables': 0, 'skip': 0}
        
        for pdf_path in pdfs:
            try:
                catalog = self.process_pdf(pdf_path)
                if catalog:
                    self.save_catalog(catalog)
                    stats['ok'] += 1
                    stats['tables'] += len(catalog.tables)
                else:
                    stats['skip'] += 1
            except Exception as e:
                print(f"  [ERROR] {e}")
                stats['skip'] += 1
        
        print(f"\n{'='*60}")
        print(f"GOTOWE: {stats['ok']} katalogów, {stats['tables']} tablic")
        print(f"Pominięto: {stats['skip']}")
        
        return stats


def main():
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    extractor = KNRExtractorV2()
    extractor.process_all(limit=limit)


if __name__ == '__main__':
    main()

"""
KNR Catalog Extractor v1.0
Ekstrakcja danych z PDF katalogów KNR do SQLite + ChromaDB
"""
import os
import re
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict

import pdfplumber
import fitz  # PyMuPDF
import pytesseract

# Konfiguracja Tesseract
os.environ['TESSDATA_PREFIX'] = r'C:\Users\Gabriel\clawd\tessdata'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Ścieżki
DB_PATH = Path(__file__).parent / 'knr.db'
SOURCES_PATH = Path(r'C:\Users\Gabriel\Desktop\knr_sources')

@dataclass
class Position:
    """Pozycja KNR"""
    full_code: str          # "KNR 2-01 0301-01"
    description: str
    unit: str
    labor_hours: float = 0
    materials_value: float = 0
    equipment_hours: float = 0
    raw_text: str = ""
    confidence: float = 1.0

@dataclass  
class ExtractedCatalog:
    """Wyekstrahowany katalog"""
    id: str                 # "KNR 2-01"
    name: str
    publisher: str = ""
    source_file: str = ""
    pages_count: int = 0
    positions: List[Position] = field(default_factory=list)
    chapters: Dict[str, str] = field(default_factory=dict)
    tables: Dict[str, str] = field(default_factory=dict)


class KNRExtractor:
    """Główny ekstraktor katalogów KNR"""
    
    # Wzorce regex
    CATALOG_PATTERNS = [
        r'(KNR\s*[-/]?\s*(\d+[-/]\d+))',           # KNR 2-01, KNR-2-01
        r'(KNR\s+AT[-/]?\s*(\d+))',                 # KNR AT-31
        r'(KNR\s+K[-/]?\s*(\d+))',                  # KNR K-10
        r'(KNR\s+SEK\s*(\d+[-/]\d+))',              # KNR SEK 02-04
        r'(KNR\s+BC[-/]?\s*(\d+))',                 # KNR BC-06
        r'(KNNR\s*(\d+))',                          # KNNR 5
    ]
    
    POSITION_PATTERN = r'''
        (?P<code>(?:KNR|KNNR)[\s\-/]*[\w\-]+\s+\d{4}[-/]\d{2})  # KNR 2-01 0301-01
        [\s\-:]+
        (?P<desc>.+?)                                            # Opis
        [\s\-]+
        (?P<unit>m[23²³]?|szt\.?|km|mb|kg|t|kpl\.?|r-g|m-g)     # Jednostka
    '''
    
    TABLE_PATTERN = r'[Tt]ablica\s+(\d{4})\s*[-:]?\s*(.+?)(?=\n|$)'
    CHAPTER_PATTERN = r'[Rr]ozdział\s+(\d+)\s*[-:]?\s*(.+?)(?=\n|$)'
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicjalizacja bazy danych"""
        schema_path = self.db_path.parent / 'schema.sql'
        conn = sqlite3.connect(self.db_path)
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print(f"[DB] Zainicjalizowano: {self.db_path}")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> tuple[str, str]:
        """
        Ekstrakcja tekstu z PDF.
        Zwraca: (full_text, method: 'text'|'ocr')
        """
        # Najpierw próbuj pdfplumber (szybsze dla PDF z tekstem)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                texts = []
                for page in pdf.pages:
                    text = page.extract_text() or ''
                    texts.append(text)
                
                full_text = '\n\n'.join(texts)
                if len(full_text.strip()) > 500:
                    return full_text, 'text'
        except Exception as e:
            print(f"[WARN] pdfplumber failed: {e}")
        
        # Fallback: OCR
        print(f"[OCR] Przetwarzanie skanu: {pdf_path.name}")
        return self._ocr_pdf(pdf_path), 'ocr'
    
    def _ocr_pdf(self, pdf_path: Path) -> str:
        """OCR dla skanów"""
        doc = fitz.open(pdf_path)
        texts = []
        
        for i, page in enumerate(doc):
            if i % 10 == 0:
                print(f"  [OCR] Strona {i+1}/{len(doc)}")
            
            # Renderuj stronę jako obraz
            pix = page.get_pixmap(dpi=150)
            img_path = Path(__file__).parent / f'_temp_page_{i}.png'
            pix.save(str(img_path))
            
            # OCR
            try:
                text = pytesseract.image_to_string(
                    str(img_path), 
                    lang='pol',
                    config='--psm 6'
                )
                texts.append(text)
            except Exception as e:
                print(f"  [WARN] OCR failed page {i}: {e}")
            finally:
                if img_path.exists():
                    img_path.unlink()
        
        doc.close()
        return '\n\n'.join(texts)
    
    def detect_catalog_id(self, text: str, filename: str) -> tuple[str, str]:
        """Wykryj ID katalogu i nazwę z tekstu lub nazwy pliku"""
        # Z tekstu
        for pattern in self.CATALOG_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                catalog_id = match.group(1).upper().replace('/', '-').replace('  ', ' ')
                # Normalizacja
                catalog_id = re.sub(r'\s+', ' ', catalog_id).strip()
                return catalog_id, self._extract_catalog_name(text, catalog_id)
        
        # Z nazwy pliku
        for pattern in self.CATALOG_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                catalog_id = match.group(1).upper().replace('/', '-').replace('  ', ' ')
                catalog_id = re.sub(r'\s+', ' ', catalog_id).strip()
                return catalog_id, filename
        
        # Fallback
        return f"UNKNOWN-{filename[:20]}", filename
    
    def _extract_catalog_name(self, text: str, catalog_id: str) -> str:
        """Wyciągnij nazwę katalogu"""
        # Szukaj linii po ID katalogu
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if catalog_id.replace(' ', '').lower() in line.replace(' ', '').lower():
                # Zwróć następną niepustą linię jako nazwę
                for j in range(i+1, min(i+5, len(lines))):
                    name = lines[j].strip()
                    if len(name) > 10 and not re.match(r'^[\d\s\-\.]+$', name):
                        return name[:100]
        return catalog_id
    
    def extract_positions(self, text: str, catalog_id: str) -> List[Position]:
        """Ekstrakcja pozycji KNR z tekstu"""
        positions = []
        
        # Wzorzec dla pozycji (różne formaty)
        patterns = [
            # Format: KNR 2-01 0301-01 Opis... m3
            r'((?:KNR|KNNR)[\s\-]*[\w\-]+\s+\d{4}[-/]\d{2})\s+(.+?)\s+(m[23²³]?|szt\.?|km|mb|kg|t|kpl\.?|r-g|m-g|prób\.?)(?:\s|$)',
            
            # Format: 0301-01 Opis... m3 (gdy katalog znany)
            r'(\d{4}[-/]\d{2})\s+(.+?)\s+(m[23²³]?|szt\.?|km|mb|kg|t|kpl\.?|r-g|m-g|prób\.?)(?:\s|$)',
        ]
        
        seen_codes = set()
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                code = match.group(1).strip()
                desc = match.group(2).strip()
                unit = match.group(3).strip().lower()
                
                # Normalizuj kod
                if not code.upper().startswith(('KNR', 'KNNR')):
                    code = f"{catalog_id} {code}"
                
                code = code.upper().replace('/', '-')
                
                # Deduplikacja
                if code in seen_codes:
                    continue
                seen_codes.add(code)
                
                # Wyczyść opis
                desc = re.sub(r'\s+', ' ', desc).strip()
                desc = desc[:500]  # Ogranicz długość
                
                if len(desc) > 10:  # Minimum sensownego opisu
                    positions.append(Position(
                        full_code=code,
                        description=desc,
                        unit=unit,
                        raw_text=match.group(0)[:200]
                    ))
        
        return positions
    
    def extract_rms_values(self, text: str, position: Position) -> Position:
        """Próba ekstrakcji wartości R/M/S dla pozycji"""
        # Szukaj w okolicy pozycji
        pos_idx = text.find(position.full_code)
        if pos_idx == -1:
            pos_idx = text.find(position.description[:50])
        
        if pos_idx != -1:
            context = text[pos_idx:pos_idx+500]
            
            # Wzorce dla R/M/S
            r_match = re.search(r'[Rr](?:obocizna)?[\s:=]+(\d+[,\.]\d+)', context)
            m_match = re.search(r'[Mm](?:ateriały)?[\s:=]+(\d+[,\.]\d+)', context)
            s_match = re.search(r'[Ss](?:przęt)?[\s:=]+(\d+[,\.]\d+)', context)
            
            if r_match:
                position.labor_hours = float(r_match.group(1).replace(',', '.'))
            if m_match:
                position.materials_value = float(m_match.group(1).replace(',', '.'))
            if s_match:
                position.equipment_hours = float(s_match.group(1).replace(',', '.'))
        
        return position
    
    def process_pdf(self, pdf_path: Path) -> Optional[ExtractedCatalog]:
        """Przetwórz pojedynczy PDF"""
        print(f"\n{'='*60}")
        print(f"[PROCESSING] {pdf_path.name}")
        
        # Ekstrakcja tekstu
        text, method = self.extract_text_from_pdf(pdf_path)
        print(f"[INFO] Metoda: {method}, Tekst: {len(text)} znaków")
        
        if len(text) < 100:
            print(f"[SKIP] Za mało tekstu")
            return None
        
        # Wykryj katalog
        catalog_id, catalog_name = self.detect_catalog_id(text, pdf_path.name)
        print(f"[INFO] Katalog: {catalog_id}")
        print(f"[INFO] Nazwa: {catalog_name[:60]}...")
        
        # Ekstrakcja pozycji
        positions = self.extract_positions(text, catalog_id)
        print(f"[INFO] Znaleziono pozycji: {len(positions)}")
        
        # Próba ekstrakcji R/M/S
        for pos in positions:
            self.extract_rms_values(text, pos)
        
        # Zlicz strony
        with pdfplumber.open(pdf_path) as pdf:
            pages_count = len(pdf.pages)
        
        catalog = ExtractedCatalog(
            id=catalog_id,
            name=catalog_name,
            source_file=pdf_path.name,
            pages_count=pages_count,
            positions=positions
        )
        
        # Pokaż sample
        if positions:
            print(f"[SAMPLE] Pierwsze pozycje:")
            for p in positions[:3]:
                print(f"  - {p.full_code}: {p.description[:50]}... [{p.unit}]")
        
        return catalog
    
    def save_to_db(self, catalog: ExtractedCatalog):
        """Zapisz katalog do bazy"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Zapisz katalog
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
            0.9 if catalog.positions else 0.5
        ))
        
        # Zapisz pozycje
        for pos in catalog.positions:
            cur.execute('''
                INSERT OR REPLACE INTO positions
                (id, catalog_id, full_code, description, unit, 
                 labor_hours, materials_value, equipment_hours,
                 raw_text, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pos.full_code,
                catalog.id,
                pos.full_code,
                pos.description,
                pos.unit,
                pos.labor_hours,
                pos.materials_value,
                pos.equipment_hours,
                pos.raw_text,
                pos.confidence,
                'ocr'
            ))
        
        conn.commit()
        conn.close()
        print(f"[DB] Zapisano: {catalog.id} ({len(catalog.positions)} pozycji)")
    
    def process_all(self, source_dir: Path = SOURCES_PATH):
        """Przetwórz wszystkie PDF w folderze"""
        pdfs = list(source_dir.glob('*.pdf'))
        print(f"Znaleziono {len(pdfs)} plików PDF")
        
        stats = {'processed': 0, 'positions': 0, 'errors': 0}
        
        for pdf_path in pdfs:
            try:
                catalog = self.process_pdf(pdf_path)
                if catalog:
                    self.save_to_db(catalog)
                    stats['processed'] += 1
                    stats['positions'] += len(catalog.positions)
            except Exception as e:
                print(f"[ERROR] {pdf_path.name}: {e}")
                stats['errors'] += 1
        
        print(f"\n{'='*60}")
        print(f"PODSUMOWANIE:")
        print(f"  Przetworzono: {stats['processed']} katalogów")
        print(f"  Pozycji: {stats['positions']}")
        print(f"  Błędów: {stats['errors']}")
        
        return stats


def main():
    extractor = KNRExtractor()
    extractor.process_all()


if __name__ == '__main__':
    main()

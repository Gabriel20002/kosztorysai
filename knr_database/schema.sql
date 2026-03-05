-- KNR Database Schema v1.0
-- Hybrydowa baza: SQLite (struktura) + ChromaDB (wektory)

-- Katalogi (KNR 2-01, KNR AT-31, KNR K-10, ...)
CREATE TABLE IF NOT EXISTS catalogs (
    id TEXT PRIMARY KEY,            -- "KNR 2-01", "KNR AT-31"
    name TEXT NOT NULL,             -- "Roboty ziemne", "Systemy ociepleń Baumit"
    publisher TEXT,                 -- "WACETOB", "Athenasoft", "Koprin"
    description TEXT,
    source_file TEXT,               -- nazwa pliku PDF
    pages_count INTEGER,
    extraction_date TEXT,
    confidence REAL DEFAULT 1.0     -- jakość ekstrakcji
);

-- Rozdziały
CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,            -- "KNR 2-01/03"
    catalog_id TEXT NOT NULL,
    number TEXT NOT NULL,           -- "03"
    name TEXT NOT NULL,             -- "Roboty ręczne ziemne"
    FOREIGN KEY (catalog_id) REFERENCES catalogs(id)
);

-- Tablice
CREATE TABLE IF NOT EXISTS tables (
    id TEXT PRIMARY KEY,            -- "KNR 2-01/0301"
    chapter_id TEXT,
    catalog_id TEXT NOT NULL,
    number TEXT NOT NULL,           -- "0301"
    name TEXT NOT NULL,             -- "Roboty ziemne z transportem urobku"
    FOREIGN KEY (chapter_id) REFERENCES chapters(id),
    FOREIGN KEY (catalog_id) REFERENCES catalogs(id)
);

-- Pozycje (główna tabela nakładów)
CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,            -- "KNR 2-01 0301-01"
    table_id TEXT,
    catalog_id TEXT NOT NULL,
    full_code TEXT NOT NULL,        -- "KNR 2-01 0301-01"
    variant TEXT,                   -- "01"
    description TEXT NOT NULL,      -- pełny opis pozycji
    unit TEXT NOT NULL,             -- "m3", "m2", "szt"
    
    -- Nakłady sumaryczne (cache)
    labor_hours REAL,               -- R: roboczogodziny na jednostkę
    materials_value REAL,           -- M: wartość materiałów
    equipment_hours REAL,           -- S: maszynogodziny
    
    -- Metadata
    confidence REAL DEFAULT 1.0,
    source TEXT,                    -- "ocr", "manual", "import"
    raw_text TEXT,                  -- oryginalny tekst z OCR
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (table_id) REFERENCES tables(id),
    FOREIGN KEY (catalog_id) REFERENCES catalogs(id)
);

-- Zasoby (materiały i sprzęt) - słownik
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT CHECK(type IN ('M', 'S')) NOT NULL,  -- M=materiał, S=sprzęt
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    default_price REAL,
    UNIQUE(type, name, unit)
);

-- Nakłady szczegółowe (relacja pozycja-zasób)
CREATE TABLE IF NOT EXISTS position_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id TEXT NOT NULL,
    resource_id INTEGER,
    resource_type TEXT CHECK(resource_type IN ('R', 'M', 'S')) NOT NULL,
    resource_name TEXT,             -- nazwa jeśli nie ma w resources
    quantity REAL NOT NULL,         -- ilość na jednostkę pozycji
    unit TEXT,
    FOREIGN KEY (position_id) REFERENCES positions(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

-- Indeksy dla wydajności
CREATE INDEX IF NOT EXISTS idx_positions_catalog ON positions(catalog_id);
CREATE INDEX IF NOT EXISTS idx_positions_table ON positions(table_id);
CREATE INDEX IF NOT EXISTS idx_positions_code ON positions(full_code);
CREATE INDEX IF NOT EXISTS idx_chapters_catalog ON chapters(catalog_id);
CREATE INDEX IF NOT EXISTS idx_tables_chapter ON tables(chapter_id);
CREATE INDEX IF NOT EXISTS idx_pos_res_position ON position_resources(position_id);

-- Widok: pełne pozycje z hierarchią
CREATE VIEW IF NOT EXISTS v_positions_full AS
SELECT 
    p.id,
    p.full_code,
    c.id as catalog_id,
    c.name as catalog_name,
    ch.number as chapter_number,
    ch.name as chapter_name,
    t.number as table_number,
    t.name as table_name,
    p.description,
    p.unit,
    p.labor_hours,
    p.materials_value,
    p.equipment_hours,
    p.confidence
FROM positions p
LEFT JOIN catalogs c ON p.catalog_id = c.id
LEFT JOIN tables t ON p.table_id = t.id
LEFT JOIN chapters ch ON t.chapter_id = ch.id;

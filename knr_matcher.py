# -*- coding: utf-8 -*-
"""
KNR Matcher v1.0 - Inteligentne dopasowywanie pozycji KNR
Architektura: Embedding Search + AI Ranking

Pipeline:
1. ChromaDB → top 10 kandydatów (semantic search)
2. LLM → ranking i wybór najlepszego (AI in the loop)
3. Confidence check → auto vs human verification
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import logging

log = logging.getLogger(__name__)

# Konfiguracja
DB_PATH = Path(__file__).parent / "knr_database" / "knr.db"
CHROMA_PATH = Path(__file__).parent / "knr_database" / "chroma"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:8b"

# Lazy imports
chromadb = None
requests = None


def _ensure_imports():
    """Lazy import dla opcjonalnych zależności"""
    global chromadb, requests
    if chromadb is None:
        try:
            import chromadb as _chromadb
            chromadb = _chromadb
        except ImportError:
            log.warning("chromadb nie zainstalowany. pip install chromadb")
    if requests is None:
        try:
            import requests as _requests
            requests = _requests
        except ImportError:
            log.warning("requests nie zainstalowany. pip install requests")


@dataclass
class MatchResult:
    """Wynik dopasowania KNR"""
    knr_code: str           # "KNR 2-02 0114"
    description: str        # Opis z bazy
    unit: str              # Jednostka
    confidence: float      # 0.0 - 1.0
    reasoning: str         # Uzasadnienie AI
    alternatives: List[str] # Inne kandydaci
    source: str            # "ai", "exact", "fuzzy"


class KNRMatcher:
    """Inteligentny matcher pozycji KNR"""
    
    def __init__(self, use_ai: bool = True, use_embeddings: bool = True):
        self.use_embeddings = use_embeddings
        self.db_path = DB_PATH
        self.chroma_client = None
        self.collection = None

        # Cache dla wyników
        self._cache = {}

        # Załaduj bazę do pamięci dla szybkiego dostępu
        self._load_positions()

        # Inicjalizuj ChromaDB jeśli dostępny
        if use_embeddings:
            self._init_chroma()

        # Sprawdź raz czy Ollama działa — wyłącz AI jeśli nie
        self.use_ai = use_ai and self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Sprawdź czy Ollama działa (jednokrotne połączenie przy starcie)."""
        _ensure_imports()
        if requests is None:
            return False
        try:
            r = requests.get("http://localhost:11434", timeout=2)
            if r.status_code == 200:
                log.info("Ollama dostępna — AI ranking aktywny")
                return True
        except Exception:
            pass
        log.info("Ollama niedostępna — używam dopasowania bez AI")
        return False

    @staticmethod
    def _is_valid_position(code: str, description: str) -> bool:
        """Sprawdza czy rekord to prawdziwa pozycja KNR (nie śmieć z OCR)."""
        if not code or not description:
            return False
        # Odrzuć kody UNKNOWN
        if code.upper().startswith('UNKNOWN'):
            return False
        # Odrzuć za krótkie opisy
        if len(description.strip()) < 10:
            return False
        # Odrzuć fragmenty spisu treści (dużo kropek lub samych cyfr)
        dot_ratio = description.count('.') / max(len(description), 1)
        if dot_ratio > 0.15:
            return False
        # Odrzuć wiersze z typowymi nagłówkami PDF
        garbage_phrases = ('spis treści', 'rozdział', 'tablica', 'część ogólna')
        desc_lower = description.lower()
        if any(phrase in desc_lower for phrase in garbage_phrases):
            return False
        return True

    def _load_positions(self):
        """Załaduj pozycje z SQLite, filtrując śmieciowe rekordy OCR."""
        self.positions = []

        if not self.db_path.exists():
            log.warning("Brak bazy KNR: %s", self.db_path)
            return

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            SELECT id, full_code, description, unit, catalog_id
            FROM positions
            WHERE description != ''
        ''')

        skipped = 0
        for row in cur.fetchall():
            code, description = row[1], row[2]
            if not self._is_valid_position(code, description):
                skipped += 1
                continue
            self.positions.append({
                'id': row[0],
                'code': code,
                'description': description,
                'unit': row[3] or 'm2',
                'catalog': row[4]
            })

        conn.close()
        log.info("Załadowano %d pozycji KNR (odfiltrowano %d śmieciowych)", len(self.positions), skipped)
    
    def _init_chroma(self):
        """Inicjalizuj ChromaDB z embeddingami"""
        _ensure_imports()
        if chromadb is None:
            self.use_embeddings = False
            return
        
        try:
            self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

            collections = [c.name for c in self.chroma_client.list_collections()]

            if "knr_positions" in collections:
                self.collection = self.chroma_client.get_collection("knr_positions")
                log.info("ChromaDB: załadowano kolekcję (%d pozycji)", self.collection.count())
            else:
                self._build_embeddings()
        except Exception as e:
            log.warning("ChromaDB niedostępny: %s", e)
            self.use_embeddings = False
    
    def _build_embeddings(self):
        """Zbuduj embeddingi dla wszystkich pozycji"""
        if not self.positions:
            return
        
        log.info("ChromaDB: buduję embeddingi dla %d pozycji...", len(self.positions))
        
        self.collection = self.chroma_client.create_collection(
            name="knr_positions",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Batch add
        batch_size = 500
        for i in range(0, len(self.positions), batch_size):
            batch = self.positions[i:i+batch_size]
            
            self.collection.add(
                ids=[p['id'] for p in batch],
                documents=[f"{p['code']}: {p['description']}" for p in batch],
                metadatas=[{
                    'code': p['code'],
                    'unit': p['unit'],
                    'catalog': p['catalog']
                } for p in batch]
            )
            log.debug("ChromaDB: dodano %d/%d", min(i + batch_size, len(self.positions)), len(self.positions))

        log.info("ChromaDB: gotowe (%d pozycji zaindeksowanych)", self.collection.count())
    
    def find_candidates(self, description: str, podstawa: str = "", n: int = 10) -> List[Dict]:
        """Znajdź kandydatów przez embedding search"""
        
        # Najpierw szukaj dokładnego dopasowania po podstawie
        if podstawa:
            podstawa_norm = re.sub(r'[\s\-/]+', '', podstawa.upper())
            for p in self.positions:
                code_norm = re.sub(r'[\s\-/]+', '', p['code'].upper())
                if podstawa_norm == code_norm:
                    return [{'position': p, 'distance': 0.0, 'source': 'exact'}]
        
        # Semantic search przez ChromaDB
        if self.use_embeddings and self.collection:
            query = f"{podstawa} {description}" if podstawa else description
            results = self.collection.query(
                query_texts=[query],
                n_results=n
            )
            
            candidates = []
            if results['ids'] and results['ids'][0]:
                for i, id_ in enumerate(results['ids'][0]):
                    # Znajdź pozycję
                    pos = next((p for p in self.positions if p['id'] == id_), None)
                    if pos:
                        candidates.append({
                            'position': pos,
                            'distance': results['distances'][0][i] if results['distances'] else 0.5,
                            'source': 'embedding'
                        })
            return candidates
        
        # Fallback: prosty fuzzy match
        return self._fuzzy_search(description, n)
    
    def _fuzzy_search(self, description: str, n: int = 10) -> List[Dict]:
        """Prosty fuzzy search jako fallback"""
        desc_words = set(description.lower().split())
        
        scored = []
        for p in self.positions:
            p_words = set(p['description'].lower().split())
            common = len(desc_words & p_words)
            if common > 0:
                scored.append({
                    'position': p,
                    'distance': 1.0 - (common / max(len(desc_words), 1)),
                    'source': 'fuzzy'
                })
        
        scored.sort(key=lambda x: x['distance'])
        return scored[:n]
    
    def ai_rank(self, description: str, candidates: List[Dict], podstawa: str = "") -> MatchResult:
        """Użyj AI do wyboru najlepszego dopasowania - TRYB HYBRYDOWY"""
        
        if not candidates:
            return MatchResult(
                knr_code="",
                description="",
                unit="m2",
                confidence=0.0,
                reasoning="Brak kandydatów",
                alternatives=[],
                source="none"
            )
        
        # 1. EXACT MATCH - bez AI
        if len(candidates) >= 1 and candidates[0].get('source') == 'exact':
            pos = candidates[0]['position']
            return MatchResult(
                knr_code=pos['code'],
                description=pos['description'],
                unit=pos['unit'],
                confidence=0.95,
                reasoning="Dokładne dopasowanie po podstawie KNR",
                alternatives=[],
                source="exact"
            )
        
        # 2. WYSOKIE PODOBIEŃSTWO EMBEDDING (> 0.8) - bez AI
        if candidates and candidates[0].get('distance', 1.0) < 0.2:  # distance < 0.2 = confidence > 0.8
            pos = candidates[0]['position']
            dist = candidates[0]['distance']
            return MatchResult(
                knr_code=pos['code'],
                description=pos['description'],
                unit=pos['unit'],
                confidence=1.0 - dist,
                reasoning="Wysokie podobieństwo semantyczne",
                alternatives=[c['position']['code'] for c in candidates[1:5]],
                source="embedding-high"
            )
        
        # 3. BEZ AI - weź najlepszego kandydata
        if not self.use_ai:
            pos = candidates[0]['position']
            dist = candidates[0]['distance']
            return MatchResult(
                knr_code=pos['code'],
                description=pos['description'],
                unit=pos['unit'],
                confidence=max(0.3, 1.0 - dist),
                reasoning="Najlepsze dopasowanie semantyczne (bez AI)",
                alternatives=[c['position']['code'] for c in candidates[1:5]],
                source="embedding"
            )
        
        # 4. NISKIE PODOBIEŃSTWO - użyj AI do rankingu
        return self._call_llm_ranking(description, candidates, podstawa)
    
    def _call_llm_ranking(self, description: str, candidates: List[Dict], podstawa: str) -> MatchResult:
        """Wywołaj LLM do rankingu"""
        _ensure_imports()
        
        if requests is None:
            # Fallback bez AI
            pos = candidates[0]['position']
            return MatchResult(
                knr_code=pos['code'],
                description=pos['description'],
                unit=pos['unit'],
                confidence=0.5,
                reasoning="Brak AI - wybrano najlepsze dopasowanie",
                alternatives=[c['position']['code'] for c in candidates[1:5]],
                source="fallback"
            )
        
        # Przygotuj prompt - PROSTY FORMAT
        candidates_text = "\n".join([
            f"{i+1}. {c['position']['code']} - {c['position']['description'][:60]}"
            for i, c in enumerate(candidates[:5])
        ])
        
        prompt = f"""Ktora pozycja KNR najlepiej pasuje do opisu roboty budowlanej?

Opis: {description[:80]}

{candidates_text}

Odpowiedz TYLKO numerem (1-{min(5, len(candidates))}) lub 0. /no_think"""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 150}
                },
                timeout=30  # Timeout dla AI
            )
            if response.status_code == 200:
                data = response.json()
                result_text = data.get('response', '').strip()
                # Jeśli response pusty, sprawdź thinking (qwen3)
                if not result_text:
                    thinking = data.get('thinking', '')
                    # Szukaj numeru w thinking
                    nums = re.findall(r'\b([1-5])\b', thinking[-200:])  # Ostatnie 200 znaków
                    if nums:
                        result_text = nums[-1]  # Ostatni numer
                # Parsuj numer z odpowiedzi
                num_match = re.search(r'^(\d+)', result_text)
                if num_match:
                    wybor = int(num_match.group(1))
                    
                    if 1 <= wybor <= len(candidates):
                        pos = candidates[wybor - 1]['position']
                        dist = candidates[wybor - 1].get('distance', 0.3)
                        return MatchResult(
                            knr_code=pos['code'],
                            description=pos['description'],
                            unit=pos['unit'],
                            confidence=max(0.7, 1.0 - dist),  # AI wybór = min 0.7
                            reasoning=f"AI wybral pozycje {wybor}",
                            alternatives=[c['position']['code'] for c in candidates if c != candidates[wybor-1]][:5],
                            source="ai"
                        )
        except Exception as e:
            log.warning("Błąd wywołania AI (Ollama): %s", e)

        # Fallback
        pos = candidates[0]['position']
        return MatchResult(
            knr_code=pos['code'],
            description=pos['description'],
            unit=pos['unit'],
            confidence=0.4,
            reasoning="Fallback - AI niedostępne",
            alternatives=[c['position']['code'] for c in candidates[1:5]],
            source="fallback"
        )
    
    def match(self, description: str, podstawa: str = "", jm: str = "") -> MatchResult:
        """Główna metoda - dopasuj opis do KNR"""
        
        # Cache key
        cache_key = f"{podstawa}:{description[:50]}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 1. Znajdź kandydatów
        candidates = self.find_candidates(description, podstawa)
        
        # 2. AI ranking
        result = self.ai_rank(description, candidates, podstawa)
        
        # Cache
        self._cache[cache_key] = result
        
        return result
    
    def match_batch(self, items: List[Dict]) -> List[MatchResult]:
        """Dopasuj wiele pozycji"""
        results = []
        for item in items:
            result = self.match(
                description=item.get('opis', ''),
                podstawa=item.get('podstawa', ''),
                jm=item.get('jm', '')
            )
            results.append(result)
        return results


# Singleton dla łatwego użycia
_matcher_instance = None

def get_matcher(use_ai: bool = True, use_embeddings: bool = True) -> KNRMatcher:
    """Pobierz instancję matchera (singleton)"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = KNRMatcher(use_ai=use_ai, use_embeddings=use_embeddings)
    return _matcher_instance


# Test
if __name__ == '__main__':
    matcher = KNRMatcher(use_ai=True, use_embeddings=True)
    
    # Test
    test_cases = [
        {"opis": "Wykopy jamiste o głębokości do 1.5m ze skarpami w gruncie kat. III", "podstawa": "KNR 2-01 0310-03"},
        {"opis": "Ściany budynków jednokondygnacyjnych z cegieł pełnych grubości 1 cegły", "podstawa": "KNR 2-02"},
        {"opis": "Ocieplenie ścian styropianem gr. 15cm z wyprawą tynkarską", "podstawa": ""},
    ]
    
    print("\n=== TEST DOPASOWANIA KNR ===\n")
    for test in test_cases:
        result = matcher.match(test['opis'], test['podstawa'])
        print(f"Opis: {test['opis'][:50]}...")
        print(f"  -> {result.knr_code} (confidence: {result.confidence:.2f})")
        print(f"  -> {result.description[:60]}...")
        print(f"  -> Reasoning: {result.reasoning}")
        print(f"  -> Source: {result.source}")
        print()

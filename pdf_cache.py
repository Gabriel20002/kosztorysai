# -*- coding: utf-8 -*-
"""
PDF Cache v1.0
Cache wyników parsowania PDF dla szybszego developmentu

Używa MD5 hash pliku → JSON z wynikami parsowania.
Cache w katalogu output/cache/

Użycie:
    from pdf_cache import PDFCache
    
    cache = PDFCache()
    
    # Sprawdź czy jest w cache
    cached = cache.get(pdf_path)
    if cached:
        pozycje = cached
    else:
        pozycje = parse_pdf(pdf_path)
        cache.set(pdf_path, pozycje)
"""

import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

CACHE_TTL_HOURS = 24

try:
    from logger import get_logger
except ImportError:
    import logging
    def get_logger(name): return logging.getLogger(name)

log = get_logger(__name__)


class PDFCache:
    """Cache dla wyników parsowania PDF"""
    
    def __init__(self, cache_dir: str = None, enabled: bool = True):
        """
        Args:
            cache_dir: katalog cache (domyślnie: output/cache/)
            enabled: czy cache jest włączony
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent / "output" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache skrótów MD5 w pamięci (w obrębie sesji unika wielokrotnego czytania)
        self._hash_cache: dict = {}

    def _get_file_hash(self, file_path: str) -> str:
        """Oblicza MD5 hash pliku (wynik jest cache'owany w pamięci)"""
        if file_path in self._hash_cache:
            return self._hash_cache[file_path]

        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)

        result = md5.hexdigest()
        self._hash_cache[file_path] = result
        return result
    
    def _get_cache_path(self, file_path: str) -> Path:
        """Zwraca ścieżkę do pliku cache"""
        file_hash = self._get_file_hash(file_path)
        filename = Path(file_path).stem
        return self.cache_dir / f"{filename}_{file_hash[:8]}.json"
    
    def get(self, file_path: str) -> Optional[List[Dict]]:
        """
        Pobiera dane z cache.
        
        Args:
            file_path: ścieżka do pliku PDF
            
        Returns:
            Lista pozycji lub None jeśli nie ma w cache
        """
        if not self.enabled:
            return None
        
        if not os.path.exists(file_path):
            return None
        
        cache_path = self._get_cache_path(file_path)

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Sprawdź wersję cache
            if data.get('version', 0) < 1:
                log.debug("Cache outdated: %s", file_path)
                return None

            # Sprawdź TTL
            created_at = data.get('created_at')
            if created_at:
                age = datetime.now() - datetime.fromisoformat(created_at)
                if age > timedelta(hours=CACHE_TTL_HOURS):
                    log.debug("Cache expired (%dh): %s", int(age.total_seconds() / 3600), file_path)
                    return None

            log.info("Cache hit: %s (%d pozycji)",
                     Path(file_path).name, len(data.get('pozycje', [])))

            return data.get('pozycje')

        except FileNotFoundError:
            log.debug("Cache miss: %s", file_path)
            return None
        except Exception as e:
            log.warning("Blad odczytu cache: %s", e)
            return None
    
    def set(self, file_path: str, pozycje: List[Dict]) -> bool:
        """
        Zapisuje dane do cache.
        
        Args:
            file_path: ścieżka do pliku PDF
            pozycje: lista pozycji do zapisania
            
        Returns:
            True jeśli zapisano pomyślnie
        """
        if not self.enabled:
            return False
        
        cache_path = self._get_cache_path(file_path)
        
        try:
            data = {
                'version': 1,
                'source_file': str(file_path),
                'source_hash': self._get_file_hash(file_path),
                'created_at': datetime.now().isoformat(),
                'pozycje_count': len(pozycje),
                'pozycje': pozycje,
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            log.debug("Cache saved: %s (%d pozycji)", cache_path.name, len(pozycje))
            return True
            
        except Exception as e:
            log.warning("Blad zapisu cache: %s", e)
            return False
    
    def invalidate(self, file_path: str) -> bool:
        """Usuwa cache dla pliku"""
        if not self.enabled:
            return False
        
        cache_path = self._get_cache_path(file_path)
        
        if cache_path.exists():
            cache_path.unlink()
            log.debug("Cache invalidated: %s", cache_path.name)
            return True
        
        return False
    
    def clear(self) -> int:
        """Czyści cały cache. Zwraca liczbę usuniętych plików."""
        if not self.enabled or not self.cache_dir.exists():
            return 0
        
        count = 0
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
            count += 1
        
        log.info("Cache cleared: %d plikow", count)
        return count
    
    def stats(self) -> Dict[str, Any]:
        """Zwraca statystyki cache"""
        if not self.enabled or not self.cache_dir.exists():
            return {'enabled': False, 'files': 0, 'size_kb': 0}
        
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            'enabled': True,
            'directory': str(self.cache_dir),
            'files': len(files),
            'size_kb': round(total_size / 1024, 1),
        }


# Singleton dla łatwego użycia
_cache = None

def get_cache() -> PDFCache:
    """Zwraca globalną instancję cache"""
    global _cache
    if _cache is None:
        _cache = PDFCache()
    return _cache


# ============ TEST ============
if __name__ == "__main__":
    cache = PDFCache()
    
    print("PDF Cache Test")
    print("-" * 40)
    print("Stats:", cache.stats())
    
    # Test z dummy danymi
    test_data = [
        {'lp': 1, 'opis': 'Test pozycja', 'ilosc': 10},
        {'lp': 2, 'opis': 'Druga pozycja', 'ilosc': 20},
    ]
    
    # Użyj tego samego pliku jako test
    test_file = __file__  # pdf_cache.py jako "PDF"
    
    print(f"\nTest file: {test_file}")
    print(f"Get (before set): {cache.get(test_file)}")
    
    cache.set(test_file, test_data)
    print(f"Get (after set): {cache.get(test_file)}")
    
    cache.invalidate(test_file)
    print(f"Get (after invalidate): {cache.get(test_file)}")
    
    print("\nStats after test:", cache.stats())
    print("\nOK!")

# -*- coding: utf-8 -*-
"""
Logger dla projektu kosztorysAI

Użycie:
    from logger import get_logger
    
    log = get_logger(__name__)
    log.info("Załadowano dane")
    log.debug("Szczegóły: %s", data)
    log.warning("Coś podejrzanego")
    log.error("Błąd!")

Konfiguracja przez zmienne środowiskowe:
    KOSZTORYS_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR (domyślnie: INFO)
    KOSZTORYS_LOG_FILE=ścieżka (opcjonalnie, loguje też do pliku)
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Domyślny poziom
DEFAULT_LEVEL = os.environ.get('KOSZTORYS_LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.environ.get('KOSZTORYS_LOG_FILE', None)

# Mapowanie nazw na poziomy
LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


class SafeStreamHandler(logging.StreamHandler):
    """Handler który nie crashuje na problemach z kodowaniem"""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            # Zamień problematyczne znaki na ASCII
            safe_msg = msg.encode('ascii', 'replace').decode('ascii')
            self.stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logging(level=None, log_file=None):
    """
    Konfiguruje logging dla całego projektu.
    
    Args:
        level: poziom logowania (DEBUG, INFO, WARNING, ERROR)
        log_file: opcjonalna ścieżka do pliku logów
    """
    if level is None:
        level = DEFAULT_LEVEL
    
    if log_file is None:
        log_file = LOG_FILE
    
    # Poziom
    log_level = LEVEL_MAP.get(level.upper(), logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler konsoli (bezpieczny dla cp1250)
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger('kosztorysAI')
    root_logger.setLevel(log_level)
    
    # Usuń stare handlery
    root_logger.handlers = []
    root_logger.addHandler(console_handler)
    
    # Handler pliku (opcjonalnie)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Plik zawsze DEBUG
        file_handler.setFormatter(logging.Formatter(
            fmt='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name=None):
    """
    Zwraca logger dla modułu.
    
    Args:
        name: nazwa modułu (zazwyczaj __name__)
        
    Returns:
        logging.Logger
    """
    if name is None:
        name = 'kosztorysAI'
    elif not name.startswith('kosztorysAI'):
        name = f'kosztorysAI.{name}'
    
    return logging.getLogger(name)


# Automatyczna konfiguracja przy imporcie
_root = setup_logging()


# ============ TEST ============
if __name__ == "__main__":
    log = get_logger('test')
    
    print("Test loggera (poziom:", DEFAULT_LEVEL, ")")
    print("-" * 50)
    
    log.debug("To jest DEBUG - widoczne tylko przy KOSZTORYS_LOG_LEVEL=DEBUG")
    log.info("To jest INFO - domyslnie widoczne")
    log.warning("To jest WARNING - ostrzezenie")
    log.error("To jest ERROR - blad")
    
    print("-" * 50)
    print("OK!")

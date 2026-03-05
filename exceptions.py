# -*- coding: utf-8 -*-
"""
Hierarchia wyjątków dla kosztorysAI.

Użycie:
    from exceptions import PDFParsingError, KNRMatchingError, ValidationError

    raise PDFParsingError("Nie można odczytać pliku PDF")
"""


class KosztorysError(Exception):
    """Bazowy wyjątek projektu — łap ten jeśli chcesz obsłużyć wszystkie błędy."""


class PDFParsingError(KosztorysError):
    """Błąd podczas parsowania przedmiaru z pliku PDF."""


class KNRMatchingError(KosztorysError):
    """Błąd podczas dopasowywania pozycji do bazy KNR."""


class NormaPROError(KosztorysError):
    """Błąd podczas generowania lub zapisu pliku ATH (Norma PRO)."""


class ValidationError(KosztorysError):
    """Błąd walidacji danych (pozycje, parametry, bazy)."""

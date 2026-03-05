# -*- coding: utf-8 -*-
"""
kosztorysAI — Generator kosztorysów budowlanych

Użycie CLI:
    python -m kosztorysAI przedmiar.pdf -o nazwa
    
Użycie jako biblioteka:
    from kosztorysAI import KosztorysGenerator
    gen = KosztorysGenerator()
    gen.generate("przedmiar.pdf", output_ath="out.ath")
"""

__version__ = "3.2.0"
__author__ = "Gabriel Dlugi"

from .kosztorys_generator import KosztorysGenerator
from .ath_generator import ATHGenerator
from .calculator_engine import CalculatorEngine

__all__ = [
    "KosztorysGenerator",
    "ATHGenerator", 
    "CalculatorEngine",
    "__version__",
]

# -*- coding: utf-8 -*-
"""
Formattery liczb dla kosztorysAI.

Centralne miejsce dla wszystkich formatów liczbowych używanych w projekcie,
eliminuje 3 różne implementacje rozrzucone po modułach.

Użycie:
    from formatters import fmt_ath, fmt_ath4, fmt_pdf, fmt_summary
"""
import math


def fmt_ath(val: float) -> str:
    """Format ATH (Norma PRO): przecinek dziesiętny, 2 miejsca.
    Przykład: 1234.56 → '1234,56'
    """
    if not math.isfinite(val):
        return "0,00"
    return f"{val:.2f}".replace(".", ",")


def fmt_ath4(val: float) -> str:
    """Format ATH z 4 miejscami, bez zbędnych zer na końcu.
    Przykład: 1.5000 → '1,5', 1.0000 → '1'
    """
    if not math.isfinite(val):
        return "0"
    return f"{val:.4f}".replace(".", ",").rstrip("0").rstrip(",") or "0"


def fmt_pdf(val: float) -> str:
    """Format PDF: spacja jako separator tysięcy, kropka dziesiętna.
    Przykład: 12345.67 → '12 345.67'
    """
    if not math.isfinite(val):
        return "0.00"
    return f"{val:,.2f}".replace(",", " ")


def fmt_summary(val: float) -> str:
    """Format podsumowania (CLI/logi): spacja jako separator tysięcy.
    Przykład: 12345.67 → '12 345.67'
    """
    if not math.isfinite(val):
        return "0.00"
    return f"{val:,.2f}".replace(",", " ")

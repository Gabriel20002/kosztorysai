# kosztorysAI v3.2

Generator kosztorysów budowlanych ATH + PDF z przedmiarów.

## Instalacja

```bash
# Z repozytorium
cd kosztorysAI
pip install -e .

# Wymagane zależności
pip install pdfplumber fpdf2
```

## Użycie

### CLI (zalecane)

```bash
# Podstawowe użycie
python -m kosztorysAI przedmiar.pdf

# Lub bezpośrednio
python cli.py przedmiar.pdf

# Z opcjami
python -m kosztorysAI przedmiar.pdf -o nazwa_wyjscia --nazwa "Remont budynku" --inwestor "Gmina Brzeg"

# Tylko ATH
python -m kosztorysAI przedmiar.pdf --ath

# Podgląd bez generowania
python -m kosztorysAI przedmiar.pdf --dry-run
```

### Jako biblioteka

```python
from kosztorysAI import KosztorysGenerator

gen = KosztorysGenerator()
gen.generate(
    "przedmiar.pdf",
    output_ath="kosztorys.ath",
    output_pdf="kosztorys.pdf",
    dane_tytulowe={
        "nazwa_inwestycji": "Remont budynku",
        "inwestor": "Gmina Brzeg",
    }
)
```

## Opcje CLI

| Opcja | Opis | Domyślnie |
|-------|------|-----------|
| `-o, --output` | Ścieżka wyjściowa (bez rozszerzenia) | nazwa_przedmiaru |
| `--ath` | Generuj tylko ATH | oba |
| `--pdf` | Generuj tylko PDF | oba |
| `--nazwa` | Nazwa inwestycji | - |
| `--inwestor` | Nazwa inwestora | - |
| `--wykonawca` | Nazwa wykonawcy | KLONEKS |
| `--stawka-rg` | Stawka roboczogodziny | 35.00 zł |
| `--kp` | Koszty pośrednie % | 70% |
| `--zysk` | Zysk % | 12% |
| `--vat` | VAT % | 23% |
| `--dry-run` | Podgląd bez generowania | - |
| `--no-cache` | Wyłącz cache PDF | - |

## Struktura projektu

```
kosztorysAI/
├── cli.py                    # Entry point CLI
├── kosztorys_generator.py    # Główny generator
├── ath_generator.py          # Generator ATH (Norma PRO)
├── calculator_engine.py      # Obliczenia R/M/S
├── pdf_generator_v2.py       # Generator PDF
├── validators/               # Walidatory tekstu i obliczeń
├── learned_kosztorysy/       # Baza nakładów (689) i wzorców (987)
├── tests/                    # Testy jednostkowe (42)
├── docs/                     # Dokumentacja formatu ATH
├── output/                   # Generowane pliki
└── archive/                  # Stare wersje (backup)
```

## Format ATH

Generowane pliki ATH są zgodne z **Norma PRO** i zawierają:
- Globalne zestawienie RMS (R=robocizna, M=materiały, S=sprzęt)
- Pozycje z referencjami do RMS ZEST
- Narzuty (Kp, Z)
- Kodowanie CP1250

Dokumentacja formatu: `docs/ATH_FORMAT.md`

## Testy

```bash
python tests/run_all.py
```

## Licencja

MIT

# AUDYT kosztorysAI

**Data:** 2025-07-15  
**Cel:** Konsolidacja do jednego programu BEZ cofania progresu

---

## 🟢 AKTYWNA ŚCIEŻKA (CLI) — DZIAŁA, NIE RUSZAĆ

```
cli.py
  └── kosztorys_generator.py (KosztorysGenerator)
        ├── validators/
        │     ├── text_fixer.py      ✅ używany
        │     ├── calc_validator.py  ✅ używany  
        │     └── logic_validator.py ✅ używany
        ├── calculator_engine.py     ✅ używany (obliczenia R/M/S)
        ├── ath_generator.py         ✅ używany (generuje ATH) ← NAPRAWIONE DZIŚ
        ├── pdf_generator_v2.py      ✅ używany (generuje PDF)
        ├── db_validator.py          ✅ używany (walidacja baz)
        ├── logger.py                ✅ używany
        ├── pdf_cache.py             ✅ używany
        └── learned_kosztorysy/
              ├── naklady_rms.json   ✅ 689 rekordów
              └── pozycje_wzorcowe.json ✅ 987 rekordów
```

**Komenda działająca:**
```bash
python cli.py "przedmiar.pdf" -o nazwa
```

---

## 🟡 STARE WERSJE WEB (Streamlit) — DO USUNIĘCIA LUB ARCHIWIZACJI

| Plik | Co robi | Status |
|------|---------|--------|
| `main.py` | Streamlit v3 (używa engine_v2) | ❌ STARE |
| `app.py` | Streamlit v4 + AI (używa ai_engine + engine_v2) | ❌ STARE |
| `app_v2.py` | Streamlit v2 (używa engine_v2) | ❌ STARE |
| `run_server.py` | Runner dla app.py | ❌ STARE |
| `START.bat` | Uruchamia main.py | ❌ STARE |
| `START_SERVER.bat` | ? | ❌ STARE |
| `START_V2.bat` | ? | ❌ STARE |

**Dlaczego STARE:**
- Używają `engine_v2.py` który ma inną bazę KNR (z `kosztorys/knowledge/knr/`)
- Nie korzystają z naprawionego `ath_generator.py`
- Generują ATH przez stary `output/ath_generator.py` (inna ścieżka!)

---

## 🟡 SILNIKI — DUPLIKATY

| Plik | Używany przez | Baza danych | Status |
|------|---------------|-------------|--------|
| `kosztorys_generator.py` | CLI | `learned_kosztorysy/` | ✅ AKTYWNY |
| `engine.py` | (nikt?) | `knr_base.json` | ❌ STARY |
| `engine_v2.py` | main.py, app.py, app_v2.py | `kosztorys/knowledge/knr/` | ❌ STARY |
| `ai_engine.py` | app.py | Claude/GPT API | 🔶 OPCJONALNY |
| `calculator_engine.py` | kosztorys_generator | - | ✅ AKTYWNY |

---

## 🟡 GENERATORY PDF — DUPLIKATY

| Plik | Używany przez | Status |
|------|---------------|--------|
| `pdf_generator_v2.py` | kosztorys_generator | ✅ AKTYWNY |
| `pdf_generator.py` | (nikt?) | ❌ STARY |

---

## 🟡 PARSERY — OK

| Plik | Używany przez | Status |
|------|---------------|--------|
| `pdf_parser.py` | main.py, app.py (Streamlit) | 🔶 tylko dla Streamlit |

**Uwaga:** `kosztorys_generator.py` ma WŁASNY parser wbudowany (metoda `parse_przedmiar_pdf`)!

---

## 🔴 ŚMIECI — DO USUNIĘCIA

| Plik | Co to | Usunąć? |
|------|-------|---------|
| `brzeg_sanitariaty.py` | Jednorazowy skrypt generujący konkretny kosztorys | ✅ TAK |
| `brzeg_sanitariaty_v2.py` | j.w. | ✅ TAK |
| `check_pdf.py` | Debug tool | ✅ TAK |
| `learn_from_pdfs.py` | Jednorazowy skrypt uczący | 🔶 archiwum |
| `test_all.py` | Stare testy | ✅ TAK (są nowe w tests/) |
| `test_formula.py` | Stare testy | ✅ TAK |
| `test_full.py` | Stare testy | ✅ TAK |
| `test_parser.py` | Stare testy | ✅ TAK |
| `output_*.ath`, `output_*.pdf` | Pliki wyjściowe w głównym katalogu | ✅ TAK |
| `test_*.pdf`, `test_*.ath` | Pliki testowe w głównym katalogu | ✅ TAK |
| `knr_base.json` | Stara baza dla engine.py | ❌ sprawdź czy używane |

---

## 📊 PODSUMOWANIE

### Zachować (core):
```
cli.py
kosztorys_generator.py
calculator_engine.py
ath_generator.py
pdf_generator_v2.py
db_validator.py
logger.py
pdf_cache.py
validators/
learned_kosztorysy/
config/
tests/
docs/
```

### Usunąć (śmieci):
```
brzeg_sanitariaty.py
brzeg_sanitariaty_v2.py
check_pdf.py
test_all.py
test_formula.py
test_full.py
test_parser.py
output_*.ath
output_*.pdf
test_*.pdf (w głównym)
```

### Zarchiwizować (stare wersje):
```
main.py → archive/
app.py → archive/
app_v2.py → archive/
engine.py → archive/
engine_v2.py → archive/
ai_engine.py → archive/
pdf_parser.py → archive/
pdf_generator.py → archive/
run_server.py → archive/
START*.bat → archive/
knr_base.json → archive/
learn_from_pdfs.py → archive/
```

---

## 🎯 PLAN KONSOLIDACJI

### Faza 1: Backup + archiwizacja ✅
- Backup: `C:\Users\Gabriel\Desktop\backup4_kosztorysAI`
- 18 plików → `archive/`
- 12 plików → usunięte
- Commit: `b46f0a7`

### Faza 2: Pakiet Python ✅
- Dodano `__init__.py`, `__main__.py`, `pyproject.toml`
- Użycie: `python -m kosztorysAI przedmiar.pdf`
- Instalacja: `pip install -e .` → komenda `kosztorys`
- Commit: `a7d2144`

---

## 📊 FINALNA STRUKTURA

```
kosztorysAI/
├── __init__.py               # Eksporty: KosztorysGenerator, ATHGenerator
├── __main__.py               # Entry: python -m kosztorysAI
├── pyproject.toml            # Instalacja pip
├── cli.py                    # CLI entry point
├── kosztorys_generator.py    # Główny generator
├── ath_generator.py          # ATH (Norma PRO)
├── calculator_engine.py      # Obliczenia R/M/S
├── pdf_generator_v2.py       # PDF output
├── db_validator.py
├── logger.py
├── pdf_cache.py
├── validators/               # TextFixer, CalcValidator, LogicValidator
├── learned_kosztorysy/       # 689 nakładów, 987 wzorców
├── tests/                    # 42 testy ✅
├── docs/                     # ATH_FORMAT.md
├── config/
├── output/
├── archive/                  # Stare wersje
├── README.md
├── ROADMAP.md
└── AUDYT.md
```

---

## ✅ STATUS

| Metryka | Wartość |
|---------|---------|
| Pliki w głównym | 12 (było 35+) |
| Testy | 42/42 ✅ |
| CLI | ✅ działa |
| Moduł | ✅ `python -m kosztorysAI` |
| ATH | ✅ R+M+S |
| Backup | ✅ backup4 |

---

## 🔮 PRZYSZŁOŚĆ (opcjonalne)

1. **Naprawa UI Streamlit** — użyć nowego generatora
2. **Publikacja PyPI** — `pip install kosztorysAI`
3. **AI engine** — przywrócić jako opcjonalny moduł

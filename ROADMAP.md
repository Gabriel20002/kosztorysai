# kosztorysAI - ROADMAP

**Wersja aktualna:** 2.0.0
**Data:** 2026-02-25

---

## 🎯 CEL: Idealne kosztorysy

Priorytet Gabriela: **nauka robienia idealnych kosztorysów**

---

## FAZA 1: JAKOŚĆ DOPASOWANIA (aktualnie)

### Problem
- Baza ma 355 pozycji KNR, ale dopasowanie jest słabe (~30-50%)
- Brakuje wielu katalogów i pozycji
- Ceny są nieaktualne

### Zadania
- [ ] **Rozbudowa bazy KNR** - cel: 1000+ pozycji
  - [ ] Import kolejnych kosztorysów od Gabriela
  - [ ] Parsowanie katalogów KNR z PDF/skanów
  - [ ] Ręczne dodawanie brakujących pozycji

- [ ] **Lepszy matching**
  - [ ] Normalizacja numerów KNR (różne formaty)
  - [ ] Synonimowe opisy (np. "beton" = "mieszanka betonowa")
  - [ ] Scoring wieloczynnikowy (KNR + opis + jednostka)

- [ ] **Walidacja cenowa**
  - [ ] Benchmarki min/max dla kategorii
  - [ ] Flagi dla podejrzanych cen
  - [ ] Sugestie alternatywnych pozycji

### Metryki sukcesu
- Match rate: >80%
- Confidence score: >0.7 dla dopasowanych
- 0 pozycji z ceną domyślną 50 zł

---

## FAZA 2: PARSER PDF (następna)

### Problem
- Obecny parser PDF jest prosty
- Nie radzi sobie z różnymi formatami przedmiarów
- Gubią się dane (KNR, ilości, jednostki)

### Zadania
- [ ] **Analiza wzorców**
  - [ ] Zebrać 10+ różnych formatów przedmiarów
  - [ ] Zidentyfikować wspólne struktury
  - [ ] Obsłużyć edge cases

- [ ] **Ulepszony parser**
  - [ ] Regex patterns dla różnych formatów KNR
  - [ ] Parsowanie tabel (pdfplumber/camelot)
  - [ ] Wykrywanie działów i struktury

- [ ] **Fallback do OCR**
  - [ ] Skany słabej jakości → OCR → parsing
  - [ ] Tesseract/EasyOCR

### Metryki sukcesu
- Poprawne parsowanie 90%+ pozycji
- Zachowanie struktury działów
- Minimalne straty danych

---

## FAZA 3: GENERATOR ATH (doskonalenie)

### Problem
- Generator działa, ale:
  - Wszystko w jednym dziale
  - Brak rozdziału na branże
  - Uproszczone narzuty

### Zadania
- [ ] **Grupowanie w działy**
  - [ ] Automatyczne rozpoznawanie branży (budowlana, elektryczna, sanitarna)
  - [ ] Hierarchia: Element → Pozycja
  - [ ] Numeracja zgodna z przedmiarem

- [ ] **Pełne RMS**
  - [ ] Rozdzielenie R/M/S dla każdej pozycji
  - [ ] Materiały pomocnicze
  - [ ] Nakłady rzeczowe

- [ ] **Zgodność z Normą**
  - [ ] Testowanie na różnych wersjach Norma PRO
  - [ ] Obsługa wszystkich typów kosztorysów

### Metryki sukcesu
- Import bez błędów w Norma PRO
- Zachowanie struktury działów
- Poprawne sumy kontrolne

---

## FAZA 4: UCZENIE Z KOSZTORYSÓW

### Problem
- Każdy nowy kosztorys to wiedza
- Obecnie baza jest statyczna

### Zadania
- [ ] **Learning loop**
  - [ ] Parser kosztorysów gotowych (nie przedmiarów)
  - [ ] Ekstrakcja: KNR → cena → data
  - [ ] Aktualizacja bazy automatyczna

- [ ] **Wersjonowanie cen**
  - [ ] Historia cen dla każdej pozycji
  - [ ] Trend cenowy (rośnie/spada)
  - [ ] Prognoza cen

- [ ] **Feedback od użytkownika**
  - [ ] "Ta cena jest za niska/wysoka"
  - [ ] Korekta w bazie
  - [ ] Uczenie z korekt

---

## FAZA 5: SaaS (później)

- Landing page
- System płatności
- Panel klienta
- API dla firm

---

## 📊 METRYKI DO ŚLEDZENIA

| Metryka | Obecna | Cel | 
|---------|--------|-----|
| Pozycji KNR | 355 | 1000+ |
| Match rate | ~40% | >80% |
| Czas generowania | ~5s | <2s |
| Sukces parsowania PDF | ~60% | >90% |
| Import ATH do Normy | ✅ | ✅ |

---

## 📝 NOTATKI

### Do zrobienia natychmiast:
1. Zebrać więcej kosztorysów od Gabriela
2. Testować na realnych przedmiarach
3. Notować problemy i edge cases

### Pytania do Gabriela:
- Jakie formaty przedmiarów najczęściej spotykasz?
- Które katalogi KNR są najważniejsze?
- Czy masz dostęp do gotowych kosztorysów (nie przedmiarów)?

---

*Ostatnia aktualizacja: 2026-02-25*

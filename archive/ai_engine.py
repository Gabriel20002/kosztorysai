# -*- coding: utf-8 -*-
"""
kosztorysAI - AI Engine
Używa Claude/GPT do rozumienia przedmiarów jak człowiek
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
import pdfplumber
from io import BytesIO

# API - importuj tylko jeśli dostępne
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

# Klucze API
ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY')
OPENAI_KEY = os.environ.get('OPENAI_API_KEY')


class AIKosztorysEngine:
    """
    AI-powered engine do kosztorysowania.
    Rozumie przedmiary tak jak człowiek.
    """
    
    def __init__(self):
        self.anthropic_client = None
        self.openai_client = None
        
        if ANTHROPIC_KEY and anthropic:
            self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        if OPENAI_KEY and openai:
            self.openai_client = openai.OpenAI(api_key=OPENAI_KEY)
        
        # Baza KNR
        self._load_knr_base()
    
    def _load_knr_base(self):
        """Wczytaj bazę KNR jako kontekst dla AI"""
        self.knr_base = {}
        knr_dir = Path(__file__).parent.parent / "kosztorys" / "knowledge" / "knr"
        
        if knr_dir.exists():
            for file in knr_dir.glob("*.json"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for poz in data.get('pozycje', []):
                            key = poz.get('podstawa', '')
                            if key:
                                self.knr_base[key] = poz
                except:
                    pass
        
        print(f"[AI Engine] Załadowano {len(self.knr_base)} pozycji KNR")
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Wyciągnij tekst z PDF"""
        text_parts = []
        
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                text_parts.append(text)
                
                # Tabele
                tables = page.extract_tables() or []
                for table in tables:
                    for row in table:
                        if row:
                            text_parts.append(" | ".join(str(c or '') for c in row))
        
        return "\n".join(text_parts)
    
    def process_with_ai(self, content: str, content_type: str = "przedmiar") -> Dict:
        """
        Główna metoda - przetwarza treść przez AI.
        
        Args:
            content: Tekst z PDF, opis słowny, cokolwiek
            content_type: "przedmiar", "opis", "zapytanie"
        
        Returns:
            Kompletny kosztorys (dict)
        """
        
        # Przykładowe pozycje KNR jako kontekst
        knr_examples = self._get_knr_examples()
        
        # Prompt dla AI
        system_prompt = f"""Jesteś ekspertem kosztorysantem budowlanym z 20-letnim doświadczeniem.

TWOJE ZADANIE:
Przeanalizuj podany dokument/opis i wygeneruj profesjonalny kosztorys budowlany.

ZASADY:
1. Zidentyfikuj WSZYSTKIE pozycje robót (nawet jeśli nie mają numerów KNR)
2. Dla każdej pozycji określ:
   - Numer KNR (jeśli znasz) lub zostaw puste
   - Opis robót
   - Jednostkę miary (m2, m3, mb, szt, kpl, kg, t)
   - Ilość (oblicz jeśli podane wymiary, lub weź z dokumentu)
   - Cenę jednostkową (R+M+S) - oszacuj na podstawie wiedzy
3. Podziel na logiczne działy (Roboty ziemne, Fundamenty, Ściany, etc.)
4. Bądź dokładny - lepiej więcej pozycji niż mniej

PRZYKŁADOWE POZYCJE KNR Z MOJEJ BAZY (użyj jako referencję cen):
{knr_examples}

STAWKI REFERENCYJNE (2024-2025):
- Roboczogodzina: 35-45 zł
- Beton C25/30: 400-500 zł/m3
- Stal zbrojeniowa: 4500-5500 zł/t
- Cegła/bloczek: 8-15 zł/szt
- Izolacja termiczna: 30-80 zł/m2

ODPOWIEDZ W FORMACIE JSON:
{{
  "tytul": "Nazwa inwestycji",
  "dzialy": [
    {{
      "nazwa": "Nazwa działu",
      "pozycje": [
        {{
          "knr": "KNR X-XX XXXX-XX lub puste",
          "opis": "Pełny opis pozycji",
          "jednostka": "m2/m3/mb/szt/kpl/kg",
          "ilosc": 123.45,
          "cena_R": 10.00,
          "cena_M": 50.00,
          "cena_S": 5.00
        }}
      ]
    }}
  ],
  "uwagi": "Dodatkowe uwagi do kosztorysu"
}}

WAŻNE: Odpowiedz TYLKO JSON, bez dodatkowego tekstu."""

        user_prompt = f"""Przeanalizuj ten {content_type} i wygeneruj kosztorys:

---
{content[:15000]}
---

Wygeneruj kompletny kosztorys w formacie JSON."""

        # Wywołaj AI
        response = self._call_ai(system_prompt, user_prompt)
        
        if not response:
            return {"error": "Brak odpowiedzi z AI"}
        
        # Parsuj JSON z odpowiedzi
        kosztorys_data = self._parse_ai_response(response)
        
        if not kosztorys_data:
            return {"error": "Nie udało się sparsować odpowiedzi AI", "raw": response}
        
        # Konwertuj do standardowego formatu
        return self._convert_to_standard_format(kosztorys_data)
    
    def _call_ai(self, system: str, user: str) -> Optional[str]:
        """Wywołaj AI (Claude lub GPT)"""
        
        # Próbuj Claude
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8000,
                    system=system,
                    messages=[{"role": "user", "content": user}]
                )
                return response.content[0].text
            except Exception as e:
                print(f"[AI] Claude error: {e}")
        
        # Fallback do GPT
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    max_tokens=8000
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[AI] GPT error: {e}")
        
        return None
    
    def _get_knr_examples(self) -> str:
        """Pobierz przykłady KNR jako kontekst"""
        examples = []
        
        # Wybierz reprezentatywne pozycje
        sample_keys = list(self.knr_base.keys())[:30]
        
        for key in sample_keys:
            poz = self.knr_base[key]
            examples.append(
                f"- {key}: {poz.get('opis', '')[:80]}... "
                f"[{poz.get('jednostka', 'm2')}] "
                f"R={poz.get('cena_R', 0):.2f} M={poz.get('cena_M', 0):.2f} S={poz.get('cena_S', 0):.2f}"
            )
        
        return "\n".join(examples)
    
    def _parse_ai_response(self, response: str) -> Optional[Dict]:
        """Parsuj JSON z odpowiedzi AI"""
        
        # Wyczyść odpowiedź
        response = response.strip()
        
        # Usuń markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Spróbuj znaleźć JSON w tekście
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        
        return None
    
    def _convert_to_standard_format(self, ai_data: Dict, vat_rate: int = 8, kp_rate: float = 68.0, zysk_rate: float = 10.0) -> Dict:
        """Konwertuj odpowiedź AI do standardowego formatu kosztorysu"""
        
        positions = []
        lp = 0
        
        for dzial in ai_data.get('dzialy', []):
            for poz in dzial.get('pozycje', []):
                lp += 1
                
                cena_R = float(poz.get('cena_R', 0) or 0)
                cena_M = float(poz.get('cena_M', 0) or 0)
                cena_S = float(poz.get('cena_S', 0) or 0)
                ilosc = float(poz.get('ilosc', 1) or 1)
                
                cena_jedn = cena_R + cena_M + cena_S
                wartosc = ilosc * cena_jedn
                
                positions.append({
                    'lp': lp,
                    'knr': poz.get('knr', ''),
                    'description': poz.get('opis', 'Pozycja kosztorysowa'),
                    'unit': poz.get('jednostka', 'm2'),
                    'quantity': round(ilosc, 3),
                    'price_unit': round(cena_jedn, 2),
                    'price_R': round(cena_R, 2),
                    'price_M': round(cena_M, 2),
                    'price_S': round(cena_S, 2),
                    'value_netto': round(wartosc, 2),
                    'dzial': dzial.get('nazwa', 'Roboty budowlane'),
                    'source': 'ai'
                })
        
        # Obliczenia
        suma_R = sum(p['quantity'] * p['price_R'] for p in positions)
        suma_M = sum(p['quantity'] * p['price_M'] for p in positions)
        suma_S = sum(p['quantity'] * p['price_S'] for p in positions)
        razem_bezp = suma_R + suma_M + suma_S
        
        kp = (suma_R + suma_S) * (kp_rate / 100)
        zysk = (suma_R + suma_S + kp) * (zysk_rate / 100)
        netto = razem_bezp + kp + zysk
        vat = netto * (vat_rate / 100)
        brutto = netto + vat
        
        return {
            'meta': {
                'title': ai_data.get('tytul', 'Kosztorys'),
                'type': 'Kosztorys ofertowy (AI)',
                'generated_by': 'kosztorysAI + Claude/GPT',
                'status': 'PROJEKT - wymaga weryfikacji'
            },
            'investment': {
                'description': ai_data.get('tytul', ''),
                'investor': '',
                'location': ''
            },
            'rates': {
                'stawka_rg': 35.0,
                'koszty_posrednie_pct': kp_rate,
                'zysk_pct': zysk_rate,
                'vat_pct': vat_rate
            },
            'positions': positions,
            'summary': {
                'suma_R': round(suma_R, 2),
                'suma_M': round(suma_M, 2),
                'suma_S': round(suma_S, 2),
                'razem_bezposrednie': round(razem_bezp, 2),
                'koszty_posrednie': round(kp, 2),
                'zysk': round(zysk, 2),
                'total_netto': round(netto, 2),
                'vat': round(vat, 2),
                'total_brutto': round(brutto, 2),
                'positions_count': len(positions)
            },
            'uwagi': ai_data.get('uwagi', '')
        }
    
    def process_pdf(self, pdf_bytes: bytes, vat_rate: int = 8, kp_rate: float = 68.0, zysk_rate: float = 10.0) -> Dict:
        """Przetwórz PDF przez AI"""
        
        # Wyciągnij tekst
        text = self.extract_text_from_pdf(pdf_bytes)
        
        if len(text) < 50:
            return {"error": "PDF jest pusty lub nie można wyciągnąć tekstu"}
        
        # Przetwórz przez AI
        result = self.process_with_ai(text, "przedmiar")
        
        # Zastosuj stawki
        if 'positions' in result:
            result = self._convert_to_standard_format(
                {'tytul': result['meta']['title'], 'dzialy': [{'nazwa': 'Roboty', 'pozycje': [
                    {'knr': p['knr'], 'opis': p['description'], 'jednostka': p['unit'], 
                     'ilosc': p['quantity'], 'cena_R': p['price_R'], 'cena_M': p['price_M'], 'cena_S': p['price_S']}
                    for p in result['positions']
                ]}]},
                vat_rate, kp_rate, zysk_rate
            )
        
        return result
    
    def process_description(self, description: str, vat_rate: int = 8, kp_rate: float = 68.0, zysk_rate: float = 10.0) -> Dict:
        """Przetwórz opis słowny przez AI"""
        
        result = self.process_with_ai(description, "opis inwestycji")
        
        if 'dzialy' in result:
            result = self._convert_to_standard_format(result, vat_rate, kp_rate, zysk_rate)
        
        return result


# Singleton
_engine = None

def get_ai_engine() -> AIKosztorysEngine:
    global _engine
    if _engine is None:
        _engine = AIKosztorysEngine()
    return _engine


# Test
if __name__ == "__main__":
    engine = get_ai_engine()
    
    # Test z opisem
    result = engine.process_description(
        "Fundament pod dom jednorodzinny 10x12m. Ławy fundamentowe 40x30cm, "
        "beton C25/30, zbrojenie stal A-IIIN. Izolacja pozioma 2x papa."
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

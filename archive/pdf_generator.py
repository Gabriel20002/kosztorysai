# -*- coding: utf-8 -*-
"""
Generator PDF kosztorysów - format Norma PRO
Wersja: 1.0
"""

from fpdf import FPDF
from datetime import datetime
import json
import os
import re

class KosztorysPDF(FPDF):
    """PDF kosztorysu w formacie Norma PRO"""
    
    def __init__(self, dane_tytulowe=None):
        super().__init__()
        self.dane = dane_tytulowe or {}
        self.set_auto_page_break(auto=True, margin=20)
        
        # Próba załadowania czcionki z polskimi znakami
        font_path = r"C:\Windows\Fonts\arial.ttf"
        if os.path.exists(font_path):
            self.add_font("Arial", "", font_path, uni=True)
            self.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf", uni=True)
            self.font_name = "Arial"
        else:
            self.font_name = "Helvetica"
    
    def header(self):
        """Nagłówek na każdej stronie (poza tytułową)"""
        if self.page_no() > 1:
            self.set_font(self.font_name, '', 8)
            self.set_y(5)
            self.cell(0, 5, "Kosztorys", 0, 1, 'L')
    
    def footer(self):
        """Stopka z numerem strony"""
        self.set_y(-15)
        self.set_font(self.font_name, '', 8)
        self.cell(0, 5, f"- {self.page_no()} -", 0, 0, 'C')
        self.ln(4)
        self.cell(0, 5, f"kosztorysAI v1.0 | {datetime.now().strftime('%Y-%m-%d')}", 0, 0, 'C')
    
    def strona_tytulowa(self, dane):
        """Generuje stronę tytułową"""
        self.add_page()
        
        # Dane wykonawcy (góra)
        self.set_font(self.font_name, '', 10)
        wykonawca = dane.get('wykonawca', 'WYKONAWCA')
        adres_wyk = dane.get('adres_wykonawcy', '')
        self.multi_cell(0, 5, f"{wykonawca}\n{adres_wyk}")
        
        self.ln(15)
        
        # Tytuł
        self.set_font(self.font_name, 'B', 16)
        self.cell(0, 10, "KOSZTORYS OFERTOWY", 0, 1, 'C')
        
        branza = dane.get('branza', 'BUDOWLANA')
        self.set_font(self.font_name, 'B', 12)
        self.cell(0, 8, f"BRANŻA {branza.upper()}", 0, 1, 'C')
        
        self.ln(10)
        
        # Dane inwestycji
        self.set_font(self.font_name, 'B', 10)
        self.cell(50, 6, "NAZWA INWESTYCJI:", 0, 0)
        self.set_font(self.font_name, '', 10)
        nazwa = dane.get('nazwa_inwestycji', 'Inwestycja')
        self.multi_cell(0, 6, nazwa)
        
        self.set_font(self.font_name, 'B', 10)
        self.cell(50, 6, "ADRES INWESTYCJI:", 0, 0)
        self.set_font(self.font_name, '', 10)
        self.cell(0, 6, dane.get('adres_inwestycji', ''), 0, 1)
        
        self.ln(5)
        
        # Dane inwestora
        self.set_font(self.font_name, 'B', 10)
        self.cell(50, 6, "INWESTOR:", 0, 0)
        self.set_font(self.font_name, '', 10)
        self.cell(0, 6, dane.get('inwestor', ''), 0, 1)
        
        self.set_font(self.font_name, 'B', 10)
        self.cell(50, 6, "ADRES INWESTORA:", 0, 0)
        self.set_font(self.font_name, '', 10)
        self.cell(0, 6, dane.get('adres_inwestora', ''), 0, 1)
        
        self.ln(5)
        
        # Wykonawca (powtórzenie)
        self.set_font(self.font_name, 'B', 10)
        self.cell(50, 6, "WYKONAWCA:", 0, 0)
        self.set_font(self.font_name, '', 10)
        self.cell(0, 6, wykonawca, 0, 1)
        
        self.set_font(self.font_name, 'B', 10)
        self.cell(50, 6, "ADRES WYKONAWCY:", 0, 0)
        self.set_font(self.font_name, '', 10)
        self.cell(0, 6, adres_wyk, 0, 1)
        
        self.ln(5)
        
        # Data
        self.set_font(self.font_name, 'B', 10)
        self.cell(50, 6, "DATA OPRACOWANIA:", 0, 0)
        self.set_font(self.font_name, '', 10)
        self.cell(0, 6, dane.get('data', datetime.now().strftime('%m.%Y')), 0, 1)
        
        self.ln(15)
        
        # Wartości
        netto = dane.get('wartosc_netto', 0)
        vat_proc = dane.get('vat_procent', 23)
        vat = netto * vat_proc / 100
        brutto = netto + vat
        
        self.set_font(self.font_name, 'B', 11)
        self.cell(120, 7, "WARTOŚĆ KOSZTORYSOWA ROBÓT BEZ VAT:", 0, 0)
        self.set_font(self.font_name, '', 11)
        self.cell(0, 7, f"{netto:,.2f} zł".replace(",", " ").replace(".", ","), 0, 1, 'R')
        
        self.set_font(self.font_name, 'B', 11)
        self.cell(120, 7, f"PODATEK VAT ({vat_proc}%):", 0, 0)
        self.set_font(self.font_name, '', 11)
        self.cell(0, 7, f"{vat:,.2f} zł".replace(",", " ").replace(".", ","), 0, 1, 'R')
        
        self.ln(3)
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        
        self.set_font(self.font_name, 'B', 12)
        self.cell(120, 8, "OGÓŁEM WARTOŚĆ KOSZTORYSOWA ROBÓT:", 0, 0)
        self.cell(0, 8, f"{brutto:,.2f} zł".replace(",", " ").replace(".", ","), 0, 1, 'R')
        
        # Słownie
        self.ln(5)
        self.set_font(self.font_name, '', 10)
        slownie = self._kwota_slownie(brutto)
        self.multi_cell(0, 5, f"Słownie: {slownie}")
        
        # Podpisy
        self.ln(30)
        self.set_font(self.font_name, '', 10)
        self.cell(90, 6, "WYKONAWCA:", 0, 0, 'C')
        self.cell(0, 6, "INWESTOR:", 0, 1, 'C')
        self.ln(15)
        self.cell(90, 6, ".............................", 0, 0, 'C')
        self.cell(0, 6, ".............................", 0, 1, 'C')
    
    def tabela_pozycji(self, pozycje, naglowek_dzialu=None):
        """Generuje tabelę z pozycjami kosztorysu"""
        if naglowek_dzialu:
            self.set_font(self.font_name, 'B', 11)
            self.cell(0, 8, naglowek_dzialu, 0, 1)
            self.ln(2)
        
        # Nagłówki kolumn
        self.set_font(self.font_name, 'B', 8)
        self.set_fill_color(230, 230, 230)
        
        col_widths = [10, 25, 70, 12, 15, 20, 20, 18]  # Lp, Podst, Opis, JM, Ilość, Cena, Wartość, R/M/S
        headers = ['Lp.', 'Podstawa', 'Opis', 'J.m.', 'Ilość', 'Cena j.', 'Wartość', 'R/M/S']
        
        for i, (w, h) in enumerate(zip(col_widths, headers)):
            self.cell(w, 7, h, 1, 0, 'C', True)
        self.ln()
        
        # Pozycje
        self.set_font(self.font_name, '', 8)
        for poz in pozycje:
            # Sprawdź czy zmieści się na stronie
            if self.get_y() > 250:
                self.add_page()
                # Powtórz nagłówki
                self.set_font(self.font_name, 'B', 8)
                for i, (w, h) in enumerate(zip(col_widths, headers)):
                    self.cell(w, 7, h, 1, 0, 'C', True)
                self.ln()
                self.set_font(self.font_name, '', 8)
            
            lp = str(poz.get('lp', ''))
            podstawa = poz.get('podstawa', '')[:12]
            opis = poz.get('opis', '')[:45]
            jm = poz.get('jm', '')
            ilosc = poz.get('ilosc', 0)
            cena = poz.get('cena_jednostkowa', 0)
            wartosc = poz.get('wartosc', ilosc * cena)
            
            # R/M/S info
            r = poz.get('R', 0)
            m = poz.get('M', 0)
            s = poz.get('S', 0)
            rms = f"R:{r:.0f}" if r else ""
            
            self.cell(col_widths[0], 6, lp, 1, 0, 'C')
            self.cell(col_widths[1], 6, podstawa, 1, 0, 'L')
            self.cell(col_widths[2], 6, opis, 1, 0, 'L')
            self.cell(col_widths[3], 6, jm, 1, 0, 'C')
            self.cell(col_widths[4], 6, f"{ilosc:.3f}" if ilosc else "", 1, 0, 'R')
            self.cell(col_widths[5], 6, f"{cena:.2f}" if cena else "", 1, 0, 'R')
            self.cell(col_widths[6], 6, f"{wartosc:.2f}" if wartosc else "", 1, 0, 'R')
            self.cell(col_widths[7], 6, rms, 1, 0, 'C')
            self.ln()
    
    def podsumowanie(self, dane):
        """Podsumowanie kosztorysu"""
        self.ln(10)
        self.set_font(self.font_name, 'B', 10)
        
        # Linia
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
        # Wartości
        netto = dane.get('wartosc_netto', 0)
        vat_proc = dane.get('vat_procent', 23)
        vat = netto * vat_proc / 100
        brutto = netto + vat
        
        kp = dane.get('koszty_posrednie', 0)
        zysk = dane.get('zysk', 0)
        
        col1 = 130
        col2 = 60
        
        # Rozbicie R/M/S jeśli dostępne
        if 'suma_R' in dane:
            self.set_font(self.font_name, '', 9)
            self.cell(col1, 6, "Robocizna (R):", 0, 0, 'R')
            self.cell(col2, 6, f"{dane['suma_R']:,.2f} zł".replace(",", " "), 0, 1, 'R')
            self.cell(col1, 6, "Materiały (M):", 0, 0, 'R')
            self.cell(col2, 6, f"{dane['suma_M']:,.2f} zł".replace(",", " "), 0, 1, 'R')
            self.cell(col1, 6, "Sprzęt (S):", 0, 0, 'R')
            self.cell(col2, 6, f"{dane['suma_S']:,.2f} zł".replace(",", " "), 0, 1, 'R')
            self.ln(3)
        
        if kp:
            self.cell(col1, 6, "Koszty pośrednie (Kp):", 0, 0, 'R')
            self.cell(col2, 6, f"{kp:,.2f} zł".replace(",", " "), 0, 1, 'R')
        
        if zysk:
            self.cell(col1, 6, "Zysk (Z):", 0, 0, 'R')
            self.cell(col2, 6, f"{zysk:,.2f} zł".replace(",", " "), 0, 1, 'R')
        
        self.ln(3)
        self.set_font(self.font_name, 'B', 10)
        self.cell(col1, 7, "RAZEM NETTO:", 0, 0, 'R')
        self.cell(col2, 7, f"{netto:,.2f} zł".replace(",", " "), 0, 1, 'R')
        
        self.set_font(self.font_name, '', 10)
        self.cell(col1, 6, f"VAT ({vat_proc}%):", 0, 0, 'R')
        self.cell(col2, 6, f"{vat:,.2f} zł".replace(",", " "), 0, 1, 'R')
        
        self.ln(2)
        self.line(100, self.get_y(), 200, self.get_y())
        self.ln(3)
        
        self.set_font(self.font_name, 'B', 12)
        self.cell(col1, 8, "RAZEM BRUTTO:", 0, 0, 'R')
        self.cell(col2, 8, f"{brutto:,.2f} zł".replace(",", " "), 0, 1, 'R')
        
        # Słownie
        self.ln(5)
        self.set_font(self.font_name, '', 9)
        slownie = self._kwota_slownie(brutto)
        self.multi_cell(0, 5, f"Słownie: {slownie}")
    
    def _kwota_slownie(self, kwota):
        """Konwertuje kwotę na słownie (uproszczone)"""
        jednosci = ['', 'jeden', 'dwa', 'trzy', 'cztery', 'pięć', 'sześć', 'siedem', 'osiem', 'dziewięć']
        nastki = ['dziesięć', 'jedenaście', 'dwanaście', 'trzynaście', 'czternaście', 
                  'piętnaście', 'szesnaście', 'siedemnaście', 'osiemnaście', 'dziewiętnaście']
        dziesiatki = ['', 'dziesięć', 'dwadzieścia', 'trzydzieści', 'czterdzieści', 
                      'pięćdziesiąt', 'sześćdziesiąt', 'siedemdziesiąt', 'osiemdziesiąt', 'dziewięćdziesiąt']
        setki = ['', 'sto', 'dwieście', 'trzysta', 'czterysta', 
                 'pięćset', 'sześćset', 'siedemset', 'osiemset', 'dziewięćset']
        
        def _0_999(n):
            if n == 0:
                return ''
            s = setki[n // 100]
            n = n % 100
            if 10 <= n <= 19:
                return f"{s} {nastki[n-10]}".strip()
            d = dziesiatki[n // 10]
            j = jednosci[n % 10]
            return f"{s} {d} {j}".strip()
        
        zl = int(kwota)
        gr = int(round((kwota - zl) * 100))
        
        if zl == 0:
            return f"zero złotych {gr}/100"
        
        miliony = zl // 1000000
        tysiace = (zl % 1000000) // 1000
        reszta = zl % 1000
        
        wynik = []
        if miliony:
            if miliony == 1:
                wynik.append("jeden milion")
            elif 2 <= miliony <= 4:
                wynik.append(f"{_0_999(miliony)} miliony")
            else:
                wynik.append(f"{_0_999(miliony)} milionów")
        
        if tysiace:
            if tysiace == 1:
                wynik.append("jeden tysiąc")
            elif 2 <= tysiace % 10 <= 4 and not (12 <= tysiace % 100 <= 14):
                wynik.append(f"{_0_999(tysiace)} tysiące")
            else:
                wynik.append(f"{_0_999(tysiace)} tysięcy")
        
        if reszta:
            wynik.append(_0_999(reszta))
        
        zlotych = "złotych"
        if zl == 1:
            zlotych = "złoty"
        elif 2 <= zl % 10 <= 4 and not (12 <= zl % 100 <= 14):
            zlotych = "złote"
        
        return f"{' '.join(wynik)} {zlotych} {gr}/100"


def generuj_pdf_z_danych(dane_kosztorysu, output_path):
    """
    Generuje PDF z danych kosztorysu
    
    dane_kosztorysu = {
        'tytul': {...},       # dane strony tytułowej
        'pozycje': [...],     # lista pozycji
        'podsumowanie': {...} # wartości końcowe
    }
    """
    pdf = KosztorysPDF()
    
    # Strona tytułowa
    tytul = dane_kosztorysu.get('tytul', {})
    pdf.strona_tytulowa(tytul)
    
    # Pozycje
    pdf.add_page()
    pozycje = dane_kosztorysu.get('pozycje', [])
    
    # Grupuj po działach jeśli są
    dzialy = {}
    for poz in pozycje:
        dzial = poz.get('dzial', 'Kosztorys')
        if dzial not in dzialy:
            dzialy[dzial] = []
        dzialy[dzial].append(poz)
    
    for dzial, poz_list in dzialy.items():
        pdf.tabela_pozycji(poz_list, dzial if len(dzialy) > 1 else None)
    
    # Podsumowanie
    podsum = dane_kosztorysu.get('podsumowanie', tytul)
    pdf.podsumowanie(podsum)
    
    # Zapisz
    pdf.output(output_path)
    return output_path


def generuj_pdf_z_ath(ath_path, output_path=None):
    """Generuje PDF bezpośrednio z pliku ATH"""
    from ath_parser import parse_ath_file  # zakładam że masz parser
    
    dane = parse_ath_file(ath_path)
    
    if not output_path:
        output_path = ath_path.replace('.ath', '.pdf')
    
    return generuj_pdf_z_danych(dane, output_path)


# ============ TEST ============
if __name__ == "__main__":
    # Przykładowe dane testowe
    dane_testowe = {
        'tytul': {
            'wykonawca': 'KLONEX II DŁUGI GRZEGORZ',
            'adres_wykonawcy': 'ul. Kasztanowa 10, 49-318 Skarbimierz-Osiedle',
            'nazwa_inwestycji': 'Budowa placu betonowego przy budynku gospodarczym',
            'adres_inwestycji': 'Skarbimierz, dz. nr 123/4',
            'inwestor': 'Jan Kowalski',
            'adres_inwestora': 'ul. Przykładowa 1, 49-300 Brzeg',
            'branza': 'BUDOWLANA',
            'data': '07.2025',
            'wartosc_netto': 89_786.18,
            'vat_procent': 23,
        },
        'pozycje': [
            {'lp': 1, 'podstawa': 'KNR 2-31 0703-03', 'opis': 'Mechaniczne rozebranie nawierzchni z mieszanek mineralno-bitumicznych', 
             'jm': 'm2', 'ilosc': 150.0, 'cena_jednostkowa': 12.50, 'wartosc': 1875.00, 'R': 450, 'M': 0, 'S': 1425},
            {'lp': 2, 'podstawa': 'KNR 2-31 0113-06', 'opis': 'Podbudowa z kruszywa łamanego 0-31,5mm, warstwa dolna gr. 20cm',
             'jm': 'm2', 'ilosc': 200.0, 'cena_jednostkowa': 45.00, 'wartosc': 9000.00, 'R': 1800, 'M': 5400, 'S': 1800},
            {'lp': 3, 'podstawa': 'KNR 2-33 0403-01', 'opis': 'Nawierzchnia z betonu C25/30, grubość 15cm',
             'jm': 'm2', 'ilosc': 200.0, 'cena_jednostkowa': 185.00, 'wartosc': 37000.00, 'R': 7400, 'M': 25900, 'S': 3700},
            {'lp': 4, 'podstawa': 'KNR 2-31 0502-02', 'opis': 'Obrzeża betonowe 8x30cm na podsypce cementowo-piaskowej',
             'jm': 'm', 'ilosc': 60.0, 'cena_jednostkowa': 35.00, 'wartosc': 2100.00, 'R': 630, 'M': 1260, 'S': 210},
        ],
        'podsumowanie': {
            'suma_R': 10280.00,
            'suma_M': 32560.00,
            'suma_S': 7135.00,
            'koszty_posrednie': 14992.50,  # 30% od R+S
            'zysk': 4893.68,  # 10% od R+S+Kp
            'wartosc_netto': 89_786.18,
            'vat_procent': 23,
        }
    }
    
    output = "test_kosztorys.pdf"
    generuj_pdf_z_danych(dane_testowe, output)
    print(f"✅ Wygenerowano: {output}")

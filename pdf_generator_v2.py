# -*- coding: utf-8 -*-
"""
Generator PDF kosztorysów - format Norma PRO v3
Z ramkami i czytelną strukturą tabelaryczną
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import os


class KosztorysPDF(FPDF):
    """PDF kosztorysu w formacie Norma PRO"""
    
    # Szerokości kolumn (suma = 190mm dla A4 z marginesami 10mm)
    COL = [8, 20, 82, 12, 17, 17, 17, 17]  # Lp, Podst, Opis, jm, Nakł, Koszt j., R, M+S
    
    def __init__(self, dane_tytulowe=None):
        super().__init__()
        self.dane = dane_tytulowe or {}
        self.set_auto_page_break(auto=True, margin=25)
        self.alias_nb_pages()
        # Współczynnik narzutów do obliczania "Razem z narzutami" per pozycja
        # wartosc_z_narzutami = M + (R+S) * f_rs
        self._kp = 0.70
        self._z  = 0.12
        
        # Czcionka z polskimi znakami — szukaj w kolejności
        _FONT_CANDIDATES = [
            # Windows (natywnie)
            (r"C:\Windows\Fonts\arial.ttf",    r"C:\Windows\Fonts\arialbd.ttf",    "Arial"),
            # Windows przez WSL
            ("/mnt/c/Windows/Fonts/arial.ttf", "/mnt/c/Windows/Fonts/arialbd.ttf", "Arial"),
            # Linux DejaVu
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "DejaVuSans"),
        ]
        _ITALIC = {
            "Arial":      r"C:\Windows\Fonts\ariali.ttf",
            "DejaVuSans": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        }
        self.font_name = "Helvetica"
        for reg, bold, name in _FONT_CANDIDATES:
            if os.path.exists(reg):
                self.add_font(name, "", reg)
                if os.path.exists(bold):
                    self.add_font(name, "B", bold)
                italic = _ITALIC.get(name, "")
                if italic and os.path.exists(italic):
                    self.add_font(name, "I", italic)
                self.font_name = name
                break
        
        self.tytul_kosztorysu = ""
    
    def header(self):
        """Nagłówek na każdej stronie (poza tytułową)"""
        if self.page_no() > 1:
            self.set_font(self.font_name, 'B', 9)
            self.set_y(8)
            self.cell(0, 4, "Kosztorys", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            self.ln(2)
            self._naglowki_tabeli()
    
    def footer(self):
        """Stopka z numerem strony"""
        self.set_y(-15)
        self.set_font(self.font_name, '', 8)
        self.cell(0, 4, f"- {self.page_no()} -", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font(self.font_name, '', 7)
        self.cell(0, 4, f"kosztorysAI | Norma PRO", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    def _naglowki_tabeli(self):
        """Nagłówki kolumn tabeli pozycji z ramkami"""
        self.set_font(self.font_name, 'B', 7)
        self.set_fill_color(220, 220, 220)
        
        col = self.COL
        h = 8
        
        self.cell(col[0], h, "Lp.", 1, align='C', fill=True)
        self.cell(col[1], h, "Podstawa", 1, align='C', fill=True)
        self.cell(col[2], h, "Opis", 1, align='C', fill=True)
        self.cell(col[3], h, "j.m.", 1, align='C', fill=True)
        self.cell(col[4], h, "Nakłady", 1, align='C', fill=True)
        self.cell(col[5], h, "Koszt\njedn.", 1, align='C', fill=True)
        self.cell(col[6], h, "R", 1, align='C', fill=True)
        self.cell(col[7], h, "M    S", 1, align='C', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    def strona_tytulowa(self, dane):
        """Generuje stronę tytułową"""
        self.add_page()
        
        # Nagłówek wykonawcy
        self.set_font(self.font_name, 'B', 11)
        wykonawca = dane.get('wykonawca', 'WYKONAWCA')
        adres_wyk = dane.get('adres_wykonawcy', '')
        self.cell(0, 5, f'"{wykonawca}"  {adres_wyk}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(12)
        
        # Tytuł
        self.set_font(self.font_name, 'B', 16)
        self.cell(0, 8, "KOSZTORYS OFERTOWY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        self.ln(8)
        
        # Dane inwestycji
        def wiersz(etykieta, wartosc):
            self.set_font(self.font_name, 'B', 10)
            self.cell(55, 6, etykieta, new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_font(self.font_name, '', 10)
            self.multi_cell(130, 6, str(wartosc) if wartosc else '')
        
        wiersz("NAZWA INWESTYCJI :", dane.get('nazwa_inwestycji', ''))
        self.ln(2)
        wiersz("ADRES INWESTYCJI :", dane.get('adres_inwestycji', ''))
        self.ln(2)
        wiersz("INWESTOR :", dane.get('inwestor', ''))
        wiersz("ADRES INWESTORA :", dane.get('adres_inwestora', ''))
        self.ln(2)
        wiersz("WYKONAWCA ROBÓT :", wykonawca)
        wiersz("ADRES WYKONAWCY :", adres_wyk)
        self.ln(2)
        wiersz("BRANŻA :", dane.get('branza', 'budowlana'))
        wiersz("SPORZĄDZIŁ :", dane.get('sporzadzil', ''))
        wiersz("DATA OPRACOWANIA :", dane.get('data', datetime.now().strftime('%m.%Y')))
        
        # Stawka
        stawka = dane.get('stawka_rg', 35.00)
        self.ln(2)
        wiersz("Stawka roboczogodziny :", f"{stawka:.2f} zł")
        
        self.ln(8)
        
        # NARZUTY
        self.set_font(self.font_name, 'B', 10)
        self.cell(0, 6, "NARZUTY", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        kp_proc = dane.get('kp_procent', 70)
        z_proc = dane.get('z_procent', 12)
        vat_proc = dane.get('vat_procent', 23)
        
        self.set_font(self.font_name, '', 10)
        self.cell(100, 5, f"Koszty pośrednie [Kp]", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(0, 5, f"{kp_proc:.1f}% R+S", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(100, 5, f"Zysk [Z]", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(0, 5, f"{z_proc:.1f}% (R+Kp(R)+S+Kp(S))", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(100, 5, f"VAT [V]", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(0, 5, f"{vat_proc:.1f}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(10)
        
        # Wartości
        netto = dane.get('wartosc_netto', 0)
        vat = netto * vat_proc / 100
        brutto = netto + vat
        
        self.set_font(self.font_name, '', 11)
        self.cell(110, 7, "Wartość kosztorysowa robót bez podatku VAT :", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font(self.font_name, 'B', 11)
        self.cell(0, 7, self._fmt_kwota(netto), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        self.set_font(self.font_name, '', 11)
        self.cell(110, 7, "Podatek VAT :", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(0, 7, self._fmt_kwota(vat), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        self.set_font(self.font_name, 'B', 11)
        self.cell(110, 7, "Ogółem wartość kosztorysowa robót :", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(0, 7, self._fmt_kwota(brutto), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        # Słownie
        self.ln(3)
        self.set_font(self.font_name, '', 10)
        slownie = self._kwota_slownie(brutto)
        self.multi_cell(0, 5, f"Słownie: {slownie}")
        
        # Podpisy
        self.ln(20)
        self.set_font(self.font_name, 'B', 10)
        self.cell(90, 6, "WYKONAWCA :", align='C')
        self.cell(0, 6, "INWESTOR :", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Stopka
        self.ln(20)
        self.set_font(self.font_name, '', 8)
        self.cell(0, 4, "Dokument opracowany przy pomocy programu kosztorysAI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    def _fmt_kwota(self, val):
        """Formatuje kwotę: 1 234,56 zł"""
        return f"{val:,.2f} zł".replace(",", " ").replace(".", ",")
    
    def _fmt_num(self, val, decimals=2):
        """Formatuje liczbę"""
        if val == 0:
            return ""
        fmt = f"{{:,.{decimals}f}}"
        return fmt.format(val).replace(",", " ").replace(".", ",")
    
    def dzial(self, nazwa, numer=None):
        """Nagłówek działu z ramką"""
        if self.get_y() > 240:
            self.add_page()
        
        self.ln(2)
        self.set_font(self.font_name, 'B', 9)
        self.set_fill_color(240, 240, 240)
        
        tekst = f"{numer}  {nazwa}" if numer else nazwa
        self.cell(sum(self.COL), 7, tekst, 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    
    def pozycja(self, poz, lp):
        """Renderuje pozycję w stylu Norma PRO z ramkami"""
        col = self.COL
        
        # Sprawdź czy zmieści się
        if self.get_y() > 220:
            self.add_page()
        
        podstawa = poz.get('podstawa', '')[:18]
        opis = poz.get('opis', '')
        jm = poz.get('jm', '')
        ilosc = poz.get('ilosc', 0)
        
        r_val = poz.get('R', 0)
        m_val = poz.get('M', 0)
        s_val = poz.get('S', 0)
        razem = r_val + m_val + s_val
        koszt_j = razem / ilosc if ilosc else 0
        
        # === WIERSZ GŁÓWNY POZYCJI ===
        self.set_font(self.font_name, '', 8)
        y_start = self.get_y()
        
        # Lp
        self.cell(col[0], 6, str(lp), 'LTR', align='C')
        x_po_lp = self.get_x()
        
        # Podstawa
        self.set_font(self.font_name, 'B', 7)
        self.cell(col[1], 6, podstawa, 'LTR', align='L')
        x_po_podst = self.get_x()
        
        # Opis (multi-line w ramce)
        self.set_font(self.font_name, '', 7)
        x_opis = self.get_x()
        
        # Oblicz wysokość opisu
        self.set_xy(x_opis, y_start)
        opis_lines = self._wrap_text(opis, col[2] - 2)
        opis_h = max(6, len(opis_lines) * 3.5)
        
        # Narysuj ramkę opisu
        self.rect(x_opis, y_start, col[2], opis_h)
        self.set_xy(x_opis + 1, y_start + 1)
        for line in opis_lines[:5]:  # max 5 linii
            self.cell(col[2] - 2, 3.5, line, new_x=XPos.LEFT, new_y=YPos.NEXT)
            self.set_x(x_opis + 1)
        
        # jm, Nakłady, Koszt j., R, M+S - w jednym wierszu obok opisu
        x_jm = x_opis + col[2]
        self.set_xy(x_jm, y_start)
        self.cell(col[3], opis_h, jm, 1, align='C')
        self.cell(col[4], opis_h, "", 1, align='R')  # nakłady - puste
        self.cell(col[5], opis_h, self._fmt_num(koszt_j), 1, align='R')
        self.cell(col[6], opis_h, self._fmt_num(r_val / ilosc if ilosc else 0), 1, align='R')
        self.cell(col[7], opis_h, self._fmt_num((m_val + s_val) / ilosc if ilosc else 0), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        # Dopełnij ramki Lp i Podstawa
        self.rect(10, y_start, col[0], opis_h)
        self.rect(10 + col[0], y_start, col[1], opis_h)
        
        # === WIERSZ OBMIARU ===
        self.set_font(self.font_name, '', 7)
        y_obm = self.get_y()
        self.cell(col[0] + col[1], 5, "", 'LR')
        self.cell(col[2], 5, f"obmiar = {self._fmt_num(ilosc, 3)} {jm}", 'LR')
        self.cell(col[3] + col[4] + col[5] + col[6] + col[7], 5, "", 'LR', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # === NAKŁADY R, M, S ===
        self._render_naklady(poz, col)
        
        # === RAZEM KOSZTY BEZPOŚREDNIE ===
        self.set_font(self.font_name, '', 7)
        self.cell(col[0] + col[1], 5, "", 'LR')
        self.cell(col[2] - 40, 5, "Razem koszty bezpośrednie", 'L')
        self.cell(40, 5, self._fmt_num(razem), 'R', align='R')
        self.cell(col[3], 5, "", 1)
        self.cell(col[4], 5, "", 1)
        self.cell(col[5], 5, "", 1)
        self.cell(col[6], 5, self._fmt_num(r_val), 1, align='R')
        self.cell(col[7], 5, self._fmt_num(m_val + s_val), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        # === RAZEM Z NARZUTAMI ===
        # Narzuty proporcjonalne: M bez zmian, (R+S) × (1 + Kp + Z×(1+Kp))
        f_rs = 1 + self._kp + self._z * (1 + self._kp)
        wartosc = m_val + (r_val + s_val) * f_rs
        cena_j = wartosc / ilosc if ilosc else 0
        
        self.set_font(self.font_name, 'B', 7)
        self.cell(col[0] + col[1], 5, "", 'LR')
        self.cell(col[2] - 40, 5, "Razem z narzutami", 'L')
        self.cell(40, 5, self._fmt_num(wartosc), 'R', align='R')
        self.cell(col[3], 5, "", 1)
        self.cell(col[4], 5, "", 1)
        self.cell(col[5], 5, self._fmt_num(cena_j), 1, align='R')
        self.cell(col[6], 5, "", 1)
        self.cell(col[7], 5, "", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # === CENA JEDNOSTKOWA ===
        r_j = r_val / ilosc if ilosc else 0
        ms_j = (m_val + s_val) / ilosc if ilosc else 0
        
        self.set_font(self.font_name, '', 7)
        self.cell(col[0] + col[1], 5, "", 'LBR')
        self.cell(col[2] - 40, 5, "Cena jednostkowa", 'LB')
        self.cell(40, 5, self._fmt_num(cena_j), 'BR', align='R')
        self.cell(col[3], 5, "", 1)
        self.cell(col[4], 5, "", 1)
        self.cell(col[5], 5, "", 1)
        self.cell(col[6], 5, self._fmt_num(r_j), 1, align='R')
        self.cell(col[7], 5, self._fmt_num(ms_j), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        self.ln(1)
    
    def _render_naklady(self, poz, col):
        """Renderuje nakłady R, M, S"""
        naklady = poz.get('naklady', [])
        ilosc = poz.get('ilosc', 1) or 1
        stawka_rg = poz.get('stawka_rg', 35.0)
        
        # -- R --
        r_naklady = [n for n in naklady if n.get('typ') == 'R']
        if r_naklady or poz.get('R', 0) > 0:
            self.set_font(self.font_name, 'B', 7)
            self.cell(col[0] + col[1], 4, "", 'LR')
            self.cell(col[2] + col[3] + col[4] + col[5] + col[6] + col[7], 4, "-- R --", 'LR', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            self.set_font(self.font_name, '', 6)
            for n in r_naklady:
                nazwa = n.get('nazwa', 'robocizna')[:35]
                wartosc = n.get('wartosc', 0)
                jedn = n.get('jednostka', 'r-g')
                cena = n.get('cena', stawka_rg)
                
                self.cell(col[0] + col[1], 4, "", 'LR')
                self.cell(5, 4, "*", 'L')
                self.cell(col[2] - 5 - 30, 4, nazwa, '')
                self.cell(10, 4, jedn, '', align='C')
                self.cell(20, 4, self._fmt_num(wartosc, 4), 'R', align='R')
                self.cell(col[3] + col[4] + col[5] + col[6] + col[7], 4, self._fmt_num(wartosc * cena if wartosc < 100 else poz.get('R', 0)), 'LR', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        # -- M --
        m_naklady = [n for n in naklady if n.get('typ') == 'M']
        if m_naklady or poz.get('M', 0) > 0:
            self.set_font(self.font_name, 'B', 7)
            self.cell(col[0] + col[1], 4, "", 'LR')
            self.cell(col[2] + col[3] + col[4] + col[5] + col[6] + col[7], 4, "-- M --", 'LR', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            self.set_font(self.font_name, '', 6)
            for n in m_naklady:
                nazwa = n.get('nazwa', 'materiał')[:35]
                wartosc = n.get('wartosc', 0)
                jedn = n.get('jednostka', 'szt')
                cena = n.get('cena', 0)
                
                self.cell(col[0] + col[1], 4, "", 'LR')
                self.cell(5, 4, "*", 'L')
                self.cell(col[2] - 5 - 30, 4, nazwa, '')
                self.cell(10, 4, jedn, '', align='C')
                self.cell(20, 4, self._fmt_num(wartosc, 4), 'R', align='R')
                self.cell(col[3] + col[4] + col[5] + col[6] + col[7], 4, self._fmt_num(wartosc * cena if cena else poz.get('M', 0)), 'LR', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        # -- S --
        s_naklady = [n for n in naklady if n.get('typ') == 'S']
        if s_naklady or poz.get('S', 0) > 0:
            self.set_font(self.font_name, 'B', 7)
            self.cell(col[0] + col[1], 4, "", 'LR')
            self.cell(col[2] + col[3] + col[4] + col[5] + col[6] + col[7], 4, "-- S --", 'LR', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            self.set_font(self.font_name, '', 6)
            for n in s_naklady:
                nazwa = n.get('nazwa', 'sprzęt')[:35]
                wartosc = n.get('wartosc', 0)
                jedn = n.get('jednostka', 'm-g')
                cena = n.get('cena', 0)
                
                self.cell(col[0] + col[1], 4, "", 'LR')
                self.cell(5, 4, "*", 'L')
                self.cell(col[2] - 5 - 30, 4, nazwa, '')
                self.cell(10, 4, jedn, '', align='C')
                self.cell(20, 4, self._fmt_num(wartosc, 4), 'R', align='R')
                self.cell(col[3] + col[4] + col[5] + col[6] + col[7], 4, self._fmt_num(wartosc * cena if cena else poz.get('S', 0)), 'LR', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    
    def _wrap_text(self, text, width):
        """Łamie tekst na linie o max szerokości"""
        words = text.split()
        lines = []
        current = ""
        
        for word in words:
            test = f"{current} {word}".strip()
            if self.get_string_width(test) < width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        
        if current:
            lines.append(current)
        
        return lines if lines else [""]
    
    def podsumowanie(self, dane, dzialy=None):
        """Strona podsumowania kosztorysu"""
        self.add_page()
        
        self.set_font(self.font_name, 'B', 12)
        self.cell(0, 8, "PODSUMOWANIE KOSZTORYSU", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)
        
        # Tabela działów
        if dzialy:
            self.set_font(self.font_name, 'B', 8)
            self.set_fill_color(220, 220, 220)
            self.cell(10, 7, "Lp.", 1, align='C', fill=True)
            self.cell(70, 7, "Nazwa", 1, align='C', fill=True)
            self.cell(28, 7, "R+M+S", 1, align='C', fill=True)
            self.cell(28, 7, "R", 1, align='C', fill=True)
            self.cell(27, 7, "M", 1, align='C', fill=True)
            self.cell(27, 7, "S", 1, align='C', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            self.set_font(self.font_name, '', 8)
            suma_r, suma_m, suma_s = 0, 0, 0
            
            for i, d in enumerate(dzialy, 1):
                r = d.get('R', 0)
                m = d.get('M', 0)
                s = d.get('S', 0)
                razem = r + m + s
                suma_r += r
                suma_m += m
                suma_s += s
                
                self.cell(10, 6, str(i), 1, align='C')
                self.cell(70, 6, d.get('nazwa', '')[:40], 1)
                self.cell(28, 6, self._fmt_num(razem), 1, align='R')
                self.cell(28, 6, self._fmt_num(r), 1, align='R')
                self.cell(27, 6, self._fmt_num(m), 1, align='R')
                self.cell(27, 6, self._fmt_num(s), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            
            # Suma
            suma_bezp = suma_r + suma_m + suma_s
            self.set_font(self.font_name, 'B', 8)
            self.cell(10, 7, "", 1)
            self.cell(70, 7, "RAZEM koszty bezpośrednie", 1)
            self.cell(28, 7, self._fmt_num(suma_bezp), 1, align='R')
            self.cell(28, 7, self._fmt_num(suma_r), 1, align='R')
            self.cell(27, 7, self._fmt_num(suma_m), 1, align='R')
            self.cell(27, 7, self._fmt_num(suma_s), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            
            self.ln(5)
        
        # Kalkulacja końcowa
        suma_r = dane.get('suma_R', 0)
        suma_m = dane.get('suma_M', 0)
        suma_s = dane.get('suma_S', 0)
        kp = dane.get('koszty_posrednie', 0)
        zysk = dane.get('zysk', 0)
        netto = dane.get('wartosc_netto', 0)
        vat = dane.get('vat', 0)
        brutto = dane.get('wartosc_brutto', netto + vat)
        
        kp_proc = dane.get('kp_procent', 70)
        z_proc = dane.get('z_procent', 12)
        vat_proc = dane.get('vat_procent', 23)
        
        self.ln(3)
        self.set_font(self.font_name, '', 10)
        
        # Tabela kalkulacji
        self.set_fill_color(245, 245, 245)
        
        def row(label, value, bold=False, fill=False):
            self.set_font(self.font_name, 'B' if bold else '', 10)
            self.cell(120, 7, label, 1, fill=fill)
            self.cell(70, 7, self._fmt_kwota(value) if value else "", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R', fill=fill)
        
        row("Robocizna (R)", suma_r)
        row("Materiały (M)", suma_m)
        row("Sprzęt (S)", suma_s)
        row("Razem koszty bezpośrednie (R+M+S)", suma_r + suma_m + suma_s, bold=True, fill=True)
        self.ln(2)
        row(f"Koszty pośrednie [Kp] {kp_proc}% od (R+S)", kp)
        row(f"Zysk [Z] {z_proc}% od (R+S+Kp)", zysk)
        self.ln(2)
        self.set_fill_color(220, 220, 220)
        row("RAZEM NETTO", netto, bold=True, fill=True)
        row(f"VAT [{vat_proc}%]", vat)
        self.set_fill_color(200, 200, 200)
        row("OGÓŁEM BRUTTO", brutto, bold=True, fill=True)
        
        # Słownie
        self.ln(5)
        self.set_font(self.font_name, '', 10)
        slownie = self._kwota_slownie(brutto)
        self.multi_cell(0, 5, f"Słownie: {slownie}")
    
    def _kwota_slownie(self, kwota):
        """Konwertuje kwotę na słownie"""
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


def generuj_pdf(dane_kosztorysu, output_path):
    """Generuje PDF kosztorysu"""
    pdf = KosztorysPDF()

    tytul = dane_kosztorysu.get('tytul', {})
    podsum = dane_kosztorysu.get('podsumowanie', {})
    # Przekaż parametry narzutów do obliczeń per-pozycja
    pdf._kp = podsum.get('kp_procent', tytul.get('kp_procent', 70)) / 100
    pdf._z  = podsum.get('z_procent',  tytul.get('z_procent',  12)) / 100

    pdf.tytul_kosztorysu = tytul.get('nazwa_inwestycji', 'Kosztorys')[:50]
    pdf.strona_tytulowa(tytul)
    
    pdf.add_page()
    dzialy = dane_kosztorysu.get('dzialy', [])
    
    lp = 1
    dzialy_podsumowanie = []
    
    for i, dzial in enumerate(dzialy, 1):
        nazwa_dzialu = dzial.get('nazwa', f'Dział {i}')
        pdf.dzial(nazwa_dzialu, i)
        
        suma_r, suma_m, suma_s = 0, 0, 0
        
        for poz in dzial.get('pozycje', []):
            pdf.pozycja(poz, lp)
            suma_r += poz.get('R', 0)
            suma_m += poz.get('M', 0)
            suma_s += poz.get('S', 0)
            lp += 1
        
        dzialy_podsumowanie.append({
            'nazwa': nazwa_dzialu,
            'R': suma_r,
            'M': suma_m,
            'S': suma_s
        })
    
    podsum = dane_kosztorysu.get('podsumowanie', tytul)
    pdf.podsumowanie(podsum, dzialy_podsumowanie)
    
    pdf.output(output_path)
    return output_path

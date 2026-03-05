# -*- coding: utf-8 -*-
"""
kosztorysAI v3.0 — Profesjonalny generator kosztorysów
Upload PDF → Kosztorys PDF + ATH
"""

import streamlit as st
import json
import tempfile
import base64
from datetime import datetime
from pathlib import Path
from io import BytesIO
import sys

# Ścieżki
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent / "kosztorys"))

# ============================================
# KONFIGURACJA STRONY
# ============================================
st.set_page_config(
    page_title="kosztorysAI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CSS - ANIMACJE I STYLE
# ============================================
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

/* Animacja fade-in */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* Główny nagłówek */
.hero-section {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3d7ab8 100%);
    padding: 3rem 2rem;
    border-radius: 20px;
    text-align: center;
    color: white;
    margin-bottom: 2rem;
    animation: fadeIn 0.6s ease-out;
    box-shadow: 0 20px 60px rgba(30, 58, 95, 0.3);
}

.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.hero-subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
    font-weight: 400;
}

/* Karty metryk */
.metric-card {
    background: linear-gradient(145deg, #ffffff, #f5f7fa);
    padding: 1.5rem;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.8);
    animation: fadeIn 0.5s ease-out;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 0.25rem;
}

.metric-label {
    font-size: 0.9rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Upload area */
.upload-area {
    border: 3px dashed #cbd5e1;
    border-radius: 20px;
    padding: 3rem;
    text-align: center;
    background: linear-gradient(145deg, #f8fafc, #f1f5f9);
    transition: all 0.3s ease;
    animation: fadeIn 0.6s ease-out;
}

.upload-area:hover {
    border-color: #3d7ab8;
    background: linear-gradient(145deg, #f1f5f9, #e2e8f0);
}

/* Przyciski */
.stButton > button {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    color: white;
    border: none;
    padding: 0.75rem 2rem;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(30, 58, 95, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(30, 58, 95, 0.4);
}

/* Tabela pozycji */
.position-table {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    animation: fadeIn 0.6s ease-out;
}

/* Progress bar animowany */
.progress-bar {
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #1e3a5f, #3d7ab8, #1e3a5f);
    background-size: 200% 100%;
    animation: shimmer 2s infinite linear;
    border-radius: 4px;
}

/* Sekcje */
.section-header {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1e3a5f;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #3d7ab8;
    animation: fadeIn 0.5s ease-out;
}

/* Success box */
.success-box {
    background: linear-gradient(145deg, #d1fae5, #a7f3d0);
    border-left: 4px solid #10b981;
    padding: 1rem 1.5rem;
    border-radius: 0 12px 12px 0;
    animation: fadeIn 0.5s ease-out;
}

/* Warning box */
.warning-box {
    background: linear-gradient(145deg, #fef3c7, #fde68a);
    border-left: 4px solid #f59e0b;
    padding: 1rem 1.5rem;
    border-radius: 0 12px 12px 0;
    animation: fadeIn 0.5s ease-out;
}

/* Download buttons */
.download-section {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-top: 1.5rem;
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem;
    color: #64748b;
    font-size: 0.85rem;
    border-top: 1px solid #e2e8f0;
    margin-top: 3rem;
}

/* Animacja ładowania */
.loading-spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #1e3a5f;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNKCJE POMOCNICZE
# ============================================

@st.cache_resource
def load_knr_base():
    """Wczytaj bazę KNR"""
    from engine_v2 import BazaKNR
    baza = BazaKNR()
    baza._load()
    return baza

@st.cache_resource
def get_generator():
    """Pobierz generator"""
    from engine_v2 import KosztorysGeneratorV2
    return KosztorysGeneratorV2()

def parse_pdf(pdf_bytes):
    """Parsuj PDF przedmiaru"""
    from pdf_parser import parse_przedmiar
    return parse_przedmiar(pdf_bytes)

def generate_pdf_report(kosztorys):
    """Generuj PDF z kosztorysem"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Font
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', 'C:/Windows/Fonts/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'C:/Windows/Fonts/DejaVuSans-Bold.ttf'))
        FONT = 'DejaVu'
        FONT_BOLD = 'DejaVu-Bold'
    except:
        FONT = 'Helvetica'
        FONT_BOLD = 'Helvetica-Bold'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitlePL', fontName=FONT_BOLD, fontSize=18, alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='BodyPL', fontName=FONT, fontSize=10, spaceAfter=6))
    styles.add(ParagraphStyle(name='RightPL', fontName=FONT_BOLD, fontSize=12, alignment=TA_RIGHT))
    
    story = []
    
    # Tytuł
    story.append(Paragraph("KOSZTORYS OFERTOWY", styles['TitlePL']))
    story.append(Paragraph(kosztorys['meta']['title'], styles['BodyPL']))
    story.append(Spacer(1, 0.5*cm))
    
    # Info
    story.append(Paragraph(f"Data: {datetime.now().strftime('%d.%m.%Y')}", styles['BodyPL']))
    story.append(Paragraph(f"Status: {kosztorys['meta']['status']}", styles['BodyPL']))
    story.append(Spacer(1, 1*cm))
    
    # Tabela pozycji
    data = [['Lp', 'KNR', 'Opis', 'Jm', 'Ilość', 'Cena', 'Wartość']]
    for p in kosztorys['positions']:
        data.append([
            str(p['lp']),
            p['knr'][:15] if p['knr'] else '-',
            p['description'][:35] + '...' if len(p['description']) > 35 else p['description'],
            p['unit'],
            f"{p['quantity']:.2f}",
            f"{p['price_unit']:.2f}",
            f"{p['value_netto']:.2f}"
        ])
    
    table = Table(data, colWidths=[1*cm, 2.5*cm, 6*cm, 1.2*cm, 1.5*cm, 2*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(table)
    story.append(Spacer(1, 1*cm))
    
    # Podsumowanie
    summary = kosztorys['summary']
    sum_data = [
        ['Razem netto:', f"{summary['total_netto']:,.2f} zł"],
        [f"VAT ({kosztorys['rates']['vat_pct']}%):", f"{summary['vat']:,.2f} zł"],
        ['BRUTTO:', f"{summary['total_brutto']:,.2f} zł"],
    ]
    sum_table = Table(sum_data, colWidths=[12*cm, 4*cm])
    sum_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.white),
    ]))
    story.append(sum_table)
    
    # Footer
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("Wygenerowano przez kosztorysAI", styles['BodyPL']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_ath_file(kosztorys):
    """Generuj plik ATH"""
    from output.ath_generator import ATH_Kosztorys, ATH_Element, ATH_Pozycja, ATHGenerator
    
    k = ATH_Kosztorys(
        nazwa=kosztorys['meta']['title'],
        inwestor=kosztorys['investment'].get('investor', ''),
        adres=kosztorys['investment'].get('location', ''),
        stawka_robocizny=kosztorys['rates'].get('stawka_rg', 35.0),
        koszty_posrednie=kosztorys['rates'].get('koszty_posrednie_pct', 68.0),
        zysk=kosztorys['rates'].get('zysk_pct', 10.0),
        vat=kosztorys['rates'].get('vat_pct', 23),
    )
    
    elem = ATH_Element(id=1, numer="1", nazwa="Roboty budowlane")
    
    for i, pos in enumerate(kosztorys['positions'], 1):
        knr_parts = (pos.get('knr') or '').split()
        katalog = ' '.join(knr_parts[:2]) if len(knr_parts) >= 2 else (pos.get('knr') or 'KALK')
        numer = knr_parts[2] if len(knr_parts) >= 3 else ''
        
        poz = ATH_Pozycja(
            id=i,
            katalog=katalog,
            numer=numer,
            opis=pos['description'],
            jednostka=pos['unit'],
            ilosc=pos['quantity'],
            cena_R=pos.get('price_R', 0),
            cena_M=pos.get('price_M', pos['price_unit']),
            cena_S=pos.get('price_S', 0),
        )
        elem.pozycje.append(poz)
    
    k.elementy.append(elem)
    
    gen = ATHGenerator(k)
    content = gen.generate()
    return content.encode('cp1250')

# ============================================
# GŁÓWNA APLIKACJA
# ============================================

def main():
    # Hero section
    st.markdown('''
    <div class="hero-section">
        <div class="hero-title">🏗️ kosztorysAI</div>
        <div class="hero-subtitle">Wgraj przedmiar PDF → Otrzymaj profesjonalny kosztorys</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Ładowanie zasobów
    try:
        generator = get_generator()
        baza = load_knr_base()
        stats = baza.get_stats()
    except Exception as e:
        st.error(f"Błąd ładowania systemu: {e}")
        return
    
    # Statystyki - animowane karty
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{stats["liczba_pozycji"]}</div>
            <div class="metric-label">Pozycji KNR</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown('''
        <div class="metric-card">
            <div class="metric-value">PDF + ATH</div>
            <div class="metric-label">Formaty eksportu</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown('''
        <div class="metric-card">
            <div class="metric-value">&lt; 10s</div>
            <div class="metric-label">Czas generowania</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Upload sekcja
    st.markdown('<div class="section-header">📄 Wgraj przedmiar</div>', unsafe_allow_html=True)
    
    col_upload, col_info = st.columns([2, 1])
    
    with col_upload:
        uploaded_file = st.file_uploader(
            "Wybierz plik PDF z przedmiarem robót",
            type=['pdf'],
            help="Akceptowane: PDF z przedmiarem w standardowym formacie kosztorysowym"
        )
    
    with col_info:
        st.markdown("""
        <div style="background: #f1f5f9; padding: 1rem; border-radius: 12px; margin-top: 1rem;">
            <p style="margin: 0; font-size: 0.9rem; color: #475569;">
                <strong>💡 Wskazówka:</strong><br>
                Najlepiej działają przedmiary z programów:<br>
                • Norma PRO<br>
                • WINBUD<br>
                • Zuzia
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Podgląd wgranego pliku
    if uploaded_file:
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #dbeafe, #bfdbfe); padding: 1rem; border-radius: 12px; margin: 1rem 0;">
            <p style="margin: 0; font-size: 1rem;">
                📎 <strong>Wgrany plik:</strong> {uploaded_file.name}<br>
                📏 <strong>Rozmiar:</strong> {uploaded_file.size / 1024:.1f} KB
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Ustawienia
    with st.expander("⚙️ Ustawienia kosztorysu", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            vat_rate = st.selectbox("Stawka VAT", [8, 23], format_func=lambda x: f"{x}%")
        with col2:
            kp_rate = st.slider("Koszty pośrednie (%)", 50, 90, 68)
        with col3:
            zysk_rate = st.slider("Zysk (%)", 5, 20, 10)
    
    # Przetwarzanie
    if uploaded_file is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Przycisk generowania
        generate_btn = st.button(
            "🚀 GENERUJ KOSZTORYS",
            type="primary",
            use_container_width=True
        )
        
        if not generate_btn:
            st.info("👆 Kliknij przycisk powyżej aby wygenerować kosztorys")
            st.stop()
        
        st.markdown('<div class="section-header">🔄 Przetwarzanie</div>', unsafe_allow_html=True)
        
        # Progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Krok 1: Parsowanie
            status_text.text("📖 Parsowanie PDF...")
            progress_bar.progress(20)
            
            przedmiar = parse_pdf(uploaded_file.getvalue())
            
            if not przedmiar.get('positions'):
                st.error("❌ Nie znaleziono pozycji w pliku PDF")
                return
            
            progress_bar.progress(40)
            status_text.text(f"✅ Znaleziono {len(przedmiar['positions'])} pozycji")
            
            # Krok 2: Generowanie kosztorysu
            status_text.text("🧮 Kalkulacja kosztorysu...")
            progress_bar.progress(60)
            
            kosztorys = generator.generate_from_przedmiar(
                przedmiar_positions=przedmiar['positions'],
                metadata=przedmiar.get('metadata', {}),
                vat_rate=vat_rate,
                kp_rate=kp_rate,
                zysk_rate=zysk_rate
            )
            
            progress_bar.progress(80)
            status_text.text("📄 Generowanie dokumentów...")
            
            # Krok 3: Generowanie plików
            pdf_bytes = generate_pdf_report(kosztorys)
            ath_bytes = generate_ath_file(kosztorys)
            
            progress_bar.progress(100)
            status_text.text("✅ Gotowe!")
            
            # Wyniki
            st.markdown('<div class="section-header">📊 Wynik kosztorysowania</div>', unsafe_allow_html=True)
            
            # Metryki wynikowe
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{kosztorys["summary"]["total_netto"]:,.0f} zł</div>
                    <div class="metric-label">Netto</div>
                </div>
                ''', unsafe_allow_html=True)
            with col2:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{kosztorys["summary"]["vat"]:,.0f} zł</div>
                    <div class="metric-label">VAT {vat_rate}%</div>
                </div>
                ''', unsafe_allow_html=True)
            with col3:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{kosztorys["summary"]["total_brutto"]:,.0f} zł</div>
                    <div class="metric-label">Brutto</div>
                </div>
                ''', unsafe_allow_html=True)
            with col4:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{kosztorys["summary"]["match_rate"]:.0f}%</div>
                    <div class="metric-label">Dopasowanie KNR</div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Szczegóły
            with st.expander("📈 Szczegóły kalkulacji", expanded=False):
                st.markdown(f"""
                | Składnik | Wartość |
                |----------|---------|
                | Robocizna (R) | {kosztorys['summary']['suma_R']:,.2f} zł |
                | Materiały (M) | {kosztorys['summary']['suma_M']:,.2f} zł |
                | Sprzęt (S) | {kosztorys['summary']['suma_S']:,.2f} zł |
                | **Razem bezpośrednie** | **{kosztorys['summary']['razem_bezposrednie']:,.2f} zł** |
                | Koszty pośrednie ({kp_rate}%) | {kosztorys['summary']['koszty_posrednie']:,.2f} zł |
                | Zysk ({zysk_rate}%) | {kosztorys['summary']['zysk']:,.2f} zł |
                """)
            
            # Podgląd pozycji
            with st.expander(f"📋 Pozycje kosztorysu ({len(kosztorys['positions'])})", expanded=False):
                for p in kosztorys['positions'][:20]:
                    st.text(f"{p['lp']:3}. [{p['knr'][:20]}] {p['description'][:50]}... | {p['quantity']:.2f} {p['unit']} × {p['price_unit']:.2f} = {p['value_netto']:.2f} zł")
                if len(kosztorys['positions']) > 20:
                    st.caption(f"... i {len(kosztorys['positions']) - 20} więcej pozycji")
            
            # Ostrzeżenie
            st.markdown('''
            <div class="warning-box">
                ⚠️ <strong>PROJEKT kosztorysu</strong> — wymaga weryfikacji przez wykwalifikowanego kosztorysanta przed użyciem!
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Download sekcja
            st.markdown('<div class="section-header">💾 Pobierz dokumenty</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: #f8fafc; padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem;">
                <p style="margin: 0 0 1rem 0; font-size: 1rem; color: #334155;">
                    <strong>Gotowe pliki do pobrania:</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            with col1:
                st.markdown("""
                <div style="text-align: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 2rem;">📄</span><br>
                    <small style="color: #64748b;">Dokument do druku</small>
                </div>
                """, unsafe_allow_html=True)
                st.download_button(
                    label="Pobierz PDF",
                    data=pdf_bytes,
                    file_name=f"kosztorys_{timestamp}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col2:
                st.markdown("""
                <div style="text-align: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 2rem;">🔧</span><br>
                    <small style="color: #64748b;">Import do Norma PRO</small>
                </div>
                """, unsafe_allow_html=True)
                st.download_button(
                    label="Pobierz ATH",
                    data=ath_bytes,
                    file_name=f"kosztorys_{timestamp}.ath",
                    mime="application/octet-stream",
                    use_container_width=True
                )
            
            with col3:
                st.markdown("""
                <div style="text-align: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 2rem;">💾</span><br>
                    <small style="color: #64748b;">Dane surowe</small>
                </div>
                """, unsafe_allow_html=True)
                st.download_button(
                    label="Pobierz JSON",
                    data=json.dumps(kosztorys, indent=2, ensure_ascii=False),
                    file_name=f"kosztorys_{timestamp}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            # Sukces
            st.markdown('''
            <div class="success-box">
                ✅ <strong>Kosztorys wygenerowany pomyślnie!</strong> Pliki gotowe do pobrania.
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Błąd: {str(e)}")
            st.exception(e)
    
    # Footer
    st.markdown('''
    <div class="footer">
        <p>kosztorysAI v3.0 | Profesjonalne kosztorysy budowlane</p>
        <p>Eksport: PDF • ATH (Norma PRO) • JSON</p>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
kosztorysAI v4.0 — AI-Powered
Rozumie przedmiary jak człowiek
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from io import BytesIO
import sys
import os

# Ścieżki
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent / "kosztorys"))

# Sprawdź klucze API
HAS_ANTHROPIC = bool(os.environ.get('ANTHROPIC_API_KEY'))
HAS_OPENAI = bool(os.environ.get('OPENAI_API_KEY'))
HAS_AI = HAS_ANTHROPIC or HAS_OPENAI

# Konfiguracja
st.set_page_config(page_title="kosztorysAI", page_icon="🏗️", layout="wide")

# CSS
st.markdown("""
<style>
.header {
    background: linear-gradient(135deg, #1e3a5f, #2d5a87, #3d7ab8);
    padding: 2.5rem;
    border-radius: 20px;
    text-align: center;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(30,58,95,0.3);
}
.header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
.header p { opacity: 0.9; font-size: 1.1rem; }
.ai-badge {
    background: linear-gradient(90deg, #10b981, #059669);
    color: white;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    display: inline-block;
    margin-top: 0.5rem;
}
.metric-box {
    background: linear-gradient(145deg, #ffffff, #f8fafc);
    padding: 1.5rem;
    border-radius: 16px;
    text-align: center;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    transition: transform 0.2s;
}
.metric-box:hover { transform: translateY(-3px); }
.metric-value { font-size: 1.8rem; font-weight: bold; color: #1e3a5f; }
.metric-label { color: #64748b; font-size: 0.9rem; }
.info-box {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    margin: 1rem 0;
}
.success-box {
    background: #ecfdf5;
    border-left: 4px solid #10b981;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
}
.warning-box {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
}
</style>
""", unsafe_allow_html=True)


# ============================================
# FUNKCJE
# ============================================

@st.cache_resource
def load_ai_engine():
    """Załaduj AI engine"""
    if HAS_AI:
        from ai_engine import get_ai_engine
        return get_ai_engine()
    return None

@st.cache_resource  
def load_legacy_generator():
    """Załaduj stary generator (fallback)"""
    from engine_v2 import KosztorysGeneratorV2
    return KosztorysGeneratorV2()

def parse_pdf_legacy(pdf_bytes):
    """Stary parser PDF (fallback)"""
    from pdf_parser import parse_przedmiar
    return parse_przedmiar(pdf_bytes)

def generate_pdf(kosztorys):
    """Generuj PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', 'C:/Windows/Fonts/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'C:/Windows/Fonts/DejaVuSans-Bold.ttf'))
        FONT, FONT_B = 'DejaVu', 'DejaVu-Bold'
    except:
        FONT, FONT_B = 'Helvetica', 'Helvetica-Bold'
    
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitlePL', fontName=FONT_B, fontSize=16, alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='BodyPL', fontName=FONT, fontSize=9, spaceAfter=4))
    
    story = []
    story.append(Paragraph("KOSZTORYS OFERTOWY", styles['TitlePL']))
    story.append(Paragraph(f"{kosztorys['meta']['title']}", styles['BodyPL']))
    story.append(Paragraph(f"Data: {datetime.now().strftime('%d.%m.%Y')}", styles['BodyPL']))
    story.append(Paragraph(f"Wygenerowano przez: {kosztorys['meta'].get('generated_by', 'kosztorysAI')}", styles['BodyPL']))
    story.append(Spacer(1, 0.5*cm))
    
    # Tabela
    data = [['Lp', 'KNR', 'Opis', 'Jm', 'Ilość', 'Cena', 'Wartość']]
    for p in kosztorys['positions'][:50]:
        data.append([
            str(p['lp']),
            (p.get('knr') or '-')[:12],
            (p.get('description') or '-')[:30],
            p.get('unit', 'm2'),
            f"{p.get('quantity', 1):.2f}",
            f"{p.get('price_unit', 0):.2f}",
            f"{p.get('value_netto', 0):.2f}"
        ])
    
    t = Table(data, colWidths=[0.8*cm, 2*cm, 5.5*cm, 1*cm, 1.5*cm, 1.8*cm, 2.2*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), FONT_B),
        ('FONTNAME', (0,1), (-1,-1), FONT),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))
    
    # Suma
    s = kosztorys['summary']
    story.append(Paragraph(f"<b>NETTO: {s['total_netto']:,.2f} zł</b>", styles['BodyPL']))
    story.append(Paragraph(f"<b>VAT: {s['vat']:,.2f} zł</b>", styles['BodyPL']))
    story.append(Paragraph(f"<b>BRUTTO: {s['total_brutto']:,.2f} zł</b>", styles['BodyPL']))
    
    if kosztorys.get('uwagi'):
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Uwagi: {kosztorys['uwagi']}", styles['BodyPL']))
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("PROJEKT - wymaga weryfikacji przez kosztorysanta", styles['BodyPL']))
    
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

def generate_ath(kosztorys):
    """Generuj ATH"""
    from output.ath_generator import ATH_Kosztorys, ATH_Element, ATH_Pozycja, ATHGenerator
    
    k = ATH_Kosztorys(
        nazwa=kosztorys['meta']['title'],
        inwestor=kosztorys['investment'].get('investor', ''),
        stawka_robocizny=kosztorys['rates'].get('stawka_rg', 35.0),
        koszty_posrednie=kosztorys['rates'].get('koszty_posrednie_pct', 68.0),
        zysk=kosztorys['rates'].get('zysk_pct', 10.0),
        vat=kosztorys['rates'].get('vat_pct', 23),
    )
    
    # Grupuj po działach
    dzialy = {}
    for pos in kosztorys['positions']:
        dzial = pos.get('dzial', 'Roboty budowlane')
        if dzial not in dzialy:
            dzialy[dzial] = []
        dzialy[dzial].append(pos)
    
    for i, (dzial_nazwa, pozycje) in enumerate(dzialy.items(), 1):
        elem = ATH_Element(id=i, numer=str(i), nazwa=dzial_nazwa)
        
        for j, pos in enumerate(pozycje, 1):
            knr_parts = (pos.get('knr') or 'KALK').split()
            katalog = ' '.join(knr_parts[:2]) if len(knr_parts) >= 2 else knr_parts[0] if knr_parts else 'KALK'
            numer = knr_parts[2] if len(knr_parts) >= 3 else ''
            
            elem.pozycje.append(ATH_Pozycja(
                id=(i-1)*100 + j,
                katalog=katalog,
                numer=numer,
                opis=pos.get('description', ''),
                jednostka=pos.get('unit', 'm2'),
                ilosc=pos.get('quantity', 1),
                cena_R=pos.get('price_R', 0),
                cena_M=pos.get('price_M', pos.get('price_unit', 0)),
                cena_S=pos.get('price_S', 0),
            ))
        
        k.elementy.append(elem)
    
    return ATHGenerator(k).generate().encode('cp1250')


# ============================================
# APLIKACJA
# ============================================

# Header
ai_status = "🤖 AI Enabled" if HAS_AI else "⚠️ AI Disabled"
st.markdown(f'''
<div class="header">
    <h1>🏗️ kosztorysAI</h1>
    <p>Inteligentny generator kosztorysów budowlanych</p>
    <div class="ai-badge">{ai_status}</div>
</div>
''', unsafe_allow_html=True)

# Ładowanie
ai_engine = load_ai_engine()
legacy_gen = load_legacy_generator()

# Info o AI
if HAS_AI:
    st.markdown('''
    <div class="info-box">
        <strong>🤖 Tryb AI aktywny</strong><br>
        System rozumie przedmiary jak człowiek. Możesz wgrać PDF lub opisać inwestycję słownie.
    </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown('''
    <div class="warning-box">
        <strong>⚠️ Brak klucza API</strong><br>
        Ustaw ANTHROPIC_API_KEY lub OPENAI_API_KEY dla pełnej funkcjonalności AI.<br>
        Aktualnie działa tryb podstawowy (tylko PDF z KNR).
    </div>
    ''', unsafe_allow_html=True)

# Statystyki
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-box"><div class="metric-value">{len(legacy_gen.baza._cache) if hasattr(legacy_gen.baza, "_cache") else "350+"}</div><div class="metric-label">Pozycji KNR</div></div>', unsafe_allow_html=True)
with col2:
    mode = "Claude/GPT" if HAS_AI else "Regex"
    st.markdown(f'<div class="metric-box"><div class="metric-value">{mode}</div><div class="metric-label">Silnik</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-box"><div class="metric-value">PDF+ATH</div><div class="metric-label">Eksport</div></div>', unsafe_allow_html=True)

st.markdown("---")

# === WYBÓR TRYBU ===
st.subheader("📝 1. Wybierz sposób wprowadzenia danych")

input_mode = st.radio(
    "Jak chcesz wprowadzić dane?",
    ["📄 Wgraj PDF z przedmiarem", "✍️ Opisz inwestycję słownie"],
    horizontal=True,
    label_visibility="collapsed"
)

# Dane wejściowe
pdf_bytes = None
description = None

if "PDF" in input_mode:
    uploaded = st.file_uploader("Wybierz plik PDF", type=['pdf'])
    if uploaded:
        pdf_bytes = uploaded.getvalue()
        st.success(f"✅ Wgrano: **{uploaded.name}** ({len(pdf_bytes)/1024:.1f} KB)")
else:
    description = st.text_area(
        "Opisz inwestycję",
        placeholder="np. Budowa domu jednorodzinnego 120m2. Fundamenty ławowe, ściany z bloczków Ytong 24cm, strop monolityczny, dach dwuspadowy z dachówką ceramiczną...",
        height=150
    )
    if description:
        st.success(f"✅ Opis: {len(description)} znaków")

# === USTAWIENIA ===
st.subheader("⚙️ 2. Ustawienia")

col1, col2, col3 = st.columns(3)
with col1:
    vat = st.selectbox("VAT", [8, 23], format_func=lambda x: f"{x}%")
with col2:
    kp = st.slider("Koszty pośrednie (%)", 50, 90, 68)
with col3:
    zysk = st.slider("Zysk (%)", 5, 20, 10)

st.markdown("---")

# === GENEROWANIE ===
st.subheader("🚀 3. Generuj kosztorys")

can_generate = pdf_bytes is not None or (description and len(description) > 20)

if not can_generate:
    st.info("👆 Wgraj PDF lub wpisz opis inwestycji")
else:
    if st.button("🚀 GENERUJ KOSZTORYS", type="primary", use_container_width=True):
        
        with st.spinner("🤖 AI analizuje dane..." if HAS_AI else "Przetwarzanie..."):
            try:
                kosztorys = None
                
                # === TRYB AI ===
                if HAS_AI and ai_engine:
                    if pdf_bytes:
                        kosztorys = ai_engine.process_pdf(pdf_bytes, vat, kp, zysk)
                    elif description:
                        kosztorys = ai_engine.process_description(description, vat, kp, zysk)
                
                # === FALLBACK (bez AI) ===
                if not kosztorys or 'error' in kosztorys:
                    if pdf_bytes:
                        przedmiar = parse_pdf_legacy(pdf_bytes)
                        if przedmiar.get('positions'):
                            kosztorys = legacy_gen.generate_from_przedmiar(
                                przedmiar_positions=przedmiar['positions'],
                                metadata=przedmiar.get('metadata', {}),
                                vat_rate=vat, kp_rate=kp, zysk_rate=zysk
                            )
                        else:
                            st.error("❌ Nie znaleziono pozycji. Spróbuj trybu AI lub innego pliku.")
                            st.stop()
                    else:
                        st.error("❌ Opis tekstowy wymaga AI. Ustaw klucz API.")
                        st.stop()
                
                # Sprawdź błędy
                if not kosztorys or 'error' in kosztorys:
                    st.error(f"❌ Błąd: {kosztorys.get('error', 'Nieznany błąd')}")
                    if kosztorys.get('raw'):
                        with st.expander("Surowa odpowiedź AI"):
                            st.text(kosztorys['raw'][:2000])
                    st.stop()
                
                # === WYNIKI ===
                st.markdown("---")
                st.subheader("📊 Wynik")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Netto", f"{kosztorys['summary']['total_netto']:,.0f} zł")
                c2.metric("VAT", f"{kosztorys['summary']['vat']:,.0f} zł")
                c3.metric("Brutto", f"{kosztorys['summary']['total_brutto']:,.0f} zł")
                c4.metric("Pozycji", f"{len(kosztorys['positions'])}")
                
                # Szczegóły
                with st.expander("📈 Szczegóły kalkulacji"):
                    st.markdown(f"""
                    | Składnik | Wartość |
                    |----------|---------|
                    | Robocizna (R) | {kosztorys['summary']['suma_R']:,.2f} zł |
                    | Materiały (M) | {kosztorys['summary']['suma_M']:,.2f} zł |
                    | Sprzęt (S) | {kosztorys['summary']['suma_S']:,.2f} zł |
                    | Razem bezpośrednie | {kosztorys['summary']['razem_bezposrednie']:,.2f} zł |
                    | Koszty pośrednie ({kp}%) | {kosztorys['summary']['koszty_posrednie']:,.2f} zł |
                    | Zysk ({zysk}%) | {kosztorys['summary']['zysk']:,.2f} zł |
                    """)
                
                # Pozycje
                with st.expander(f"📋 Lista pozycji ({len(kosztorys['positions'])})"):
                    for p in kosztorys['positions'][:50]:
                        dzial = f"[{p.get('dzial', '')}] " if p.get('dzial') else ""
                        knr = f"[{p['knr']}] " if p.get('knr') else ""
                        st.text(f"{p['lp']:3}. {dzial}{knr}{p['description'][:45]:45} | {p['quantity']:.2f} {p['unit']} = {p['value_netto']:.2f} zł")
                    if len(kosztorys['positions']) > 50:
                        st.caption(f"... i {len(kosztorys['positions'])-50} więcej")
                
                # Uwagi AI
                if kosztorys.get('uwagi'):
                    st.info(f"💡 **Uwagi AI:** {kosztorys['uwagi']}")
                
                st.markdown('''
                <div class="warning-box">
                    ⚠️ <strong>PROJEKT kosztorysu</strong> — wymaga weryfikacji przez wykwalifikowanego kosztorysanta!
                </div>
                ''', unsafe_allow_html=True)
                
                # === POBIERANIE ===
                st.markdown("---")
                st.subheader("💾 Pobierz")
                
                col1, col2, col3 = st.columns(3)
                ts = datetime.now().strftime('%Y%m%d_%H%M')
                
                with col1:
                    st.download_button("📥 PDF", generate_pdf(kosztorys), f"kosztorys_{ts}.pdf", "application/pdf", use_container_width=True)
                
                with col2:
                    st.download_button("📥 ATH (Norma)", generate_ath(kosztorys), f"kosztorys_{ts}.ath", use_container_width=True)
                
                with col3:
                    st.download_button("📥 JSON", json.dumps(kosztorys, indent=2, ensure_ascii=False), f"kosztorys_{ts}.json", "application/json", use_container_width=True)
                
                st.markdown('''
                <div class="success-box">
                    ✅ <strong>Gotowe!</strong> Pobierz pliki powyżej.
                </div>
                ''', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Błąd: {e}")
                st.exception(e)

# Footer
st.markdown("---")
st.caption(f"kosztorysAI v4.0 | {'🤖 AI-Powered' if HAS_AI else '📊 Standard'} | Profesjonalne kosztorysy budowlane")

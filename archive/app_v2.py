# -*- coding: utf-8 -*-
"""
kosztorysAI v2.0 - Profesjonalny interfejs z bazą 688 KNR + eksport ATH
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent))

from engine_v2 import KosztorysGeneratorV2, generate_ath, BazaKNR
from pdf_parser import parse_przedmiar

# Konfiguracja strony
st.set_page_config(
    page_title="kosztorysAI v2.0",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .stats-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Cache generatora
@st.cache_resource
def get_generator():
    return KosztorysGeneratorV2()

@st.cache_resource
def get_baza_stats():
    baza = BazaKNR()
    return baza.get_stats()

generator = get_generator()

# Nagłówek
st.markdown('''
<div class="main-header">
    <h1>🏗️ kosztorysAI v2.0</h1>
    <p>Profesjonalne kosztorysy budowlane | 355+ pozycji KNR | Eksport do Norma PRO (.ath)</p>
</div>
''', unsafe_allow_html=True)

# Sidebar - statystyki
with st.sidebar:
    st.markdown("### 📊 Statystyki bazy")
    stats = get_baza_stats()
    st.metric("Pozycji KNR", stats['liczba_pozycji'])
    st.metric("Katalogów", stats['liczba_katalogow'])
    
    with st.expander("Top katalogi"):
        for kat, count in list(stats['katalogi'].items())[:10]:
            st.text(f"{kat}: {count}")
    
    st.markdown("---")
    st.markdown("### ⚙️ Ustawienia")
    
    default_vat = st.selectbox("Domyślny VAT", [8, 23], format_func=lambda x: f"{x}%")
    default_kp = st.slider("Koszty pośrednie (%)", 50, 90, 68)
    default_zysk = st.slider("Zysk (%)", 5, 20, 10)

# Główna zawartość - zakładki
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Z przedmiaru PDF",
    "✍️ Ręczne wprowadzanie",
    "🔍 Przeszukaj bazę KNR",
    "ℹ️ O projekcie"
])

# ====== TAB 1: Z przedmiaru PDF ======
with tab1:
    st.markdown("### Wgraj przedmiar PDF")
    st.info("System automatycznie rozpozna pozycje i dopasuje ceny z bazy KNR")
    
    uploaded_file = st.file_uploader(
        "Wybierz plik PDF z przedmiarem",
        type=['pdf'],
        help="Akceptowane formaty: PDF z przedmiarem robót"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        vat_rate = st.selectbox("VAT", [8, 23], index=0 if default_vat == 8 else 1, format_func=lambda x: f"{x}%", key="vat1")
    with col2:
        kp_rate = st.number_input("Koszty pośrednie (%)", value=float(default_kp), key="kp1")
    with col3:
        zysk_rate = st.number_input("Zysk (%)", value=float(default_zysk), key="zysk1")
    
    if uploaded_file:
        try:
            with st.spinner("Parsowanie przedmiaru..."):
                przedmiar = parse_przedmiar(uploaded_file.getvalue())
            
            st.success(f"✅ Znaleziono **{len(przedmiar['positions'])}** pozycji")
            
            if przedmiar['metadata'].get('title'):
                st.info(f"📋 Inwestycja: **{przedmiar['metadata']['title']}**")
            
            # Podgląd pozycji
            with st.expander(f"👁️ Podgląd pozycji ({len(przedmiar['positions'])})", expanded=False):
                for i, p in enumerate(przedmiar['positions'][:20], 1):
                    knr = p.get('knr', '-')
                    desc = p.get('description', '')[:60]
                    qty = p.get('quantity', '-')
                    unit = p.get('unit', '')
                    st.text(f"{i:3}. [{knr}] {desc}... | {qty} {unit}")
                if len(przedmiar['positions']) > 20:
                    st.caption(f"... i {len(przedmiar['positions']) - 20} więcej")
            
            # Generowanie
            if st.button("🚀 GENERUJ KOSZTORYS", type="primary", use_container_width=True):
                with st.spinner("Generowanie kosztorysu..."):
                    kosztorys = generator.generate_from_przedmiar(
                        przedmiar_positions=przedmiar['positions'],
                        metadata=przedmiar['metadata'],
                        vat_rate=vat_rate,
                        kp_rate=kp_rate,
                        zysk_rate=zysk_rate
                    )
                
                st.markdown("---")
                st.markdown("## 📊 Wynik kosztorysowania")
                
                # Metryki
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Netto", f"{kosztorys['summary']['total_netto']:,.2f} zł")
                col2.metric("VAT", f"{kosztorys['summary']['vat']:,.2f} zł")
                col3.metric("Brutto", f"{kosztorys['summary']['total_brutto']:,.2f} zł")
                col4.metric("Dopasowanie KNR", f"{kosztorys['summary']['match_rate']:.0f}%")
                
                # Szczegóły sum
                with st.expander("📈 Szczegóły kalkulacji"):
                    st.markdown(f"""
                    | Składnik | Wartość |
                    |----------|---------|
                    | Robocizna (R) | {kosztorys['summary']['suma_R']:,.2f} zł |
                    | Materiały (M) | {kosztorys['summary']['suma_M']:,.2f} zł |
                    | Sprzęt (S) | {kosztorys['summary']['suma_S']:,.2f} zł |
                    | **Razem bezpośrednie** | **{kosztorys['summary']['razem_bezposrednie']:,.2f} zł** |
                    | Koszty pośrednie ({kp_rate}%) | {kosztorys['summary']['koszty_posrednie']:,.2f} zł |
                    | Zysk ({zysk_rate}%) | {kosztorys['summary']['zysk']:,.2f} zł |
                    | **NETTO** | **{kosztorys['summary']['total_netto']:,.2f} zł** |
                    | VAT ({vat_rate}%) | {kosztorys['summary']['vat']:,.2f} zł |
                    | **BRUTTO** | **{kosztorys['summary']['total_brutto']:,.2f} zł** |
                    """)
                
                # Pozycje
                st.markdown("### 📋 Pozycje kosztorysu")
                
                # Konwertuj do DataFrame
                df = pd.DataFrame(kosztorys['positions'])
                df = df[['lp', 'knr', 'description', 'unit', 'quantity', 'price_unit', 'value_netto', 'source']]
                df.columns = ['Lp', 'KNR', 'Opis', 'Jm', 'Ilość', 'Cena jdn.', 'Wartość', 'Źródło']
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Cena jdn.': st.column_config.NumberColumn(format="%.2f zł"),
                        'Wartość': st.column_config.NumberColumn(format="%.2f zł"),
                        'Ilość': st.column_config.NumberColumn(format="%.3f"),
                    }
                )
                
                # Ostrzeżenie
                st.warning("⚠️ **PROJEKT kosztorysu** - wymaga weryfikacji przez kosztorysanta!")
                
                # Eksport
                st.markdown("### 💾 Eksport")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "📥 Pobierz JSON",
                        json.dumps(kosztorys, indent=2, ensure_ascii=False),
                        f"kosztorys_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        "application/json",
                        use_container_width=True
                    )
                
                with col2:
                    # CSV
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        "📥 Pobierz CSV",
                        csv,
                        f"kosztorys_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                
                with col3:
                    # ATH dla Norma PRO
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.ath') as tmp:
                            generate_ath(kosztorys, tmp.name)
                            with open(tmp.name, 'rb') as f:
                                ath_content = f.read()
                        
                        st.download_button(
                            "📥 Pobierz ATH (Norma PRO)",
                            ath_content,
                            f"kosztorys_{datetime.now().strftime('%Y%m%d_%H%M')}.ath",
                            "application/octet-stream",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Błąd generowania ATH: {e}")
                
                # Zapisz w sesji
                st.session_state['last_kosztorys'] = kosztorys
                
        except Exception as e:
            st.error(f"❌ Błąd: {str(e)}")
            st.exception(e)

# ====== TAB 2: Ręczne wprowadzanie ======
with tab2:
    st.markdown("### Ręczne wprowadzanie pozycji")
    st.info("Wprowadź pozycje ręcznie lub wklej z Excela")
    
    # Formularz dodawania pozycji
    if 'manual_positions' not in st.session_state:
        st.session_state.manual_positions = []
    
    with st.form("add_position"):
        col1, col2 = st.columns(2)
        with col1:
            knr = st.text_input("Numer KNR", placeholder="np. KNR 2-02 0205-03")
            opis = st.text_area("Opis pozycji", placeholder="np. Ławy fundamentowe żelbetowe...", height=100)
        with col2:
            jednostka = st.selectbox("Jednostka", ['m3', 'm2', 'm', 'szt', 'kg', 't', 'kpl'])
            ilosc = st.number_input("Ilość", min_value=0.001, value=1.0, step=0.1)
            cena = st.number_input("Cena jednostkowa (zł)", min_value=0.0, value=0.0, help="Zostaw 0 dla automatycznego dopasowania")
        
        submitted = st.form_submit_button("➕ Dodaj pozycję")
        
        if submitted and (knr or opis):
            st.session_state.manual_positions.append({
                'knr': knr,
                'description': opis,
                'unit': jednostka,
                'quantity': ilosc,
                'price_override': cena if cena > 0 else None
            })
            st.success("Dodano pozycję")
            st.rerun()
    
    # Lista pozycji
    if st.session_state.manual_positions:
        st.markdown(f"### Pozycje ({len(st.session_state.manual_positions)})")
        
        for i, pos in enumerate(st.session_state.manual_positions):
            col1, col2, col3 = st.columns([6, 2, 1])
            with col1:
                st.text(f"{i+1}. [{pos['knr']}] {pos['description'][:40]}...")
            with col2:
                st.text(f"{pos['quantity']} {pos['unit']}")
            with col3:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.manual_positions.pop(i)
                    st.rerun()
        
        if st.button("🗑️ Wyczyść wszystko"):
            st.session_state.manual_positions = []
            st.rerun()
        
        if st.button("🚀 GENERUJ KOSZTORYS", type="primary", key="gen_manual"):
            kosztorys = generator.generate_from_przedmiar(
                przedmiar_positions=st.session_state.manual_positions,
                metadata={'title': 'Kosztorys ręczny'},
                vat_rate=default_vat,
                kp_rate=default_kp,
                zysk_rate=default_zysk
            )
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            col1.metric("Netto", f"{kosztorys['summary']['total_netto']:,.2f} zł")
            col2.metric("VAT", f"{kosztorys['summary']['vat']:,.2f} zł")
            col3.metric("Brutto", f"{kosztorys['summary']['total_brutto']:,.2f} zł")
            
            st.download_button(
                "📥 Pobierz JSON",
                json.dumps(kosztorys, indent=2, ensure_ascii=False),
                "kosztorys_reczny.json",
                "application/json"
            )
    else:
        st.info("Brak pozycji. Dodaj pierwszą pozycję powyżej.")

# ====== TAB 3: Przeszukaj bazę KNR ======
with tab3:
    st.markdown("### 🔍 Przeszukaj bazę KNR")
    
    search_query = st.text_input("Szukaj", placeholder="np. fundament, izolacja, tynk...")
    
    if search_query:
        wyniki = generator.baza.szukaj(search_query, limit=20)
        
        if wyniki:
            st.success(f"Znaleziono {len(wyniki)} pozycji")
            
            for w in wyniki:
                with st.expander(f"**{w.get('podstawa', '-')}** | {w.get('cena_jednostkowa', 0):.2f} zł/{w.get('jednostka', 'szt')}"):
                    st.markdown(f"**Opis:** {w.get('opis', '-')}")
                    st.markdown(f"**Katalog:** {w.get('katalog', '-')}")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("R", f"{w.get('cena_R', 0):.2f} zł")
                    col2.metric("M", f"{w.get('cena_M', 0):.2f} zł")
                    col3.metric("S", f"{w.get('cena_S', 0):.2f} zł")
        else:
            st.warning("Brak wyników. Spróbuj innych słów kluczowych.")

# ====== TAB 4: O projekcie ======
with tab4:
    st.markdown("""
    ### 🏗️ kosztorysAI v2.0
    
    System AI do automatycznego generowania projektów kosztorysów budowlanych.
    
    #### ✨ Funkcje
    - **Import PDF** z przedmiarem - automatyczne rozpoznawanie pozycji
    - **Baza 355+ pozycji KNR** z realnymi cenami
    - **Fuzzy matching** - dopasowywanie pozycji nawet przy niepełnych danych
    - **Eksport do Norma PRO** - format .ath gotowy do importu
    - **Kalkulacja narzutów** - Kp, zysk, VAT
    
    #### 📊 Źródła danych
    Baza KNR zbudowana na podstawie rzeczywistych kosztorysów:
    - Budynki użyteczności publicznej
    - Domy jednorodzinne
    - Remonty i modernizacje
    
    #### ⚠️ Ważne
    Generowane kosztorysy są **projektami/draftami** wymagającymi weryfikacji 
    przez wykwalifikowanego kosztorysanta. Ceny mogą wymagać aktualizacji 
    do aktualnych stawek rynkowych.
    
    ---
    
    **Wersja:** 2.0.0  
    **Generator:** kosztorysAI  
    **Backend:** Python + Streamlit  
    **Baza KNR:** 355+ pozycji  
    **Eksport:** JSON, CSV, ATH (Norma PRO)
    """)

# Footer
st.markdown("---")
st.caption("kosztorysAI v2.0 | Profesjonalne kosztorysy budowlane")

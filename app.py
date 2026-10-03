import streamlit as st
import time
import random
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from modules.mod1_radar.radar import RadarEngine
from modules.mod2_trend.trend_engine import TrendEngine
from modules.mod3_sourcing.aliexpress_scraper import AliExpressScraper
from modules.mod3_sourcing.alibaba_scraper import AlibabaScraper
from modules.mod4_benchmark.amazon_scraper import AmazonBenchmarkEngine

st.set_page_config(page_title="TrendScraper", layout="wide")

st.title("TrendScraper Pro Dashboard")
st.markdown("Scopri prodotti ad alta richiesta e alto margine in tempo reale.")

# --- SIDEBAR: Impostazioni ---
with st.sidebar:
    st.header("Impostazioni Ricerca")
    
    # 1. Scelta della Modalità
    mode = st.radio(
        "Modalità di Ricerca",
        options=["Ricerca Esatta (Singolo Prodotto)", "Esplora Nicchia (Alphabet Soup)"],
        help="Esatta: Analizza esattamente il nome che scrivi. Esplora: Cerca nuovi prodotti in una categoria."
    )
    
    category = st.text_input("Nome Prodotto o Nicchia", value="Blink Mini 2K+")
    limit = st.slider("Numero massimo di prodotti", min_value=1, max_value=20, value=3)

    use_alibaba = False
    if mode == "Ricerca Esatta (Singolo Prodotto)":
        use_alibaba = st.checkbox(
            "Verifica prezzo wholesale su Alibaba",
            value=True,
            help="1 sola richiesta lenta (~45s tra una e l'altra), risultato in cache 30 giorni. Se Alibaba blocca, vedrai N/D."
        )
    
    st.markdown("---")
    st.markdown("**Stato Motore SerpApi:**")
    engine_temp = TrendEngine()
    crediti = engine_temp.get_remaining_credits()
    if crediti is None:
        st.error("Crediti non verificabili: controlla SERPAPI_KEY nel file .env")
    elif crediti > 10:
        st.success(f"{crediti} ricerche disponibili")
    else:
        st.error(f"Attenzione: {crediti} ricerche rimaste!")
        
    start_button = st.button("AVVIA SCANSIONE", use_container_width=True, type="primary")

# --- CORE LOGIC ---
if start_button:
    if crediti is None or crediti <= 10:
        st.error("Crediti SerpApi non verificabili o insufficienti.")
        st.stop()
        
    radar = RadarEngine()
    trend_engine = TrendEngine()
    sourcing_engine = AliExpressScraper()
    amazon_engine = AmazonBenchmarkEngine()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    with log_container:
        st.markdown("### Log di Sistema")
        log_box = st.empty()
    
    logs = []
    def add_log(text):
        logs.append(text)
        log_box.code("\n".join(logs[-10:]))
        
    # FASE 1: RADAR (Esatto vs Esplora)
    status_text.info("Fase 1: Preparazione Keyword...")
    
    if mode == "Ricerca Esatta (Singolo Prodotto)":
        add_log(f"-> Modalità Esatta: Bypass Radar. Analizzo solo '{category}'")
        candidates = [{
            "keyword": category,
            "source": "manual_exact",
            "category": category,
            "initial_traction_score": 100,
            "raw_title": category
        }]
    else:
        add_log(f"-> Avvio Radar Alphabet Soup per: '{category}'")
        candidates = radar.run_scan(category=category)
    
    if not candidates:
        st.error("Nessun candidato trovato dal Radar. Prova un'altra categoria.")
        st.stop()
        
    add_log(f"-> Pronti per analizzare {min(len(candidates), limit)} keyword.")
    progress_bar.progress(25)
    
    candidates = candidates[:limit]
    valid_candidates = []
    
    # FASE 2: TREND
    status_text.info(f"Fase 2: Validazione Trend...")
    for i, c in enumerate(candidates):
        if i > 0: time.sleep(random.uniform(1, 2))
        add_log(f"-> Analisi Trend per: {c['keyword']}")
        trend_res = trend_engine.evaluate_keyword(c['keyword'])
        c['trend_score'] = trend_res.get('trend_score', 0.0)
        valid_candidates.append(c)
        
    progress_bar.progress(50)
    
    # FASE 3: SOURCING
    status_text.info(f"Fase 3: Ricerca costi di fabbrica...")
    for i, c in enumerate(valid_candidates):
        if i > 0: time.sleep(random.uniform(2, 4))
        add_log(f"-> Ricerca costo per: {c['keyword']}")
        sourcing_res = sourcing_engine.estimate_sourcing_cost(c['keyword'])
        c['base_cost'] = sourcing_res.get('estimated_cost_usd', 0.0)
        
    # FASE 3b: ALIBABA (solo ricerca esatta, opzionale)
    if use_alibaba:
        status_text.info("Fase 3b: Verifica wholesale Alibaba (gentile, puo' richiedere qualche secondo)...")
        alibaba = AlibabaScraper()
        for c in valid_candidates:
            add_log(f"-> Alibaba wholesale per: {c['keyword']}")
            ab = alibaba.estimate_wholesale(c['keyword'])
            if ab.get("blocked"):
                add_log(f"   Alibaba non disponibile: {ab.get('reason')}")
            elif ab.get("error"):
                add_log(f"   Alibaba: {ab.get('error')}")
            else:
                c['ali_min'] = ab['wholesale_min']
                c['ali_max'] = ab['wholesale_max']
                c['ali_moq'] = ab.get('moq_typical')
                add_log(f"   Alibaba: EUR {ab['wholesale_min']}-{ab['wholesale_max']} (MOQ {ab.get('moq_typical')}){' [cache]' if ab.get('from_cache') else ''}")

    progress_bar.progress(75)
    
    # FASE 4: BENCHMARK
    status_text.info(f"Fase 4: Analisi prezzi di mercato (Amazon/eBay proxy)...")
    for i, c in enumerate(valid_candidates):
        if i > 0: time.sleep(random.uniform(2, 4))
        add_log(f"-> Ricerca prezzo per: {c['keyword']}")
        amazon_res = amazon_engine.estimate_selling_price(c['keyword'])
        c['sell_price'] = amazon_res.get('estimated_price_eur', 0.0)
        
        if c['sell_price'] > 0 and c['base_cost'] > 0:
            margin = ((c['sell_price'] - c['base_cost']) / c['sell_price']) * 100
            c['margin_percent'] = round(margin, 1)
        else:
            c['margin_percent'] = 0.0

        # Margine su costo Alibaba (usa il valore alto del range = scenario prudente)
        if c.get('ali_max') and c['sell_price'] > 0:
            c['margin_alibaba'] = round(((c['sell_price'] - c['ali_max']) / c['sell_price']) * 100, 1)
            
    progress_bar.progress(100)
    status_text.success("Scansione completata con successo!")
    
    st.markdown("### Risultati Finali")
    df = pd.DataFrame(valid_candidates)
    
    if not df.empty:
        for col in ['ali_min', 'ali_max', 'ali_moq', 'margin_alibaba']:
            if col not in df.columns:
                df[col] = float('nan')
        df['alibaba_range'] = df.apply(
            lambda r: f"€ {r['ali_min']:.2f} - {r['ali_max']:.2f}" if pd.notna(r['ali_min']) else "N/D", axis=1)
        df['alibaba_moq'] = df['ali_moq'].apply(lambda v: str(int(v)) if pd.notna(v) else "N/D")

        cols = ['keyword', 'trend_score', 'base_cost', 'sell_price', 'margin_percent']
        names = ['Prodotto', 'Trend (0-100)', 'Costo AliExpress (stima €)', 'Prezzo Mercato (€)', 'Margine su AliExpress (%)']
        if use_alibaba:
            cols += ['alibaba_range', 'alibaba_moq', 'margin_alibaba']
            names += ['Wholesale Alibaba (€)', 'MOQ Alibaba', 'Margine su Alibaba (%)']
        df_clean = df[cols].copy()
        df_clean.columns = names
        df_clean = df_clean.sort_values(by=['Trend (0-100)', 'Margine su AliExpress (%)'], ascending=[False, False]).reset_index(drop=True)
        
        # Formattazione per evitare 6 zeri decimali brutti
        styled_df = df_clean.style.background_gradient(
            cmap='Greens', subset=['Trend (0-100)', 'Margine su AliExpress (%)']
        ).format({
            'Trend (0-100)': "{:.1f}",
            'Costo AliExpress (stima €)': "€ {:.2f}",
            'Prezzo Mercato (€)': "€ {:.2f}",
            'Margine su AliExpress (%)': "{:.1f}%",
            'Margine su Alibaba (%)': lambda v: "N/D" if pd.isna(v) else f"{v:.1f}%",
        }, na_rep="N/D")
        
        html_table = styled_df.to_html(index=False)
        st.markdown(html_table, unsafe_allow_html=True)
        
        st.download_button(
            label="Scarica Report (CSV)",
            data=df_clean.to_csv(index=False).encode('utf-8'),
            file_name=f"trendscraper_{category}.csv",
            mime="text/csv",
        )
else:
    st.info("Imposta i filtri a sinistra e avvia la scansione.")
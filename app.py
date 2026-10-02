import streamlit as st
import time
import random
import pandas as pd
import sys
import os
from dotenv import load_dotenv
load_dotenv()


# Aggiungiamo backend al PATH così può importare i moduli originali
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from modules.mod1_radar.radar import RadarEngine
from modules.mod2_trend.trend_engine import TrendEngine
from modules.mod3_sourcing.aliexpress_scraper import AliExpressScraper
from modules.mod4_benchmark.amazon_scraper import AmazonBenchmarkEngine

st.set_page_config(page_title="TrendScraper", page_icon="??", layout="wide")

st.title("?? TrendScraper Pro Dashboard")
st.markdown("Scopri prodotti ad alta richiesta e alto margine in tempo reale.")

# --- SIDEBAR: Impostazioni ---
with st.sidebar:
    st.header("⚙️ Impostazioni Ricerca")
    category = st.text_input("Categoria o Nicchia", value="giardinaggio", help="Es: accessori auto, cani, giardinaggio")
    limit = st.slider("Numero massimo di prodotti", min_value=1, max_value=20, value=3)
    
    st.markdown("---")
    st.markdown("**Stato Motore SerpApi:**")
    # Inizializziamo il TrendEngine per controllare i crediti
    engine_temp = TrendEngine()
    crediti = engine_temp.get_remaining_credits()
    if crediti > 10:
        st.success(f"?? {crediti} ricerche disponibili")
    else:
        st.error(f"?? Attenzione: {crediti} ricerche rimaste!")
        
    start_button = st.button("?? AVVIA SCANSIONE", use_container_width=True, type="primary")

# --- CORE LOGIC ---
if start_button:
    if crediti <= 10:
        st.error("Crediti SerpApi insufficienti. Controlla il tuo abbonamento.")
        st.stop()
        
    # Inizializza i motori
    radar = RadarEngine()
    trend_engine = TrendEngine()
    sourcing_engine = AliExpressScraper()
    amazon_engine = AmazonBenchmarkEngine()
    
    # UI Elementi per il feedback
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    with log_container:
        st.markdown("### ?? Log di Sistema")
        log_box = st.empty()
    
    logs = []
    def add_log(text):
        logs.append(text)
        log_box.code("\n".join(logs[-10:])) # Mostra solo gli ultimi 10 log
        
    # FASE 1: RADAR
    status_text.info("?? Fase 1: Scansione Radar in corso...")
    add_log(f"-> Avvio Radar Alphabet Soup per: '{category}'")
    candidates = radar.run_scan(category=category)
    
    if not candidates:
        st.error("Nessun candidato trovato dal Radar. Prova un'altra categoria.")
        st.stop()
        
    add_log(f"-> Radar completato: trovate {len(candidates)} keyword potenziali.")
    progress_bar.progress(25)
    
    # Limitiamo
    candidates = candidates[:limit]
    valid_candidates = []
    
    # FASE 2: TREND
    status_text.info(f"?? Fase 2: Validazione Trend per {len(candidates)} candidati...")
    for i, c in enumerate(candidates):
        if i > 0: time.sleep(random.uniform(2, 4))
        add_log(f"-> Analisi Trend per: {c['keyword']}")
        trend_res = trend_engine.evaluate_keyword(c['keyword'])
        c['trend_score'] = trend_res.get('trend_score', 0.0)
        valid_candidates.append(c)
        
    progress_bar.progress(50)
    
    # FASE 3: SOURCING (Cina)
    status_text.info(f"?? Fase 3: Ricerca costi di fabbrica (AliExpress)...")
    for i, c in enumerate(valid_candidates):
        if i > 0: time.sleep(random.uniform(2, 4))
        add_log(f"-> Ricerca costo Cina per: {c['keyword']}")
        sourcing_res = sourcing_engine.estimate_sourcing_cost(c['keyword'])
        c['base_cost'] = sourcing_res.get('estimated_cost_usd', 0.0)
        
    progress_bar.progress(75)
    
    # FASE 4: BENCHMARK (Amazon)
    status_text.info(f"?? Fase 4: Analisi prezzi di mercato (Amazon IT)...")
    for i, c in enumerate(valid_candidates):
        if i > 0: time.sleep(random.uniform(2, 4))
        add_log(f"-> Ricerca prezzo Amazon per: {c['keyword']}")
        amazon_res = amazon_engine.estimate_selling_price(c['keyword'])
        c['sell_price'] = amazon_res.get('estimated_price_eur', 0.0)
        
        # Calcolo Margine
        if c['sell_price'] > 0 and c['base_cost'] > 0:
            margin = ((c['sell_price'] - c['base_cost']) / c['sell_price']) * 100
            c['margin_percent'] = round(margin, 1)
        else:
            c['margin_percent'] = 0.0
            
    progress_bar.progress(100)
    status_text.success("? Scansione completata con successo!")
    
    # --- PREPARAZIONE TABELLA ---
    st.markdown("### ?? Risultati Finali")
    
    # Convertiamo in DataFrame Pandas per visualizzazione e filtri
    df = pd.DataFrame(valid_candidates)
    
    if not df.empty:
        # Pulisco e riordino le colonne
        df_clean = df[['keyword', 'trend_score', 'base_cost', 'sell_price', 'margin_percent']].copy()
        df_clean.columns = ['Prodotto', 'Trend (0-100)', 'Costo Ali (€)', 'Prezzo Amz (€)', 'Margine Lordo (%)']
        
        # Ordiniamo per Trend (dal più alto al più basso) come chiesto dall'utente
        df_clean = df_clean.sort_values(by=['Trend (0-100)', 'Margine Lordo (%)'], ascending=[False, False]).reset_index(drop=True)
        
        # Mostriamo il DataFrame con opzioni interattive Streamlit
        st.dataframe(
            df_clean.style.background_gradient(cmap='Greens', subset=['Trend (0-100)', 'Margine Lordo (%)']),
            use_container_width=True,
            height=400
        )
        
        # Pulsante Download Excel
        st.download_button(
            label="?? Scarica Report (CSV)",
            data=df_clean.to_csv(index=False).encode('utf-8'),
            file_name=f"trendscraper_{category}_{time.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Nessun dato finale disponibile.")

else:
    st.info("Imposta la categoria nella barra di sinistra e clicca su 'AVVIA SCANSIONE' per cominciare.")
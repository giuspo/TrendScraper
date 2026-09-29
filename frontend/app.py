import streamlit as st
import pandas as pd
import sys
import os

# Aggiungiamo la directory 'backend' al sys.path per importare core e modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from core.database import create_db_and_tables

st.set_page_config(
    page_title="TrendRadar & Sourcing Engine",
    page_icon="📈",
    layout="wide"
)

st.title("📈 SGTech TrendRadar & Sourcing Engine")
st.markdown("Dashboard operativa per intercettare trend e prodotti ad alta marginalità.")

# Sidebar per Filtri e Controlli
st.sidebar.header("🕹️ Controlli Operativi")
category = st.sidebar.selectbox("Filtra per Categoria", ["Tutte", "Tech", "Home Office", "Lifestyle"])

if st.sidebar.button("🚀 Avvia Scansione Trend Giornaliera", use_container_width=True):
    st.sidebar.success("Scansione avviata in background! (Funzionalità in costruzione)")

st.sidebar.divider()
st.sidebar.subheader("⚙️ Override Regole Esclusione")
min_margin = st.sidebar.slider("Margine Netto FBA Minimo (%)", min_value=10, max_value=50, value=20)
max_weight = st.sidebar.slider("Peso Massimo (g)", min_value=100, max_value=2500, value=800)
allow_220v = st.sidebar.toggle("Consenti Alimentazione 220V AC", value=False)

# Vista a Griglia / Tabella (Mock temporaneo in attesa di SQLite)
st.subheader("🎯 Opportunità Trovate")

# Dati di esempio (mock) per mostrare l'interfaccia a Marie
data = [
    {"Badge": "🟢 Verde", "Prodotto": "Supporto Laptop Alluminio", "Score": 85, "Prezzo AZ": "€ 29.90", "Costo FOB": "€ 4.50", "Margine": "31%"},
    {"Badge": "🟡 Giallo", "Prodotto": "Lampada LED da Scrivania USB", "Score": 68, "Prezzo AZ": "€ 24.50", "Costo FOB": "€ 6.00", "Margine": "23%"},
    {"Badge": "🔴 Rosso", "Prodotto": "Caricatore Wireless 3 in 1", "Score": 45, "Prezzo AZ": "€ 15.90", "Costo FOB": "€ 5.50", "Margine": "12% (Scartato)"},
]

df = pd.DataFrame(data)

# Configurazione colori tabella (in Streamlit si può usare style su dataframe pandas)
def highlight_badge(val):
    if "Verde" in str(val): return "color: #00FF00; font-weight: bold"
    if "Giallo" in str(val): return "color: #FFA500; font-weight: bold"
    if "Rosso" in str(val): return "color: #FF0000; font-weight: bold"
    return ""

st.dataframe(df.style.map(highlight_badge, subset=["Badge"]), use_container_width=True, hide_index=True)

# Drawer / Dettaglio (Mock di una UI espandibile)
st.markdown("---")
with st.expander("🔍 Visualizza Dettaglio: Supporto Laptop Alluminio (Esempio)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Grafico Trend a 90 Giorni (Google Trends)**")
        # Inseriremo grafico plotly
        st.info("Area Grafico Plotly (in arrivo)")
        
        st.write("**Concorrenza Amazon**")
        st.table(pd.DataFrame([
            {"Brand": "BrandX", "Prezzo": "28.00", "Recensioni": 140, "Rating": 4.1},
            {"Brand": "BrandY", "Prezzo": "32.00", "Recensioni": 85, "Rating": 4.0}
        ]))
        
    with col2:
        st.write("**Checklist Normativa & Gatekeeper**")
        st.success("✅ Nessun materiale vietato")
        st.success("✅ Alimentazione USB (Sicuro)")
        st.success("✅ Peso < 800g (Pacco FBA Standard)")
        
        st.write("**Azioni Sourcing**")
        st.button("🔗 Cerca Fornitori su Alibaba (Sicuro)", type="primary", use_container_width=True)
        st.button("📋 Copia Modello RFQ Inglese", use_container_width=True)

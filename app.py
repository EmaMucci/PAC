import streamlit as st
import pandas as pd
import yfinance as yf
import os
from datetime import datetime

# Layout wide e dark
st.set_page_config(layout="wide", page_title="Dashboard PAC")

# === Titolo Principale ===
st.title("📈 Dashboard PAC")

# === Sezione Prezzi Live ETF ===
st.subheader("📊 Prezzi Live ETF")

etf_symbols = {
    "SPDR S&P 500 UCITS ETF": "SPY5L.MI",
    "iShares Core MSCI World UCITS ETF": "SWDA.L",
    "iShares NASDAQ 100 UCITS ETF EUR Hedged": "NSQE.DE"
}

cols = st.columns(3)

prezzi_live = {}

for i, (nome, simbolo) in enumerate(etf_symbols.items()):
    ticker = yf.Ticker(simbolo)
    try:
        prezzo = ticker.history(period="1d")["Close"].iloc[-1]
    except:
        prezzo = 0.0
    prezzi_live[nome] = prezzo
    with cols[i]:
        st.metric(label=nome, value=f"{prezzo:.2f} €", delta="Live")

# === Caricamento dati PAC da CSV ===
csv_file = "dati_pac.csv"
if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
else:
    df = pd.DataFrame(columns=["Data", "ETF", "Importo Versato", "Prezzo Acquisto", "Quantità"])

# === Calcolo Valore Attuale ===
df["Valore Attuale"] = df.apply(
    lambda row: row["Quantità"] * prezzi_live.get(row["ETF"], 0.0), axis=1
)
df["Guadagno"] = df["Valore Attuale"] - df["Importo Versato"]

# === KPI ===
totale_investito = df["Importo Versato"].sum()
valore_attuale = df["Valore Attuale"].sum()
guadagno_totale = valore_attuale - totale_investito

st.markdown("---")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("💰 Totale Investito", f"{totale_investito:.2f} €")
kpi2.metric("📊 Valore Attuale", f"{valore_attuale:.2f} €")
kpi3.metric("📈 Guadagno", f"{guadagno_totale:.2f} €")

# === Visualizzazione tabella operazioni ===
st.markdown("### 📋 Operazioni registrate")
st.dataframe(df)

# === Aggiunta manuale nuova operazione ===
st.markdown("---")
st.markdown("### ➕ Aggiungi operazione manualmente")

with st.form("aggiungi_operazione"):
    data = st.date_input("Data")
    etf = st.selectbox("ETF", list(etf_symbols.keys()))
    importo = st.number_input("Importo Versato (€)", min_value=0.0, step=10.0)
    prezzo = st.number_input("Prezzo Acquisto (€)", min_value=0.0, step=0.01)
    quantita = st.number_input("Quantità Acquistata", min_value=0.0, step=0.01)
    submit = st.form_submit_button("Aggiungi")

    if submit:
        nuova_op = {
            "Data": data.strftime("%Y-%m-%d"),
            "ETF": etf,
            "Importo Versato": importo,
            "Prezzo Acquisto": prezzo,
            "Quantità": quantita
        }
        df = pd.concat([df, pd.DataFrame([nuova_op])], ignore_index=True)
        df.to_csv(csv_file, index=False)
        st.success("✅ Operazione aggiunta con successo!")
        st.experimental_rerun()

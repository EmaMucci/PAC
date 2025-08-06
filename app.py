import streamlit as st
import pandas as pd
import yfinance as yf
import os
import csv
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Dashboard PAC")

# --- Funzione per ottenere i prezzi live ---
def get_live_prices(tickers):
    prices = {}
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period="1d")
            prices[ticker] = round(data["Close"].iloc[-1], 2)
        except:
            prices[ticker] = 0.0
    return prices

# --- Percorso file CSV ---
csv_file = "dati_pac.csv"

# --- Inizializza il file CSV se non esiste ---
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Data", "ETF", "Importo", "Prezzo", "Quantità"])

# --- Carica i dati ---
df = pd.read_csv(csv_file)
df["Data"] = pd.to_datetime(df["Data"])

# --- Prezzi live ---
tickers_mapping = {
    "SPY5L": "SPY5L.MI",
    "SWDA.L": "SWDA.L",
    "NSQE.DE": "NSQE.DE"
}
prezzi_live = get_live_prices(tickers_mapping.values())

# --- Calcolo valore attuale ---
df["Valore Attuale"] = df.apply(
    lambda row: row["Quantità"] * prezzi_live.get(tickers_mapping.get(row["ETF"], ""), 0.0),
    axis=1
)

# --- KPI ---
totale_investito = df["Importo"].sum()
valore_attuale = df["Valore Attuale"].sum()
guadagno = valore_attuale - totale_investito

# --- HEADER ---
st.markdown("### 📊 Dashboard PAC")
col1, col2, col3 = st.columns(3)
col1.metric("Totale Investito", f"€{totale_investito:.2f}")
col2.metric("Valore Attuale", f"€{valore_attuale:.2f}")
col3.metric("Guadagno", f"€{guadagno:.2f}", delta_color="inverse" if guadagno < 0 else "normal")

# --- GRAFICO ---
if not df.empty:
    df_grouped = df.groupby(df["Data"].dt.strftime("%Y-%m"))[["Importo", "Valore Attuale"]].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_grouped["Data"], y=df_grouped["Importo"], name="Investito", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df_grouped["Data"], y=df_grouped["Valore Attuale"], name="Valore Attuale", fill='tozeroy', line=dict(color="green")))
    fig.update_layout(title="Andamento PAC", xaxis_title="Data", yaxis_title="€", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nessuna operazione inserita ancora.")

# --- PORTAFOGLIO ---
st.markdown("### 📁 Profilo PAC")
if not df.empty:
    pac_summary = df.groupby("ETF")[["Importo", "Quantità"]].sum()
    pac_summary["% Allocazione"] = (pac_summary["Importo"] / totale_investito) * 100
    pac_summary["Prezzo Live"] = pac_summary.index.map(lambda x: prezzi_live.get(tickers_mapping.get(x, ""), 0.0))
    st.dataframe(pac_summary[["% Allocazione", "Prezzo Live"]])

    fig_alloc = go.Figure(data=[go.Pie(labels=pac_summary.index, values=pac_summary["% Allocazione"], hole=.4)])
    fig_alloc.update_layout(title="Distribuzione Portafoglio")
    st.plotly_chart(fig_alloc, use_container_width=True)

# --- OBIETTIVI ---
st.markdown("### 🎯 Obiettivi")
target_values = [100_000, 250_000, 500_000]
for target in target_values:
    progress = min(100, valore_attuale / target * 100)
    st.progress(progress / 100, text=f"Obiettivo €{target:,.0f} - {progress:.2f}%")

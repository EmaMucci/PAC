import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Dashboard PAC", layout="wide", page_icon="📈")

def load_data():
    try:
        return pd.read_csv("dati_pac.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Data", "ETF", "Versato", "Prezzo Acquisto", "Quantità"])

def save_data(df):
    df.to_csv("dati_pac.csv", index=False)

# Simboli compatibili Yahoo Finance
etf_mapping = {
    "SPY5L": "SPY5L.MI",
    "SWDA": "SWDA.L",
    "NSQE": "NSQE.DE"
}

prezzi_live = {}
for nome, ticker in etf_mapping.items():
    try:
        ticker_yf = yf.Ticker(ticker)
        prezzo = ticker_yf.history(period="1d")["Close"].iloc[-1]
        prezzi_live[nome] = round(prezzo, 2)
    except:
        prezzi_live[nome] = 0.0

# Sidebar di navigazione
pagina = st.sidebar.selectbox("Navigazione", ["Dashboard", "Aggiungi Operazione"])

if pagina == "Aggiungi Operazione":
    st.title("➕ Aggiungi Operazione al PAC")
    with st.form("form_op"):
        data = st.date_input("Data", value=datetime.today())
        etf = st.selectbox("ETF", list(etf_mapping.keys()))
        versato = st.number_input("Importo Versato (€)", min_value=0.0, step=1.0)
        prezzo = st.number_input("Prezzo di Acquisto", min_value=0.0, step=0.01)
        quantita = st.number_input("Quantità", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Aggiungi")
        if submitted:
            nuovo = pd.DataFrame([[data, etf, versato, prezzo, quantita]],
                                 columns=["Data", "ETF", "Versato", "Prezzo Acquisto", "Quantità"])
            df = load_data()
            df = pd.concat([df, nuovo], ignore_index=True)
            save_data(df)
            st.success("✅ Operazione aggiunta!")

else:
    st.title("📊 Dashboard PAC")
    df = load_data()

    if df.empty:
        st.warning("Non ci sono ancora dati. Aggiungi una operazione dal menu laterale.")
        st.stop()

    df["Valore Attuale"] = df.apply(lambda row: row["Quantità"] * prezzi_live.get(row["ETF"], 0.0), axis=1)
    totale_investito = df["Versato"].sum()
    valore_attuale = df["Valore Attuale"].sum()
    profitto = valore_attuale - totale_investito
    percentuale = (profitto / totale_investito * 100) if totale_investito else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Totale Investito", f"€ {totale_investito:,.2f}")
    col2.metric("📈 Valore Attuale", f"€ {valore_attuale:,.2f}")
    col3.metric("📊 Guadagno/Perdita", f"€ {profitto:,.2f}", f"{percentuale:.2f}%")

    # Andamento temporale
    df["Data"] = pd.to_datetime(df["Data"])
    df_line = df.groupby(["Data", "ETF"])["Versato"].sum().reset_index()
    fig1 = px.line(df_line, x="Data", y="Versato", color="ETF", title="Andamento Investimenti")
    st.plotly_chart(fig1, use_container_width=True)

    # Distribuzione ETF
    df_pie = df.groupby("ETF")["Valore Attuale"].sum().reset_index()
    fig2 = px.pie(df_pie, names="ETF", values="Valore Attuale", title="Distribuzione Portafoglio")
    st.plotly_chart(fig2, use_container_width=True)

    # Obiettivi dinamici
    st.subheader("🎯 Obiettivi di lungo termine")
    for target in [100_000, 250_000, 500_000]:
        progress = min(valore_attuale / target, 1.0)
        st.write(f"Obiettivo €{target:,.0f}")
        st.progress(progress)

# === SEZIONE PREZZI LIVE ETF ===
st.subheader("📊 Prezzi Live ETF")

etf_symbols = {
    "SPDR S&P 500 UCITS ETF": "SPY5L.MI",
    "iShares Core MSCI World UCITS ETF": "SWDA.L",
    "iShares NASDAQ 100 UCITS ETF EUR Hedged": "NSQE.DE"
}

cols = st.columns(3)

for i, (nome, simbolo) in enumerate(etf_symbols.items()):
    ticker = yf.Ticker(simbolo)
    try:
        prezzo = ticker.history(period="1d")["Close"].iloc[-1]
    except:
        prezzo = 0.0
    with cols[i]:
        st.metric(label=nome, value=f"{prezzo:.2f} €", delta="Live")

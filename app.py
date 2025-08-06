import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(layout="wide", page_title="Dashboard PAC")

# === CONFIG ===
ETF_LIST = [
    {"symbol": "SPY5L", "name": "SPDR S&P 500", "color": "green"},
    {"symbol": "SWDA.L", "name": "iShares MSCI World", "color": "blue"},
    {"symbol": "NSQE.DE", "name": "iShares Nasdaq 100", "color": "red"}
]
GOALS = [100_000, 250_000, 500_000]

# === Simulazione prezzi live (sostituibile con API reali) ===
def get_prices():
    return {
        "SPY5L": 630.09,
        "SWDA.L": 88.45,
        "NSQE.DE": 104.10
    }

# === Caricamento dati
data = pd.read_csv("dati_pac.csv")
data['Data'] = pd.to_datetime(data['Data'], format='%Y-%m-%d')

# === Prezzi
prezzi = get_prices()

# === Calcoli
etf_status = []
tot_investito = 0
valore_attuale = 0

for etf in ETF_LIST:
    df = data[data['Simbolo'] == etf['symbol']]
    quantità = df['Quantità'].sum()
    investito = df['Totale Investito'].sum()
    prezzo = prezzi[etf['symbol']]
    valore = quantità * prezzo
    guadagno = valore - investito
    allocazione = investito / data['Totale Investito'].sum() * 100

    etf_status.append({
        **etf,
        "quantità": quantità,
        "investito": investito,
        "valore": valore,
        "guadagno": guadagno,
        "allocazione": allocazione,
        "prezzo": prezzo
    })

    tot_investito += investito
    valore_attuale += valore

guadagno_tot = valore_attuale - tot_investito

# === Layout
st.title("📊 Dashboard PAC")
col1, col2, col3 = st.columns(3)
col1.metric("💸 Totale Investito", f"€{tot_investito:,.2f}")
col2.metric("📈 Valore Attuale", f"€{valore_attuale:,.2f}")
col3.metric("📈 Guadagno", f"€{guadagno_tot:,.2f}", delta=f"{(guadagno_tot/tot_investito)*100:.2f}%" if tot_investito > 0 else "")

# === Profilo PAC
st.subheader("📘 Profilo PAC")
for etf in etf_status:
    st.markdown(
        f"- **{etf['name']} ({etf['symbol']})** – Prezzo attuale: €{etf['prezzo']} – Allocazione: {etf['allocazione']:.2f}%"
    )

# === Grafico Allocazione
st.subheader("📈 Allocazione ETF")
fig1, ax1 = plt.subplots()
ax1.pie([e['allocazione'] for e in etf_status], labels=[e['symbol'] for e in etf_status], autopct='%1.1f%%', colors=[e['color'] for e in etf_status])
ax1.axis("equal")
st.pyplot(fig1)

# === Andamento
st.subheader("📆 Andamento nel tempo")
fig2, ax2 = plt.subplots()
for symbol in data['Simbolo'].unique():
    df_etf = data[data['Simbolo'] == symbol].groupby('Data').sum().cumsum().reset_index()
    ax2.plot(df_etf['Data'], df_etf['Totale Investito'], label=f"{symbol} Investito")
ax2.set_title("Investimenti cumulativi")
ax2.legend()
st.pyplot(fig2)

# === Obiettivi
st.subheader("🌟 Obiettivi PAC")
for goal in GOALS:
    perc = valore_attuale / goal * 100
    st.progress(min(perc, 100), text=f"Progresso verso €{goal:,.0f}: {perc:.2f}%")

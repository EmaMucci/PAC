import streamlit as st
import pandas as pd
import os
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt

# Configurazione iniziale Streamlit
st.set_page_config(page_title="Dashboard PAC", layout="wide")

# ========================
# DEFINIZIONE ETF + PREZZI LIVE
# ========================
etf_symbols = {
    "SPY5L": "SPY5L.MI",
    "SWDA.L": "SWDA.L",
    "NSQE.DE": "NSQE.DE"
}

def get_prezzi_live():
    prezzi = {}
    for nome, ticker in etf_symbols.items():
        try:
            data = yf.Ticker(ticker).info
            prezzi[nome] = data.get("regularMarketPrice", 0.0)
        except Exception:
            prezzi[nome] = 0.0
    return prezzi

prezzi_live = get_prezzi_live()

# ========================
# CARICAMENTO / CREAZIONE CSV
# ========================
csv_file = "transazioni_pac.csv"
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["Data", "ETF", "Importo", "Prezzo", "Quantità"])
    df.to_csv(csv_file, index=False)
else:
    df = pd.read_csv(csv_file)

# ========================
# FORM INSERIMENTO TRANSAZIONI
# ========================
st.sidebar.header("📥 Inserisci Nuova Transazione")
with st.sidebar.form("transazione_form"):
    data = st.date_input("Data", value=datetime.today())
    etf = st.selectbox("ETF", list(etf_symbols.keys()))
    importo = st.number_input("Importo Versato (€)", min_value=0.0, step=1.0)
    prezzo = st.number_input("Prezzo di Acquisto (€)", min_value=0.0, step=0.01)
    quantita = st.number_input("Quantità Acquistata", min_value=0.0, step=0.0001, format="%.4f")
    submitted = st.form_submit_button("Aggiungi")
    if submitted:
        nuova = pd.DataFrame([[data.strftime("%Y-%m-%d"), etf, importo, prezzo, quantita]],
                             columns=["Data", "ETF", "Importo", "Prezzo", "Quantità"])
        df = pd.concat([df, nuova], ignore_index=True)
        df.to_csv(csv_file, index=False)
        st.success("✅ Transazione aggiunta con successo!")

# ========================
# CALCOLI E AGGREGAZIONI
# ========================
df["Importo"] = df["Importo"].astype(float)
df["Quantità"] = df["Quantità"].astype(float)
df["Valore Attuale"] = df.apply(lambda row: row["Quantità"] * prezzi_live.get(row["ETF"], 0.0), axis=1)
df["Guadagno"] = df["Valore Attuale"] - df["Importo"]

totale_investito = df["Importo"].sum()
totale_valore = df["Valore Attuale"].sum()
totale_guadagno = totale_valore - totale_investito

# ========================
# HEADER + PREZZI LIVE
# ========================
st.title("📊 Dashboard PAC - Piano di Accumulo")
st.markdown("### Prezzi Live degli ETF")
cols = st.columns(3)
for i, (etf, prezzo) in enumerate(prezzi_live.items()):
    cols[i].metric(label=etf, value=f"{prezzo:.2f} €")

# ========================
# KPI CARDS
# ========================
st.markdown("### 📈 Panoramica Investimento")
col1, col2, col3 = st.columns(3)
col1.metric("Totale Investito", f"{totale_investito:.2f} €")
col2.metric("Valore Attuale", f"{totale_valore:.2f} €")
col3.metric("Guadagno/Perdita", f"{totale_guadagno:.2f} €", delta=f"{(totale_guadagno/totale_investito)*100:.2f}%")

# ========================
# GRAFICO A TORTA
# ========================
st.markdown("### 🧩 Suddivisione Portafoglio per ETF")
alloc = df.groupby("ETF")["Valore Attuale"].sum()
fig1, ax1 = plt.subplots()
ax1.pie(alloc, labels=alloc.index, autopct='%1.1f%%', startangle=90)
ax1.axis('equal')
st.pyplot(fig1)

# ========================
# BARRA PROGRESSI OBIETTIVI
# ========================
st.markdown("### 🎯 Obiettivi di Capitale")
obiettivi = [100_000, 250_000, 500_000]
for target in obiettivi:
    percentuale = min(totale_valore / target, 1.0)
    st.progress(percentuale, text=f"Obiettivo {target:,} € raggiunto: {percentuale*100:.2f}%")

# ========================
# DETTAGLIO TRANSAZIONI
# ========================
st.markdown("### 📄 Dettaglio Transazioni")
st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)

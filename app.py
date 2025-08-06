import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import streamlit as st

# ✅ Configurazione layout Streamlit
st.set_page_config(page_title="PAC Dashboard", layout="wide", initial_sidebar_state="expanded")

# ✅ Lista ETF e relativi ticker su Yahoo Finance
etf_info = {
    "SPDR S&P 500 UCITS ETF": "SPY5L.MI",
    "iShares Core MSCI World UCITS ETF": "SWDA.L",
    "iShares NASDAQ 100 UCITS ETF EUR Hedged": "NSQE.DE"
}

# ✅ Funzione per ottenere prezzi live da Yahoo Finance
def get_live_prices(tickers):
    prices = {}
    for name, ticker in tickers.items():
        try:
            ticker_data = yf.Ticker(ticker)
            prices[name] = ticker_data.info.get("regularMarketPrice", 0.0)
        except Exception:
            prices[name] = 0.0
    return prices

# ✅ Caricamento operazioni dal file CSV
def load_data():
    try:
        df = pd.read_csv("operazioni_pac.csv", parse_dates=["Data"])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Data", "ETF", "Importo", "Prezzo", "Quantità"])

# ✅ Caricamento dati
df = load_data()
prezzi_live = get_live_prices(etf_info)

# ✅ Calcolo valore attuale per ogni riga
df["Valore Attuale"] = df.apply(lambda row: row["Quantità"] * prezzi_live.get(row["ETF"], 0.0), axis=1)
df["Importo"] = df["Importo"].astype(float)
df["Guadagno"] = df["Valore Attuale"] - df["Importo"]

# ✅ KPI principali
totale_investito = df["Importo"].sum()
valore_attuale = df["Valore Attuale"].sum()
guadagno = valore_attuale - totale_investito

# ✅ Intestazione
st.markdown("<h1 style='text-align: center;'>💼 Dashboard PAC</h1>", unsafe_allow_html=True)

# ✅ Visualizzazione dei KPI in colonne
col1, col2, col3 = st.columns(3)
col1.metric("💰 Totale Investito", f"€{totale_investito:.2f}")
col2.metric("📊 Valore Attuale", f"€{valore_attuale:.2f}")
col3.metric("📈 Guadagno", f"€{guadagno:.2f}", delta=f"{(guadagno/totale_investito)*100:.2f}%" if totale_investito > 0 else "")

# ✅ Grafico a torta per asset allocation
st.subheader("📌 Allocazione Portafoglio")
allocation = df.groupby("ETF")["Importo"].sum()
fig1, ax1 = plt.subplots()
ax1.pie(allocation, labels=allocation.index, autopct='%1.1f%%', startangle=90)
ax1.axis('equal')
st.pyplot(fig1)

# ✅ Grafico andamento temporale
st.subheader("📈 Andamento PAC")
df_andamento = df.groupby("Data")[["Importo", "Valore Attuale"]].sum().sort_index()
fig2, ax2 = plt.subplots()
df_andamento.plot(ax=ax2)
st.pyplot(fig2)

# ✅ Obiettivi con progress bar
st.subheader("🎯 Obiettivi")
target_list = [100000, 250000, 500000]
for target in target_list:
    progress = min(valore_attuale / target, 1.0)
    st.write(f"Target: €{target:,.0f}")
    st.progress(progress)

# ✅ Prezzi live ETF
st.subheader("📢 Prezzi Live ETF")
for nome, ticker in etf_info.items():
    prezzo = prezzi_live.get(nome, 0.0)
    st.markdown(f"**{nome}** – €{prezzo:.2f}")

# ✅ Tabella operazioni registrate
st.subheader("📋 Operazioni registrate")
st.dataframe(df[["Data", "ETF", "Importo", "Prezzo", "Quantità"]].sort_values(by="Data"))

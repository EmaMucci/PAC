import streamlit as st
import pandas as pd
import yfinance as yf
import os
import csv
from datetime import datetime

st.set_page_config(page_title="Dashboard PAC", layout="wide")

# Percorso del file CSV
csv_file = "dati_pac.csv"

# Funzione per ottenere i prezzi live da Yahoo Finance
@st.cache_data(ttl=60)
def get_live_prices(etfs):
    prices = {}
    for etf in etfs:
        try:
            ticker = yf.Ticker(etf)
            data = ticker.history(period="1d")
            prices[etf] = round(data["Close"].iloc[-1], 2)
        except Exception as e:
            prices[etf] = 0.0
    return prices

# Pagine della dashboard
page = st.sidebar.radio("Vai a", ["📊 Dashboard", "➕ Aggiungi Operazione"])

# ETF supportati
etf_list = ["SPY5L", "SWDA.L", "NSQE.DE"]

if page == "📊 Dashboard":
    st.title("📊 Dashboard PAC")
    if not os.path.exists(csv_file) or os.stat(csv_file).st_size == 0:
        st.info("Nessuna operazione inserita ancora.")
    else:
        df = pd.read_csv(csv_file)
        prezzi_live = get_live_prices(etf_list)
        df["Valore Attuale"] = df.apply(lambda row: row["Quantità"] * prezzi_live.get(row["ETF"], 0.0), axis=1)

        totale_investito = df["Importo"].sum()
        valore_attuale = df["Valore Attuale"].sum()
        guadagno = valore_attuale - totale_investito

        # KPI
        col1, col2, col3 = st.columns(3)
        col1.metric("Totale Investito", f"€{totale_investito:.2f}")
        col2.metric("Valore Attuale", f"€{valore_attuale:.2f}")
        col3.metric("Guadagno", f"{'+' if guadagno >= 0 else ''}€{guadagno:.2f}")

        # Andamento
        df_grouped = df.groupby("Data").agg({"Importo": "sum", "Valore Attuale": "sum"}).cumsum().reset_index()
        st.subheader("📈 Andamento PAC")
        st.line_chart(df_grouped.set_index("Data"))

        # Profilo PAC
        st.subheader("🧾 Profilo PAC")
        pac_ratio = df.groupby("ETF")["Importo"].sum() / totale_investito * 100
        for etf, ratio in pac_ratio.items():
            st.write(f"{etf}: {ratio:.0f}% - Prezzo live: €{prezzi_live.get(etf, 0.0)}")

elif page == "➕ Aggiungi Operazione":
    st.title("➕ Aggiungi Operazione al PAC")
    with st.form("add_op"):
        data = st.date_input("📅 Data", value=datetime.today())
        etf = st.selectbox("📈 ETF", etf_list)
        importo = st.number_input("💸 Importo versato (€)", min_value=0.0, step=1.0)
        prezzo = st.number_input("📊 Prezzo di acquisto (€)", min_value=0.0, step=0.01)
        quantita = st.number_input("📦 Quantità acquistata", min_value=0.0, step=0.001)
        submitted = st.form_submit_button("💾 Salva operazione")

        if submitted:
            nuova_op = {
                "Data": data.strftime("%Y-%m-%d"),
                "ETF": etf,
                "Importo": importo,
                "Prezzo": prezzo,
                "Quantità": quantita
            }

            file_esiste = os.path.exists(csv_file)
            with open(csv_file, mode="a", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["Data", "ETF", "Importo", "Prezzo", "Quantità"])
                if not file_esiste or os.stat(csv_file).st_size == 0:
                    writer.writeheader()
                writer.writerow(nuova_op)

            st.success("✅ Operazione aggiunta correttamente.")

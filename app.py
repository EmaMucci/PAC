import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# === Funzioni utili ===
@st.cache_data
def load_data():
    try:
        return pd.read_csv("dati_pac.csv", parse_dates=["Data"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["Data", "ETF", "Importo", "Prezzo", "Quantità"])

def save_data(df):
    df.to_csv("dati_pac.csv", index=False)

def get_price_yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    try:
        response = requests.get(url).json()
        return response["quoteResponse"]["result"][0]["regularMarketPrice"]
    except:
        return 0.0

# === UI Principale ===
st.set_page_config(page_title="Dashboard PAC", layout="wide")
st.title("📊 Dashboard PAC")

# Menu di navigazione
page = st.sidebar.radio("Vai a", ["Dashboard", "➕ Aggiungi Operazione"])

# === Pagina: Aggiungi Operazione ===
if page == "➕ Aggiungi Operazione":
    st.header("➕ Inserisci un nuovo acquisto")
    with st.form("inserimento_form"):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data", value=datetime.today())
            etf = st.selectbox("ETF", ["SPY5L.MI", "SWDA.L", "CSNDX.SW"])
            prezzo = st.number_input("Prezzo di acquisto", min_value=0.0, step=0.01)
        with col2:
            importo = st.number_input("Importo versato (€)", min_value=0.0, step=1.0)
            quantita = st.number_input("Quantità acquistata", min_value=0.0, step=0.01)

        submitted = st.form_submit_button("Salva")
        if submitted:
            df = load_data()
            nuova_riga = pd.DataFrame([{
                "Data": data,
                "ETF": etf,
                "Importo": importo,
                "Prezzo": prezzo,
                "Quantità": quantita
            }])
            df = pd.concat([df, nuova_riga], ignore_index=True)
            save_data(df)
            st.success("✅ Operazione aggiunta con successo!")

# === Pagina: Dashboard ===
elif page == "Dashboard":
    st.header("📈 Andamento PAC")
    df = load_data()

    if df.empty:
        st.info("Nessuna operazione inserita ancora.")
    else:
        # Prezzi live
        prezzi_live = {
            "SPY5L.MI": get_price_yahoo("SPY5L.MI"),
            "SWDA.L": get_price_yahoo("SWDA.L"),
            "CSNDX.SW": get_price_yahoo("CSNDX.SW")
        }

        df["Valore Attuale"] = df.apply(lambda row: row["Quantità"] * prezzi_live.get(row["ETF"], 0.0), axis=1)
        totale_investito = df["Importo"].sum()
        valore_attuale = df["Valore Attuale"].sum()
        guadagno = valore_attuale - totale_investito
        rendimento = (guadagno / totale_investito) * 100 if totale_investito > 0 else 0

        # KPI
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Totale Investito", f"{totale_investito:,.2f} €")
        col2.metric("📈 Valore Attuale", f"{valore_attuale:,.2f} €")
        col3.metric("📊 Guadagno/Perdita", f"{guadagno:,.2f} €", f"{rendimento:.2f}%")

        # Obiettivi
        st.markdown("### 🎯 Obiettivi PAC")
        progress = valore_attuale
        st.progress(min(progress / 100000, 1.0), text="Obiettivo 100K €")
        st.progress(min(progress / 250000, 1.0), text="Obiettivo 250K €")
        st.progress(min(progress / 500000, 1.0), text="Obiettivo 500K €")

        # Grafico allocazione
        alloc = df.groupby("ETF")["Importo"].sum()
        fig, ax = plt.subplots()
        ax.pie(alloc, labels=alloc.index, autopct='%1.1f%%', startangle=90)
        ax.axis("equal")
        st.pyplot(fig)

        # Storico operazioni
        st.subheader("📜 Storico Operazioni")
        st.dataframe(df.sort_values("Data", ascending=False), use_container_width=True)

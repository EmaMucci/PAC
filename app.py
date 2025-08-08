# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD PAC – Streamlit (MVP)
# Funzioni:
#  - Prezzi live ETF (Yahoo Finance) con auto-refresh configurabile (slider)
#  - Inserimento transazioni dal frontend (niente Excel)
#  - KPI (Investito / Valore / PnL)
#  - Grafico andamento cumulato (Investito vs Valore attuale)
#  - Grafico allocazione portafoglio
#  - 3 Target (100k / 250k / 500k) con progress bar
# NOTE: su ETF europei Yahoo può dare prezzi ritardati o 0. Per realtime vero serve un provider WS.
# ─────────────────────────────────────────────────────────────────────────────

import os, csv
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG BASE APP
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="PAC Dashboard", layout="wide", page_icon="📈")

# Percorso file CSV (creato/aggiornato dall’app)
CSV_PATH = "transazioni_pac.csv"

# Mappatura ETF -> ticker Yahoo Finance
# ⚠️ Se un prezzo resta a 0.00, prova a cambiare ticker con uno più liquido/visibile su Yahoo.
TICKERS = {
    "SPY5L": "SPY5L.MI",   # SPDR S&P 500 UCITS (Borsa Italiana) – a volte ritardato su Yahoo
    "SWDA.L": "SWDA.L",    # iShares Core MSCI World UCITS (LSE)
    "NSQE.DE": "NSQE.DE",  # iShares Nasdaq 100 UCITS EUR Hedged (DE) – può dare 0 su Yahoo
}

# Obiettivi di lungo periodo
TARGETS = [100_000, 250_000, 500_000]

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-REFRESH UI (per sembrare “live” senza ricaricare manualmente)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    refresh_sec = st.slider("⏱️ Aggiorna ogni (secondi)", 1, 30, 1)
st_autorefresh(interval=refresh_sec * 1000, key="auto_refresh")

# (CSS rapido per tono scuro un po’ più “app-like”)
st.markdown("""
<style>
  .stMetric { background: #111; border-radius: 12px; padding: 12px; }
  .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FUNZIONI DI SUPPORTO: CSV + PREZZI
# ─────────────────────────────────────────────────────────────────────────────
def ensure_csv_exists():
    """Crea il file CSV con intestazione se non esiste o è vuoto."""
    if not os.path.exists(CSV_PATH) or os.stat(CSV_PATH).st_size == 0:
        with open(CSV_PATH, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Data","ETF","Importo","Prezzo","Quantità"])

@st.cache_data(ttl=10)
def load_df():
    """Carica le transazioni dal CSV (cache 10s)."""
    ensure_csv_exists()
    df = pd.read_csv(CSV_PATH)
    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"])
        for c in ["Importo","Prezzo","Quantità"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df

def append_tx(row):
    """Aggiunge una transazione in coda al CSV."""
    ensure_csv_exists()
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow(row)

@st.cache_data(ttl=5)
def get_live_prices():
    """
    Recupera i prezzi “live” da Yahoo (cache 5s).
    Usa fast_info.last_price (più rapido), fallback su ultimo close “1d”.
    """
    prices = {}
    for etf, ticker in TICKERS.items():
        try:
            tk = yf.Ticker(ticker)
            info = tk.fast_info
            px = float(info.get("last_price") or 0)
            if px == 0:  # Fallback se Yahoo non dà last_price per l’ETF
                hist = tk.history(period="1d")
                if not hist.empty:
                    px = float(hist["Close"].iloc[-1])
            prices[etf] = round(px, 4)
        except Exception:
            prices[etf] = 0.0
    return prices

# ─────────────────────────────────────────────────────────────────────────────
# HEADER + PREZZI LIVE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("## 📈 Dashboard PAC")

prices = get_live_prices()

price_cols = st.columns(3)
for i, etf in enumerate(TICKERS.keys()):
    price_cols[i].metric(f"{etf} (live)", f"€ {prices.get(etf,0):,.2f}")

st.caption("ℹ️ Prezzi via Yahoo Finance (demo). Per vero realtime ogni secondo: provider con WebSocket (es. Finnhub/Polygon/TwelveData).")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR: INSERIMENTO TRANSAZIONE (niente Excel 🎉)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ➕ Aggiungi operazione")
    d = st.date_input("Data", value=datetime.today())
    sym = st.selectbox("ETF", list(TICKERS.keys()))
    invested = st.number_input("Importo versato (€)", min_value=0.0, step=1.0)
    price_in = st.number_input("Prezzo di acquisto (€)", min_value=0.0, step=0.01)
    qty = st.number_input("Quantità", min_value=0.0, step=0.0001, format="%.4f")
    if st.button("Salva operazione"):
        append_tx([d.strftime("%Y-%m-%d"), sym, invested, price_in, qty])
        st.success("Operazione salvata.")
        st.experimental_rerun()  # ricarica per aggiornare KPI/grafici subito

# ─────────────────────────────────────────────────────────────────────────────
# KPI + CALCOLI
# ─────────────────────────────────────────────────────────────────────────────
df = load_df()

if df.empty:
    st.info("Nessuna operazione. Inseriscine una dalla sidebar.")
else:
    # Valore attuale riga per riga = Quantità * prezzo live del relativo ETF
    df["Valore Attuale"] = df.apply(lambda r: r["Quantità"] * prices.get(r["ETF"], 0.0), axis=1)

    tot_investito = float(df["Importo"].sum())
    valore_attuale = float(df["Valore Attuale"].sum())
    pnl = valore_attuale - tot_investito
    pnl_pct = (pnl / tot_investito * 100) if tot_investito > 0 else 0.0

    k1,k2,k3 = st.columns(3)
    k1.metric("💰 Totale investito", f"€ {tot_investito:,.2f}")
    k2.metric("📊 Valore attuale", f"€ {valore_attuale:,.2f}")
    k3.metric("📈 PnL", f"€ {pnl:,.2f}", f"{pnl_pct:.2f}%")

    st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # GRAFICO ANDAMENTO (Investito vs Valore attuale) – cumulato nel tempo
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### 📉 Andamento cumulato")
    series = (
        df.groupby("Data")[["Importo","Valore Attuale"]]
        .sum().cumsum().reset_index()
    )
    fig_line = px.area(
        series, x="Data", y=["Importo","Valore Attuale"],
        template="plotly_dark", labels={"value":"€","variable":"Serie"}
    )
    st.plotly_chart(fig_line, use_container_width=True, theme=None)

    # ─────────────────────────────────────────────────────────────────────────
    # ALLOCAZIONE PORTAFOGLIO (sul Valore Attuale)
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### 🧩 Allocazione portafoglio")
    alloc = df.groupby("ETF")["Valore Attuale"].sum().reset_index()
    fig_pie = px.pie(
        alloc, names="ETF", values="Valore Attuale",
        hole=0.45, template="plotly_dark"
    )
    st.plotly_chart(fig_pie, use_container_width=True, theme=None)

    # ─────────────────────────────────────────────────────────────────────────
    # TARGET (100k / 250k / 500k) – progress bar
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### 🎯 Obiettivi")
    for target in TARGETS:
        prog = min(1.0, (valore_attuale/target) if target else 0.0)
        st.progress(prog, text=f"€ {target:,.0f} – {prog*100:.2f}%")

    # ─────────────────────────────────────────────────────────────────────────
    # STORICO OPERAZIONI
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### 📜 Storico operazioni")
    st.dataframe(
        df.sort_values("Data", ascending=False),
        use_container_width=True
    )

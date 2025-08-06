import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.set_page_config(layout="wide", page_title="Dashboard PAC", initial_sidebar_state="collapsed")

# DARK MODE
st.markdown("""
    <style>
        body {
            background-color: #111111;
            color: #f0f0f0;
        }
        .stProgress > div > div > div > div {
            background-color: #00ccff;
        }
        .element-container {
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

ETF_LIST = [
    {"symbol": "SPY5L", "tv_symbol": "SPY", "name": "SPDR S&P 500", "color": "#00ccff"},
    {"symbol": "SWDA.L", "tv_symbol": "URTH", "name": "iShares MSCI World", "color": "#e67e22"},
    {"symbol": "NSQE.DE", "tv_symbol": "QQQ", "name": "iShares Nasdaq 100", "color": "#9b59b6"}
]
GOALS = [100_000, 250_000, 500_000]

@st.cache_data(ttl=60)
def get_tradingview_price(symbol):
    try:
        r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m")
        data = r.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return round(price, 2)
    except:
        return 0.0

data = pd.read_csv("dati_pac.csv")
data['Data'] = pd.to_datetime(data['Data'], format='%Y-%m-%d')

# Preleva prezzi live
prices = {etf['symbol']: get_tradingview_price(etf['tv_symbol']) for etf in ETF_LIST}

tot_investito = data['Totale Investito'].sum()
valore_attuale = sum(data[data['Simbolo']==etf['symbol']]['Quantità'].sum() * prices[etf['symbol']] for etf in ETF_LIST)
guadagno_tot = valore_attuale - tot_investito

# INTESTAZIONE
st.markdown("<h1 style='color:#00ccff;'>📊 DASHBOARD PAC</h1>", unsafe_allow_html=True)

# KPI
c1, c2, c3 = st.columns(3)
c1.metric("💸 Totale Investito", f"€{tot_investito:,.2f}")
c2.metric("📈 Valore Attuale", f"€{valore_attuale:,.2f}")
c3.metric("📊 Guadagno", f"€{guadagno_tot:,.2f}", delta=f"{(guadagno_tot/tot_investito)*100:.2f}%")

# PROFILO PAC
st.markdown("---")
st.markdown("### 🧾 Profilo PAC")
for etf in ETF_LIST:
    alloc = (data[data['Simbolo']==etf['symbol']]['Totale Investito'].sum()) / tot_investito * 100
    st.markdown(f"<b style='color:{etf['color']}'>{etf['name']} ({etf['symbol']})</b> — 💵 Prezzo live: €{prices[etf['symbol']]:.2f} — 🧮 Allocazione: {alloc:.1f}%", unsafe_allow_html=True)

# GRAFICO ALLOCAZIONE
st.markdown("---")
st.markdown("### 📊 Allocazione ETF")
fig1, ax1 = plt.subplots()
ax1.pie(
    [ (data[data['Simbolo']==etf['symbol']]['Totale Investito'].sum()/tot_investito)*100 for etf in ETF_LIST ],
    labels=[e['symbol'] for e in ETF_LIST], 
    autopct='%1.1f%%', 
    colors=[e['color'] for e in ETF_LIST]
)
ax1.axis("equal")
st.pyplot(fig1)

# GRAFICO ANDAMENTO
st.markdown("---")
st.markdown("### 📈 Andamento cumulativo")
fig2, ax2 = plt.subplots()
for etf in ETF_LIST:
    df_e = data[data['Simbolo']==etf['symbol']].groupby('Data')['Totale Investito'].sum().cumsum()
    ax2.plot(df_e.index, df_e.values, label=etf['symbol'], color=etf['color'])
ax2.set_facecolor("#222222")
fig2.patch.set_facecolor('#222222')
ax2.set_title("Investito cumulato per ETF", color='white')
ax2.tick_params(axis='x', colors='white')
ax2.tick_params(axis='y', colors='white')
ax2.legend()
st.pyplot(fig2)

# OBIETTIVI
st.markdown("---")
st.markdown("### 🎯 Obiettivi PAC")
for goal in GOALS:
    perc = valore_attuale / goal * 100
    st.write(f"Progresso verso €{goal:,}: {perc:.1f}%")
    st.progress(min(int(perc), 100))

# AGGIORNAMENTO AUTOMATICO
st.markdown("---")
st.markdown("🔁 I dati si aggiornano automaticamente ogni 60 secondi.")

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

st.set_page_config(page_title="SweetMomentum ELITE V3", layout="wide")
st.title("🚀 SweetMomentum ELITE V3 – 35‑Stock Scanner")

# Clear any old cache
st.cache_data.clear()

# 35 Stock List
default_stocks = ",".join([
    "ADANIENT.NS","CGPOWER.NS","BAJFINANCE.NS","ADANIGREEN.NS","MAZDOCK.NS",
    "HINDALCO.NS","CHOLAFIN.NS","HAL.NS","PFC.NS","BANKBARODA.NS",
    "SBIN.NS","TATAPOWER.NS","DLF.NS","TATAMOTORS.NS","VEDL.NS",
    "TRENT.NS","RECLTD.NS","LTIM.NS","BEL.NS","AXISBANK.NS",
    "SHRIRAMFIN.NS","TITAN.NS","BPCL.NS","ADANIPORTS.NS","DMART.NS",
    "VBL.NS","ICICIBANK.NS","KOTAKBANK.NS","TECHM.NS","SIEMENS.NS",
    "ASIANPAINT.NS","LT.NS","ICICIGI.NS","TATACONSUM.NS"
])
stocks_input = st.text_area(
    "📥 Enter comma‑separated NSE tickers:",
    value=default_stocks, height=120
)
tickers = [s.strip().upper() for s in stocks_input.split(",") if s.strip()]

results = []
progress = st.progress(0)
for i, symbol in enumerate(tickers):
    try:
        df = yf.download(symbol, period="5y", interval="1d", progress=False)
        if df.empty or "Close" not in df: continue
        df.dropna(inplace=True)
        df["RSI"] = RSIIndicator(df["Close"]).rsi()
        df["ATR"] = AverageTrueRange(
            high=df["High"], low=df["Low"], close=df["Close"]
        ).average_true_range()
        df.dropna(inplace=True)

        latest = df.iloc[-1]
        entry_price = latest["Close"]
        atr_val     = latest["ATR"]
        rsi_val     = latest["RSI"]

        if rsi_val < 30:
            signal = "🟢 BUY"
            sl     = round(entry_price - atr_val, 2)
            tgt    = round(entry_price + 3 * atr_val, 2)
        elif rsi_val > 70:
            signal = "🔴 SELL"
            sl     = round(entry_price + atr_val, 2)
            tgt    = round(entry_price - 3 * atr_val, 2)
        else:
            signal = "⚖️ HOLD"
            sl = tgt = None

        buys = df[df["RSI"] < 30]
        wins = sum(
            1 for dt, row in buys.iterrows()
            if dt + pd.Timedelta(days=5) in df.index
            and df.at[dt + pd.Timedelta(days=5), "Close"] > row["Close"]
        )
        win_rate = round(wins / len(buys) * 100, 2) if buys.size else 0

        if win_rate >= 85:
            results.append({
                "Type":    "Intraday" if signal=="🟢 BUY" else "Swing" if signal=="🔴 SELL" else "None",
                "Stock":   symbol,
                "Entry":   f"₹{entry_price:.2f}",
                "SL":      f"₹{sl:.2f}" if sl else "—",
                "Target":  f"₹{tgt:.2f}" if tgt else "—",
                "RR":      f"1:{round((tgt-entry_price)/(entry_price-sl),2) if sl and tgt else '-'}",
                "WinRate": f"{win_rate}%"
            })
    except Exception:
        pass
    progress.progress((i+1)/len(tickers))

if results:
    for r in results:
        st.markdown(f"""
        ---
        **Type:** {r['Type']}  
        **Stock:** {r['Stock']}  
        **Entry:** {r['Entry']}  
        **SL:** {r['SL']}  
        **Target:** {r['Target']}  
        **RR:** {r['RR']}  
        **Win Rate:** {r['WinRate']}
        """)
else:
    st.warning("😔 No stocks met the ≥85% win‑rate criterion.")

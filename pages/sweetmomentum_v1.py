import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

st.set_page_config(page_title="SweetMomentum ELITE V3", layout="wide")
st.title("🚀 SweetMomentum ELITE V3 – 35‑Stock Scanner")

# 35 Stock List (comma‑separated by default)
default_stocks = ",".join([
    "ADANIENT.NS","CGPOWER.NS","BAJFINANCE.NS","ADANIGREEN.NS","MAZDOCK.NS",
    "HINDALCO.NS","CHOLAFIN.NS","HAL.NS","PFC.NS","BANKBARODA.NS",
    "SBIN.NS","ADANIENT.NS","TATAPOWER.NS","DLF.NS","TATAMOTORS.NS",
    "VEDL.NS","TRENT.NS","RECLTD.NS","LTIM.NS","BEL.NS",
    "AXISBANK.NS","SHRIRAMFIN.NS","TITAN.NS","BPCL.NS","ADANIPORTS.NS",
    "DMART.NS","VBL.NS","ICICIBANK.NS","KOTAKBANK.NS","TECHM.NS",
    "SIEMENS.NS","ASIANPAINT.NS","LT.NS","ICICIGI.NS","TATACONSUM.NS"
])
stocks_input = st.text_area("📥 Enter comma‑separated NSE tickers:", value=default_stocks, height=120)
tickers = [s.strip().upper() for s in stocks_input.split(",") if s.strip()]

# Scan
results = []
progress = st.progress(0)
for i, symbol in enumerate(tickers):
    try:
        df = yf.download(symbol, period="5y", interval="1d", progress=False)
        if df.empty or "Close" not in df:
            continue
        df.dropna(inplace=True)

        # Indicators
        df["RSI"] = RSIIndicator(df["Close"]).rsi()
        df["ATR"] = AverageTrueRange(
            high=df["High"], low=df["Low"], close=df["Close"]
        ).average_true_range()
        df.dropna(inplace=True)

        latest = df.iloc[-1]
        entry_price = latest["Close"]
        atr_val     = latest["ATR"]
        rsi_val     = latest["RSI"]

        # Signal
        if rsi_val < 30:
            signal = "🟢 BUY"
            sl     = round(entry_price - atr_val, 2)
            tgt    = round(entry_price + 2 * atr_val, 2)
        elif rsi_val > 70:
            signal = "🔴 SELL"
            sl     = round(entry_price + atr_val, 2)
            tgt    = round(entry_price - 2 * atr_val, 2)
        else:
            signal = "⚖️ HOLD"
            sl = tgt = None

        # Backtest (5‑day forward on BUYs only)
        buys = df[df["RSI"] < 30]
        wins = 0
        for dt, row in buys.iterrows():
            exit_dt = dt + pd.Timedelta(days=5)
            if exit_dt in df.index and df.at[exit_dt, "Close"] > row["Close"]:
                wins += 1
        win_rate = round(wins / len(buys) * 100, 2) if len(buys) else 0

        # Filter ≥85%
        if win_rate >= 85:
            results.append({
                "Ticker":   symbol,
                "Signal":   signal,
                "Entry":    round(entry_price,2),
                "SL":       sl,
                "Target":   tgt,
                "RSI":      round(rsi_val,2),
                "Win Rate": f"{win_rate}%",
            })
    except Exception:
        pass
    progress.progress((i+1)/len(tickers))

# Display
if results:
    st.success("🔥 High‑Probability Stocks (Win Rate ≥85%)")
    df_res = pd.DataFrame(results)
    st.dataframe(df_res)
else:
    st.warning("😔 No stocks met the ≥85% win‑rate criterion.")

# Chart for selected
sel = st.selectbox("🔍 Show charts for:", [r["Ticker"] for r in results] if results else [])
if sel:
    df2 = yf.download(sel, period="6mo", interval="1d", progress=False)
    df2.dropna(inplace=True)
    df2["RSI"] = RSIIndicator(df2["Close"]).rsi()
    df2["ATR"] = AverageTrueRange(df2["High"], df2["Low"], df2["Close"]).average_true_range()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df2.index, open=df2["Open"], high=df2["High"],
        low=df2["Low"], close=df2["Close"], name="Price"
    ))
    fig.update_layout(title=f"{sel} Price Chart", height=350)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("RSI & ATR")
    st.line_chart(df2[["RSI","ATR"]])

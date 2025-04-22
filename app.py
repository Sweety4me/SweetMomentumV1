import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

st.set_page_config(page_title="SweetMomentum ELITE V3", layout="wide")
st.title("💘 SweetMomentum ELITE V3 – 35‑Stock Scanner")

# Default 35 stocks
default_stocks = ",".join([
    "ADANIENT.NS","CGPOWER.NS","BAJFINANCE.NS","ADANIGREEN.NS","MAZDOCK.NS",
    "HINDALCO.NS","CHOLAFIN.NS","HAL.NS","PFC.NS","BANKBARODA.NS",
    "SBIN.NS","TATAPOWER.NS","DLF.NS","TATAMOTORS.NS","VEDL.NS",
    "TRENT.NS","RECLTD.NS","LTIM.NS","BEL.NS","AXISBANK.NS",
    "SHRIRAMFIN.NS","TITAN.NS","BPCL.NS","ADANIPORTS.NS","DMART.NS",
    "VBL.NS","ICICIBANK.NS","KOTAKBANK.NS","TECHM.NS","SIEMENS.NS",
    "ASIANPAINT.NS","LT.NS","ICICIGI.NS","TATACONSUM.NS","HDFCBANK.NS"
])
stocks_input = st.text_area("📥 Enter comma‑separated NSE tickers:", value=default_stocks, height=120)
tickers = [s.strip().upper() for s in stocks_input.split(",") if s.strip()]

results = []
progress = st.progress(0)

for i, symbol in enumerate(tickers):
    try:
        df = yf.download(symbol, period="5y", interval="1d", progress=False)
        if df.empty or "Close" not in df:
            continue
        df.dropna(inplace=True)

        df["RSI"] = RSIIndicator(df["Close"]).rsi()
        df["ATR"] = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"]).average_true_range()
        df.dropna(inplace=True)

        latest = df.iloc[-1]
        entry = round(latest["Close"], 2)
        atr = latest["ATR"]
        rsi = latest["RSI"]

        # Generate signal
        if rsi < 30:
            signal = "🟢 BUY"
            sl = round(entry - atr, 2)
            tgt = round(entry + 2 * atr, 2)
        elif rsi > 70:
            signal = "🔴 SELL"
            sl = round(entry + atr, 2)
            tgt = round(entry - 2 * atr, 2)
        else:
            signal = "⚖️ HOLD"
            sl = tgt = None

        # Backtest Buy signals
        buys = df[df["RSI"] < 30]
        wins = 0
        for dt, row in buys.iterrows():
            future_dt = dt + pd.Timedelta(days=5)
            if future_dt in df.index and df.at[future_dt, "Close"] > row["Close"]:
                wins += 1
        win_rate = round(wins / len(buys) * 100, 2) if len(buys) else 0

        if win_rate >= 85:
            results.append({
                "Ticker": symbol,
                "Signal": signal,
                "Entry": entry,
                "SL": sl,
                "Target": tgt,
                "RSI": round(rsi, 2),
                "Win Rate": f"{win_rate}%",
            })
    except Exception:
        pass
    progress.progress((i + 1) / len(tickers))

# Show table
if results:
    st.success("🔥 High‑Probability Stocks (Win Rate ≥85%)")
    st.dataframe(pd.DataFrame(results))
else:
    st.warning("😔 No stocks met the ≥85% win‑rate criterion.")

# Show chart for selected stock
selected = st.selectbox("🔍 Show charts for:", [r["Ticker"] for r in results] if results else [])
if selected:
    df = yf.download(selected, period="6mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    df["RSI"] = RSIIndicator(df["Close"]).rsi()
    df["ATR"] = AverageTrueRange(df["High"], df["Low"], df["Close"]).average_true_range()

    # Candlestick chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Candles"
    ))
    fig.update_layout(title=f"{selected} Price Chart", height=350)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 RSI & ATR")
    st.line_chart(df[["RSI", "ATR"]])

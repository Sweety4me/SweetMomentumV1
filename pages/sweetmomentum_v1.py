import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

st.set_page_config(page_title="SweetMomentum V2", layout="wide")
st.title("🚀 SweetMomentum V2 – Breakout Screener")

symbol = st.text_input(
    "📌 Enter Stock Symbol (e.g. RELIANCE or RELIANCE.NS)",
    value="RELIANCE.NS"
).upper()
if not symbol.endswith(".NS"):
    symbol += ".NS"

if symbol:
    try:
        data = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if data.empty:
            st.error("No data found for this symbol.")
            st.stop()

        st.success(f"📈 Data loaded for {symbol}")
        close = data["Close"]
        high  = data["High"]
        low   = data["Low"]

        rsi = RSIIndicator(close).rsi()
        atr = AverageTrueRange(high, low, close).average_true_range()
        data[ "RSI"] = rsi
        data["ATR"] = atr
        data.dropna(inplace=True)

        latest = data.iloc[-1]
        rsi_val = latest["RSI"]
        atr_val = latest["ATR"]

        # Strategy Logic
        if rsi_val > 70:
            signal  = "🔴 SELL"
        elif rsi_val < 30:
            signal  = "🟢 BUY"
        else:
            signal  = "⚖️ HOLD"

        st.subheader("💹 Latest Trade Details")
        st.markdown(f"""
        • **Signal:** {signal}  
        • **RSI (14):** {rsi_val:.2f}  
        • **ATR (14):** {atr_val:.2f}
        """)

        # Simple backtest on BUY signals
        buys  = data[data["RSI"] < 30]
        wins  = 0
        for dt, row in buys.iterrows():
            exit_dt = dt + pd.Timedelta(days=5)
            if exit_dt in data.index and data.at[exit_dt, "Close"] > row["Close"]:
                wins += 1
        win_rate = round(wins / len(buys) * 100, 2) if len(buys) else 0

        st.subheader("📊 5D Backtest Win Rate")
        st.metric("Win Rate", f"{win_rate}%")

        # Optional charts
        if st.checkbox("📉 Show Charts"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=close, mode="lines", name="Price"))
            fig.add_trace(go.Scatter(x=data.index, y=rsi, mode="lines", name="RSI"))
            fig.update_layout(height=400, title="Price & RSI")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"🔥 Unexpected error: {e}")

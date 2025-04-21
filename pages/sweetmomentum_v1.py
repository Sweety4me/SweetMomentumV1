import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

st.set_page_config(page_title="SweetMomentum V2", layout="wide")
st.title("🚀 SweetMomentum V2 – Breakout Screener")

symbol = st.text_input("📌 Enter Stock Symbol (e.g. RELIANCE or RELIANCE.NS)", value="RELIANCE.NS").upper()
if not symbol.endswith(".NS"):
    symbol += ".NS"

try:
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if data.empty:
        st.error("No data found for this symbol.")
        st.stop()

    st.success(f"📈 Data loaded for {symbol}")

    # Ensure values are 1D arrays
    close = data["Close"].values.flatten()
    high = data["High"].values.flatten()
    low = data["Low"].values.flatten()

    # Re-create DataFrame for indicator operations
    df = pd.DataFrame({
        "Date": data.index,
        "Close": close,
        "High": high,
        "Low": low
    })
    df.set_index("Date", inplace=True)

    # Indicators
    df["RSI"] = RSIIndicator(close=df["Close"]).rsi()
    df["ATR"] = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"]).average_true_range()
    df.dropna(inplace=True)

    latest = df.iloc[-1]
    rsi_val = latest["RSI"]
    atr_val = latest["ATR"]

    # Signal logic
    if rsi_val > 70:
        signal = "🔴 SELL"
    elif rsi_val < 30:
        signal = "🟢 BUY"
    else:
        signal = "⚖️ HOLD"

    st.subheader("💹 Latest Trade Details")
    st.markdown(f"""
    • **Signal:** {signal}  
    • **RSI (14):** {rsi_val:.2f}  
    • **ATR (14):** {atr_val:.2f}
    """)

    # 5D backtest for RSI < 30 BUY
    buys = df[df["RSI"] < 30]
    wins = 0
    for dt, row in buys.iterrows():
        exit_dt = dt + pd.Timedelta(days=5)
        if exit_dt in df.index and df.at[exit_dt, "Close"] > row["Close"]:
            wins += 1
    win_rate = round((wins / len(buys)) * 100, 2) if len(buys) else 0

    st.subheader("📊 5D Backtest Win Rate")
    st.metric("Win Rate", f"{win_rate}%")

    # Plot chart
    if st.checkbox("📉 Show Charts"):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Price"))
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"))
        fig.update_layout(height=400, title="Price & RSI")
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"🔥 Error occurred: {e}")

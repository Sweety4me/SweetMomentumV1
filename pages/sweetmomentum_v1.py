import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# ── Streamlit page setup ─────────────────────────────────────────────────────
st.set_page_config(page_title="SweetMomentum V1", layout="centered")
st.title("🚀 SweetMomentum V1 – Breakout Screener")

# ── User Input ────────────────────────────────────────────────────────────────
symbol_input = st.text_input(
    "📌 Enter Stock Symbol (e.g. RELIANCE or RELIANCE.NS)",
    value="RELIANCE.NS",
).strip().upper()
if symbol_input and not symbol_input.endswith(".NS"):
    symbol = symbol_input + ".NS"
else:
    symbol = symbol_input

# ── Fetch Data ────────────────────────────────────────────────────────────────
if symbol:
    with st.spinner(f"🔄 Fetching data for {symbol}..."):
        try:
            data = yf.download(symbol, period="5y", interval="1d", progress=False)
        except Exception as e:
            st.error(f"📡 Data fetch failed: {e}")
            st.stop()

    if data.empty or "Close" not in data.columns:
        st.error("❌ No data found. Please check the symbol.")
        st.stop()

    st.success(f"📈 Data loaded for {symbol}")

    # ── Indicator Calculations ───────────────────────────────────────────────
    close = data["Close"].astype(float)
    # Ensure 'close' is a 1D series for RSIIndicator
    rsi = RSIIndicator(close).rsi().dropna()
    data["RSI"] = rsi
    # ATR
    atr = AverageTrueRange(
        high=data["High"],
        low=data["Low"],
        close=close,
        window=14,
    ).average_true_range().dropna()
    data["ATR14"] = atr

    latest = data.iloc[-1]
    price  = latest["Close"]
    latest_rsi = latest["RSI"]
    latest_atr = latest["ATR14"]

    # ── Trade Signal Logic ─────────────────────────────────────────────────────
    if latest_rsi < 30:
        signal = "📈 BUY"
        entry  = price
        sl     = round(entry - latest_atr, 2)
        target = round(entry + latest_atr * 2, 2)  # RR 1:2
    elif latest_rsi > 70:
        signal = "📉 SELL"
        entry  = price
        sl     = round(entry + latest_atr, 2)
        target = round(entry - latest_atr * 2, 2)
    else:
        signal = "⚖️ HOLD"
        entry = sl = target = None

    # ── Simple Backtest ────────────────────────────────────────────────────────
    def backtest_momentum(df, rsi_low=30, rsi_high=70):
        trades = []
        for i in range(len(df) - 1):
            if df["RSI"].iloc[i] < rsi_low:
                # Simulate buy next day
                entry_price = df["Close"].iloc[i + 1]
                # Exit when RSI > rsi_high or after 10 days
                exit_price = entry_price
                for j in range(i + 2, min(i + 12, len(df))):
                    if df["RSI"].iloc[j] > rsi_high:
                        exit_price = df["Close"].iloc[j]
                        break
                trades.append(exit_price > entry_price)
        return round(sum(trades) / len(trades) * 100, 2) if trades else 0.0

    win_rate = backtest_momentum(data)

    # ── Display Results ─────────────────────────────────────────────────────────
    st.subheader("💹 Latest Trade Details")
    st.write(f"• **Signal:** {signal}")
    if entry:
        st.write(f"• **Entry:** ₹{entry:.2f}")
        st.write(f"• **Stop‑Loss:** ₹{sl:.2f}")
        st.write(f"• **Target:** ₹{target:.2f}")
    st.write(f"• **RSI (14):** {latest_rsi:.2f}")
    st.write(f"• **ATR (14):** {latest_atr:.2f}")

    st.subheader("📊 5Y Backtest Performance")
    st.metric("Win Rate", f"{win_rate}%")

    # ── (Optional) Price & RSI Chart ───────────────────────────────────────────
    with st.expander("Show Price & RSI Charts"):
        st.line_chart(data[["Close", "RSI"]])

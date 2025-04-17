import streamlit as st
import yfinance as yf
import pandas as pd

# ── Indicator Helpers ─────────────────────────────────────────────────────────
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"]
    low  = df["Low"]
    prev_close = df["Close"].shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return atr

# ── Streamlit Page Setup ──────────────────────────────────────────────────────
st.set_page_config(page_title="SweetMomentum V1", layout="centered")
st.title("🚀 SweetMomentum V1 – Breakout Screener")

# ── User Input ────────────────────────────────────────────────────────────────
symbol_input = st.text_input(
    "📌 Enter Stock Symbol (e.g. RELIANCE or RELIANCE.NS)",
    value="RELIANCE.NS",
).strip().upper()
symbol = symbol_input if symbol_input.endswith(".NS") else symbol_input + ".NS"

# ── Fetch Data ────────────────────────────────────────────────────────────────
if symbol:
    with st.spinner(f"🔄 Fetching 5Y data for {symbol}..."):
        try:
            data = yf.download(symbol, period="5y", interval="1d", progress=False)
        except Exception as e:
            st.error(f"📡 Data fetch failed: {e}")
            st.stop()

    if data.empty or "Close" not in data.columns:
        st.error("❌ No data found. Check the symbol and try again.")
        st.stop()

    st.success(f"📈 Data loaded for {symbol}")

    # ── Clean MultiIndex Columns ──────────────────────────────────────────────
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # ── Calculate Indicators ───────────────────────────────────────────────────
    data["RSI"]  = compute_rsi(data["Close"], 14)
    data["ATR14"]= compute_atr(data, 14)
    data.dropna(inplace=True)

    latest = data.iloc[-1]
    price      = latest["Close"]
    latest_rsi = latest["RSI"]
    latest_atr = latest["ATR14"]

    # ── Trade Signal Logic ─────────────────────────────────────────────────────
    if latest_rsi < 30:
        signal = "📈 BUY"
        entry  = price
        sl     = round(entry - latest_atr, 2)
        target = round(entry + latest_atr * 2, 2)
    elif latest_rsi > 70:
        signal = "📉 SELL"
        entry  = price
        sl     = round(entry + latest_atr, 2)
        target = round(entry - latest_atr * 2, 2)
    else:
        signal = "⚖️ HOLD"
        entry = sl = target = None

    # ── Backtest Logic ─────────────────────────────────────────────────────────
    def backtest_momentum(df, low=30, high=70):
        wins = 0; total = 0
        for i in range(len(df) - 1):
            if df["RSI"].iat[i] < low:
                entry_p = df["Close"].iat[i + 1]
                # exit when RSI crosses above high
                for j in range(i + 2, min(i + 12, len(df))):
                    if df["RSI"].iat[j] > high:
                        if df["Close"].iat[j] > entry_p: wins += 1
                        total += 1
                        break
        return round((wins / total) * 100, 2) if total else 0.0

    win_rate = backtest_momentum(data)

    # ── Display Results ─────────────────────────────────────────────────────────
    st.subheader("💹 Latest Trade Details")
    st.write(f"• **Signal:** {signal}")
    if entry is not None:
        st.write(f"• **Entry:** ₹{entry:.2f}")
        st.write(f"• **Stop‑Loss:** ₹{sl:.2f}")
        st.write(f"• **Target:** ₹{target:.2f}")
    st.write(f"• **RSI (14):** {latest_rsi:.2f}")
    st.write(f"• **ATR (14):** {latest_atr:.2f}")

    st.subheader("📊 5Y Backtest Win Rate")
    st.metric("Win Rate", f"{win_rate}%")

    # ── Optional Charts ────────────────────────────────────────────────────────
    with st.expander("Show Price, RSI & ATR Charts"):
        st.line_chart(data[["Close", "RSI", "ATR14"]])

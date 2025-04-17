import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

st.set_page_config(page_title="SweetMomentum V1", layout="centered")
st.title("🚀 SweetMomentum V1 – Breakout Screener")

symbol = st.text_input("📌 Enter Stock Symbol (e.g. RELIANCE or RELIANCE.NS)", value="RELIANCE.NS").upper()

# Forcefully fix to NSE
if symbol and not symbol.endswith(".NS"):
    symbol += ".NS"

if symbol:
    try:
        data = yf.download(symbol, period="6mo", interval="1d")

        if not data.empty and "Close" in data.columns:
            st.success(f"📈 Showing data for {symbol}")

            try:
                # 💥 THE FIX: Ensure it's a 1D Series
                close_series = data["Close"].astype(float).copy()
                if len(close_series.shape) > 1:
                    close_series = close_series.squeeze()  # Flatten if needed

                rsi = RSIIndicator(close=close_series)
                data["momentum"] = rsi.rsi()
                data.dropna(inplace=True)

                # Plotting
                st.line_chart(data[["Close"]])
                st.line_chart(data[["momentum"]])

                latest = data.iloc[-1]
                st.info(f"""
                🔎 **Latest Close**: ₹{latest['Close']:.2f}  
                ⚡ **Momentum RSI**: {latest['momentum']:.2f}
                """)

                if latest["momentum"] > 70:
                    st.success("✅ Strong momentum! Possible breakout 🔥")
                elif latest["momentum"] < 30:
                    st.warning("⚠️ Weak momentum! Possible dip 💧")
                else:
                    st.write("📊 Neutral zone. Wait for confirmation.")

            except Exception as calc_err:
                st.error(f"🥺 RSI calculation error: {calc_err}")

        else:
            st.error("❌ No data found or 'Close' column missing.")

    except Exception as fetch_err:
        st.error(f"📡 Data fetch failed: {fetch_err}")

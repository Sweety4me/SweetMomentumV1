import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.title("🚀 SweetMomentum V1 – Breakout Screener")

symbol = st.text_input("📌 Enter Stock Symbol (e.g. RELIANCE.NS)", value="RELIANCE.NS")

if symbol:
    data = yf.download(symbol, period="6mo", interval="1d")
    if not data.empty:
        st.success(f"Showing data for {symbol}")

        # Add momentum indicator
        data["momentum"] = ta.momentum.RSIIndicator(data["Close"]).rsi()

        st.line_chart(data[["Close", "momentum"]])
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
    else:
        st.error("No data found for symbol.")

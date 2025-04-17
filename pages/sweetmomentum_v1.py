import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

st.set_page_config(page_title="SweetMomentum V2", layout="wide")
st.title("🚀 SweetMomentum V2 – Breakout Screener")

symbol = st.text_input("📌 Enter Stock Symbol (e.g. RELIANCE or RELIANCE.NS)", value="RELIANCE.NS").upper()
if not symbol.endswith('.NS'):
    symbol += '.NS'

if symbol:
    try:
        data = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if not data.empty:
            st.success(f"📈 Data loaded for {symbol}")
            close = data['Close']
            high = data['High']
            low = data['Low']

            rsi = RSIIndicator(close).rsi()
            atr = AverageTrueRange(high, low, close).average_true_range()

            data['RSI'] = rsi
            data['ATR'] = atr

            latest = data.iloc[-1]
            rsi_val = latest['RSI']
            atr_val = latest['ATR']

            # Strategy Logic
            if rsi_val > 70:
                signal = "🔴 SELL"
                strategy = "Swing"
            elif rsi_val < 30:
                signal = "🟢 BUY"
                strategy = "Swing"
            else:
                signal = "⚖️ HOLD"
                strategy = "Swing"

            st.subheader("💹 Latest Trade Details")
            st.markdown(f"""
            • Signal: {signal}  
            • RSI (14): {rsi_val:.2f}  
            • ATR (14): {atr_val:.2f}  
            • Strategy: `{strategy}`
            """)

            # Backtest win rate (simple)
            buy_signals = data[data['RSI'] < 30]
            sell_signals = data[data['RSI'] > 70]
            total_signals = len(buy_signals) + len(sell_signals)

            wins = 0
            for idx in buy_signals.index:
                if idx + pd.Timedelta(days=5) in data.index:
                    if data.loc[idx + pd.Timedelta(days=5), 'Close'] > data.loc[idx, 'Close']:
                        wins += 1

            win_rate = (wins / len(buy_signals)) * 100 if len(buy_signals) > 0 else 0

            st.subheader("📊 5D Backtest Win Rate (BUY signals only)")
            st.metric("Win Rate", f"{win_rate:.2f}%" if total_signals > 0 else "N/A")

            # Show chart
            if st.checkbox("📉 Show Price, RSI & ATR Charts"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data.index, y=close, mode='lines', name='Price'))
                fig.update_layout(title="Stock Price", xaxis_title="Date", yaxis_title="Price", height=300)
                st.plotly_chart(fig, use_container_width=True)

                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI'))
                fig2.update_layout(title="RSI (14)", xaxis_title="Date", yaxis_title="RSI", height=300)
                st.plotly_chart(fig2, use_container_width=True)

                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=data.index, y=data['ATR'], mode='lines', name='ATR'))
                fig3.update_layout(title="ATR (14)", xaxis_title="Date", yaxis_title="ATR", height=300)
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.error("No data found for this symbol.")
    except Exception as e:
        st.error(f"🥺 Error: {str(e)}")

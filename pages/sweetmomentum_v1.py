import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import matplotlib.pyplot as plt
import plotly.graph_objs as go

st.set_page_config(page_title="SweetMomentum V2", layout="centered")
st.title("SweetMomentum V2 – Breakout Screener")

symbol = st.text_input("\ud83d\udccc Enter Stock Symbol (e.g. RELIANCE or RELIANCE.NS)", "RELIANCE.NS")
symbol = symbol.upper().strip()

if symbol:
    try:
        df = yf.download(symbol, period="6mo", interval="1d")
        if df.empty:
            st.warning("No data found. Please check the stock symbol.")
        else:
            st.markdown(f"### \ud83d\udcc8 Data loaded for `{symbol}`")

            df.dropna(inplace=True)
            df['RSI'] = RSIIndicator(df['Close']).rsi()
            df['ATR'] = AverageTrueRange(df['High'], df['Low'], df['Close']).average_true_range()
            latest_close = df['Close'].iloc[-1]
            latest_rsi = round(df['RSI'].iloc[-1], 2)
            latest_atr = round(df['ATR'].iloc[-1], 2)

            # Signal logic
            if latest_rsi < 30:
                signal = "🔓 BUY"
                strategy_type = "Swing"
            elif latest_rsi > 70:
                signal = "❌ SELL"
                strategy_type = "Swing"
            else:
                signal = "⚖️ HOLD"
                strategy_type = "Neutral"

            # Backtesting logic (simple RSI-based swing strategy)
            def swing_backtest(data, rsi_buy=30, rsi_sell=70, target_pct=0.05, stoploss_pct=0.025):
                data = data.copy()
                data['RSI'] = RSIIndicator(data['Close']).rsi()
                data.dropna(inplace=True)

                trades = []
                in_trade = False
                entry_price = 0
                entry_date = ""

                for i in range(1, len(data)):
                    row = data.iloc[i]
                    prev_row = data.iloc[i - 1]

                    if not in_trade:
                        if prev_row['RSI'] < rsi_buy:
                            entry_price = row['Open']
                            entry_date = row.name
                            in_trade = True
                    else:
                        high = row['High']
                        low = row['Low']
                        target_price = entry_price * (1 + target_pct)
                        stoploss_price = entry_price * (1 - stoploss_pct)

                        if high >= target_price:
                            trades.append({'entry': entry_date, 'exit': row.name, 'result': 'win'})
                            in_trade = False
                        elif low <= stoploss_price:
                            trades.append({'entry': entry_date, 'exit': row.name, 'result': 'loss'})
                            in_trade = False

                df_trades = pd.DataFrame(trades)
                win_rate = 0
                if not df_trades.empty:
                    win_rate = round(100 * len(df_trades[df_trades['result'] == 'win']) / len(df_trades), 2)
                return win_rate

            win_rate = swing_backtest(df)

            # Display output
            st.markdown(f"""
                ### 📉 Latest Trade Details
                • Signal: {signal}

                • RSI (14): {latest_rsi}

                • ATR (14): {latest_atr}

                • Strategy Type: **{strategy_type}**

                ### 📊 5M Backtest Win Rate
                **Win Rate**: `{win_rate}%`
            """)

            # Optional chart toggle
            if st.checkbox("Show Price, RSI & ATR Charts"):
                st.subheader("Price Chart")
                fig_price = go.Figure(data=[go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'])])
                st.plotly_chart(fig_price, use_container_width=True)

                st.subheader("RSI Chart")
                st.line_chart(df['RSI'])

                st.subheader("ATR Chart")
                st.line_chart(df['ATR'])

    except Exception as e:
        st.error(f"\ud83d\ude97 Error: {e}")

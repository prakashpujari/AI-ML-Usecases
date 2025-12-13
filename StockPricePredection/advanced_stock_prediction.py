import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objs as go
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import requests
from bs4 import BeautifulSoup

# Page config
st.set_page_config(page_title="Stock Analysis & Prediction", layout="wide")

# Define the list of top stocks to analyze (you can extend this list)
STOCK_LIST = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'NVDA': 'NVIDIA Corporation',
    'META': 'Meta Platforms Inc.',
    'TSLA': 'Tesla Inc.',
    'V': 'Visa Inc.',
    'JPM': 'JPMorgan Chase & Co.',
    'JNJ': 'Johnson & Johnson'
}

def fetch_stock_data(symbol, period='10y'):
    """Fetch historical stock data using yfinance with error handling"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        if df.empty:
            st.error(f"No data available for {symbol}")
            return None, {}
        
        # Get stock info with error handling
        try:
            info = stock.info
            if not info:
                raise ValueError("Empty info dictionary")
        except Exception as e:
            st.warning(f"Could not fetch detailed info for {symbol}. Using basic data only.")
            info = {
                'forwardPE': None,
                'priceToBook': None,
                'profitMargins': None,
                'debtToEquity': None,
                'returnOnEquity': None,
                'beta': None
            }
        return df, info
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None, {}

def create_lstm_model(sequence_length):
    """Create and return LSTM model for stock prediction"""
    model = Sequential([
        LSTM(100, return_sequences=True, input_shape=(sequence_length, 1)),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def prepare_data(data, sequence_length):
    """Prepare data for LSTM model with error handling"""
    try:
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(data.reshape(-1, 1))
        
        X, y = [], []
        for i in range(len(scaled_data) - sequence_length):
            X.append(scaled_data[i:(i + sequence_length), 0])
            y.append(scaled_data[i + sequence_length, 0])
        
        return np.array(X), np.array(y), scaler
    except Exception as e:
        st.error(f"Error preparing data: {str(e)}")
        return None, None, None

def predict_future_prices(model, last_sequence, scaler, steps=1825):  # 5 years
    """Predict future stock prices"""
    future_prices = []
    current_sequence = last_sequence.copy()
    
    for _ in range(steps):
        current_sequence_scaled = current_sequence.reshape((1, current_sequence.shape[0], 1))
        next_pred = model.predict(current_sequence_scaled, verbose=0)
        future_prices.append(scaler.inverse_transform(next_pred)[0, 0])
        current_sequence = np.roll(current_sequence, -1)
        current_sequence[-1] = next_pred[0]
    
    return future_prices

def calculate_metrics(data):
    """Calculate key financial metrics"""
    returns = data['Close'].pct_change()
    volatility = returns.std() * np.sqrt(252)  # Annualized volatility
    sharpe_ratio = (returns.mean() * 252) / volatility  # Annualized Sharpe ratio
    max_drawdown = ((data['Close'].cummax() - data['Close']) / data['Close'].cummax()).max()
    
    return {
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown
    }

def analyze_stock_fundamentals(info):
    """Analyze stock fundamentals and provide recommendations"""
    reasons = []
    score = 0
    
    if info.get('forwardPE', float('inf')) < 20:
        reasons.append("✅ Forward P/E ratio is attractive")
        score += 1
    
    if info.get('priceToBook', float('inf')) < 3:
        reasons.append("✅ Price-to-Book ratio is reasonable")
        score += 1
    
    if info.get('profitMargins', 0) > 0.15:
        reasons.append("✅ Strong profit margins")
        score += 1
    
    if info.get('debtToEquity', float('inf')) < 1:
        reasons.append("✅ Healthy debt levels")
        score += 1
    
    if info.get('returnOnEquity', 0) > 0.15:
        reasons.append("✅ Good return on equity")
        score += 1
    
    return reasons, score

# Main App
st.title("Advanced Stock Analysis & Prediction System")

# Sidebar
st.sidebar.header("Settings")
selected_stock = st.sidebar.selectbox("Select Stock", list(STOCK_LIST.keys()), format_func=lambda x: f"{x} - {STOCK_LIST[x]}")
analysis_period = st.sidebar.selectbox("Analysis Period", ['5y', '10y'], index=1)
prediction_years = st.sidebar.slider("Prediction Years", 5, 10, 5)

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Analysis for {STOCK_LIST[selected_stock]} ({selected_stock})")
    
    # Fetch and display current stock data
    with st.spinner("Fetching stock data..."):
        df, stock_info = fetch_stock_data(selected_stock, analysis_period)
        
        # Display current stock price and basic info
        current_price = df['Close'].iloc[-1]
        st.metric("Current Stock Price", f"${current_price:.2f}", 
                 f"{((df['Close'].iloc[-1] - df['Close'].iloc[-2])/df['Close'].iloc[-2]*100):.2f}%")
        
        # Calculate and display metrics
        metrics = calculate_metrics(df)
        
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        metrics_col1.metric("Volatility", f"{metrics['volatility']:.2%}")
        metrics_col2.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
        metrics_col3.metric("Max Drawdown", f"{metrics['max_drawdown']:.2%}")

with col2:
    st.subheader("Investment Analysis")
    reasons, score = analyze_stock_fundamentals(stock_info)
    
    st.write("Investment Potential Score:", "🌟" * score)
    for reason in reasons:
        st.write(reason)

# Price Prediction
st.subheader("Price Predictions & Trends")

# Prepare data for LSTM
sequence_length = 60  # 60 days of historical data
X, y, scaler = prepare_data(df['Close'].values, sequence_length)

# Split data and train model
split = int(0.8 * len(X))
X_train, y_train = X[:split], y[:split]

with st.spinner("Training prediction model..."):
    model = create_lstm_model(sequence_length)
    model.fit(X_train.reshape(-1, sequence_length, 1), y_train, epochs=50, batch_size=32, verbose=0)

# Make future predictions
last_sequence = X[-1]
future_days = prediction_years * 365
future_prices = predict_future_prices(model, last_sequence, scaler, future_days)

# Create date range for future predictions
last_date = df.index[-1]
future_dates = [last_date + timedelta(days=x) for x in range(1, len(future_prices) + 1)]

# Plot historical and predicted prices
fig = go.Figure()

# Historical prices
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Close'],
    name='Historical Price',
    line=dict(color='blue')
))

# Predicted prices
fig.add_trace(go.Scatter(
    x=future_dates,
    y=future_prices,
    name='Predicted Price',
    line=dict(color='red', dash='dash')
))

fig.update_layout(
    title=f'{selected_stock} Stock Price Prediction',
    xaxis_title='Date',
    yaxis_title='Price ($)',
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# Price Targets
st.subheader("Price Targets")
intervals = [1, 2, 3, 5, prediction_years]
targets_data = []

for year in intervals:
    if year <= prediction_years:
        target_price = future_prices[year * 365 - 1]
        potential_return = (target_price - current_price) / current_price * 100
        targets_data.append({
            "Year": year,
            "Predicted Price": f"${target_price:.2f}",
            "Potential Return": f"{potential_return:.1f}%"
        })

st.table(pd.DataFrame(targets_data))

# Risk Analysis
st.subheader("Risk Analysis")
risk_col1, risk_col2 = st.columns(2)

with risk_col1:
    st.write("Short-term Risk Factors:")
    volatility_risk = "High" if metrics['volatility'] > 0.3 else "Moderate" if metrics['volatility'] > 0.2 else "Low"
    st.write(f"- Volatility Risk: {volatility_risk}")
    st.write(f"- Market Beta: {stock_info.get('beta', 'N/A')}")

with risk_col2:
    st.write("Long-term Risk Factors:")
    st.write(f"- Debt/Equity: {stock_info.get('debtToEquity', 'N/A')}")
    st.write(f"- Profit Margin: {stock_info.get('profitMargins', 'N/A'):.2%}")

# Disclaimer
st.markdown("""
---
**Disclaimer:** This tool provides analysis for educational purposes only. 
Always conduct your own research and consult with a financial advisor before making investment decisions.
Stock market investments involve risk and past performance does not guarantee future results.
""")
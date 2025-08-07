import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time

# Page configuration
st.set_page_config(
    page_title="MSTR Preferred Stock Yield Curve",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean, professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e293b;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: none;
    }
    
    .metric-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }
    
    .metric-symbol {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 8px;
    }
    
    .metric-price {
        font-size: 1.6rem;
        font-weight: 700;
        color: #3b82f6;
        margin: 5px 0;
    }
    
    .metric-yield {
        font-size: 1.2rem;
        font-weight: 600;
        color: #10b981;
        margin: 5px 0;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
        margin: 25px 0 15px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .dataframe th {
        background-color: #1e293b !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px !important;
        text-align: left !important;
    }
    
    .dataframe td {
        background-color: white !important;
        color: #1e293b !important;
        padding: 10px !important;
        border-bottom: 1px solid #e5e7eb !important;
    }
    
    .dataframe tr:hover td {
        background-color: #f8fafc !important;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">MicroStrategy Preferred Stock Yield Dashboard</h1>', unsafe_allow_html=True)

# Sidebar for controls
st.sidebar.header("⚙️ Dashboard Controls")

# MSTR Preferred Stock symbols - Ordered by duration (STRC, STRD, STRF, STRK)
PREFERRED_STOCKS = {
    'STRC': 'MicroStrategy Inc. 6.75% Pfd Stock Series D',
    'STRD': 'MicroStrategy Inc. 0.875% Pfd Stock Series C',
    'STRF': 'MicroStrategy Inc. 0.750% Pfd Stock Series B', 
    'STRK': 'MicroStrategy Inc. 6.125% Pfd Stock Series A'
}

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (30s)", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 30)

# Data source selection
data_period = st.sidebar.selectbox(
    "📅 Historical Period",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=2
)

# Function to calculate yield metrics
def calculate_yield_metrics(stock_data, symbol):
    """Calculate various yield metrics for preferred stocks"""
    if stock_data.empty:
        return None
    
    current_price = stock_data['Close'].iloc[-1]
    
    # MSTR Preferred stock dividend rates and par values (ordered by duration)
    stock_info = {
        'STRC': {'rate': 9.0, 'par': 100.0},    # $9.00 annual dividend
        'STRD': {'rate': 10.0, 'par': 100.0},   # 10% on $100 par = $10.00 annual
        'STRF': {'rate': 10.0, 'par': 100.0},   # 10% on $100 par = $10.00 annual  
        'STRK': {'rate': 8.0, 'par': 100.0}     # 8% on $100 par = $8.00 annual
    }
    
    # Get par value and rate for this symbol
    par_value = stock_info.get(symbol, {}).get('par', 100.0)
    dividend_rate = stock_info.get(symbol, {}).get('rate', 0.0)
    annual_dividend = par_value * (dividend_rate / 100)
    
    # Current yield
    current_yield = (annual_dividend / current_price) * 100 if current_price > 0 else 0
    
    return {
        'current_price': current_price,
        'current_yield': current_yield,
        'annual_dividend': annual_dividend,
        'par_value': par_value
    }

# Function to calculate historical yields
def calculate_historical_yields(stock_data, symbol):
    """Calculate historical yield data"""
    if stock_data.empty:
        return pd.DataFrame()
    
    # Stock info for dividend calculations (ordered by duration)
    stock_info = {
        'STRC': {'rate': 9.0, 'par': 100.0},    # $9.00 annual dividend
        'STRD': {'rate': 10.0, 'par': 100.0},   # 10% on $100 par = $10.00 annual
        'STRF': {'rate': 10.0, 'par': 100.0},   # 10% on $100 par = $10.00 annual
        'STRK': {'rate': 8.0, 'par': 100.0}     # 8% on $100 par = $8.00 annual
    }
    
    par_value = stock_info.get(symbol, {}).get('par', 100.0)
    dividend_rate = stock_info.get(symbol, {}).get('rate', 0.0)
    annual_dividend = par_value * (dividend_rate / 100)
    
    # Calculate historical yields
    yields = (annual_dividend / stock_data['Close']) * 100
    yields = yields.replace([np.inf, -np.inf], np.nan).dropna()
    
    return yields

# Function to fetch stock data
@st.cache_data(ttl=30)  # Cache for 30 seconds
def fetch_stock_data(symbols, period="1mo"):
    """Fetch stock data for multiple symbols"""
    data = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            if not hist.empty:
                data[symbol] = hist
            else:
                st.warning(f"⚠️ No data available for {symbol}")
                # Create dummy data for demonstration
                dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
                dummy_price = 25 + np.random.randn(len(dates)) * 2
                data[symbol] = pd.DataFrame({
                    'Close': dummy_price,
                    'Open': dummy_price * 0.99,
                    'High': dummy_price * 1.02,
                    'Low': dummy_price * 0.98,
                    'Volume': np.random.randint(1000, 10000, len(dates))
                }, index=dates)
        except Exception as e:
            st.error(f"❌ Error fetching data for {symbol}: {str(e)}")
            # Create dummy data as fallback
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
            dummy_price = 25 + np.random.randn(len(dates)) * 2
            data[symbol] = pd.DataFrame({
                'Close': dummy_price,
                'Open': dummy_price * 0.99,
                'High': dummy_price * 1.02,
                'Low': dummy_price * 0.98,
                'Volume': np.random.randint(1000, 10000, len(dates))
            }, index=dates)
    
    return data

# Main dashboard logic
def main_dashboard():
    # Fetch data
    with st.spinner("📊 Fetching real-time data..."):
        stock_data = fetch_stock_data(list(PREFERRED_STOCKS.keys()), period=data_period)
    
    # Current metrics row
    st.markdown('<h2 class="section-header">📈 Current Yield Metrics</h2>', unsafe_allow_html=True)
    
    cols = st.columns(len(PREFERRED_STOCKS))
    yield_data = {}
    
    for i, (symbol, name) in enumerate(PREFERRED_STOCKS.items()):
        with cols[i]:
            if symbol in stock_data and not stock_data[symbol].empty:
                metrics = calculate_yield_metrics(stock_data[symbol], symbol)
                if metrics:
                    yield_data[symbol] = metrics
                    
                    # Enhanced metric cards with beautiful styling
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-symbol">{symbol}</div>
                        <div class="metric-price">${metrics['current_price']:.2f}</div>
                        <div class="metric-yield">{metrics['current_yield']:.2f}% Yield</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"📊 {symbol} Details"):
                        st.write(f"**Full Name:** {name}")
                        st.write(f"**Current Price:** ${metrics['current_price']:.2f}")
                        st.write(f"**Par Value:** ${metrics['par_value']:.2f}")
                        st.write(f"**Annual Dividend:** ${metrics['annual_dividend']:.2f}")
                        st.write(f"**Current Yield:** {metrics['current_yield']:.2f}%")
                else:
                    st.error(f"❌ Unable to calculate metrics for {symbol}")
            else:
                st.error(f"❌ No data available for {symbol}")
    
    # Yield Curve Chart
    st.markdown('<h2 class="section-header">📊 Yield Curve Visualization</h2>', unsafe_allow_html=True)
    
    if yield_data:
        # Create yield curve data
        symbols = list(yield_data.keys())
        current_yields = [yield_data[symbol]['current_yield'] for symbol in symbols]
        prices = [yield_data[symbol]['current_price'] for symbol in symbols]
        
        # Create yield curve chart
        fig = go.Figure()
        
        # Current Yield line
        fig.add_trace(go.Scatter(
            x=symbols,
            y=current_yields,
            mode='lines+markers',
            name='Current Yield (%)',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=12, color='#1f77b4'),
            text=[f"{y:.2f}%" for y in current_yields],
            textposition="top center"
        ))
        
        fig.update_layout(
            title="Current Yield Curve",
            xaxis_title="Symbol (Ordered by Duration)",
            yaxis_title="Current Yield (%)",
            hovermode='x unified',
            height=500,
            showlegend=True,
            template="plotly_white",
            font=dict(color="#1e293b"),
            title_font=dict(size=16, color="#1e293b")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Price comparison chart
        st.markdown('<h2 class="section-header">💰 Price Comparison</h2>', unsafe_allow_html=True)
        
        price_fig = go.Figure()
        price_fig.add_trace(go.Bar(
            x=symbols,
            y=prices,
            name='Current Price ($)',
            marker_color='lightblue',
            text=[f"${p:.2f}" for p in prices],
            textposition='auto'
        ))
        
        # Add par value line
        price_fig.add_hline(y=100, line_dash="dash", line_color="red", 
                           annotation_text="Par Value ($100)")
        
        price_fig.update_layout(
            title="Current Prices vs Par Value",
            xaxis_title="Symbol (Ordered by Duration)",
            yaxis_title="Price ($)",
            height=400,
            template="plotly_white",
            font=dict(color="#1e293b"),
            title_font=dict(size=16, color="#1e293b")
        )
        
        st.plotly_chart(price_fig, use_container_width=True)
    
    # Historical yield charts - Changed from price to yield history
    st.markdown('<h2 class="section-header">📈 Historical Yield Trends</h2>', unsafe_allow_html=True)
    
    if stock_data:
        fig_hist = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        for i, (symbol, data) in enumerate(stock_data.items()):
            if not data.empty:
                historical_yields = calculate_historical_yields(data, symbol)
                if not historical_yields.empty:
                    fig_hist.add_trace(go.Scatter(
                        x=historical_yields.index,
                        y=historical_yields.values,
                        mode='lines',
                        name=f"{symbol} Yield",
                        line=dict(color=colors[i % len(colors)], width=2)
                    ))
        
        fig_hist.update_layout(
            title=f"Historical Yield Trends ({data_period})",
            xaxis_title="Date",
            yaxis_title="Yield (%)",
            hovermode='x unified',
            height=500,
            template="plotly_white",
            font=dict(color="#1e293b"),
            title_font=dict(size=16, color="#1e293b")
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Detailed metrics table
    st.markdown('<h2 class="section-header">📋 Detailed Metrics Table</h2>', unsafe_allow_html=True)
    
    if yield_data:
        table_data = []
        for symbol, metrics in yield_data.items():
            table_data.append({
                'Symbol': symbol,
                'Name': PREFERRED_STOCKS[symbol],
                'Current Price': f"${metrics['current_price']:.2f}",
                'Par Value': f"${metrics['par_value']:.2f}",
                'Annual Dividend': f"${metrics['annual_dividend']:.2f}",
                'Current Yield': f"{metrics['current_yield']:.2f}%",
                'Premium/Discount': f"{((metrics['current_price'] / metrics['par_value'] - 1) * 100):.2f}%"
            })
        
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    
    # Last update timestamp
    st.sidebar.info(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Auto-refresh logic
if auto_refresh:
    # Create a placeholder for the dashboard
    dashboard_placeholder = st.empty()
    
    while True:
        with dashboard_placeholder.container():
            main_dashboard()
        
        # Wait for the specified interval
        time.sleep(refresh_interval)
        
        # Rerun to refresh data
        st.rerun()
else:
    main_dashboard()

# Footer with enhanced styling
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; font-size: 0.9em; font-family: Inter, sans-serif; padding: 20px 0; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); border-radius: 10px; margin-top: 30px;'>
    💡 <strong>Professional Yield Analysis Dashboard</strong><br>
    Real-time yield curve analysis for MicroStrategy preferred stocks ordered by duration<br>
    <small>Data sourced from Yahoo Finance • For investment decisions, consult professional financial advice</small>
</div>
""", unsafe_allow_html=True)

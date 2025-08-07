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

# Custom CSS for enhanced styling and visual appeal
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        margin: 20px;
        padding: 30px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    }
    
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 40px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 10px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    }
    
    .metric-symbol {
        font-family: 'Inter', sans-serif;
        font-size: 1.4rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 8px;
    }
    
    .metric-price {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #3b82f6;
        margin: 5px 0;
    }
    
    .metric-yield {
        font-family: 'Inter', sans-serif;
        font-size: 1.4rem;
        font-weight: 600;
        color: #10b981;
        margin: 5px 0;
    }
    
    .stSelectbox > div > div {
        background-color: white;
        border-radius: 8px;
    }
    
    .stCheckbox > label {
        font-weight: 500;
        color: #374151;
    }
    
    .stSlider > div > div {
        color: #374151;
    }
    
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: #1e293b;
        margin: 30px 0 20px 0;
        padding-bottom: 10px;
        border-bottom: 3px solid #e2e8f0;
    }
    
    .stExpander {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin: 5px 0;
    }
    
    .data-table {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }
    
    .dataframe {
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        color: #374151 !important;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px !important;
        text-align: center !important;
    }
    
    .dataframe td {
        background-color: white !important;
        color: #374151 !important;
        padding: 10px !important;
        text-align: center !important;
        border-bottom: 1px solid #e5e7eb !important;
    }
    
    .dataframe tr:hover td {
        background-color: #f9fafb !important;
    }
    
    .sidebar-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🏦 MSTR Preferred Stock Yield Curve Dashboard</h1>', unsafe_allow_html=True)

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
    st.subheader("📈 Current Yield Metrics")
    
    cols = st.columns(len(PREFERRED_STOCKS))
    yield_data = {}
    
    for i, (symbol, name) in enumerate(PREFERRED_STOCKS.items()):
        with cols[i]:
            if symbol in stock_data and not stock_data[symbol].empty:
                metrics = calculate_yield_metrics(stock_data[symbol], symbol)
                if metrics:
                    yield_data[symbol] = metrics
                    
                    # Use improved styling for better visibility
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 10px; border: 2px solid #1f77b4; margin: 5px 0;">
                        <h4 style="color: #1f77b4; margin: 0; font-weight: bold;">{symbol}</h4>
                        <p style="color: #262730; font-size: 1.2em; font-weight: bold; margin: 5px 0;">
                            Price: ${metrics['current_price']:.2f}
                        </p>
                        <p style="color: #2ca02c; font-size: 1.1em; font-weight: bold; margin: 5px 0;">
                            Yield: {metrics['current_yield']:.2f}%
                        </p>
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
    st.subheader("📊 Yield Curve Visualization")
    
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
            title="MSTR Preferred Stock Current Yield Curve",
            xaxis_title="Preferred Stock Symbol",
            yaxis_title="Current Yield (%)",
            hovermode='x unified',
            height=500,
            showlegend=True,
            template="plotly_white",
            font=dict(color="black")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Price comparison chart
        st.subheader("💰 Price Comparison")
        
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
            xaxis_title="Preferred Stock Symbol",
            yaxis_title="Price ($)",
            height=400,
            template="plotly_white",
            font=dict(color="black")
        )
        
        st.plotly_chart(price_fig, use_container_width=True)
    
    # Historical yield charts - Changed from price to yield history
    st.subheader("📈 Historical Yield Trends")
    
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
            font=dict(color="black")
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Data table with enhanced visibility
    st.subheader("📋 Detailed Metrics Table")
    
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
        
        # Style the dataframe for better visibility
        st.markdown("""
        <style>
        .dataframe {
            font-size: 14px !important;
            color: black !important;
        }
        .dataframe th {
            background-color: #1f77b4 !important;
            color: white !important;
            font-weight: bold !important;
        }
        .dataframe td {
            background-color: white !important;
            color: black !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(df_table, use_container_width=True)
    
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

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    💡 This dashboard provides real-time yield curve analysis for MSTR preferred stocks.<br>
    Data sourced from Yahoo Finance. For investment decisions, please consult professional financial advice.
</div>
""", unsafe_allow_html=True)

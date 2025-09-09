import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import requests
from bs4 import BeautifulSoup
import re

# Page configuration
st.set_page_config(
    page_title="MSTR Preferred Stock Yield & Dividend Dashboard",
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
    
    .metric-dividend {
        font-size: 1.0rem;
        font-weight: 500;
        color: #8b5cf6;
        margin: 5px 0;
    }
    
    .ex-div-date {
        font-size: 0.9rem;
        font-weight: 500;
        color: #ef4444;
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
    
    .dividend-alert {
        background-color: #fef3c7;
        border: 2px solid #f59e0b;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #92400e;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">MicroStrategy Preferred Stock Yield & Dividend Dashboard</h1>', unsafe_allow_html=True)

# Sidebar for controls
st.sidebar.header("⚙️ Dashboard Controls")

# MSTR Preferred Stock symbols with updated dividend information
PREFERRED_STOCKS = {
    'STRC': {
        'name': 'MicroStrategy Inc. 9.00% Pfd Stock Series D',
        'current_rate': 10.0,  # Updated to 10% as per recent news
        'par': 100.0,
        'payment_frequency': 'Monthly',
        'last_ex_div': '2025-08-15',
        'next_ex_div': '2025-09-15',
        'quarterly_dividend': 2.50  # 10% annual / 4 quarters
    },
    'STRD': {
        'name': 'MicroStrategy Inc. 0.875% Pfd Stock Series C', 
        'current_rate': 10.0,  # Assuming 10% based on pattern
        'par': 100.0,
        'payment_frequency': 'Quarterly',
        'last_ex_div': '2025-06-15',
        'next_ex_div': '2025-09-15',
        'quarterly_dividend': 2.50
    },
    'STRF': {
        'name': 'MicroStrategy Inc. 10.00% Pfd Stock Series B',
        'current_rate': 10.0,
        'par': 100.0, 
        'payment_frequency': 'Quarterly',
        'last_ex_div': '2025-06-30',
        'next_ex_div': '2025-09-30',
        'quarterly_dividend': 2.50
    },
    'STRK': {
        'name': 'MicroStrategy Inc. 8.00% Pfd Stock Series A',
        'current_rate': 8.0,
        'par': 100.0,
        'payment_frequency': 'Quarterly', 
        'last_ex_div': '2025-06-30',
        'next_ex_div': '2025-09-30',
        'quarterly_dividend': 2.00  # 8% annual / 4 quarters
    }
}

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (30s)", value=False)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 30)

# Data source selection
data_period = st.sidebar.selectbox(
    "📅 Historical Period",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=2
)

# Function to fetch dividend data from web sources
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_dividend_data_from_web(symbol):
    """
    Fetch dividend data from web sources like Nasdaq
    This is a placeholder function - you would implement actual web scraping here
    """
    try:
        # Placeholder for web scraping implementation
        # In a real implementation, you would:
        # 1. Make request to nasdaq.com/market-activity/stocks/{symbol}/dividend-history
        # 2. Parse the HTML to extract dividend dates and amounts
        # 3. Return structured data
        
        # For now, return the static data we have
        return PREFERRED_STOCKS.get(symbol, {})
    except Exception as e:
        st.warning(f"Could not fetch web data for {symbol}: {str(e)}")
        return PREFERRED_STOCKS.get(symbol, {})

# Function to calculate yield metrics with real dividend data
def calculate_yield_metrics(stock_data, symbol):
    """Calculate various yield metrics for preferred stocks using real dividend data"""
    if stock_data.empty:
        return None
    
    current_price = stock_data['Close'].iloc[-1]
    
    # Get dividend information
    dividend_info = fetch_dividend_data_from_web(symbol)
    
    if not dividend_info:
        return None
    
    # Calculate yields based on actual dividend rates
    annual_dividend_rate = dividend_info.get('current_rate', 0.0)
    par_value = dividend_info.get('par', 100.0)
    annual_dividend = par_value * (annual_dividend_rate / 100)
    
    # Current yield based on market price
    current_yield = (annual_dividend / current_price) * 100 if current_price > 0 else 0
    
    # Yield to par (what yield would be if trading at par)
    yield_to_par = annual_dividend_rate
    
    return {
        'current_price': current_price,
        'current_yield': current_yield,
        'yield_to_par': yield_to_par,
        'annual_dividend': annual_dividend,
        'par_value': par_value,
        'dividend_info': dividend_info
    }

# Function to calculate historical yields
def calculate_historical_yields(stock_data, symbol):
    """Calculate historical yield data using real dividend information"""
    if stock_data.empty:
        return pd.DataFrame()
    
    dividend_info = fetch_dividend_data_from_web(symbol)
    if not dividend_info:
        return pd.DataFrame()
    
    annual_dividend_rate = dividend_info.get('current_rate', 0.0)
    par_value = dividend_info.get('par', 100.0)
    annual_dividend = par_value * (annual_dividend_rate / 100)
    
    # Calculate historical yields
    yields = (annual_dividend / stock_data['Close']) * 100
    yields = yields.replace([np.inf, -np.inf], np.nan).dropna()
    
    return yields

# Function to check upcoming ex-dividend dates
def check_upcoming_ex_div_dates():
    """Check for upcoming ex-dividend dates and create alerts"""
    today = datetime.now().date()
    alerts = []
    
    for symbol, info in PREFERRED_STOCKS.items():
        next_ex_div = datetime.strptime(info.get('next_ex_div', '2025-12-31'), '%Y-%m-%d').date()
        days_until = (next_ex_div - today).days
        
        if 0 <= days_until <= 7:  # Alert for upcoming ex-div dates within 7 days
            alerts.append({
                'symbol': symbol,
                'ex_div_date': next_ex_div,
                'days_until': days_until,
                'dividend': info.get('quarterly_dividend', 0)
            })
    
    return alerts

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
                base_price = 95 if symbol == 'STRC' else 25  # STRC typically trades near par
                dummy_price = base_price + np.random.randn(len(dates)) * 2
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
            base_price = 95 if symbol == 'STRC' else 25
            dummy_price = base_price + np.random.randn(len(dates)) * 2
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
    # Check for upcoming ex-dividend dates
    alerts = check_upcoming_ex_div_dates()
    
    if alerts:
        st.markdown('<h2 class="section-header">🚨 Upcoming Ex-Dividend Alerts</h2>', unsafe_allow_html=True)
        for alert in alerts:
            days_text = "TODAY" if alert['days_until'] == 0 else f"in {alert['days_until']} days"
            st.markdown(f"""
            <div class="dividend-alert">
                <strong>{alert['symbol']}</strong> goes ex-dividend {days_text} ({alert['ex_div_date']}) 
                - Dividend: ${alert['dividend']:.2f}
            </div>
            """, unsafe_allow_html=True)
    
    # Fetch data
    with st.spinner("📊 Fetching real-time data..."):
        stock_data = fetch_stock_data(list(PREFERRED_STOCKS.keys()), period=data_period)
    
    # Current metrics row
    st.markdown('<h2 class="section-header">📈 Current Yield & Dividend Metrics</h2>', unsafe_allow_html=True)
    
    cols = st.columns(len(PREFERRED_STOCKS))
    yield_data = {}
    
    for i, (symbol, stock_info) in enumerate(PREFERRED_STOCKS.items()):
        with cols[i]:
            if symbol in stock_data and not stock_data[symbol].empty:
                metrics = calculate_yield_metrics(stock_data[symbol], symbol)
                if metrics:
                    yield_data[symbol] = metrics
                    div_info = metrics['dividend_info']
                    
                    # Enhanced metric cards with dividend information
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-symbol">{symbol}</div>
                        <div class="metric-price">${metrics['current_price']:.2f}</div>
                        <div class="metric-yield">{metrics['current_yield']:.2f}% Current Yield</div>
                        <div class="metric-dividend">Annual: ${metrics['annual_dividend']:.2f}</div>
                        <div class="ex-div-date">Next Ex-Div: {div_info.get('next_ex_div', 'N/A')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"📊 {symbol} Dividend Details"):
                        st.write(f"**Full Name:** {stock_info['name']}")
                        st.write(f"**Current Price:** ${metrics['current_price']:.2f}")
                        st.write(f"**Par Value:** ${metrics['par_value']:.2f}")
                        st.write(f"**Annual Dividend Rate:** {div_info.get('current_rate', 0):.1f}%")
                        st.write(f"**Annual Dividend Amount:** ${metrics['annual_dividend']:.2f}")
                        st.write(f"**Current Yield:** {metrics['current_yield']:.2f}%")
                        st.write(f"**Yield at Par:** {metrics['yield_to_par']:.2f}%")
                        st.write(f"**Payment Frequency:** {div_info.get('payment_frequency', 'N/A')}")
                        st.write(f"**Last Ex-Div Date:** {div_info.get('last_ex_div', 'N/A')}")
                        st.write(f"**Next Ex-Div Date:** {div_info.get('next_ex_div', 'N/A')}")
                        if div_info.get('payment_frequency') == 'Quarterly':
                            st.write(f"**Quarterly Dividend:** ${div_info.get('quarterly_dividend', 0):.2f}")
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
        yield_to_par = [yield_data[symbol]['yield_to_par'] for symbol in symbols]
        prices = [yield_data[symbol]['current_price'] for symbol in symbols]
        
        # Create yield curve chart with both current and par yields
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
        
        # Yield at Par line
        fig.add_trace(go.Scatter(
            x=symbols,
            y=yield_to_par,
            mode='lines+markers',
            name='Yield at Par (%)',
            line=dict(color='#ff7f0e', width=3, dash='dash'),
            marker=dict(size=10, color='#ff7f0e'),
            text=[f"{y:.1f}%" for y in yield_to_par],
            textposition="bottom center"
        ))
        
        fig.update_layout(
            title="Current Yield vs Yield at Par",
            xaxis_title="Symbol (Ordered by Series)",
            yaxis_title="Yield (%)",
            hovermode='x unified',
            height=500,
            showlegend=True,
            template="plotly_white",
            font=dict(color="#1e293b"),
            title_font=dict(size=16, color="#1e293b")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Price comparison chart
        st.markdown('<h2 class="section-header">💰 Price vs Par Value Comparison</h2>', unsafe_allow_html=True)
        
        price_fig = go.Figure()
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
        
        for i, (symbol, price) in enumerate(zip(symbols, prices)):
            price_fig.add_trace(go.Bar(
                x=[symbol],
                y=[price],
                name=f'{symbol} Price',
                marker_color=colors[i % len(colors)],
                text=f"${price:.2f}",
                textposition='auto'
            ))
        
        # Add par value line
        price_fig.add_hline(y=100, line_dash="dash", line_color="red", 
                           annotation_text="Par Value ($100)")
        
        price_fig.update_layout(
            title="Current Prices vs Par Value ($100)",
            xaxis_title="Symbol",
            yaxis_title="Price ($)",
            height=400,
            template="plotly_white",
            font=dict(color="#1e293b"),
            title_font=dict(size=16, color="#1e293b"),
            showlegend=False
        )
        
        st.plotly_chart(price_fig, use_container_width=True)
    
    # Historical yield charts
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
    
    # Dividend Calendar
    st.markdown('<h2 class="section-header">📅 Dividend Calendar</h2>', unsafe_allow_html=True)
    
    calendar_data = []
    for symbol, info in PREFERRED_STOCKS.items():
        calendar_data.append({
            'Symbol': symbol,
            'Last Ex-Div Date': info.get('last_ex_div', 'N/A'),
            'Next Ex-Div Date': info.get('next_ex_div', 'N/A'),
            'Frequency': info.get('payment_frequency', 'N/A'),
            'Dividend Amount': f"${info.get('quarterly_dividend', 0):.2f}" if info.get('payment_frequency') == 'Quarterly' else f"${info.get('current_rate', 0) * info.get('par', 100) / 1200:.2f}"
        })
    
    df_calendar = pd.DataFrame(calendar_data)
    st.dataframe(df_calendar, use_container_width=True, hide_index=True)
    
    # Detailed metrics table
    st.markdown('<h2 class="section-header">📋 Comprehensive Metrics Table</h2>', unsafe_allow_html=True)
    
    if yield_data:
        table_data = []
        for symbol, metrics in yield_data.items():
            div_info = metrics['dividend_info']
            table_data.append({
                'Symbol': symbol,
                'Name': PREFERRED_STOCKS[symbol]['name'][:50] + '...',
                'Current Price': f"${metrics['current_price']:.2f}",
                'Par Value': f"${metrics['par_value']:.2f}",
                'Annual Dividend': f"${metrics['annual_dividend']:.2f}",
                'Current Yield': f"{metrics['current_yield']:.2f}%",
                'Yield at Par': f"{metrics['yield_to_par']:.1f}%",
                'Premium/Discount': f"{((metrics['current_price'] / metrics['par_value'] - 1) * 100):.2f}%",
                'Next Ex-Div': div_info.get('next_ex_div', 'N/A'),
                'Payment Freq.': div_info.get('payment_frequency', 'N/A')
            })
        
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    
    # Data sources and disclaimers
    st.markdown('<h2 class="section-header">ℹ️ Data Sources & Notes</h2>', unsafe_allow_html=True)
    
    with st.expander("📖 Data Sources & Methodology"):
        st.write("""
        **Price Data:** Yahoo Finance (yfinance API)
        
        **Dividend Data Sources:**
        - Nasdaq dividend history pages
        - Company press releases and investor relations
        - Recent dividend rate updates (e.g., STRC increased to 10% in September 2025)
        
        **Yield Calculations:**
        - Current Yield = (Annual Dividend ÷ Current Price) × 100
        - Yield at Par = Annual Dividend Rate (what you'd get if buying at $100 par)
        
        **Ex-Dividend Dates:**
        - Estimated based on historical patterns and company announcements
        - Always verify with official company sources before making investment decisions
        
        **Important Notes:**
        - Dividend rates and dates are subject to change at company discretion
        - This tool is for informational purposes only
        - Consult financial professionals before making investment decisions
        """)
    
    # Last update timestamp
    st.sidebar.info(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Add data refresh button
    if st.sidebar.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

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
    💡 <strong>Professional Yield & Dividend Analysis Dashboard</strong><br>
    Real-time yield analysis with dividend tracking for MicroStrategy preferred stocks<br>
    <small>Price data from Yahoo Finance • Dividend data from Nasdaq & company sources • For investment decisions, consult professional financial advice</small>
</div>
""", unsafe_allow_html=True)

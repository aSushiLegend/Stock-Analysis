import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# Set up Streamlit layout
st.title('S&P 500 Stock Analyzer')

# Get S&P 500 companies list
sp500_tickers = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
sp500_symbols = sp500_tickers['Symbol'].tolist()

# Sidebar - Choose stock, options, and data interval
selected_stock = st.sidebar.selectbox('Select a stock', sp500_symbols)
data_interval = st.sidebar.selectbox('Select data interval', ['1d', '1wk', '1mo'], index=0)  # Default: 1d

# Date range selection
start_date = st.sidebar.date_input('Select start date', pd.to_datetime('2023-01-01'))
end_date = st.sidebar.date_input('Select end date', pd.to_datetime('2024-01-01'))

# Check if start date is after end date
if start_date > end_date:
    st.error("Error: Start date cannot be after end date.")
    st.stop()

# Get stock data within the selected date range and data interval
stock_data = yf.download(selected_stock, start=start_date, end=end_date, interval=data_interval)

# Create a DataFrame to store percentage changes, P/E ratio, beta, and volume for comparisons
comparison_data = pd.DataFrame(index=stock_data.index)

# Add options for moving average, Bollinger Bands, P/E Ratio Bar Chart, Beta Bar Chart, Volume Comparison, and Chart Type
chart_type = st.sidebar.selectbox('Select chart type', ['Line', 'Candlestick'], index=0)  # Default: Line
add_sma = st.sidebar.checkbox('Add 20 days SMA')
add_bollinger = st.sidebar.checkbox('Add Bollinger Bands')
add_pe_ratio_chart = st.sidebar.checkbox('Add P/E Ratio Bar Chart')
add_beta_chart = st.sidebar.checkbox('Add Beta Bar Chart')
add_volume_chart = st.sidebar.checkbox('Add Volume Comparison')
compare_with_sp500 = st.sidebar.checkbox('Compare with S&P 500 (^GSPC)')
add_balance_sheet = st.sidebar.checkbox('Show Balance Sheet')
print("Balance_sheet")

# Add 20 days SMA to the first graph
if add_sma:
    stock_data['SMA20'] = stock_data['Close'].rolling(window=20).mean()

# Add Bollinger Bands to the first graph
if add_bollinger:
    stock_data['Upper'] = stock_data['Close'].rolling(window=20).mean() + 2 * stock_data['Close'].rolling(
        window=20).std()
    stock_data['Lower'] = stock_data['Close'].rolling(window=20).mean() - 2 * stock_data['Close'].rolling(
        window=20).std()

if add_balance_sheet:
    ticker_object = yf.Ticker('AAPL')
    balancesheet = ticker_object.balancesheet
    bs_df = pd.DataFrame(balancesheet)
    st.table(bs_df)

# Plot selected stock and analysis on the first graph
fig_stock = go.Figure()

if chart_type == 'Line':
    fig_stock.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', name=selected_stock))
else:
    fig_stock.add_trace(go.Candlestick(x=stock_data.index,
                                       open=stock_data['Open'],
                                       high=stock_data['High'],
                                       low=stock_data['Low'],
                                       close=stock_data['Close'],
                                       name=selected_stock))

# Plot 20 days SMA on the first graph
if add_sma:
    fig_stock.add_trace(go.Scatter(x=stock_data.index, y=stock_data['SMA20'], mode='lines', name='20 days SMA'))

# Plot Bollinger Bands on the first graph
if add_bollinger:
    fig_stock.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Upper'], mode='lines', name='Upper Band'))
    fig_stock.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Lower'], mode='lines', name='Lower Band'))

# Update layout for the selected stock analysis
fig_stock.update_layout(title=f'Stock Analysis: {selected_stock}',
                        xaxis_title='Date',
                        yaxis_title='Stock Price',
                        xaxis_rangeslider_visible=True)

# Show the plot for the selected stock analysis
st.plotly_chart(fig_stock)

# Compare with other selected stocks on the second graph
fig_comparison = go.Figure()

# Add the selected stock's percentage change
comparison_data[selected_stock] = (stock_data['Close'] / stock_data['Close'].iloc[0] - 1) * 100
fig_comparison.add_trace(go.Scatter(x=stock_data.index, y=comparison_data[selected_stock],
                                   mode='lines', name=f'{selected_stock} (Analysis)'))

# Compare with other selected stocks
compare_stock = st.sidebar.multiselect('Compare with other stocks', sp500_tickers)

for stock in compare_stock:
    compare_data = yf.download(stock, start=start_date, end=end_date, interval=data_interval)
    comparison_data[stock] = (compare_data['Close'] / compare_data['Close'].iloc[0] - 1) * 100
    fig_comparison.add_trace(go.Scatter(x=compare_data.index, y=comparison_data[stock],
                                       mode='lines', name=f'{stock} (Comparison)'))

# Compare with S&P 500 (^GSPC)
if compare_with_sp500:
    sp500_data = yf.download('^GSPC', start=start_date, end=end_date, interval=data_interval)
    comparison_data['^GSPC'] = (sp500_data['Close'] / sp500_data['Close'].iloc[0] - 1) * 100
    fig_comparison.add_trace(go.Scatter(x=sp500_data.index, y=comparison_data['^GSPC'],
                                       mode='lines', name='S&P 500 (^GSPC)'))

# Plot P/E Ratio Bar Chart on the second graph
if add_pe_ratio_chart:
    pe_ratios = {}
    pe_ratios[selected_stock] = yf.Ticker(selected_stock).info.get('trailingPE', 'N/A')

    for stock in compare_stock:
        pe_ratios[stock] = yf.Ticker(stock).info.get('trailingPE', 'N/A')

    fig_pe_ratio = go.Figure()

    for stock, pe_ratio in pe_ratios.items():
        fig_pe_ratio.add_trace(go.Bar(x=[stock], y=[pe_ratio], name=f'{stock} (P/E Ratio)'))

    fig_pe_ratio.update_layout(title='P/E Ratio Comparison',
                               xaxis_title='Stocks',
                               yaxis_title='P/E Ratio',
                               barmode='group')

    # Show the P/E Ratio Bar Chart on the second graph
    st.plotly_chart(fig_pe_ratio)

# Plot Beta Bar Chart on the second graph
if add_beta_chart:
    betas = {}
    betas[selected_stock] = yf.Ticker(selected_stock).info.get('beta', 'N/A')

    for stock in compare_stock:
        betas[stock] = yf.Ticker(stock).info.get('beta', 'N/A')

    fig_beta = go.Figure()

    for stock, beta in betas.items():
        fig_beta.add_trace(go.Bar(x=[stock], y=[beta], name=f'{stock} (Beta)'))

    fig_beta.update_layout(title='Beta Comparison',
                           xaxis_title='Stocks',
                           yaxis_title='Beta',
                           barmode='group')

    # Show the Beta Bar Chart on the second graph
    st.plotly_chart(fig_beta)

# Plot Volume Comparison Chart on the second graph
if add_volume_chart:
    fig_volume = go.Figure()

    fig_volume.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Volume'],
                                    mode='lines', name=f'{selected_stock} (Volume)'))

    # Compare with other selected stocks
    for stock in compare_stock:
        compare_data = yf.download(stock, start=start_date, end=end_date, interval=data_interval)
        fig_volume.add_trace(go.Scatter(x=compare_data.index, y=compare_data['Volume'],
                                        mode='lines', name=f'{stock} (Volume)'))

    fig_volume.update_layout(title='Volume Comparison',
                             xaxis_title='Date',
                             yaxis_title='Volume',
                             xaxis_rangeslider_visible=True)

    # Show the Volume Comparison Chart on the second graph
    st.plotly_chart(fig_volume)

# Update layout for percentage changes comparison
fig_comparison.update_layout(title=f'Percentage Change Comparison',
                             xaxis_title='Date',
                             yaxis_title='Percentage Change',
                             xaxis_rangeslider_visible=True)

# Show the plot for percentage changes comparison
st.plotly_chart(fig_comparison)

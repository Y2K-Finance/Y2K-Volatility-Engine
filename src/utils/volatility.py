import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.style.use('dark_background')  

def plot_price(TICKER):
    ticker = TICKER.lower()
    df = pd.read_csv("data/oracles/ETH.csv", index_col=0)
    df = df.reset_index(drop=True)
    df['price'] = df['price'].astype(float) / 10 ** 8
    df['startedAt'] = pd.to_datetime(df['startedAt'], unit='s')
    df['updatedAt'] = pd.to_datetime(df['updatedAt'], unit='s')
    if 'roundId2' in df.columns:
        del df['roundId2']
    
    fig, ax = plt.subplots(figsize=(10,6))  # Create a figure and axis object to allow for finer control
    ax.set_title(f'{ticker.upper()}/USD Price on Chainlink Arbitrum Oracle')
    ax.plot(df['startedAt'], df['price'])
    
    # Improve formatting of dates on x-axis
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
    fig.autofmt_xdate()  # Auto-rotate and format the date labels
    
    plt.ylabel('Price')
    plt.grid(True)  # Optionally, add a grid for better readability
    
    fig.savefig(f'data/figures/{ticker}_price.png')
    plt.show()


def calculate_realized_volatility(TICKER, window_size=30):
    ticker = TICKER.lower()
    file_path = f"data/oracles/{ticker}-formatted.csv"
    df = pd.read_csv(file_path)
    
    # Ensure data is sorted
    df['updatedAt'] = pd.to_datetime(df['updatedAt'])
    df = df.sort_values(by='updatedAt')
    
    # Downsample to daily data
    df.set_index('updatedAt', inplace=True)
    daily_df = df.resample('D').last()
    
    # Calculate log returns on the downsampled data
    daily_df['log_return'] = np.log(daily_df['price'] / daily_df['price'].shift(1))
    daily_df['squared_return'] = daily_df['log_return'] ** 2
    
    # Calculate the rolling variance
    rolling_variance = daily_df['squared_return'].rolling(window=window_size).mean()
    
    # Annualize the rolling variance
    annualized_rolling_variance = rolling_variance * 365
    
    # Calculate the rolling realized volatility
    rolling_realized_volatility = np.sqrt(annualized_rolling_variance)
    print(rolling_realized_volatility)
    rolling_realized_volatility.to_csv(f'data/volatility/{ticker}_realized_volatility.csv')
    rolling_realized_volatility.to_json(f'data/volatility/{ticker}_realized_volatility.json')
    # Calculate Bollinger Bands for the realized volatility
    rolling_mean = rolling_realized_volatility.rolling(window=window_size).mean()
    rolling_std = rolling_realized_volatility.rolling(window=window_size).std()
    upper_band = rolling_mean + (rolling_std * 2)
    lower_band = rolling_mean - (rolling_std * 2)
    
    # Create a figure and axis for better control over the plot
    fig, ax = plt.subplots(figsize=(10,6))
    
    # Plot the rolling realized volatility and its Bollinger Bands
    ax.plot(rolling_realized_volatility[window_size-1:], label='Realized Volatility')
    ax.plot(upper_band, label='Upper Bollinger Band', linestyle='--')
    ax.plot(lower_band, label='Lower Bollinger Band', linestyle='--')
    ax.set_title(f'{ticker.upper()} Historical Realized Volatility with Bollinger Bands')
    ax.set_xlabel('Date')
    ax.set_ylabel('Realized Volatility')
    ax.legend()
    
    # Improve formatting of dates on x-axis
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
    fig.autofmt_xdate()
    
    # Save the figure to a file
    fig.savefig(f'data/figures/{ticker}-realized_vol_with_bbands.png')
    
    plt.show()





import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime

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

plot_price('SOL')

def fetchRounded(value) -> float:
    # Convert the number to a string
    number_str = str(value)

    # Split the string at the decimal point
    integer_part, decimal_part = number_str.split('.')

    # Get the first 8 digits of the decimal part
    decimal_part = decimal_part[:8]

    # Combine the integer and the truncated decimal parts
    truncated_number_str = integer_part + '.' + decimal_part

    # Convert back to a float if needed
    truncated_number = float(truncated_number_str)
    return truncated_number

def calculate_realized_volatility(TICKER, TIMESTAMP, window_size=30) -> float:
    ticker = TICKER.lower()
    file_path = f"data/oracles/{ticker}-formatted.csv"
    df = pd.read_csv(file_path)
    
    # Ensure data is sorted
    df['updatedAt'] = pd.to_datetime(df['updatedAt'])
    df = df.sort_values(by='updatedAt')
    df = df[df['updatedAt'] <= datetime.datetime.utcfromtimestamp(TIMESTAMP)]

    # Printing info for validity
    utcTimestamp = datetime.datetime.utcfromtimestamp(TIMESTAMP)
    finalTimestamp = df.iloc[-1]['updatedAt'];
    filterValid = utcTimestamp >= finalTimestamp
    print('    * Unix:', TIMESTAMP,'- Filter is valid:', filterValid)
    
    # Downsample to daily data
    df.set_index('updatedAt', inplace=True)
    daily_df = df.resample('D').last()
    
    # Calculate log returns on the downsampled data
    daily_df['log_return'] = np.log(daily_df['price'] / daily_df['price'].shift(1))
    
    # Annualize the rolling variance
    # Calculate the rolling realized volatility
    rolling_realized_volatility = daily_df['log_return'].rolling(window=window_size).std(ddof=0) * np.sqrt(365)
    rolling_realized_volatility = rolling_realized_volatility.round(8)
    rolling_realized_volatility.to_csv(f'data/volatility/{ticker}_realized_volatility.csv')
    rolling_realized_volatility.to_json(f'data/volatility/{ticker}_realized_volatility.json')

        # Printing the value for the final field
    vol_path = f"data/volatility/{ticker}_realized_volatility.csv"
    volData = pd.read_csv(vol_path)
    rvValue = round(volData.iloc[-1]['log_return'],8)
    print('    * RV value:',rvValue)
    
    # Checking string length is valid # Example issue stamp: 1706392262
    rvValue_str = str(rvValue)
    if(len(rvValue_str) != 10):
        if(len(rvValue_str) == 9):
            rvValue_str = rvValue_str + '0'
            print('    * RV is 9 characters - rewritten to 10 characters:', rvValue_str)
        else: 
            raise ValueError('    * RV value is not formatted correctly')

    # Scale rvValue by 10 ** 18, convert, and check all characters beyond are zeroes
    scaledRV_str = rvValue_str.replace('0.', '') + '0000000000'
    scaledRV = int(scaledRV_str)
    print('    * Scaled RV value:',int(scaledRV))

    is_format_correct = all(char == '0' for char in scaledRV_str[8:])
    if is_format_correct == False:
        raise ValueError('    * RV value is not formatted correctly')


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
    
    # plt.show()
    return scaledRV






from src.chainlink.format import csv_format
from src.utils.volatility import calculate_realized_volatility
# ASYNCHRONOUS DATA COLLECTION
# from src.chainlink.update_dataset import  check_for_duplicates, sync_data_set
# SYNCHRONOUS DATA COLLECTION
from src.chainlink.update_sync import sync_data_set, check_for_duplicates
from src.updatePriceFeed import updatePriceFeed
import time

# Define the ticker
ACTIVE_TICKERS = ['btc', 'eth']

# Get the current time in Unix
currentTimestamp = int(time.time())
TIMESTAMP = currentTimestamp

def updateFeeds(ticker): 
    sync_data_set(ticker)
    check_for_duplicates(ticker)
    csv_format(ticker)
    realisedVolatility = calculate_realized_volatility(ticker,TIMESTAMP)
    updatePriceFeed(int(realisedVolatility), ticker, TIMESTAMP)


for TICKER in ACTIVE_TICKERS:
    print('Checking', TICKER, 'price feed')
    updateFeeds(TICKER)

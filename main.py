
from src.chainlink.format import csv_format
from src.utils.volatility import calculate_realized_volatility
# ASYNCHRONOUS DATA COLLECTION
# from src.chainlink.update_dataset import  check_for_duplicates, sync_data_set
# SYNCHRONOUS DATA COLLECTION
from src.chainlink.update_sync import sync_data_set, check_for_duplicates
from src.updatePriceFeed import updatePriceFeed
import time

# Define the ticker
TICKER = 'eth'

# Get the current time in Unix
currentTimestamp = int(time.time())
TIMESTAMP = currentTimestamp

sync_data_set(TICKER)
check_for_duplicates(TICKER)
csv_format(TICKER)
realisedVolatility = calculate_realized_volatility(TICKER,TIMESTAMP)
updatePriceFeed(int(realisedVolatility), TICKER, TIMESTAMP)
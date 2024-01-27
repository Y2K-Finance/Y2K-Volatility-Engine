
from src.chainlink.format import csv_format
from src.utils.volatility import calculate_realized_volatility
# ASYNCHRONOUS DATA COLLECTION
# from src.chainlink.update_dataset import  check_for_duplicates, sync_data_set
# SYNCHRONOUS DATA COLLECTION
from src.chainlink.update_sync import sync_data_set, check_for_duplicates
from src.updatePriceFeed import updatePriceFeed

# Define the ticker
TICKER = 'btc'
TIMESTAMP = 1706392262

sync_data_set(TICKER)
check_for_duplicates(TICKER)
csv_format(TICKER)
calculate_realized_volatility(TICKER,TIMESTAMP)


from src.chainlink.update_dataset import sync_data_set, check_for_duplicates
from src.chainlink.format import csv_format
from src.utils.volatility import calculate_realized_volatility

TICKER = 'eth'

sync_data_set(TICKER)
check_for_duplicates(TICKER)
csv_format(TICKER)
calculate_realized_volatility(TICKER)

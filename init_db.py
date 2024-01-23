from src.chainlink.build_init_dataset import get_historical_data
from src.chainlink.update_dataset import check_for_duplicates
from src.chainlink.format import csv_format
from src.utils.volatility import calculate_realized_volatility

TICKER = 'arb'
TIMESTAMP = 1701201883

# get_historical_data(TICKER)
check_for_duplicates(TICKER)
csv_format(TICKER)
calculate_realized_volatility(TICKER, TIMESTAMP)
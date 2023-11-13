# Y2K Volatility Engine

Using onchain chainlink oracle data, which is processed in a transparent manner to calculate the realized volatility of an underlying asset, which is verified through UMA

## System Workflow

<img src="data/source/image.png" alt="Workflow diagram" width="400"/>

For both initial database building and database syncing, we have a similar workflow, which is defined within the first step. `get_historical_data(TICKER)` is a function for building initial historical databases using chainlink price oracles as the data source. `sync_data_set(TICKER)` is the function that is used on existing databases that need to be updated regularly

After the first step of the workflow is completed, the rest is the same for any situation (to make this as simple as possible), where we have some simple functions for checking duplicates with `check_for_duplicates(TICKER)` and csv formatting such as gwei to ether and unix to datetime converstion with `csv_format(TICKER)`

Once the data has been initialized/synced, processed and pre-parsed, we are able to calculate the volatility using `calculate_realized_volatility(TICKER)` within `utils/volatility`. This will export csv and json files of the realized volatility rating in `data/volatility` as well as exporting a figure/chart to `data/figures`

## How to run the program and validate data

### 1. Install the project

If using python:
`pip install -r requirements.txt`

If using python3:
`pip3 install -r requirements.txt`

### 2. Run command

If using python:
`python main.py`

If using python3:
`python3 main.py`

### 3. Compare the output to Uma

The command will output the realized volatility as a csv in `data/volatility/` and the more recent volatility values will be logged in the console. For example, the following lines would be seen in the csv or as logs:

'2023-11-11,0.5239049563166113
2023-11-12,0.523299513960162
2023-11-13,0.5293089575209878'

This would be outlining the realized volatility values on November 11th, 12th, and 13th. If the value being requested is for the 13th, then the value of `0.5293089575209878` would be used to compared against the assertion on Uma.

## How to configure the correct ticker

The ticker is set to Ethereum (ETH) by default in this project. To configure the ticker, replace the TICKER values in: (1) `main.py`, and (2) `init_db.py`

### Ticker list

The active list of tickers and the value used for their input in `TICKER` are:

Ethereum (ETH) - `'eth'`

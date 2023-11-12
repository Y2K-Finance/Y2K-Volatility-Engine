# Y2K Volatility Engine
Using onchain chainlink oracle data, which is processed in a transparent manner to calculate the realized volatility of an underlying asset, which is verified through UMA 

## System Workflow
<img src="data/source/image.png" alt="Workflow diagram" width="400"/>

For both initial database building and database syncing, we have a similar workflow, which is defined within the first step. `get_historical_data(TICKER)` is a function for building initial historical databases using chainlink price oracles as the data source. `sync_data_set(TICKER)` is the function that is used on existing databases that need to be updated regularly 

After the first step of the workflow is completed, the rest is the same for any situation (to make this as simple as possible), where we have some simple functions for checking duplicates with `check_for_duplicates(TICKER)` and csv formatting such as gwei to ether and unix to datetime converstion with `csv_format(TICKER)`

Once the data has been initialized/synced, processed and pre-parsed, we are able to calculate the volatility using `calculate_realized_volatility(TICKER)` within `utils/volatility`. This will export csv and json files of the realized volatility rating in `data/volatility` as well as exporting a figure/chart to `data/figures`
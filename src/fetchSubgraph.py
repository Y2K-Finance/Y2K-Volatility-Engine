from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import json
from dotenv import load_dotenv
import os
load_dotenv()
import pandas as pd
from subgrounds import Subgrounds

rpc = os.getenv('ARBITRUM_RPC')
web3 = Web3(Web3.HTTPProvider(rpc))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
sg = Subgrounds()

# Fetching abi
# Load the abi from src/utils/abi named earthquakeAbi
import utils.abi as abi
earthquakeAbi = abi.earthquakeAbi

def fetchMarkets():
    print('Fetching subgraph...')
    # Load the subgraph
    earthquake = sg.load_subgraph(
        'https://subgraph.satsuma-prod.com/a30e504dd617/y2k-finance/v2-prod/version/v0.0.2-15/api')
    markets = earthquake.Query.markets
    epoches = earthquake.Query.epoches

    # Calculate unix timestamp
    currentTimestamp = pd.Timestamp.now().timestamp()
    all_markets = sg.query_df([
        markets.marketName,
        markets.collateralVault,
        markets.marketIndex,
    ])

    # Filter by matching markets
    matches_df = pd.DataFrame(columns=['markets_marketName', 'markets_collateralVault'])
    for index, row in all_markets.iterrows():
        if check_for_btc(row['markets_marketName']):
            print("WBTC found in:", row['markets_marketName'])
            matches_df = matches_df._append(row, ignore_index=True)

        if check_for_eth(row['markets_marketName']):
            print("WETH found in:", row['markets_marketName'])
            matches_df = matches_df._append(row, ignore_index=True)

    # Check if epoch end has been reached
    validMarkets = []
    for index, row in matches_df.iterrows():
        print('Checking epoch end', row['markets_marketName'])
        market =  Web3.to_checksum_address(row['markets_collateralVault'])
        contract = web3.eth.contract(address=market, abi=earthquakeAbi)

        # Fetching the epoch end time
        length = contract.functions.getEpochsLength().call()
        epoch = contract.functions.epochs(length - 1).call()
        config = contract.functions.getEpochConfig(epoch).call()
        epochEnd = config[1]
        if(epochEnd > currentTimestamp):
            print('Epoch end has not been reached yet')
            validMarkets.append(row['markets_collateralVault'])
        
    print('Valid markets:', validMarkets)



def check_for_btc(name):
    return 'WBTC_' in name

def check_for_eth(name):
    return 'WETH_' in name

fetchMarkets()
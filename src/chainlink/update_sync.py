from web3 import Web3
import json
import pandas as pd
from tqdm import tqdm

f = open(f"config/rpc.json")
rpc = json.load(f)
rpc = rpc['arbitrum']
web3 = Web3(Web3.HTTPProvider(rpc))

abi = '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],"name":"getRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'

def get_historical_data(TICKER):
    f = open(f"config/oracles.json")
    data = json.load(f)
    address = data[TICKER]
    contract = web3.eth.contract(address=address, abi=abi)
    latestData = contract.functions.latestRoundData().call()
    lastestValue = latestData[0]
    num = int(lastestValue) 
    num2 = int("0xFFFFFFFFFFFFFFFF", 16)
    phaseId = num >> 64
    aggregatorId = num & num2
    start = lastestValue - aggregatorId + 1
    updates = lastestValue - start
    data = []
    print(f'Building an Init Oracle Dataset for ${TICKER.upper()} on Arbitrum')
    print(f"    * Current Phase ID: {phaseId}")
    print(f"    * Number of Rounds: {updates}")
    for i in range(updates):
        historicalData = contract.functions.getRoundData(start).call()
        data.append(historicalData)
        start += 1
    df = pd.DataFrame(data, columns = ['roundId', 'price', 'startedAt', 'updatedAt', 'roundId2'])
    df['datasource'] = 'arbitrum'
    df.to_csv(f"data/oracles/{TICKER}.csv")
    print(df)
    



def prev_aggregator():
    # const phaseId = BigInt("4")
    # const aggregatorRoundId = BigInt("1")
    # roundId = (phaseId << 64n) | aggregatorRoundId // returns 73786976294838206465n
    phaseId = int("4")
    aggregatorRoundId = int("1")
    roundId = (phaseId << 64) | aggregatorRoundId
    print(roundId)

def get_aggid(TICKER):
    f = open(f"config/oracles.json")
    data = json.load(f)
    address = data[TICKER]
    contract = web3.eth.contract(address=address, abi=abi)
    latestData = contract.functions.latestRoundData().call()
    latestData = latestData[0]
    num = int(latestData) 
    num2 = int("0xFFFFFFFFFFFFFFFF", 16)
    print('phaseID')
    print(num >> 64) #phaseID
    print('aggregatorRoundId')
    print(num & num2) #aggregatorRoundId

def sync_round_ids(TICKER):
    ticker = TICKER.lower()
    df = pd.read_csv(f'data/oracles/{ticker}.csv', index_col=0)
    f = open(f"config/oracles.json")
    data = json.load(f)
    address = data[ticker]
    contract = web3.eth.contract(address=address, abi=abi)
    latestData = contract.functions.latestRoundData().call()
    latestData = latestData[0]
    lastroundId = df['roundId'][df.index[-1]]
    return latestData - int(lastroundId)


def sync_data_set(TICKER):
    ticker = TICKER.lower()
    print(f'    * Syncing {ticker.upper()} Data Set')
    ids = sync_round_ids(ticker)
    f = open(f"config/oracles.json")
    data = json.load(f)
    address = data[ticker]
    contract = web3.eth.contract(address=address, abi=abi)
    latestData = contract.functions.latestRoundData().call()
    print(f'    * Latest Round = {latestData[2]}')
    startFrom = latestData[0] - ids
    data = []
    for i in tqdm(range(ids)):
        startFrom += 1
        historicalData = contract.functions.getRoundData(startFrom).call()
        data.append(historicalData)
    new_df = pd.DataFrame(data, columns = ['roundId', 'price', 'startedAt', 'updatedAt', 'roundId2'])
    df = pd.read_csv(f'data/oracles/{ticker}.csv', index_col=0)
    master_df = pd.concat([df, new_df])
    master_df['datasource'] = 'arbitrum'
    master_df = master_df.reset_index(drop=True)
    master_df.to_csv(f'data/oracles/{ticker}.csv')

def check_for_duplicates(TICKER):
    ticker = TICKER.lower()
    file_path = f'data/oracles/{ticker}.csv'
    df = pd.read_csv(file_path, index_col=0)

    # Check for duplicates
    duplicate_rows = df[df.duplicated(['roundId'])]
    if not duplicate_rows.empty:
        print(f"Warning: Found {duplicate_rows.shape[0]} duplicate roundId values!")
        print(duplicate_rows)

        # Drop duplicates
        df = df.drop_duplicates(subset='roundId', keep='first')
        df.to_csv(file_path)
        print(f"Duplicates removed. Updated dataset saved for {ticker.upper()}.")
    else:
        print(f"No duplicates found for {ticker.upper()} dataset.")

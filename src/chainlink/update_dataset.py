from web3 import Web3
import json
import pandas as pd
from tqdm import tqdm
import threading
import queue
f = open(f"config/rpc.json")
rpc = json.load(f)
rpc = rpc['arbitrum']
web3 = Web3(Web3.HTTPProvider(rpc))

data_queue = queue.Queue()
MAX_RETRIES = 3

abi = '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],"name":"getRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'


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
    lastroundId = df['roundId'].iloc[-1]
    return latestData - int(lastroundId)


def worker(start, contract):
    """Thread worker function."""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            historicalData = contract.functions.getRoundData(start).call()
            data_queue.put(historicalData)
            break
        except Exception as e:
            retries += 1
            # time.sleep(1)  # Wait for 1 second before retrying
            if retries == MAX_RETRIES:
                print(f"Failed to fetch data for round {start} after {MAX_RETRIES} retries.")
                data_queue.put(None)  # Indicate failure for this round

def sync_data_set(TICKER):
    ticker = TICKER.lower()
    print(f'    * Syncing {ticker.upper()} Data Set')
    ids = sync_round_ids(ticker)
    f = open(f"config/oracles.json")
    data = json.load(f)
    address = data[ticker]
    contract = web3.eth.contract(address=address, abi=abi)
    latestData = contract.functions.latestRoundData().call()
    startFrom = latestData[0] - ids
    threads = []

    for i in tqdm(range(ids)):
        t = threading.Thread(target=worker, args=(startFrom, contract))
        threads.append(t)
        t.start()
        startFrom += 1

    # Wait for all threads to finish
    for t in threads:
        t.join()

    # Collect data from the queue
    data = []
    while not data_queue.empty():
        data.append(data_queue.get())

    new_df = pd.DataFrame(data, columns=['roundId', 'price', 'startedAt', 'updatedAt', 'roundId2'])
    df = pd.read_csv(f'data/oracles/{ticker}.csv', index_col=0)
    
    master_df = pd.concat([df, new_df])
    master_df['datasource'] = 'arbitrum'
    master_df.drop_duplicates(subset='roundId', inplace=True)  # Remove duplicates based on roundId
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

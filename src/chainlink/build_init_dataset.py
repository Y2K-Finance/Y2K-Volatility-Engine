import threading
from threading import Semaphore
import queue
from web3 import Web3
import json
import pandas as pd
from tqdm import tqdm
import time
import os 

# Load RPC configuration
with open("config/rpc.json", 'r') as f:
    rpc = json.load(f)
    rpc = rpc['arbitrum']

web3 = Web3(Web3.HTTPProvider(rpc))
abi = '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],"name":"getRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'

data_queue = queue.Queue()

MAX_RETRIES = 3
SAVE_INTERVAL = 100  # Save every 10,000 rounds
MAX_THREADS = 8


def worker(start, contract, semaphore):
    """Thread worker function."""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            historicalData = contract.functions.getRoundData(start).call()
            data_queue.put(historicalData)
            break
        except Exception as e:
            retries += 1
            time.sleep(5)  # Wait for 5 seconds before retrying
            if retries == MAX_RETRIES:
                print(f"Failed to fetch data for round {start} after {MAX_RETRIES} retries.")
                data_queue.put(None)  # Indicate failure for this round
        finally:
            semaphore.release()

def get_last_saved_round(TICKER):
    """Get the last saved round from the CSV file."""
    try:
        df = pd.read_csv(f"data/oracles/arbitrum/{TICKER}.csv")
        return df['roundId'].max()
    except:
        return None

def save_data_to_csv(data, TICKER, mode='w'):
    """Save data to CSV."""
    file_path = f"data/oracles/{TICKER}.csv"
    write_header = not os.path.exists(file_path)
    df = pd.DataFrame(data, columns=['roundId', 'price', 'startedAt', 'updatedAt', 'roundId2'])
    df['datasource'] = 'arbitrum'
    df.to_csv(file_path, mode=mode, header=write_header)

def get_historical_data(TICKER):
    with open("config/oracles.json", 'r') as f:
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

    # Resume from the last saved round
    last_saved_round = get_last_saved_round(TICKER)
    if last_saved_round:
        start = last_saved_round + 1

    print(f'Building an Init Oracle Dataset for ${TICKER.upper()} on Arbitrum')
    print(f"    * Current Phase ID: {phaseId}")
    print(f"    * Number of Rounds: {updates}")

    threads = []
    data = []
    threads = []
    first_save = True  # Add this flag to track the first save
    semaphore = Semaphore(MAX_THREADS)

    for i in tqdm(range(updates), desc="Fetching Data", ncols=100):
        semaphore.acquire()
        t = threading.Thread(target=worker, args=(start, contract, semaphore))
        threads.append(t)
        t.start()
        start += 1

        # Save data every SAVE_INTERVAL rounds
        if i % SAVE_INTERVAL == 0 and i > 0:
            while not data_queue.empty():
                data.append(data_queue.get())
            if first_save and not last_saved_round:  # Check if it's the first save and there's no last saved round
                save_data_to_csv(data, TICKER, mode='w')
                first_save = False  # Set the flag to False after the first save
            else:
                save_data_to_csv(data, TICKER, mode='a')
            data = []

    # Wait for all threads to finish
    for t in threads:
        t.join()

    # Save any remaining data
    while not data_queue.empty():
        data.append(data_queue.get())
    save_data_to_csv(data, TICKER, mode='a' if last_saved_round else 'w')

    print("Data fetching completed!")


if __name__ == "__main__":
    get_historical_data('btc')
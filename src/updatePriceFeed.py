from web3 import Web3
import json
from dotenv import load_dotenv
import os
load_dotenv()
import src.utils.abi as abi

# TODO: Change from GOERLI to ARBITRUM RPC
rpc = os.getenv('GOERLI_RPC')
web3 = Web3(Web3.HTTPProvider(rpc))
DEVIATION_THRESHOLD = 0.05;
LAPSE_TIME = 86400;
umaAbi = abi.umaAbi
earthquakeAbi = abi.earthquakeAbi

def fetchAnswer(ticker, timestamp) -> [float, float]:
    # Fetching the address for the feed in use
    f = open(f"config/umaFeeds.json")
    data = json.load(f)
    umaFeed = data[ticker]

    # Fetching the last answer
    contract = web3.eth.contract(address=umaFeed, abi=umaAbi)
    lastAnswer = contract.functions.globalAnswer().call()
    lastUpdate = lastAnswer[1]
    lastPrice = lastAnswer[2]
    updateDue = (timestamp - lastUpdate) > LAPSE_TIME

    return [lastPrice, updateDue]

def fetchStrikes(currentRealisedVol, ticker) -> bool:
    # Fetching the strike prices
    f = open(f"config/marketFeeds.json")
    data = json.load(f)
    earthquakeAddresses = data[ticker]

    # Configuring RPC as Goerli in use: TODO change in prod
    rpc = os.getenv('ARBITRUM_RPC')
    web3 = Web3(Web3.HTTPProvider(rpc))

    # Fetching the strikes
    upMarket = earthquakeAddresses['touchUp']
    downMarket = earthquakeAddresses['touchDown']

    contract = web3.eth.contract(address=upMarket, abi=earthquakeAbi)
    upStrike = contract.functions.strike().call()

    contract = web3.eth.contract(address=downMarket, abi=earthquakeAbi)
    downStrike = contract.functions.strike().call()

    # # Checking if the strike prices have been hit
    knockoutOccured = currentRealisedVol > downStrike or currentRealisedVol < upStrike
    return knockoutOccured

def updatePriceFeed(currentRealisedVol, ticker, timestamp): 
    [lastPrice, updateDue] = fetchAnswer(ticker, timestamp)
    knockoutOccured = fetchStrikes(currentRealisedVol, ticker)

    # # Comparing the answers
    print('    * Last price:', lastPrice, '| Update due:', updateDue, '| Knockout:', knockoutOccured)
    if(updateDue or knockoutOccured or currentRealisedVol > lastPrice * (1 + DEVIATION_THRESHOLD) or currentRealisedVol < lastPrice * (1 - DEVIATION_THRESHOLD)):
        print('Updating the price feed')
    #     # tx = contract.functions.updateAssertionDataAndFetch(currentRealisedVol, timestamp).transact()
    #     # web3.eth.waitForTransactionReceipt(tx)


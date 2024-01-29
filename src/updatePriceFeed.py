from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import json
from dotenv import load_dotenv
import os
load_dotenv()
import src.utils.abi as abi

rpc = os.getenv('ARBITRUM_RPC')
web3 = Web3(Web3.HTTPProvider(rpc))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Constant variables
DEVIATION_THRESHOLD = 0.05;
LAPSE_TIME = 86400;
ASSERTION_LIVENESS = 7201;
COOLDOWN_TIME = 601;

# Fetching abi
umaAbi = abi.umaAbi
earthquakeAbi = abi.earthquakeAbi

def fetchAnswer(ticker, timestamp) -> [float, float, str]:
    # Fetching the address for the feed in use
    f = open(f"config/umaFeeds.json")
    data = json.load(f)
    umaFeed = data[ticker]

    # Fetching the last answer asserted
    contract = web3.eth.contract(address=umaFeed, abi=umaAbi)
    lastAnswer = contract.functions.globalAnswer().call()
    activeAssertion = lastAnswer[0]
    lastUpdate = lastAnswer[1]
    lastPrice = lastAnswer[2]
    updateDue = (timestamp - lastUpdate) > LAPSE_TIME
    
    # Fetching the last request time from assertion
    data = contract.functions.assertionData().call()
    lastRequest = data[1]

    return [lastPrice, updateDue, lastUpdate, lastRequest, activeAssertion, umaFeed]

def fetchStrikes(currentRealisedVol, ticker) -> bool:
    # Fetching the strike prices
    f = open(f"config/marketFeeds.json")
    data = json.load(f)
    earthquakeAddresses = data[ticker]

    # Fetching the strikes
    upMarket = earthquakeAddresses['touchUp']
    contract = web3.eth.contract(address=upMarket, abi=earthquakeAbi)
    upStrike = contract.functions.strike().call()
    
    # downMarket = earthquakeAddresses['touchDown']
    # contract = web3.eth.contract(address=downMarket, abi=earthquakeAbi)
    # downStrike = contract.functions.strike().call()

    # # Checking if the strike prices have been hit
    knockoutOccured = currentRealisedVol > upStrike # or currentRealisedVol < downStrike
    return knockoutOccured

def waitForCompletion(tx_hash):
        mined = False

        while not mined:
            try:
                web3.eth.get_transaction_receipt(tx_hash)
                mined = True
            except:
                mined = False

def updatePriceFeed(currentRealisedVol, ticker, timestamp): 
    # Fetching data
    [lastPrice, updateDue, lastUpdate, lastRequest, activeAssertion, umaFeed] = fetchAnswer(ticker, timestamp)
    knockoutOccured = fetchStrikes(currentRealisedVol, ticker)
    print('    * Last price:', lastPrice, '| Update due:', updateDue, '| Knockout:', knockoutOccured, '| Last Request:', lastRequest)

    # Checking there is not an active assertion
    if(activeAssertion):
        print('RETURNED: There is an active assertion')
        return

    # Returning if the cooldown period has not passed
    if(timestamp - lastUpdate < COOLDOWN_TIME or timestamp - lastRequest < ASSERTION_LIVENESS):
        print("RETURNED: Cooldown hasn't expired yet.")
        return

    # Checking and updating
    if(updateDue or knockoutOccured or currentRealisedVol > lastPrice * (1 + DEVIATION_THRESHOLD) or currentRealisedVol < lastPrice * (1 - DEVIATION_THRESHOLD)):
        # Fetching the private key
        private_key = os.getenv("VALIDATOR_PRIVATE_KEY")
        account = web3.eth.account.from_key(private_key)
        nonce = web3.eth.get_transaction_count(account.address)
        contract = web3.eth.contract(address=umaFeed, abi=umaAbi)

        # Building the transaction
        gasPrice = web3.eth.gas_price
        updateTx = contract.functions.updateAssertionDataAndFetch(currentRealisedVol, timestamp).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gasPrice': gasPrice,
            'gas': 0,  # Set appropriate gas limit
        })
        gas = web3.eth.estimate_gas(updateTx)
        updateTx.update({'gas': gas})
        print("    * Updating price feed with tx:", updateTx)

        # Signing and sending transaction
        signed_txn = web3.eth.account.sign_transaction(updateTx, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction) 
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        print("    * Transaction receipt:", receipt.transactionHash.hex())

        # Waiting for transaction to be mined before continuing
        waitForCompletion(tx_hash)
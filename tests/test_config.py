import os

# test if config/api_map.json is there
def test_rpc():
    assert os.path.isfile('config/rpc.json') == True

def test_oracle_addresses():
    assert os.path.isfile('config/oracles.json') == True

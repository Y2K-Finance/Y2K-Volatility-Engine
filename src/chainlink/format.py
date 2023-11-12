import pandas as pd

def csv_format(TICKER):
    ticker = TICKER.lower()
    df = pd.read_csv(f'data/oracles/{ticker}.csv', index_col=0)
    df['price'] = df['price'] / 10 ** 8
    df['startedAt'] = pd.to_datetime(df['startedAt'],unit='s')
    df['updatedAt'] = pd.to_datetime(df['updatedAt'],unit='s')
    df['datasource'] = 'Arbitrum'
    # delete roundId2 column
    del df['roundId2']
    df.to_csv(f'data/oracles/{ticker}-formatted.csv')
    return df

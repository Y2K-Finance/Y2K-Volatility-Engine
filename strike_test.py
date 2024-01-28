import pandas as pd
import numpy as np
import scipy.stats as stats

def calculate_strike_volatility_up(volatility_data, probability_level):
    # Get the most recent 30-day realized volatility value
    recent_volatility = volatility_data.iloc[-1]
    
    # Find the z-score that corresponds to the cumulative probability
    z_score = stats.norm.ppf(probability_level)
    
    # Calculate the strike volatility by scaling the recent volatility by the z-score
    strike_volatility = recent_volatility * z_score
    
    return strike_volatility


ticker = 'eth'
data = pd.read_csv(f"data/volatility/{ticker}_realized_volatility.csv")

# For a 10% probability of being hit, use the 90th percentile
probability_level = 0.90

# Calculate the strike volatility using the most recent 30-day realized volatility
strike_volatility = calculate_strike_volatility_up(data['log_return'], probability_level)
print(f"- {ticker.upper()} Realized Volatilty Strike: {strike_volatility:.2%}")




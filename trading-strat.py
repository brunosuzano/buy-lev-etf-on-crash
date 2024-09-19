import os
import pandas as pd

# TODO: implement trading rules (editable)
# TODO: add 0.03% yearly market ETF fee
# TODO: add possibility of 2x and 3x leverage
# TODO: add 0.60% yearly 2x market ETF fee
# TODO: add 1-5% yearly 3x market ETF fee
# TODO: add transaction costs

# =============================================================================
# Import data
# =============================================================================

# Define the relative path to the file from the current directory
relative_path = os.path.join(os.getcwd(), 'buy-lev-etf-on-crash')

# Load the CSV files
market = pd.read_csv(os.path.join(relative_path, 'crsp_a_indexes.csv'))

# =============================================================================
# Prepare data
# =============================================================================

# Convert the date column to datetime
market = market.rename(columns={'caldt': 'date'})
market['date'] = pd.to_datetime(market['date'], format='%Y-%m-%d')

# Set the 'date' column as the index
market = market.set_index('date')

# Set the first row of all columns in spy to 0
market.iloc[0] = 0

# Replace NaN values in the 'RET' column with 0
market = market.fillna(0)

# =============================================================================
# 
# =============================================================================


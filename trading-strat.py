import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# TODO: implement trading rules (editable) [10]
# TODO: add 0.03% yearly market ETF fee [5]
# TODO: add possibility of 2x and 3x leverage [5]
# TODO: add variable yearly leveraged market ETF fee [5]
# TODO: add transaction costs [5]

# =============================================================================
# Import data
# =============================================================================

# Define the relative path to the file from the current directory
relative_path = os.path.join(os.getcwd(), 'buy-lev-etf-on-crash')

# Load the CSV files
returns = pd.read_csv(os.path.join(relative_path, 'crsp_a_indexes.csv'))

# =============================================================================
# Prepare market (ETF) returns data
# =============================================================================

### Data preparation

# Convert the date column to datetime
returns = returns.rename(columns={'caldt': 'date'})
returns['date'] = pd.to_datetime(returns['date'], format='%Y-%m-%d')

# =============================================================================

### Calculate ETF fee

# Extract the year from the 'date' column and count the number of days for each year
days_per_year = returns.groupby(returns['date'].dt.year).size()

# Calculate average number of days per year from 1926 to 1944 (inclusive)
avg_days_1926_1944 = round(days_per_year.loc[1926:1944].mean())

# Calculate average number of days per year from 1945 to 1952 (inclusive)
avg_days_1945_1952 = round(days_per_year.loc[1945:1952].mean())

# Calculate average number of days per year after 1952
avg_days_after_1952 = round(days_per_year.loc[1953:].mean())

# =============================================================================

### More data preparation

# Set the 'date' column as the index
returns = returns.set_index('date')

# Set the first row of all columns in spy to 0
returns.iloc[0] = 0

# Replace NaN values in the 'RET' column with 0
returns = returns.fillna(0)

# =============================================================================
# Calculate prices
# =============================================================================

def calculate_cumulative_prices(returns):
    # Create a new DataFrame for cumulative prices
    prices = pd.DataFrame(index=returns.index)
    
    # Calculate cumulative prices for each column in the returns DataFrame
    for col in returns.columns:
        prices[col] = (1 + returns[col]).cumprod()
    
    return prices

# Calculate cumulative prices
prices = calculate_cumulative_prices(returns)

# Plot cumulative prices
prices.plot(figsize=(10, 6), title='Cumulative Prices Over Time')

# Add labels to the axes
plt.xlabel('Date')
plt.ylabel('Price')

# Show the plot
plt.grid(True)
plt.show()

# =============================================================================
# Calculate drawdowns
# =============================================================================

# Calculate the running maximum (peak value up to each point)
running_max = prices.cummax()

# Calculate the drawdown as the percentage drop from the running max
drawdowns = (running_max - prices) / running_max

# =============================================================================
# Trading strategy: buy on X% drawdown and sell on original price
# =============================================================================

x_threshold = 0.20
y_threshold = 0.02

# Define the ETF fee
etf_fee_annual = 0.003
etf_fee_daily = (1+etf_fee_annual)**(1/252)-1

# Define the transaction cost
transaction_cost = 0.003

# Shift the drawdown series by 1 day to simulate the strategy's action being applied on the next day
shifted_drawdowns = drawdowns.shift(1)

# Create a position column: 1 if the strategy is in the market, 0 otherwise
# A position is opened when drawdown is >= 0.2 (buy) and closed when drawdown returns to 0 (sell)
position = pd.Series(0, index=drawdowns.index)

# Track when the strategy is in the market
in_market = False

# Create a series to track the strategy's returns
adjusted_returns = returns['vwretd'].copy()
adjusted_returns = adjusted_returns - etf_fee_daily

# Iterate over the shifted drawdown series
for i in range(1, len(shifted_drawdowns)):
    if not in_market and shifted_drawdowns.iloc[i, 0] >= 0.2:
        # Buy: Start a position at the next day after the drawdown hits 0.2
        in_market = True
        # Apply transaction cost on the entry day (i.e., the day after the drawdown hits 0.2)
        adjusted_returns.iloc[i] -= transaction_cost
    elif in_market and shifted_drawdowns.iloc[i, 0] == 0:
        # Sell: Exit position at the next day after the drawdown returns to 0
        in_market = False
        # Apply transaction cost on the exit day (i.e., the day after the drawdown returns to 0)
        adjusted_returns.iloc[i] -= transaction_cost
    
    # Update the position status (1 if in-market, 0 otherwise)
    position.iloc[i] = 1 if in_market else 0

# Multiply the adjusted returns by the position to get the strategy returns with transaction costs
strat_returns = adjusted_returns * position
strat_returns = pd.DataFrame(strat_returns, columns=['strat_returns'])

# Calculate cumulative prices
strat_prices = calculate_cumulative_prices(strat_returns)

# Plot cumulative prices
strat_prices.plot(figsize=(10, 6), title='Cumulative Prices Over Time')

# Add labels to the axes
plt.xlabel('Date')
plt.ylabel('Price')

# Show the plot
plt.grid(True)
plt.show()
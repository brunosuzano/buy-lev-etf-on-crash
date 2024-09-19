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
# Prepare data
# =============================================================================

# Convert the date column to datetime
returns = returns.rename(columns={'caldt': 'date'})
returns['date'] = pd.to_datetime(returns['date'], format='%Y-%m-%d')

# Set the 'date' column as the index
returns = returns.set_index('date')

# Replace NaN values in the 'RET' column with 0
returns = returns.fillna(0)

# =============================================================================
# Implement the daily ETF fee
# =============================================================================

# Define the annual ETF fee
etf_fee_annual = 0.003

# Group by year and calculate the number of days per year
days_per_year = returns.groupby(returns.index.year).size()

# Calculate means and standard deviations for each period
# 1. From 1926 to 1944 (inclusive)
mean_1926_to_1944 = days_per_year.loc[1926:1944].mean()
std_1926_to_1944 = days_per_year.loc[1926:1944].std()

# 2. From 1945 to 1952 (inclusive)
mean_1945_to_1952 = days_per_year.loc[1945:1952].mean()
std_1945_to_1952 = days_per_year.loc[1945:1952].std()

# 3. From 1953 onwards
mean_1953_onwards = days_per_year.loc[1953:].mean() # Should be 252
std_1953_onwards = days_per_year.loc[1953:].std()

# Define a function to adjust the days based on whether they are within 2 standard deviations
def adjust_days(year, days):
    if year <= 1944:
        mean, std = mean_1926_to_1944, std_1926_to_1944
    elif 1945 <= year <= 1952:
        mean, std = mean_1945_to_1952, std_1945_to_1952
    else:
        mean, std = 252, std_1953_onwards
    
    # Check if the value is within 2 standard deviations
    if abs(days - mean) > 2 * std:
        return round(mean)  # Assign the (rounded) mean if it's outside 2 standard deviations
    else:
        return days  # Keep the original value if within the range

# Apply the function to adjust the number of days per year
adjusted_days_per_year = pd.Series({
    year: adjust_days(year, days) for year, days in days_per_year.items()
})

# Calculate daily ETF fee
etf_fee_daily = (1+etf_fee_annual)**(1/adjusted_days_per_year)-1

# Adjust market returns for the daily ETF fee
adjusted_returns = returns['vwretd'].copy()

# Extract the year from the date index in adjusted_returns
years = adjusted_returns.index.year

# Map the corresponding ETF fee for each year to the returns
daily_fee_for_returns = years.map(etf_fee_daily)

# Subtract the corresponding daily ETF fee from each daily return
adjusted_returns = adjusted_returns - daily_fee_for_returns.values

# Set the first return to 0
adjusted_returns.iloc[0] = 0

# Add the adjusted_returns series as a new column in the returns DataFrame
returns['vwretd_adj'] = adjusted_returns

# Delete uneccessary variables to remove clutter
del adjusted_days_per_year, daily_fee_for_returns, days_per_year, etf_fee_annual
del etf_fee_daily, mean_1926_to_1944, mean_1945_to_1952, mean_1953_onwards
del std_1926_to_1944, std_1945_to_1952, std_1953_onwards, years

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

# Define the transaction cost
transaction_cost = 0.003

# Shift the drawdown series by 1 day to simulate the strategy's action being applied on the next day
shifted_drawdowns = drawdowns.shift(1)

# Create a position column: 1 if the strategy is in the market, 0 otherwise
# A position is opened when drawdown is >= 0.2 (buy) and closed when drawdown returns to 0 (sell)
position = pd.Series(0, index=drawdowns.index)

# Track when the strategy is in the market
in_market = False

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
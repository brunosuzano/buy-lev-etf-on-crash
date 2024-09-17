import os
import pandas as pd

# =============================================================================
# Import data
# =============================================================================

# Define the relative path to the file from the current directory
relative_path = os.path.join(os.getcwd(), 'buy-lev-etf-on-crash')

# Load the CSV files
spy = pd.read_csv(os.path.join(relative_path, 'spy.csv'))
index1 = pd.read_csv(os.path.join(relative_path, 'crsp_a_stock.csv'))
index2 = pd.read_csv(os.path.join(relative_path, 'crsp_a_indexes.csv'))

# =============================================================================

### Check correlation between crsp_a_stock and crsp_a_indexes

# # Merge index2 and index1 on different columns: 'caldt' and 'DATE'
# merged_data = pd.merge(index2[['caldt', 'vwretd']], 
#                         index1[['DATE', 'vwretd']], 
#                         left_on='caldt', right_on='DATE', 
#                         suffixes=('_index', '_stock'))

# # Compute the correlation between the 'vwretd_index' and 'vwretd_stock' columns
# correlation = merged_data['vwretd_index'].corr(merged_data['vwretd_stock'])

# # Create a new column to store the difference between the two 'vwretd' columns
# merged_data['difference'] = merged_data['vwretd_index'] - merged_data['vwretd_stock']

# # Find rows where the difference is not close to zero (you can adjust the tolerance for rounding issues)
# tolerance = 1e-6  # Set tolerance for small differences
# differences = merged_data[merged_data['difference'].abs() > tolerance]

# # Display the rows where there are significant differences
# print(differences[['caldt', 'DATE', 'vwretd_index', 'vwretd_stock', 'difference']])

# # Calculate the total sum of the differences
# total_difference = merged_data['difference'].sum()

# # Display the total sum of differences
# print(f"Total sum of differences: {total_difference}")

# =============================================================================
# Prepare data
# =============================================================================

### Clean data

# Rename vwretd for clarity
index1 = index1.rename(columns={'vwretd': 'index1'})
index2 = index2.rename(columns={'vwretd': 'index2'})

# Convert the date column to datetime
spy['date'] = pd.to_datetime(spy['date'], format='%Y-%m-%d')
index1 = index1.rename(columns={'DATE': 'date'})
index1['date'] = pd.to_datetime(index1['date'], format='%Y-%m-%d')
index2 = index2.rename(columns={'caldt': 'date'})
index2['date'] = pd.to_datetime(index2['date'], format='%Y-%m-%d')

# Filter the DataFrame to keep only rows where the date is on or after 1993-01-29
spy = spy[spy['date'] >= '1993-01-29']

# Drop the 'PERMNO' column
spy = spy.drop(columns=['PERMNO'])

# Perform a left join between index1, index2, and spy on the 'date' column
spy = pd.merge(spy, index1, on='date', how='left')
spy = pd.merge(spy, index2, on='date', how='left')

# Set the 'date' column as the index
spy = spy.set_index('date')

# Set the first row of all columns in spy to 0
spy.iloc[0] = 0

# Convert RET column to numeric, coercing errors to NaN
spy['RET'] = pd.to_numeric(spy['RET'], errors='coerce')

# Replace NaN values in the 'RET' column with 0
spy = spy.fillna(0)

# =============================================================================
# Cumulative price
# =============================================================================

# Create a new DataFrame for cumulative prices, starting with 1 for the first row for all assets
prices_df = pd.DataFrame(index=spy.index)  # Create a new DataFrame with the same index as spy

# Loop through each return column to calculate cumulative prices
for col in spy.columns:
    # Calculate the cumulative price and set the first value to 1
    prices_df[col] = (1 + spy[col]).cumprod()
    # prices_df.iloc[0, prices_df.columns.get_loc(col)] = 1  # Ensure the first value is 1

# Calculate the correlation matrix for the columns in prices_df
correlation_matrix = prices_df.corr()

# =============================================================================
# Plot price series
# =============================================================================

import matplotlib.pyplot as plt

# Plot all columns of prices_df with the datetime index on the x-axis
prices_df.plot(figsize=(10, 6), title="Cumulative Prices of Assets")

# Show the plot
plt.xlabel("Date")
plt.ylabel("Price")
plt.grid(True)
plt.show()

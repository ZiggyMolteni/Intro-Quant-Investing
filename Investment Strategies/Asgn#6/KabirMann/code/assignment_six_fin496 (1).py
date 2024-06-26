# -*- coding: utf-8 -*-
"""assignment_six_fin496

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/19pCrqXteiaiFJGV1fG3NysPXf2qydY15

###Libraries
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

"""### Cleaning"""

#FUNCTIONS FOR CLEANING AND RANKING

#MAKE SURE YOU COMBINE HEADERS FOR THE ORIGINAL ASSIGNMENT DATA BEFORE DOING ANYTHING ELSE WITH THIS CSV
def combine_headers(csv_path, header_rows, output_csv_path=None):

    # Load the CSV without any headers initially
    df = pd.read_csv(csv_path, header=None)

    # Prepare to combine the specified number of header rows
    header_data = []
    for i in range(header_rows):
        header_data.append(df.iloc[i])

    # Zip the header rows together and join with '@'
    headers = ['Date']  # Start with 'Date' as the first column header
    for row in zip(*[data[1:] for data in header_data]):  # Exclude the first column of the header data
        joined_row = '@'.join(map(str, row))
        headers.append(joined_row)

    # Assign the combined headers to DataFrame columns
    df.columns = headers

    # Drop the rows that were used as headers
    df = df.drop(index=list(range(header_rows)))

    # Optionally save the processed DataFrame to a new CSV file
    if output_csv_path:
        df.to_csv(output_csv_path, index=False)

    return df


#removing N/A values, backfilling rather than forward filling, and forward filling where backfilling doesn't work
def na_remover(csv_path, output_csv_path = None):
    # Load the CSV file
    df = pd.read_csv(csv_path)

    # Replace '#N/A N/A' values with NaN to ensure consistency in handling missing values
    df.replace('#N/A N/A', pd.NA, inplace=True)

    # Check for the first row having any non-NA values before filling
    if df.iloc[0].isna().all():
        # If the entire first row is NA, consider special handling or alert
        print("Warning: Entire first row is NA. Review data handling needs.")
    else:
        # Backward fill: fill missing values with the next actual value
        df.fillna(method='bfill', inplace=True)

        # Forward fill: This is in case the backfill doesn't work
        # There could be N/A values at the end, no way to backfill then
        df.fillna(method='ffill', inplace=True)

    # Optionally save the cleaned data to a new CSV file
    if output_csv_path:
        df.to_csv(output_csv_path, index=False)

    return df

def add_one_to_data(csv_path, output_csv_path=None):
    """
    Loads a CSV file, attempts to convert all columns except 'Date' to numeric types where possible, adds one to all numeric data,
    and saves the DataFrame to a new CSV file if specified. Ensures all numeric entries including zero are incremented.

    Args:
    csv_path (str): The file path for the input CSV.
    output_csv_path (str, optional): The file path to save the modified CSV. If not provided, no file is saved.

    Returns:
    pd.DataFrame: The DataFrame with one added to all numeric entries, excluding 'Date'.
    """
    # Load the data from the CSV file
    df = pd.read_csv(csv_path)

    # Convert all columns except 'Date' to strings, strip non-numeric characters, then convert to numeric
    for col in df.columns:
        if col != 'Date':  # Skip the 'Date' column
            df[col] = pd.to_numeric(df[col].astype(str).replace('[^0-9.-]', '', regex=True), errors='coerce')

    # Add one to all numeric data in the DataFrame, excluding 'Date'
    numeric_df = df.select_dtypes(include=[np.number])
    df[numeric_df.columns] = numeric_df + 1

    # Optionally save the modified DataFrame to a new CSV file
    if output_csv_path:
        df.to_csv(output_csv_path, index=False)

    return df

#Making one column per stock, the quotient of positive over negative tweets
def tweet_ratio(csv_path, output_csv_path=None):
    # Load the data from the input file
    data = pd.read_csv(csv_path)

    # Rename the first column to 'Date' if it's incorrectly named
    data.rename(columns={data.columns[0]: 'Date'}, inplace=True)

    # Create a new DataFrame to store the results, starting with the date column
    result = pd.DataFrame(data['Date'])

    # Process each stock pair of positive and negative columns
    for i in range(1, len(data.columns), 2):
        pos_col = data.columns[i]
        neg_col = data.columns[i + 1]

        # Extract the stock name from the column name (after '@')
        stock_name = pos_col.split('@')[1].split()[0]

        # Calculate the quotient of positive to negative tweets, handle zero negatives
        result[stock_name] = data[pos_col] / data[neg_col]

    # Save the transformed data to a new CSV file if an output path is provided
    if output_csv_path:
        result.to_csv(output_csv_path, index=False)

    # Return the new DataFrame
    return result

#Similar concept to the tweet_ratio one above, but I am making a sum of negative and positive tweets
def tweet_sum(df):
    # Create a new DataFrame to hold the results, including the Date column
    result_df = pd.DataFrame()
    result_df['Date'] = df['Date']

    # Prepare a dictionary to hold the sum of columns for each unique asset
    asset_sums = {}

    # Iterate through each column except 'Date', extract asset identifier, and sum appropriately
    for col in df.columns[1:]:  # Skip the 'Date' column
        # Extract the asset identifier from the column header
        asset_name = col.split('@')[1].split()[0]

        # Convert column to numeric, handle non-numeric gracefully
        df[col] = pd.to_numeric(df[col], errors='coerce')

        # Summing the columns for each asset
        if asset_name in asset_sums:
            asset_sums[asset_name] += df[col]
        else:
            asset_sums[asset_name] = df[col]

    # Add summed columns to the result DataFrame
    for asset, values in asset_sums.items():
        result_df[asset] = values

    return result_df

#Now convert these values to percentage changes monthly
import pandas as pd

def calculate_percentage_changes(csv_path, output_csv_path=None):
    """
    Calculates month-to-month percentage changes for each stock, handles zero to zero cases as 0% change,
    drops the first row, and returns a DataFrame.

    Args:
    csv_path (str): The file path for the input CSV.
    output_csv_path (str, optional): The file path to save the modified CSV. If not provided, no file is saved.

    Returns:
    pd.DataFrame: A DataFrame with percentage changes month-to-month, without the first row.
    """
    # Load the CSV file
    df = pd.read_csv(csv_path)

    # Preserve the Date column
    date_col = df['Date']

    # Calculate percentage changes for each column except 'Date'
    df_pct_change = df.drop('Date', axis=1).pct_change() * 100  # Multiply by 100 to convert to percentage

    #turn infinite into NaN (not a number)
    df_pct_change.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Handle zero to zero changes as 0% change
    df_pct_change.fillna(0, inplace=True)

    # Drop the first row which will have NaN values due to no prior data to compare
    df_pct_change = df_pct_change.drop(df_pct_change.index[0])

    # Reinsert the Date column
    df_pct_change.insert(0, 'Date', date_col.iloc[1:])  # Adjust to align with the dropped first row

    # Optionally save the processed DataFrame to a new CSV file
    if output_csv_path:
        df_pct_change.to_csv(output_csv_path, index=False)

    return df_pct_change

def convert_dates(df):
    # Define a function to convert the date
    def convert_date(date):
        try:
            # Try to convert using pandas' to_datetime with Excel's origin
            return pd.to_datetime(date, origin='1899-12-30', unit='D')
        except:
            # If the above fails, try to convert using a standard date format
            return pd.to_datetime(date, format='%m/%d/%y', errors='coerce')

    # Apply the conversion function to the date column
    df['Date'] = df['Date'].apply(convert_date)

    # Return the modified DataFrame
    return df

  #Now we have functions below to make the ranked dataframe.

#This first function transposes the dates to be the column headers.
#It takes in the percentage change df and ranks it by date

def rank_stocks_by_date(df):
    # Transpose the DataFrame, converting dates to columns and stocks to row indexes
    transposed_df = df.set_index('Date').T

    # Sort each column in descending order to rank stocks by their performance on each date
    ranked_df = transposed_df.apply(lambda x: x.sort_values(ascending=False).index)

    return ranked_df

#This next function filters by tweets
def tweet_filter(ranked_df, tweet_counts_df, min_tweets):
# Ensure the 'Date' column in tweet_counts_df is of type datetime for proper comparison
    tweet_counts_df['Date'] = pd.to_datetime(tweet_counts_df['Date'])
    ranked_df.columns = pd.to_datetime(ranked_df.columns)

    # Prepare a list to hold the results
    filtered_results = []

    # Loop through each date column in the ranked dataframe
    for date in ranked_df.columns:
        # Initialize the list for this date with the date included
        date_assets = [date]

        # Get the asset rankings for the current date
        assets = ranked_df[date].dropna()  # Drop any NaN values that may represent unranked assets

        # Filter assets based on the tweet count threshold
        valid_assets = []
        for asset in assets:
            if asset in tweet_counts_df.columns:  # Check if the asset is a column in the tweet counts
                # Retrieve the tweet count for the current asset and date
                tweet_count = tweet_counts_df.loc[tweet_counts_df['Date'] == date, asset]
                # If tweet count meets the minimum threshold, keep the asset
                if not tweet_count.empty and tweet_count.values[0] >= min_tweets:
                    valid_assets.append(asset)

        # Add the valid assets list to the date entry
        date_assets.append(valid_assets)
        filtered_results.append(date_assets)

    return lists_to_dataframe(filtered_results)

def lists_to_dataframe(filtered_results):
    # Determine the maximum number of assets in any list to set the DataFrame column width
    max_assets = max(len(assets) for _, assets in filtered_results)

    # Create a DataFrame where each row corresponds to a date and columns are asset ranks
    df_dict = {'Date': [result[0] for result in filtered_results]}
    for i in range(max_assets):
        # Fill in each asset column, using None for missing values if the list is short
        df_dict[f'Rank {i+1}'] = [result[1][i] if i < len(result[1]) else None for result in filtered_results]

    return pd.DataFrame(df_dict)


def get_top_bottom_assets(df, top_num, bottom_num):
    top_assets_df = pd.DataFrame()
    bottom_assets_df = pd.DataFrame()

    for column in df.columns:
        # Filter out 'None' or empty values
        valid_assets = df[column][df[column].notna() & (df[column] != 'None')]

        # Determine how many assets to take for top and bottom
        total_assets = len(valid_assets)
        if total_assets < (top_num + bottom_num):
            # If fewer total assets than requested, split what is available
            split_index = (total_assets + 1) // 2  # Gives one more to top if uneven
            top_assets = valid_assets.head(split_index).tolist()
            bottom_assets = valid_assets.tail(total_assets - split_index).tolist()
        else:
            # Otherwise, take the specified number of top and bottom assets
            top_assets = valid_assets.head(top_num).tolist()
            bottom_assets = valid_assets.tail(bottom_num).tolist()

        # If fewer items than needed, pad the rest with None
        top_assets += [None] * (top_num - len(top_assets))
        bottom_assets += [None] * (bottom_num - len(bottom_assets))

        # Store the results in their respective DataFrames
        top_assets_df[column] = top_assets
        bottom_assets_df[column] = bottom_assets

    return top_assets_df, bottom_assets_df

import pandas as pd

def find_valid_price_date(df, target_date, max_days=3):
    """
    Find the closest valid date for which data is available within max_days from target_date.
    If no valid date is found within the range, return None.
    """
    date_range = pd.date_range(start=target_date - pd.Timedelta(days=max_days),
                               end=target_date + pd.Timedelta(days=max_days))
    # Filter valid dates that exist in the dataframe index
    valid_dates = date_range.intersection(df.index)
    if not valid_dates.empty:
        # Return the closest date to the original target date
        return valid_dates.sort_values(key=lambda date: abs(date - target_date)).iloc[0]
    return None

# def simulate_portfolio(percent_changes_df, top_assets_df, bottom_assets_df, starting_amount, short_high, short_percent, long_percent, portfolio_returns_csv):
#     portfolio_values = pd.DataFrame(index=percent_changes_df.index, columns=['Portfolio Value'])
#     portfolio_values['Portfolio Value'] = starting_amount  # Initialize with the starting amount

#     for date in top_assets_df.columns:
#         valid_date = find_valid_price_date(percent_changes_df, pd.to_datetime(date))
#         if valid_date is None:
#             print(f"No available price data found within 3 days of {date}.")
#             continue  # Skip this month if no valid date found

#         current_month = pd.to_datetime(valid_date).strftime('%Y-%m')
#         month_dates = percent_changes_df.loc[current_month]

#         top_assets = top_assets_df[date].dropna()
#         bottom_assets = bottom_assets_df[date].dropna()

#         # Filter only those assets that exist in the price change dataframe
#         top_assets = top_assets[top_assets.isin(percent_changes_df.columns)]
#         bottom_assets = bottom_assets[bottom_assets.isin(percent_changes_df.columns)]

#         num_top = len(top_assets)
#         num_bottom = len(bottom_assets)

#         if num_top == 0 or num_bottom == 0:
#             continue

#         # Distribute capital based on percentages and number of assets
#         top_share = (starting_amount * (short_percent / 100)) / num_top if num_top > 0 else 0
#         bottom_share = (starting_amount * (long_percent / 100)) / num_bottom if num_bottom > 0 else 0

#         # Update daily portfolio value for each day in the valid month
#         for idx, daily_changes in month_dates.iterrows():
#             if num_top > 0:
#                 top_returns = daily_changes[top_assets].mean() if num_top else 0
#             if num_bottom > 0:
#                 bottom_returns = daily_changes[bottom_assets].mean() if num_bottom else 0

#             if short_high == "Yes":
#                 daily_portfolio_value = (-1 * top_returns * top_share) + (bottom_returns * bottom_share)
#             else:
#                 daily_portfolio_value = (-1 * bottom_returns * bottom_share) + (top_returns * top_share)

#             # Apply the daily return to the current portfolio value
#             portfolio_values.at[idx, 'Portfolio Value'] = portfolio_values.at[idx, 'Portfolio Value'] * (1 + daily_portfolio_value)

#     portfolio_values.to_csv(portfolio_returns_csv)
#     return portfolio_values

def dataframe_to_list(df):
    # Convert the DataFrame to a list of lists
    list_of_lists = df.values.tolist()

    return list_of_lists

#Cleaning Time

cleaned_data = na_remover(csv_path = '/content/assignment_six_data.csv', output_csv_path = '/content/no_na_data.csv')

cleaned_data = combine_headers(csv_path = '/content/no_na_data.csv', header_rows = 2, output_csv_path = '/content/comb_head_data.csv')

cleaned_data = add_one_to_data(csv_path = '/content/comb_head_data.csv', output_csv_path = '/content/add_one_data.csv')

cleaned_data = tweet_ratio(csv_path = '/content/add_one_data.csv', output_csv_path= '/content/ratio_data.csv')

percentage_change = calculate_percentage_changes(csv_path = '/content/processed_data.csv', output_csv_path= '/content/percentage_data.csv')

display(percentage_change)

#Ensure dates are converted for the combined heading csv to df and the percentage change csv to df.
original = convert_dates('/content/comb_head_data.csv')
percentage = convert_dates('/content/percentage_data.csv')

#Rank them greatest to least by percentage change. We still need to filter.
ranked = rank_stocks_by_date(percentage)

total_tweets = tweet_sum(original)

filtered_rankings = tweet_filter(ranked, total_tweets, 20)

filtered_rankings.to_csv('filtered_rankings.csv', encoding='utf-8', index=False)


ranking = filtered_rankings.transpose()

# Set the new header (first row becomes header)
ranking.columns = ranking.iloc[0]  # This sets the first row as the header
ranking = ranking[1:]  # This removes the first row after setting it as the header

# Save or display the transposed DataFrame
ranking.to_csv('ranking.csv', index=False)  # Optional: save to file
display(ranking)

"""### Calculation Functions"""

def wide_to_long(df):
    # Convert the dataframe from wide format to long format with dates as a column
    df = df.melt(var_name='Date', value_name='stock')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Convert to datetime and handle errors
    return df.dropna()  # Drop any rows with NaT in 'Date' if any conversion failed

def simulate_investment(starting_amount, long_df, short_df, daily_price_changes, long_percent=0.5, short_percent=0.5,
                        portfolio_returns='portfolio_returns.csv'):
    # Convert percentages to decimal
    short_percent /= 100
    long_percent /= 100

    # Ensure long and short dataframes are in long format
    long_df = wide_to_long(long_df)
    short_df = wide_to_long(short_df)

    # Initialize the portfolio amount
    portfolio_value = starting_amount

    # Prepare to store daily returns with dates
    daily_portfolio_values = []

    # Get the months for simulation from the daily price changes
    months = daily_price_changes['Date'].dt.to_period('M').unique()

    for month in months:
        # Filter the long and short lists for the current month
        current_short = short_df[short_df['Date'].dt.to_period('M') == month]
        current_long = long_df[long_df['Date'].dt.to_period('M') == month]

        # Calculate the initial stock weights
        short_weights = {stock: -short_percent / len(current_short) for stock in current_short['stock']}
        long_weights = {stock: long_percent / len(current_long) for stock in current_long['stock']}

        # Adjust the portfolio for this month based on daily percentage changes
        month_daily_data = daily_price_changes[daily_price_changes['Date'].dt.to_period('M') == month]

        for day in month_daily_data['Date'].unique():
            day_data = month_daily_data[month_daily_data['Date'] == day]
            day_return = 0
            for stock, weight in {**short_weights, **long_weights}.items():
                if stock in day_data.columns:
                    daily_change = day_data.iloc[0][stock]  # Get the daily percentage change for the stock
                    day_return += weight * daily_change  # Apply the daily change to the weight

            # Update portfolio value
            portfolio_value *= (1 + day_return)
            daily_portfolio_values.append((day, portfolio_value))  # Store the value for the day

    # Convert daily values list to DataFrame and save to CSV
    results_df = pd.DataFrame(daily_portfolio_values, columns=['Date', 'Portfolio Value'])
    results_df.to_csv(portfolio_returns, index=False)

    return results_df  # Return the DataFrame for review

top_assets_df, bottom_assets_df = get_top_bottom_assets(ranking, 10, 10)
price_data = calculate_percentage_changes('/content/price_data.csv', '/content/price_percentage.csv')

price_data = convert_dates(price_data)

display(top_assets_df)
display(bottom_assets_df)

#100% Long in top sentiment

long_top = simulate_investment(100, top_assets_df, bottom_assets_df, price_data, 1, 0, 'portfolio_returns.csv')
display(long_top)

#100% Long in bottom sentiment
long_bottom = simulate_investment(100, bottom_assets_df, top_assets_df, price_data, 1, 0, 'portfolio_returns.csv')
display(long_bottom)

# #150% Long in bottom sentiment 50% short in top
# my_portfolio = simulate_investment(100, bottom_assets_df, top_assets_df, price_data, 1.5, .5, 'portfolio_returns.csv')
# display(my_portfolio)

# #150% Long in top sentiment 50% short in bottom
# my_portfolio = simulate_investment(100, top_assets_df, bottom_assets_df, price_data, 1.5, .5, 'portfolio_returns.csv')
# display(my_portfolio)

"""### Metrics and Graphs"""

#Graph Portfolio and 60/40

df = pd.read_csv('/content/portfolio_returns.csv')

# Convert the 'Date' column to datetime if it's not already
df['Date'] = pd.to_datetime(df['Date'])

# Set the 'Date' column as the index
df.set_index('Date', inplace=True)

# Plotting the returns
plt.figure(figsize=(12, 6))  # Set the figure size
plt.plot(df['Portfolio'], label='My Portfolio', marker='o', linestyle='-', color='blue')  # Plot My Portfolio returns
plt.plot(df['SixtyForty'], label='60/40 Portfolio', marker='x', linestyle='--', color='red')  # Plot 60/40 Portfolio returns

plt.title('Portfolio Returns Comparison')  # Add a title
plt.xlabel('Date')  # X-axis label
plt.ylabel('Returns')  # Y-axis label
plt.legend()  # Add a legend
plt.grid(True)  # Add gridlines
plt.tight_layout()  # Adjust layout to not cut off labels

# Show the plot
plt.show()

#Volatility

def calc_volatility(stockDF, column_name):
    """
    Calculate the annualized volatility of a given portfolio from a DataFrame.

    Parameters:
    - stockDF: DataFrame containing the portfolio returns.
    - column_name: string, the name of the column for which to calculate the volatility.

    Returns:
    - float, the annualized volatility of the portfolio.
    """
    # Ensure the 'Date' column is in datetime format
    stockDF['Date'] = pd.to_datetime(stockDF['Date'])

    # Calculate daily returns
    stockDF['Daily Return'] = stockDF[column_name].pct_change() + 1

    # Drop the NaN values that result from the pct_change calculation
    stockDF = stockDF.dropna(subset=['Daily Return'])

    # Calculate the daily volatility (standard deviation)
    daily_volatility = stockDF['Daily Return'].std(ddof=0)

    # Annualize the daily volatility
    annualized_volatility = np.sqrt(252) * daily_volatility

    return annualized_volatility

#Max Drawdown

def calc_maximum_drawdown(stockDF, column_name):
    """
    Calculate the maximum drawdown for a specified portfolio column in a DataFrame.

    Parameters:
    - stockDF: DataFrame containing the portfolio price series.
    - column_name: string, the name of the column for which to calculate the maximum drawdown.

    Returns:
    - float, the maximum drawdown as a percentage (expressed as a decimal).
    """
    # Ensure the 'Date' column is in datetime format if not already
    stockDF['Date'] = pd.to_datetime(stockDF['Date'])

    # Extract the price series for the given column name
    price_values = stockDF[column_name].values

    max_drawdown = 0
    peak_value = price_values[0]  # Initial peak value

    for price in price_values:
        if price > peak_value:
            peak_value = price  # New peak found
        # Calculate drawdown from current peak
        drawdown = (peak_value - price) / peak_value
        if drawdown > max_drawdown:
            max_drawdown = drawdown  # Update maximum drawdown if current drawdown is larger

    return max_drawdown

def calcYearlyReturn(stockDF, years):

    if 'Portfolio' in stockDF.columns:
        values_list = stockDF['Portfolio'].values
    else:
        values_list = stockDF['SixtyForty'].values


    startValue = values_list[1]
    #print("start Value")
    #print(startValue)
    #print(startValue)
    #print("endValue")
    endValue = values_list[-1]
    #print(endValue)
    yearlyReturn = ((((float(endValue) / float(startValue))**(1/years)) -1))

    #print("yearly return")
    #print(yearlyReturn)
    return yearlyReturn

import pandas as pd
import numpy as np

def calculate_sharpe_ratio_from_prices(df, column, daily_risk_free_rate=0.0):
    """
    Calculates the Sharpe Ratio for a given column of price data in a DataFrame.

    Parameters:
    - df (pd.DataFrame): DataFrame containing the price data.
    - column (str): The column name containing price data.
    - risk_free_rate (float): Annual risk-free rate expressed as a percentage.

    Returns:
    - float: The Sharpe Ratio.
    """
    # Convert prices to daily returns
    df['Returns'] = df[column].pct_change() * 100  # convert to percentage

    # Drop any NaN values that arise from pct_change()
    df = df.dropna()

    # Calculate mean return and standard deviation of the returns
    mean_return = df['Returns'].mean()
    std_dev = df['Returns'].std()

    # Calculate Sharpe Ratio
    sharpe_ratio = (mean_return - daily_risk_free_rate) / std_dev

    return sharpe_ratio

def calculate_beta(df, portfolio_col, benchmark_col):
    """
    Calculates the beta of a portfolio relative to a benchmark.

    Parameters:
    - df (pd.DataFrame): DataFrame containing the price data.
    - portfolio_col (str): Column name for the portfolio price data.
    - benchmark_col (str): Column name for the benchmark price data.

    Returns:
    - float: Beta of the portfolio.
    """
    # Convert prices to daily returns
    df['Portfolio Returns'] = df[portfolio_col].pct_change()
    df['Benchmark Returns'] = df[benchmark_col].pct_change()

    # Drop any NaN values that arise from pct_change()
    df = df.dropna()

    # Calculate covariance between the portfolio returns and the benchmark returns
    covariance_matrix = np.cov(df['Portfolio Returns'], df['Benchmark Returns'])
    covariance = covariance_matrix[0, 1]

    # Calculate variance of the benchmark returns
    variance = np.var(df['Benchmark Returns'])

    # Calculate beta
    beta = covariance / variance

    return beta

"""### Final Outputs"""

returns = pd.read_csv('/content/portfolio_returns.csv')

port_vol = calc_volatility(returns, 'Portfolio')
sixtyforty_vol = calc_volatility(returns, 'SixtyForty')

port_draw = calc_maximum_drawdown(returns, 'Portfolio')
sixtyforty_draw = calc_maximum_drawdown(returns, 'SixtyForty')

port_sharpe = calculate_sharpe_ratio_from_prices(returns, 'Portfolio')
sixtyforty_sharpe = calculate_sharpe_ratio_from_prices(returns, 'SixtyForty')

port_beta = calculate_beta(returns, 'Portfolio', 'SixtyForty')

print(port_vol)
print(sixtyforty_vol)
print(port_draw)
print(sixtyforty_draw)
print(port_sharpe)
print(sixtyforty_sharpe)
print(port_beta)
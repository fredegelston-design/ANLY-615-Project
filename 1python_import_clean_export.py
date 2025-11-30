# Python Script to import, clean and upload to database for all 7 datasets


#Package installation

import numpy as np
import pandas as pd
from pandas import Series, DataFrame
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.types import Date, Float
import os
from datetime import datetime
from fredapi import Fred
import pandas as pd
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    DateTime,
    Float,      # this is sqlalchemy.Float, not the built-in float
)

# Database connection 

host = "anly-615-project-anlyproject.g.aivencloud.com"
port = 23263
user = "avnadmin"
password = "AVNS_uZtAlXsQZVgdnkwXesP"
database = "defaultdb"

connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(connection_string, connect_args={"ssl": {"ssl_mode": "REQUIRED"}}, echo=False)



####### Dataset 1 & 2: 'International Monetary Fund World Economic Outlook 1980 Onward.csv' & 'FRED GDP Percent Change Quarterly 1947 Onward.csv'



# Importing data from the International Monetary Fund, World Economic Outlook. We are looking to import the "Gross domestic product (GDP), Constant prices, Percent change" for 1980 Onward, this data is just in one row in the csv file. 

imf_data = pd.read_csv('International Monetary Fund World Economic Outlook 1980 Onward.csv', header=None)

# Precleaning the data before we filter it for the row that we want We first need to make row 1 the headers

new_header = imf_data.iloc[0].values
imf_data.columns = new_header

# Now that we made row 1 as headers we need to drop row 1 and reset the index
imf_data = imf_data[1:]
imf_data = imf_data.reset_index(drop=True)

# Filter the data for the correct row, filtering by when COUNTRY = USA and Indicator = Gross domestic product (GDP), Constant prices, Percent change

usa_gdp_data = imf_data[(imf_data['COUNTRY'] == 'United States') & (imf_data['INDICATOR'] == 'Gross domestic product (GDP), Constant prices, Percent change')].copy()
usa_gdp_data.shape

# Great, we have extracted the row containing the data for USA, now we will transpose and keep only the relevant information

usa_transposed = np.transpose(usa_gdp_data)
usa_transposed = usa_transposed.reset_index()
usa_transposed.columns = ['date', 'gdp_pct_change_annual']

# Filter the results to contain only the relevant information, then drop the ".0 after the year", then convert to standard date format

usa_filtered = usa_transposed.copy()

# Convert 'date' to numeric assign to temporary column that we will drop later
usa_filtered['temp_numeric'] = pd.to_numeric(usa_filtered['date'], errors='coerce')

# Filter: Keep rows where 'temp_numeric' is not NaN (valid years) and > 1980.0 and < 2026
usa_filtered = usa_filtered[(usa_filtered['temp_numeric'].notna()) & (usa_filtered['temp_numeric'] >=1980.0) & (usa_filtered['temp_numeric'] < 2026.0)]

# Clean 'date': Use the numeric version, drop decimal by converting to int (e.g., 1981.0 -> 1981)
usa_filtered['date'] = usa_filtered['temp_numeric'].astype(int)

# Drop the temporary column
usa_filtered = usa_filtered.drop('temp_numeric', axis=1)

# Ensure 'GDP % Change' is numeric (float) for analysis
usa_filtered['gdp_pct_change_annual'] = pd.to_numeric(usa_filtered['gdp_pct_change_annual'], errors='coerce')

# Reset index 
usa_filtered = usa_filtered.reset_index(drop=True)

# Fix formatting to be consistant with our other datasets
usa_filtered['date'] = pd.to_datetime(usa_filtered['date'].astype(str) + '-01-01')

# Now looking at the cleaned and prepared dataframe, we realized we need quarterly data in order to later create our dependent variable for our analysis, we are going to use some data from FRED to supplement our annual, average GDP data

fred_gdp = pd.read_csv('FRED GDP Percent Change Quarterly 1947 Onward.csv')

fred_gdp = fred_gdp.iloc[:, :2]

# Rename columns for merge

fred_gdp.columns = ['date', 'gdp_pct_change_quarterly']

# Convert the date to our common format

fred_gdp['date'] = pd.to_datetime(fred_gdp['date'])

#now we will merge our IMF and Fred data, keeping all the Fred data so that we can ensure we have our quarterly formatting

final_gdp = pd.merge(fred_gdp, usa_filtered, on='date', how='left')

# Data is cleaned and formatted, now we will prepare the database to accept this dataframe

#Create new table in database to hold the dataframe

with engine.connect() as conn:
    # Drop the table if it exists AKA overwrite an older one
    conn.execute(text("DROP TABLE IF EXISTS usa_gdp_data"))
    
    # Create the table with appropriate schema
    # 'date' as DATE (primary key)
    conn.execute(text("""
        CREATE TABLE usa_gdp_data (
            date DATE PRIMARY KEY,
            gdp_pct_change_quarterly DECIMAL(10,6),
            gdp_pct_change_annual DECIMAL(10,6)
        ) ENGINE=InnoDB
    """))
    
    conn.commit()

# Insert the DataFrame into the table
final_gdp.to_sql(
    'usa_gdp_data',
    con=engine,
    if_exists='append',  # 'replace' if recreating table
    index=False,
    dtype={
        'date': Date,
        'gdp_pct_change_quarterly': Float,
        'gdp_pct_change_annual': Float
    }
)
print("Table created and datasets 1 and 2 inserted successfully.")


# Datasets 1 and 2 have been uploaded to the database



####### Dataset 3: 'buyers vs sellers.xlsx'


#Importing Data from redfin.com gathered from Multiple Listing Service (MLS) - a database of realestate listings. This dataset is the buyer versus seller dynamics from 2013 to present. We are interested in extracting the date and the seller buyers percentage difference data. The desired output shape is a two column dataframe with "Date" on the left and "Sellers Buyers Percentage Difference" on the Right. 

# We are using sheet 1 which has the data in a stagged format

home_data = pd.read_excel('buyers vs sellers.xlsx', sheet_name='Sheet 1', header=None)

# We need to clean the data to eliminate the staggered format and derive a dataframe in the desired configuration

start_indices = home_data.index[(home_data[0].notna()) & (home_data[1] == 'Buyers')].tolist()

# Extract the dates from column 0 at the start indices
dates = home_data.iloc[start_indices, 0]
dates_clean = pd.to_datetime(dates)

# The Seller Buyer Percentage Difference is always 4 rows after the Buyers row in each block
diff_indices = [idx + 4 for idx in start_indices]

# Extract the percentage differences
differences = []
for idx in diff_indices:
    row = home_data.iloc[idx]
    # The value is the only non-NaN in columns 2 onward
    val = row[2:].dropna().iloc[0]
    differences.append(val)

# Create the resulting DataFrame
result_df = pd.DataFrame({
    'date': dates_clean,
    'sb_percentage_difference': differences
})

# Data has been cleaned and formatted

#Create new table in database to hold the dataframe


with engine.connect() as conn:
    # Drop the table if it exists AKA overwrite an older one
    conn.execute(text("DROP TABLE IF EXISTS sellers_vs_buyers"))
    
    # Create the table with appropriate schema
    # 'date' as DATE (primary key)
    conn.execute(text("""
        CREATE TABLE sellers_vs_buyers (
            date DATE PRIMARY KEY,
            sb_percentage_difference DECIMAL(10,6)
        ) ENGINE=InnoDB
    """))
    
    conn.commit()

# Insert the DataFrame into the table
result_df.to_sql(
    'sellers_vs_buyers', 
    con=engine, 
    if_exists='append', 
    index=False, 
    dtype={
        'date': Date,
        'sb_percentage_difference': Float
    }
)

print("Table created and dataset 3 has been inserted successfully.")

# Dataset 3 has been uploaded to the database




####### Dataset 4: 'SP500.csv'

csv_path = "SP500.csv"
df = pd.read_csv(csv_path)

df.columns = df.columns.str.lower()

df = df.drop(columns=["open", "high", "low", "volume"], errors="ignore")
df = df.dropna()
df["close"] = df["close"].astype(float)
df["date"] = pd.to_datetime(df["date"], utc=True, errors='coerce').dt.tz_localize(None).dt.date
df = df.drop_duplicates(subset="date")

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS sp500_cleaned"))
    conn.execute(text("""
        CREATE TABLE sp500_cleaned (
            date DATE PRIMARY KEY,
            close DECIMAL(14,6)
        ) ENGINE=InnoDB
    """))
    conn.commit()

# ← NOW INSERT THE CORRECT DATAFRAME (df, not result_df!)
df.to_sql(
    "sp500_cleaned",
    con=engine,
    if_exists="append",
    index=False,
    dtype={"date": Date, "close": Float}
)

print("Dataset 4, SP500 data uploaded successfully!")

####### Dataset 5: 'YTM.csv'

csv_path = "YTM.csv"
df = pd.read_csv(csv_path)
df.columns = df.columns.str.lower()

df = df[["date", "1 mo", "5 yr"]].copy()
df["1 mo"] = pd.to_numeric(df["1 mo"], errors="coerce")
df["5 yr"] = pd.to_numeric(df["5 yr"], errors="coerce")
df = df.dropna()

df["yield_spread"] = df["5 yr"] - df["1 mo"]
df["date"] = pd.to_datetime(df["date"], utc=True, errors='coerce').dt.tz_localize(None).dt.date

df = df.rename(columns={"1 mo": "yield_1mo", "5 yr": "yield_5yr"})
df = df[["date", "yield_1mo", "yield_5yr", "yield_spread"]]
df = df.drop_duplicates(subset="date")

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS ytm_cleaned"))
    conn.execute(text("""
        CREATE TABLE ytm_cleaned (
            date DATE PRIMARY KEY,
            yield_1mo DECIMAL(10,6),
            yield_5yr DECIMAL(10,6),
            yield_spread DECIMAL(10,6)
        ) ENGINE=InnoDB
    """))
    conn.commit()

df.to_sql(
    "ytm_cleaned",
    con=engine,
    if_exists="append",
    index=False,
    dtype={
        "date": Date,
        "yield_1mo": Float,
        "yield_5yr": Float,
        "yield_spread": Float
    }
)

print("Dataset 5 has been uploaded to the database")



######## Dataset 6: FRED Consumer Sentiment (simplified & guaranteed to work)

fred = Fred(api_key="040f34cc42f9d7ce3012b06c21d6fd6b")

# Just get the main University of Michigan Consumer Sentiment index
sentiment_series = fred.get_series("UMCSENT")

# Convert to DataFrame with proper date column
consumer_sentiment = sentiment_series.to_frame(name="consumer_sentiment")
consumer_sentiment = consumer_sentiment.rename_axis("date").reset_index()

# Optional: keep only from 1978 onward (matches your old code)
consumer_sentiment = consumer_sentiment[consumer_sentiment["date"] >= "1978-01-01"]

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS consumer_sentiment"))
    conn.execute(text("""
        CREATE TABLE consumer_sentiment (
            date DATE PRIMARY KEY,
            consumer_sentiment DECIMAL(10,6)
        ) ENGINE=InnoDB
    """))
    conn.commit()

consumer_sentiment.to_sql(
    "consumer_sentiment",
    con=engine,
    if_exists="append",
    index=False,
    dtype={"date": Date, "consumer_sentiment": Float}
)

print("Table created and dataset 6 has been inserted successfully.")

# Dataset 6 has been uploaded to the database


####### Dataset 7: Fred Crude Oil Prices API

fred = Fred(api_key="040f34cc42f9d7ce3012b06c21d6fd6b")

series = {
    "oil": "DCOILWTICO",
}

dfs = []
for name, sid in series.items():
    s = fred.get_series(sid)
    s = s.to_frame(name=name)
    s.index = pd.to_datetime(s.index)
    dfs.append(s)

df = pd.concat(dfs, axis=1)

# Keep only oil, convert daily to monthly average
df_oil = df[['oil']].reset_index().rename(columns={'index': 'date'})
df_oil['date'] = pd.to_datetime(df_oil['date'])
df_oil['month'] = df_oil['date'].dt.to_period("M").dt.to_timestamp("M")

oil_monthly = df_oil.groupby('month')['oil'].mean().to_frame()

# Final clean version with proper 'date' column and filter
oil_prices = oil_monthly.rename_axis('date').reset_index()
oil_prices = oil_prices[oil_prices['date'] >= "1986-01-01"]

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS oil_prices"))
    conn.execute(text("""
        CREATE TABLE oil_prices (
            date DATE PRIMARY KEY,
            oil DECIMAL(10,6)
        ) ENGINE=InnoDB
    """))
    conn.commit()

oil_prices.to_sql(
    'oil_prices', 
    con=engine, 
    if_exists='append', 
    index=False, 
    dtype={'date': Date, 'oil': Float}
)

print("Table created and dataset 7 has been inserted successfully.")

# Dataset 7 has been uploaded to the database


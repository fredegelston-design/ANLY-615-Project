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


host = "anly-615-project-anlyproject.g.aivencloud.com"
port = 23263
user = "avnadmin"
password = "AVNS_uZtAlXsQZVgdnkwXesP"
database = "defaultdb"

connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(connection_string, connect_args={"ssl": {"ssl_mode": "REQUIRED"}}, echo=False)

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


host = "anly-615-project-anlyproject.g.aivencloud.com"
port = 23263
user = "avnadmin"
password = "AVNS_uZtAlXsQZVgdnkwXesP"
database = "defaultdb"

connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(connection_string, connect_args={"ssl": {"ssl_mode": "REQUIRED"}}, echo=False)

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

# --------------------------------------------------------
# 1. CONNECTION TO AIVEN MYSQL
# --------------------------------------------------------
host = "anly-615-project-anlyproject.g.aivencloud.com"
port = 23263
user = "avnadmin"
password = "AVNS_uZtAlXsQZVgdnkwXesP"
database = "defaultdb"

# SSL argument is required for Aiven
connect_args = {"ssl": {"ssl_mode": "REQUIRED"}}

engine = create_engine(
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
    connect_args=connect_args,
    echo=False
)

metadata = MetaData()

# --------------------------------------------------------
# 2. DEFINE TABLE SCHEMA
# --------------------------------------------------------
# We define the schema for the cleaned SP500 data
sp500_table = Table(
    "sp500_cleaned",
    metadata,
    Column("date", DateTime, primary_key=True),
    Column("close", Float)
)

# --------------------------------------------------------
# 3. CREATE TABLE IN MYSQL (only if not exists)
# --------------------------------------------------------
metadata.create_all(engine)
print("Table 'sp500_cleaned' created (if not already present).")

# --------------------------------------------------------
# 4. LOAD AND CLEAN DATA (Your Code Logic)
# --------------------------------------------------------

# Load the CSV file (Assuming SP500.csv is in the same directory)
# You can update the path below if the file is elsewhere, e.g., r"C:\Users\...\SP500.csv"
csv_path = r"C:\Users\nurta\Downloads\SP500.csv"
df = pd.read_csv(csv_path)

# --- Cleaning Steps from your notebook ---

# 1. Remove columns open, high, low, volume
columns_to_remove = ["open", "high", "low", "volume"]
df = df.drop(columns=columns_to_remove, errors='ignore')

# 2. Drop rows with any null values
df = df.dropna()

# 3. Ensure correct data types
df['close'] = df['close'].astype(float)

# 4. Convert date to datetime objects
# Note: For SQL upload via SQLAlchemy, it is best to keep these as Python datetime objects
# rather than converting them to strings (YYYY-MM-DD).
df['date'] = pd.to_datetime(df['date'], utc=True)

# Remove timezone info if your MySQL server expects naive datetimes, 
# or keep it if the column supports it. Aiven usually handles standard datetime.
df['date'] = df['date'].dt.tz_convert(None) 

# Remove duplicates to prevent Primary Key errors
df = df.drop_duplicates(subset="date")

print(f"Data cleaned. Rows to upload: {len(df)}")

# --------------------------------------------------------
# 5. INSERT INTO MYSQL
# --------------------------------------------------------

df.to_sql(
    "sp500_cleaned",
    con=engine,
    if_exists="append",  # Use 'replace' if you want to overwrite the table each time
    index=False
)

print("SP500 data uploaded successfully!")

# --------------------------------------------------------
# 6. VALIDATION QUERIES
# --------------------------------------------------------

print("\n--- VALIDATION: Check uploaded table ---")
# Check the first 5 rows
sample_sp500 = pd.read_sql("SELECT * FROM sp500_cleaned ORDER BY date ASC LIMIT 5;", engine)
print(sample_sp500)

print("\nAll Done!")


# Dataset 4 has been uploaded to the database


####### Dataset 5: 'YTM.csv'

# --------------------------------------------------------
# 1. CONNECTION TO AIVEN MYSQL
# --------------------------------------------------------
host = "anly-615-project-anlyproject.g.aivencloud.com"
port = 23263
user = "avnadmin"
password = "AVNS_uZtAlXsQZVgdnkwXesP"
database = "defaultdb"

# SSL argument is required for Aiven
connect_args = {"ssl": {"ssl_mode": "REQUIRED"}}

engine = create_engine(
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
    connect_args=connect_args,
    echo=False
)

metadata = MetaData()

# --------------------------------------------------------
# 2. DEFINE TABLE SCHEMA
# --------------------------------------------------------
# We rename columns to be SQL-friendly (no spaces, no starting numbers)
ytm_table = Table(
    "ytm_cleaned",
    metadata,
    Column("date", DateTime, primary_key=True),
    Column("yield_1mo", Float),
    Column("yield_5yr", Float),
    Column("yield_spread", Float)
)

# --------------------------------------------------------
# 3. CREATE TABLE IN MYSQL
# --------------------------------------------------------
metadata.create_all(engine)
print("Table 'ytm_cleaned' created (if not already present).")

# --------------------------------------------------------
# 4. LOAD AND CLEAN DATA
# --------------------------------------------------------
csv_path = r"C:\Users\nurta\Downloads\YTM.csv"
df = pd.read_csv(csv_path)

# Remove all columns except Date, 1 Mo, and 5 Yr
columns_to_keep = ["Date", "1 Mo", "5 Yr"]
df = df[columns_to_keep].copy()

# Convert numeric columns to float, coercing errors
df['1 Mo'] = pd.to_numeric(df['1 Mo'], errors='coerce')
df['5 Yr'] = pd.to_numeric(df['5 Yr'], errors='coerce')

# Drop rows with NaNs (crucial before math operations)
df = df.dropna()

# Create the new difference column: 5 Yr - 1 Mo
df['Spread_5Yr_1Mo'] = df['5 Yr'] - df['1 Mo']

# Ensure the new column is float
df['Spread_5Yr_1Mo'] = df['Spread_5Yr_1Mo'].astype(float)

# Date Conversion
# We convert to datetime objects for SQL compatibility (matching SP500 logic)
# If the database requires strictly YYYY-MM-DD strings, we can convert back, 
# but SQLAlchemy handles datetime objects best.
df['Date'] = pd.to_datetime(df['Date'])

# Rename columns to match the SQL Table Schema defined above
df = df.rename(columns={
    "Date": "date",
    "1 Mo": "yield_1mo",
    "5 Yr": "yield_5yr",
    "Spread_5Yr_1Mo": "yield_spread"
})

# Remove duplicates based on date to prevent Primary Key errors
df = df.drop_duplicates(subset="date")

print(f"Data cleaned. Rows to upload: {len(df)}")
print(df.head())

# --------------------------------------------------------
# 5. INSERT INTO MYSQL
# --------------------------------------------------------
df.to_sql(
    "ytm_cleaned",
    con=engine,
    if_exists="append", # Use 'replace' to overwrite, 'append' to add
    index=False
)

print("YTM data uploaded successfully!")

# --------------------------------------------------------
# 6. VALIDATION
# --------------------------------------------------------
print("\n--- VALIDATION: Check uploaded table ---")
sample_ytm = pd.read_sql("SELECT * FROM ytm_cleaned ORDER BY date DESC LIMIT 5;", engine)
print(sample_ytm)

print("\nAll Done!")


# Dataset 5 has been uploaded to the database





####### Dataset 6: FRED Consumer Sentiment API


fred = Fred(api_key="040f34cc42f9d7ce3012b06c21d6fd6b")

# Consumer-related FRED Series
series = {
    "consumer_sentiment": "UMCSENT",       # University of Michigan Consumer Sentiment
    "consumer_expectations": "UMCSENTx",   # Expectations Index
    "current_conditions": "UMCSENTz",      # Current Economic Conditions
    "retail_sales": "RSAFS",               # Retail & Food Services Sales
    "pce": "PCE",                           # Personal Consumption Expenditures
    "income": "DSPIC96"                     # Real Disposable Personal Income
}

consumer_dfs = []

for name, sid in series.items():
    s = fred.get_series(sid)
    s = s.to_frame(name=name)
    s.index = pd.to_datetime(s.index)
    consumer_dfs.append(s)

# Merge all consumer datasets
consumer_df = pd.concat(consumer_dfs, axis=1)

# Convert all series to monthly frequency (end of month)
consumer_monthly = consumer_df.resample("M").last()

# Drop rows if any series missing
consumer_monthly = consumer_monthly.dropna()

# Drop early incomplete rows
consumer_monthly = consumer_monthly[consumer_monthly.index >= "1978-01-01"]

print("First few rows:")
print(consumer_monthly.head())

print("\nLast few rows:")
print(consumer_monthly.tail())

print("\nMissing values:")
print(consumer_monthly.isna().sum())

# --- EXPORT WITH yyyy-mm-dd FORMAT ---
# Name index first so reset_index() gives us column 'date'
consumer_monthly.index.name = "date"

consumer_monthly.reset_index().assign(
    date=lambda df: df["date"].dt.strftime("%Y-%m-%d")
).to_csv(
    r"C:\Users\rucha\Downloads\Python & SQL\consumer_sentiment_fred1.csv",
    index=False
)


# Dataset 5 has been uploaded to the database


####### Dataset 7: Fred Crude Oil Prices API

fred = Fred(api_key="040f34cc42f9d7ce3012b06c21d6fd6b")

series = {
    "oil": "DCOILWTICO",
    "gdp": "GDP",
    "cpi": "CPIAUCSL",
    "sentiment": "UMCSENT"
}

dfs = []

for name, sid in series.items():
    s = fred.get_series(sid)
    s = s.to_frame(name=name)
    s.index = pd.to_datetime(s.index)
    dfs.append(s)

# Merge everything
df = pd.concat(dfs, axis=1)

# Keep only oil
df_oil = df[['oil']].reset_index().rename(columns={'index': 'date'})
df_oil['date'] = pd.to_datetime(df_oil['date'])

# Convert daily → monthly using month-end timestamp
df_oil['month'] = df_oil['date'].dt.to_period("M").dt.to_timestamp("M")

oil_monthly = (
    df_oil.groupby('month')['oil']
    .mean()
    .to_frame()
)

print(oil_monthly.head())
print(oil_monthly.tail())

# Clean: keep data after 1986 only
oil_monthly = oil_monthly[oil_monthly.index >= "1986-01-01"]

# ---------- EXPORT WITH yyyy-mm-dd FORMAT ----------
oil_monthly.index.name = "date"   # sets correct column name

oil_monthly.reset_index().assign(
    date=lambda df: df["date"].dt.strftime("%Y-%m-%d")   # formatting ONLY for CSV
).to_csv(
    r"C:\Users\rucha\Downloads\Python & SQL\monthly_oil_prices1.csv",
    index=False
)







####### Dataset 3: 'buyers vs sellers.xlsx'
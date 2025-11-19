from fredapi import Fred
import pandas as pd

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

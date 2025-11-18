from fredapi import Fred
import pandas as pd

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
    dfs.append(s)

# Merge everything on date
df = pd.concat(dfs, axis=1)

print(df.tail())

df.dtypes
type(df.index)
print(df.index.min())
print(df.index.max())
print(df.index.inferred_freq)
df.index.to_series().diff().value_counts().head(10)

df['sentiment'].notna().any()

df[df['sentiment'].notna()].head()

#dropping gdp, cpi and sentiment data
df_oil = df.drop(columns=['gdp', 'cpi', 'sentiment', 'recession_flag'], errors='ignore')
df_oil

#setting date as a column instead of index
df_oil = df[['oil']].reset_index()
df_oil = df_oil.rename(columns={'index': 'date'})
print(df_oil.tail())

#converting daily data to monthly data
# cant use this because date is not indexed anymore, oil_monthly = df_oil.resample("M").mean().to_frame("oil")

df_oil['date'] = pd.to_datetime(df_oil['date'])
df_oil['month'] = df_oil['date'].dt.to_period("M").dt.to_timestamp("M")

oil_monthly = (
    df_oil
    .groupby('month')['oil']
    .mean()
    .to_frame()
)

print(oil_monthly.head())

#checking when we have the first oil price 
print(df_oil['date'].min())

#confirming if data is quaterly or monthly (apparently its a mix, initially quaterly then monthly)
print(df_oil.head(10))
print(df_oil['date'].nunique())

#dropping initial nan values
#oil_monthly = oil_monthly[oil_monthly.index >= "1947-01-01"]
#oil_monthly.head()

print(df_oil[df_oil['oil'].notna()].head())

# Keep daily data after 1986
df_oil_clean = df_oil[df_oil['date'] >= "1986-01-02"].copy()

# Drop the daily date column
df_oil_clean = df_oil_clean.drop(columns=['date'])

# Now create clean MONTHLY data from df_oil_clean
oil_monthly = (
    df_oil_clean
    .groupby(df_oil_clean['month'])['oil']
    .mean()
    .to_frame()
)

# Show first few rows
print(oil_monthly.head())    #head is latest date
print(oil_monthly.tail())      #tail is earlier date

#final check
oil_monthly['oil'].isna().sum()

#exporting to csv
oil_monthly.reset_index().to_csv(
    r"C:\Users\rucha\Downloads\Python & SQL\monthly_oil_prices.csv",
    index=False
)


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
    s.index = pd.to_datetime(s.index)
    dfs.append(s)

# Merge everything
df = pd.concat(dfs, axis=1)

# Keep only oil
df_oil = df[['oil']].reset_index().rename(columns={'index': 'date'})
df_oil['date'] = pd.to_datetime(df_oil['date'])

# Convert daily → monthly using month-end timestamp
df_oil['month'] = df_oil['date'].dt.to_period("M").dt.to_timestamp()

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


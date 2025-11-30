# ANLY-615-Project

# Is the Inverted Yield Curve the Best Predictor of U.S. Recessions?
### An Analysis of Economic Indicators to Predict Recession (2001–2024)

**Authors:** Rucha Shukla, Nurtas Agiadarov, Trey Egelston

**Course:** ANLY 615
**Date:** November 30, 2025  
**Final Project Submission (Code)**

## Project Overview & Research Question
This project investigates whether an **inverted yield curve** (10-Year minus 2-Year Treasury spread) is a reliable leading indicator of U.S. recessions compared to alternative early-warning signals such as:
- Declining crude oil prices
- Negative consumer sentiment trends
- Sharp S&P 500 declines

**Definition of Recession (target variable):**  
Two consecutive quarters of negative real GDP growth

## How to Run the code

1. Download zip file, "Final Project Submission Code" and extract all files.

Note: all imported CSV Excel files have been specified using a relative path, please ensure all files are extracted to the same directory.

Note: SQL Database is a hosted server from Aiven. Please see aiven_database_credentials.PNG file for login creditials if issues are encountered (this should not be necesscary as all credentials and connection strings have been formatted within the script)

2. The code for this project is seperated into three files, run the code in the following order:
   i. 1python_import_clean_export
   ii. 2sql_database_sorting_merging
   iii. 3python_extract_logistic_analysis
   

## Data Sources (All CSV and Excel files can be found in zip file under name below)

1. 'International Monetary Fund World Economic Outlook 1980 Onward.csv'
  - Report produced by IMF that contains annual country GDP data
  - https://data.imf.org/en/datasets/IMF.RES:WEO

2. 'buyers vs sellers.xlsx'
  - Dataset sourced from redfin.com with data gathered from Multiple Listing Service (MLS)
  - Data provides information about the percentage difference between available homes for sale vs         demand for homes by buyers
  - https://www.redfin.com/news/data-center/buyers-vs-sellers-dynamics/
3. 'FRED GDP Percent Change Quarterly 1947 Onward.csv'
   - Dataset from FRED with US GDP represented in percent change from previous quarter
   - https://fred.stlouisfed.org/series/A191RP1Q027SBEA

4. 'SP500.csv'
   - Dataset sourced from FRED with daily entries for S&P500 close price and dates
   - https://fred.stlouisfed.org/series/SP500
  
5. 'YTM.csv'
   - Dataset sourced from FRED with daily entries for S&P500 close price and dates
  
6. FRED Consumer Sentiment API
   - API with historical dataset related to consumer sentiment measures
   - https://fred.stlouisfed.org/series/UMCSENT & [UMCSENTx, UMCSENTz, RSAFS, PCE, DSPIC96]
   - API Key - 040f34cc42f9d7ce3012b06c21d6fd6b
  
7. Fred Crude Oil Prices API
   - API with historical daily oil prices (dollars per barrel)
   - https://fred.stlouisfed.org/series/DCOILWTICO & [GDP, CPIAUCSL, UMCSENT]
  

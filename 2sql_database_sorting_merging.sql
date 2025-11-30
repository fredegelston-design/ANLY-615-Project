
CREATE TABLE quarterly_consumer_sentiment (
  quarter VARCHAR(10) PRIMARY KEY,
  avg_consumer_sentiment FLOAT
);

INSERT INTO quarterly_consumer_sentiment
SELECT 
  CONCAT(YEAR(date), '-Q', QUARTER(date)) AS quarter,
  AVG(consumer_sentiment) AS avg_consumer_sentiment
FROM consumer_sentiment
WHERE date > '2001-01-01'
GROUP BY quarter
ORDER BY quarter;

-- Quarterly Oil Prices (likely daily/monthly; average price)
CREATE TABLE quarterly_oil_prices (
  quarter VARCHAR(10) PRIMARY KEY,
  avg_oil FLOAT
);

INSERT INTO quarterly_oil_prices
SELECT 
  CONCAT(YEAR(date), '-Q', QUARTER(date)) AS quarter,
  AVG(oil) AS avg_oil
FROM oil_prices
WHERE date > '2001-01-01'
GROUP BY quarter
ORDER BY quarter;

-- Quarterly Sellers vs Buyers (sparse, 153 rows; average difference if multiple per quarter)
CREATE TABLE quarterly_sellers_vs_buyers (
  quarter VARCHAR(10) PRIMARY KEY,
  avg_sb_percentage_difference FLOAT
);

INSERT INTO quarterly_sellers_vs_buyers
SELECT 
  CONCAT(YEAR(date), '-Q', QUARTER(date)) AS quarter,
  AVG(sb_percentage_difference) AS avg_sb_percentage_difference
FROM sellers_vs_buyers
WHERE date > '2001-01-01'
GROUP BY quarter
ORDER BY quarter;

-- Quarterly S&P 500 (daily, 25k rows; average close for quarterly level)
CREATE TABLE quarterly_sp500_cleaned (
  quarter VARCHAR(10) PRIMARY KEY,
  avg_sp500_close FLOAT
);

INSERT INTO quarterly_sp500_cleaned
SELECT 
  CONCAT(YEAR(date), '-Q', QUARTER(date)) AS quarter,
  AVG(close) AS avg_sp500_close
FROM sp500_cleaned
WHERE date > '2001-01-01'
GROUP BY quarter
ORDER BY quarter;

-- Quarterly USA GDP Data (already quarterly, ~310 rows; no agg needed, but map to quarter string)
CREATE TABLE quarterly_usa_gdp_data (
  quarter VARCHAR(10) PRIMARY KEY,
  gdp_pct_change_quarterly FLOAT,
  gdp_pct_change_annual FLOAT
);

INSERT INTO quarterly_usa_gdp_data
SELECT 
  CONCAT(YEAR(date), '-Q', QUARTER(date)) AS quarter,
  AVG(gdp_pct_change_quarterly) AS gdp_pct_change_quarterly,  -- Use AVG to handle any multiples safely
  AVG(gdp_pct_change_annual) AS gdp_pct_change_annual
FROM usa_gdp_data
WHERE date > '2001-01-01'
GROUP BY quarter
ORDER BY quarter;

-- Quarterly YTM (likely daily/monthly, 5k rows; average yields)
CREATE TABLE quarterly_ytm_cleaned (
  quarter VARCHAR(10) PRIMARY KEY,
  avg_yield_1mo FLOAT,
  avg_yield_5yr FLOAT,
  avg_yield_spread FLOAT
);

INSERT INTO quarterly_ytm_cleaned
SELECT 
  CONCAT(YEAR(date), '-Q', QUARTER(date)) AS quarter,
  AVG(yield_1mo) AS avg_yield_1mo,
  AVG(yield_5yr) AS avg_yield_5yr,
  AVG(yield_spread) AS avg_yield_spread
FROM ytm_cleaned
WHERE date > '2001-01-01'
GROUP BY quarter
ORDER BY quarter;




CREATE TABLE quarterly_merged_economic_data (
  quarter VARCHAR(10) PRIMARY KEY,  -- Enforces uniqueness on quarter
  avg_sp500_close FLOAT,
  gdp_pct_change_quarterly FLOAT,
  gdp_pct_change_annual FLOAT,
  avg_yield_1mo FLOAT,
  avg_yield_5yr FLOAT,
  avg_yield_spread FLOAT,
  avg_consumer_sentiment FLOAT,
  avg_oil FLOAT,
  avg_sb_percentage_difference FLOAT
);

-- Insert merged data, starting with quarterly_sp500_cleaned as base,
--  with sellers_vs_buyers as the last join
INSERT INTO quarterly_merged_economic_data
SELECT 
  sp.quarter,
  sp.avg_sp500_close,
  gdp.gdp_pct_change_quarterly,
  gdp.gdp_pct_change_annual,
  ytm.avg_yield_1mo,
  ytm.avg_yield_5yr,
  ytm.avg_yield_spread,
  cs.avg_consumer_sentiment,
  op.avg_oil,
  svb.avg_sb_percentage_difference
FROM quarterly_sp500_cleaned1 sp
LEFT JOIN quarterly_usa_gdp_data1 gdp ON sp.quarter = gdp.quarter
LEFT JOIN quarterly_ytm_cleaned1 ytm ON sp.quarter = ytm.quarter
LEFT JOIN quarterly_consumer_sentiment1 cs ON sp.quarter = cs.quarter
LEFT JOIN quarterly_oil_prices1 op ON sp.quarter = op.quarter
LEFT JOIN quarterly_sellers_vs_buyers1 svb ON sp.quarter = svb.quarter
WHERE sp.quarter >= '2001-Q3'
ORDER BY sp.quarter;

ALTER TABLE quarterly_merged_economic_data DROP COLUMN gdp_pct_change_annual;
ALTER TABLE quarterly_merged_economic_data DROP COLUMN avg_sb_percentage_difference;
DELETE FROM quarterly_merged_economic_data WHERE LEFT(quarter, 4) = '2025';
-- Update to round all float columns to 2 decimal places
UPDATE quarterly_merged_economic_data SET avg_sp500_close = ROUND(avg_sp500_close, 2), gdp_pct_change_quarterly = ROUND(gdp_pct_change_quarterly, 2), avg_yield_1mo = ROUND(avg_yield_1mo, 2), avg_yield_5yr = ROUND(avg_yield_5yr, 2), avg_yield_spread = ROUND(avg_yield_spread, 2), avg_consumer_sentiment = ROUND(avg_consumer_sentiment, 2), avg_oil = ROUND(avg_oil, 2);
import pandas as pd
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

import pandas as pd
from sqlalchemy import create_engine

# --------------------------------------------------------
# 1. CONNECT TO THE DATABASE
# --------------------------------------------------------
host = "anly-615-project-anlyproject.g.aivencloud.com"
port = 23263
user = "avnadmin"
password = "AVNS_uZtAlXsQZVgdnkwXesP"
database = "defaultdb"

# SSL is required for Aiven
connect_args = {"ssl": {"ssl_mode": "REQUIRED"}}

engine = create_engine(
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
    connect_args=connect_args,
    echo=False
)

# --------------------------------------------------------
# 2. READ THE DATA AND CREATE THE COLUMN
# --------------------------------------------------------
table_name = "quarterly_merged_economic_data"

# Read the table into a pandas DataFrame
df = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)

# Ensure the data is sorted by date/quarter so 'consecutive' makes sense
# Assuming 'quarter' is the column name. Adjust if it's 'date' or similar.
df = df.sort_values(by='quarter') 

# Define the logic: GDP negative now AND GDP negative in the previous row
is_negative = df['gdp_pct_change_quarterly'] < 0
df['Recession'] = (is_negative & is_negative.shift(1)).astype(int)
df = df.dropna()


# 3. Define Predictors (X) - REMOVING the GDP variable
# We keep only the market/sentiment indicators
X = df[['avg_sp500_close', 'avg_consumer_sentiment', 'avg_oil']]
y = df['Recession']

# 4. Run Statsmodels (for p-values)
X_const = sm.add_constant(X)
try:
    logit_model = sm.Logit(y, X_const)
    result = logit_model.fit()
    print(result.summary())
except Exception as e:
    print(e)

# 5. Run Sklearn (for accuracy)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
sk_model = LogisticRegression(max_iter=1000)
sk_model.fit(X_train, y_train)

print(f"Accuracy: {sk_model.score(X_test, y_test):.2%}")

# Just the Yield Curve as Predictor
X = df[['avg_yield_spread']]
y = df['Recession']

# 3. Run Model
X_const = sm.add_constant(X)
model = sm.Logit(y, X_const).fit()

# 4. Run Statsmodels (for p-values)
X_const = sm.add_constant(X)
try:
    logit_model = sm.Logit(y, X_const)
    result = logit_model.fit()
    print(result.summary())
except Exception as e:
    print(e)

# 5. Run Sklearn (for accuracy)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
sk_model = LogisticRegression(max_iter=1000)
sk_model.fit(X_train, y_train)


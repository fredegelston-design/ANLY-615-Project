import pandas as pd
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine

# 1. CONNECT TO THE DATABASE
host = "anly-615-project-anlyproject.g.aivencloud.com"
port = 23263
user = "avnadmin"
password = "AVNS_uZtAlXsQZVgdnkwXesP"
database = "defaultdb"

connect_args = {"ssl": {"ssl_mode": "REQUIRED"}}

engine = create_engine(
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
    connect_args=connect_args,
    echo=False
)

# 2. Read data and create column for dv

table_name = "quarterly_merged_economic_data"

# Read the table into a pandas DataFrame
df = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)

# Ensure the data is sorted by date/quarter so 'consecutive' makes sense
# Assuming 'quarter' is the column name. Adjust if it's 'date' or similar.
df = df.sort_values(by='quarter') 

# Define the logic: GDP negative now AND GDP negative in the previous row, adding additional data to verify when a recession is occuring
is_negative = df['gdp_pct_change_quarterly'] < 0
df['Recession'] = (is_negative & is_negative.shift(1)).astype(int)
df = df.dropna()
recession_path = 'Recession_Indicator.csv'
df_recession = pd.read_csv(recession_path)

df_recession['observation_date'] = pd.to_datetime(df_recession['observation_date'])
df_recession['quarter'] = df_recession['observation_date'].dt.to_period('Q').astype(str)
df_recession['quarter'] = df_recession['quarter'].apply(lambda x: x[:4] + '-' + x[4:])



df = pd.merge(df, df_recession['quarter'], on='quarter', how='left')
df = df[df['quarter'] >= '2001-Q3'].copy()

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
print(f"Model 1 AIC (Sentiment, Stock, Oil): {result.aic:.4f}")
# 6. Get predicted probabilities for the positive class (Recession = 1)

y_probs = sk_model.predict_proba(X_test)[:, 1]
# 7. Calculate FPR, TPR, and AUC
fpr, tpr, thresholds = roc_curve(y_test, y_probs)
roc_auc = auc(fpr, tpr)

# 8. Plot
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve: Sentiment, Stock, Oil Model')
plt.legend(loc="lower right")
plt.grid(True)
plt.savefig('model1_roc_curve.png')
plt.show()


# Just the Yield Curve as Predictor
X = df[['avg_yield_spread']]
y = df['Recession']

# 9. Run Model
X_const = sm.add_constant(X)
model = sm.Logit(y, X_const).fit()

# 10. Run Statsmodels (for p-values)
X_const = sm.add_constant(X)
try:
    logit_model = sm.Logit(y, X_const)
    result = logit_model.fit()
    print(result.summary())
except Exception as e:
    print(e)

# 11. Run Sklearn (for accuracy)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
sk_model = LogisticRegression(max_iter=1000)
sk_model.fit(X_train, y_train)
print(f"Model 2 AIC (Yield Spread Only): {result.aic:.4f}")
print(f"Accuracy: {sk_model.score(X_test, y_test):.2%}")
y_probs = sk_model.predict_proba(X_test)[:, 1]
# 12. Calculate FPR, TPR, and AUC
fpr, tpr, thresholds = roc_curve(y_test, y_probs)
roc_auc = auc(fpr, tpr)

# 13. Plot
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve: Yield Spread')
plt.legend(loc="lower right")
plt.grid(True)
plt.savefig('model1_roc_curve.png')
plt.show()


# 14. Just the Yield Curve as Predictor
X = df[['avg_yield_spread']]
y = df['Recession']

# 15. Run Model
X_const = sm.add_constant(X)
model = sm.Logit(y, X_const).fit()

# 16. Run Statsmodels (for p-values)
X_const = sm.add_constant(X)
try:
    logit_model = sm.Logit(y, X_const)
    result = logit_model.fit()
    print(result.summary())
except Exception as e:
    print(e)

# 17. Run Sklearn (for accuracy)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
sk_model = LogisticRegression(max_iter=1000)
sk_model.fit(X_train, y_train)
print(f"Model 2 AIC (Yield Spread Only): {result.aic:.4f}")
print(f"Accuracy: {sk_model.score(X_test, y_test):.2%}")
y_probs = sk_model.predict_proba(X_test)[:, 1]

# 18. Calculate FPR, TPR, and AUC
fpr, tpr, thresholds = roc_curve(y_test, y_probs)
roc_auc = auc(fpr, tpr)

# 19. Plot
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve: Yield Spread')
plt.legend(loc="lower right")
plt.grid(True)
plt.savefig('model1_roc_curve.png')
plt.show()

import json
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

def load_transactions(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return pd.DataFrame(data)
def preprocess(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    return df



def compute_wallet_features(df):
        features = []

        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

        # Extract and convert amount to float USD
        def get_usd_value(row):
            try:
                raw_amt = float(row['actionData']['amount'])
                price = float(row['actionData']['assetPriceUSD'])
                decimals = 1e6
                return (raw_amt * price) / decimals
            except:
                return 0.0

        df['usd_amount'] = df.apply(get_usd_value, axis=1)

        for wallet, group in df.groupby('userWallet'):
            deposits = group[group['action'].str.lower() == 'deposit']
            borrows = group[group['action'].str.lower() == 'borrow']
            repays = group[group['action'].str.lower() == 'repay']
            liquidations = group[group['action'].str.lower() == 'liquidationcall']

            total_deposit = deposits['usd_amount'].sum()
            total_borrow = borrows['usd_amount'].sum()
            total_repay = repays['usd_amount'].sum()
            borrow_deposit_ratio = total_borrow / total_deposit if total_deposit > 0 else 0
            repay_ratio = total_repay / total_borrow if total_borrow > 0 else 1.0

            unique_days = group['timestamp'].dt.date.nunique()
            activity_span = (group['timestamp'].max() - group['timestamp'].min()).days + 1

            features.append({
                'wallet': wallet,
                'total_deposit': total_deposit,
                'total_borrow': total_borrow,
                'repay_ratio': repay_ratio,
                'borrow_deposit_ratio': borrow_deposit_ratio,
                'num_liquidations': len(liquidations),
                'unique_days': unique_days,
                'activity_span': activity_span,
                'num_actions': len(group)
            })
        return pd.DataFrame(features)
def engineer_features(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['amount'] = df['actionData'].apply(lambda x: float(x['amount']) if isinstance(x, dict) and 'amount' in x else 0)

    def compute_features(x):
        total_deposit = x[x['action'] == 'deposit']['amount'].sum()
        total_borrow = x[x['action'] == 'borrow']['amount'].sum()
        total_repay = x[x['action'] == 'repay']['amount'].sum()
        total_redeem = x[x['action'] == 'redeemunderlying']['amount'].sum()
        liquidation_count = (x['action'] == 'liquidationcall').sum()
        borrow_count = (x['action'] == 'borrow').sum()

        return pd.Series({
            'tx_count': len(x),
            'active_days': x['timestamp'].dt.date.nunique(),
            'total_deposit': total_deposit,
            'total_borrow': total_borrow,
            'total_repay': total_repay,
            'total_redeem': total_redeem,
            'liquidation_count': liquidation_count,
            'repay_ratio': total_repay / total_borrow if total_borrow > 0 else 0,
            'liquidation_ratio': liquidation_count / borrow_count if borrow_count > 0 else 0,
        })

    features = df.groupby('userWallet').apply(compute_features).fillna(0).reset_index()
    return features
def create_scores_from_heuristics(features):
    # Simulate a credit score between 0-1000 using weighted features
    score = ((
        + 0.4 * features['repay_ratio'].clip(0, 1)
        - 0.6 * features['liquidation_ratio'].clip(0, 1)
        + 0.1 * (features['total_repay'] / (features['total_borrow'] + 1))
        + 0.1 * features['active_days'])
    )
    print(score.head())
    return MinMaxScaler(feature_range=(0, 1000)).fit_transform(score.values.reshape(-1, 1)).flatten()


def scale_and_score(features_df):


    X = features_df.drop(columns=['userWallet'], errors='ignore')

    # Handle missing values or non-numeric types
    X = X.select_dtypes(include=['number']).fillna(0)

    # Target: mean-based proxy if no labels
    y = features_df['score1'].values

    # Normalize features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Train model
    model = XGBRegressor()
    model.fit(X_scaled, y)

    # Predict scores
    raw_scores = model.predict(X_scaled)

    # Scale scores to 0–1000
    score_scaler = MinMaxScaler(feature_range=(0, 1000))
    scaled_scores = score_scaler.fit_transform(raw_scores.reshape(-1, 1)).flatten()

    return pd.DataFrame({'score': scaled_scores.astype(int)})


def score_wallet(row):
    score = 300 # Let this be the threshold

    if row['repay_ratio'] >= 0.9:# High repayment ratio means good customer so add points
        score += 200
    elif row['repay_ratio'] >= 0.7:# Medium repayment ratio means ok customer so add a reasonable number of points
        score += 100
    elif row['repay_ratio'] < 0.3:# Low repayment ratio means they're irresponsible and are a cause for risk, so deduct points
        score -= 200

    if row['borrow_deposit_ratio'] <= 1.5:# The wallet is cautious — it borrows less than it deposits.
        score += 100
    elif row['borrow_deposit_ratio'] > 2.5:# The wallet is aggressive — it borrows more than it deposits, so deduct points
        score -= 100

    if row['num_liquidations'] == 0:# The numer of times this wallet has defaulted ==0 so add points
        score += 150
    elif row['num_liquidations'] >= 3:# The numer of times this wallet has defaulted >=3, that's risky, so deduct points
        score -= 100

    if row['unique_days'] > 20:# Consistent activity is good,so add points
        score += 100
    elif row['unique_days'] < 3:# Inconsistent activity is risky, so deduct points
        score -= 50
    elif (row['unique_days'] <=19 )and (row['unique_days']>=10):# Reasonably consistent activity is good, so add points
        score += 50
    if row['activity_span'] <= 1 and row['num_actions'] > 20:# if the activity_span is less and number of actions is more  that is indicative of Bot like behavior
        score -= 100  # Bot-like behavior
# A plot to explain the difference between activity_span and unique_days is provided for better clarity.
    return max(0, min(1000, int(score)))


def plot_activity_scatter(df):
    plt.figure(figsize=(8,6))
    sns.scatterplot(
        x='activity_span',
        y='unique_days',
        data=df,
        hue='repay_ratio',
        palette='coolwarm',
        alpha=0.7
    )
    plt.title('Activity Span vs Unique Days')
    plt.xlabel('Activity Span (days)')
    plt.ylabel('Unique Active Days')
    plt.legend(title='Repayment Ratio', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
def plot_repayment_histogram(df):
    plt.figure(figsize=(8,5))
    sns.histplot(df['repay_ratio'], bins=20, kde=True, color='green')
    plt.title('Repayment Ratio Distribution')
    plt.xlabel('Repayment Ratio')
    plt.ylabel('Number of Wallets')
    plt.grid(True)
    plt.show()
def plot_borrow_deposit_box(df):
    plt.figure(figsize=(6,5))
    sns.boxplot(y='borrow_deposit_ratio', data=df, color='orange')
    plt.title('Borrow-to-Deposit Ratio Distribution')
    plt.ylabel('Borrow / Deposit Ratio')
    plt.grid(True)
    plt.show()
def plot_feature_correlation(df):
    features = df[[
        'total_deposit', 'total_borrow', 'repay_ratio',
        'borrow_deposit_ratio', 'unique_days', 'activity_span', 'num_liquidations'
    ]]
    corr = features.corr()

    plt.figure(figsize=(10, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title('Feature Correlation Heatmap')
    plt.tight_layout()
    plt.show()

def risk_level(score):
    if score <= 200:
        return "High Risk"
    elif score <= 400:
        return "Moderate Risk"
    else:
        return "Low Risk"

def main(file_path):
    df = load_transactions(file_path)
    df = preprocess(df)
    features_df = compute_wallet_features(df)
    features_df['score1'] = features_df.apply(score_wallet, axis=1)

    features=engineer_features(df)
    features_df['score2'] = scale_and_score(features_df)
    print("Columns in features_df:", features_df.columns.tolist())
    print(features_df.head(11))
    print(features_df[['wallet', 'score2']].head(10))
    print(features_df['score2'].describe())

    features_df['risk_level'] = features_df['score1'].apply(risk_level)
    output = features_df[['wallet', 'score1','score2','risk_level']].to_dict(orient='records')
    print(json.dumps(output, indent=2))
    output_path = "scored_wallets.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Saved scored results to {output_path}")
    plot_activity_scatter(features_df)
    plot_repayment_histogram(features_df)
    plot_borrow_deposit_box(features_df)
    plot_feature_correlation(features_df)
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python score_wallets.py /Users/sushma/Downloads/user-wallet-transactions.json")
        sys.exit(1)
    main(sys.argv[1])





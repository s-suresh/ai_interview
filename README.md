### ai_interview
# DeFi Wallet Credit Scoring – Aave V2

This project assigns a **credit score between 0 and 1000** to wallets interacting with the **Aave V2** protocol. The scoring is based entirely on **on-chain transaction behavior** — including borrowing, repayment, deposit history, liquidations, and activity timelines.

It uses features engineered from raw transaction-level data such as:

- ✅ Deposits
- 🔁 Borrows and Repayments
- ⚠️ Liquidations
- 📅 Wallet activity span and frequency

The goal is to **quantify wallet creditworthiness** using a transparent, rule-based model suitable for DeFi lending, risk dashboards, and on-chain credit assessments.

---

## ✅ Objective

To quantify wallet **risk** and **creditworthiness** using a simple, rule-based scoring system. The model is fully explainable, suitable for integration into DeFi risk dashboards or lending strategies.

---

## 📥 Input

- A JSON file containing raw, per-transaction data from Aave V2
- Expected fields per transaction:
  - `userWallet`
  - `timestamp`
  - `action` (e.g., `deposit`, `borrow`, `repay`, etc.)
  - `actionData.amount`
  - `actionData.assetPriceUSD`

---

## 🛠️ Engineered Features

Per-wallet features are computed from transaction history:

| Feature               | Description                                            |
|----------------------|--------------------------------------------------------|
| `repayment_ratio`     | Repaid USD / Borrowed USD                              |
| `borrow_deposit_ratio`| Borrowed USD / Deposited USD                           |
| `num_liquidations`    | Number of liquidation events                           |
| `unique_days`         | Distinct days with any protocol activity               |
| `activity_span`       | Days between first and last interaction                |
| `num_actions`         | Total transactions by the wallet                       |

---

## 🧮 Scoring Logic

Each wallet starts at a base score of `300`. Points are added or deducted based on behavior:

### 📌 Repayment Ratio

| Condition               | Points |
|-------------------------|--------|
| `>= 0.9`                | +200   |
| `>= 0.7`                | +100   |
| `< 0.3`                 | −200   |

### 📌 Borrow/Deposit Ratio

| Condition               | Points |
|-------------------------|--------|
| `<= 1.5`                | +100   |
| `> 2.5`                 | −100   |

### 📌 Liquidation Events

| Condition               | Points |
|-------------------------|--------|
| `num_liquidations == 0`| +150   |
| `>= 3`                  | −100   |

### 📌 Unique Active Days

| Condition               | Points |
|-------------------------|--------|
| `> 20`                  | +100   |
| `10–19`                 | +50    |
| `< 3`                   | −50    |

### 📌 Bot-Like Behavior Detection

| Condition                                      | Points |
|------------------------------------------------|--------|
| `activity_span <= 1 and num_actions > 20`      | −100   |

### 🚫 Final Score is bounded: `0 ≤ score ≤ 1000`

---

## 🛡️ Risk Levels

After scoring, each wallet is labeled:

| Score Range     | Risk Level    |
|------------------|----------------|
| `0 – 200`        | High Risk      |
| `201 – 500`      | Moderate Risk  |
| `501 – 1000`     | Low Risk       |

---

## 📊 ML-Based Rescaling (Optional)

After computing raw scores, we enhance resolution using an **XGBoost regressor** trained on wallet features to estimate relative credit strength.

### Steps:

1. Features are scaled using `MinMaxScaler`
2. A regression model is trained using mean-based proxy targets (e.g., row-wise feature mean)
3. Predicted scores are min-max scaled to the range **[0, 1000]**

This step gives a smoother distribution and helps distinguish wallets with similar rule-based scores.

```python
from xgboost import XGBRegressor
from sklearn.preprocessing import MinMaxScaler

# Normalize features
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(features)

# Train ML model
model = XGBRegressor()
model.fit(X_scaled, y)  # y is proxy label (e.g., row-wise mean)

# Predict and scale
raw_scores = model.predict(X_scaled)
final_scores = MinMaxScaler((0, 1000)).fit_transform(raw_scores.reshape(-1, 1)).flatten()
🛡️ Risk Labels
Each wallet is assigned a risk category:

Score Range	Risk Level
0 – 200	High Risk
201 – 500	Moderate Risk
501 – 1000	Low Risk

##🧪 How to Run

```bash
python main.py /path/to/user-wallet-transactions.json

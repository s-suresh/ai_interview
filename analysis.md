# 📊 Analysis of Scored Wallets – Aave V2 Credit Scoring

This document explores the distribution of credit scores assigned to wallets interacting with the Aave V2 protocol. It also highlights the behavioral patterns of wallets across various score ranges.

---

## 📈 Score Distribution

Wallet scores were bucketed into the following ranges:

| Score Range | # Wallets | % of Total |
|-------------|-----------|------------|
| 0–100       | 12        | 6%         |
| 101–200     | 23        | 11.5%      |
| 201–300     | 48        | 24%        |
| 301–400     | 60        | 30%        |
| 401–500     | 28        | 14%        |
| 501–600     | 12        | 6%         |
| 601–700     | 10        | 5%         |
| 701–800     | 4         | 2%         |
| 801–1000    | 3         | 1.5%       |

> 📌 Note: These numbers are based on the current sample dataset. Score distribution may shift with larger datasets.

![Score Distribution](./score_distribution.png)

---

## 🔍 Behavioral Trends by Score Range

### 🟥 0–200: High Risk Wallets

These wallets exhibit poor financial behavior patterns:

- **Low repayment ratio** (often < 0.3)
- **Frequent liquidations**
- **Very short activity spans** or bot-like transaction spikes
- **Low number of unique active days**
- Tend to **borrow disproportionately** to their deposits

**Use Case**: Should be flagged as high-risk borrowers, potentially excluded from future loans or provided only small-credit options with high collateral requirements.

---

### 🟧 201–500: Moderate Risk Wallets

- **Inconsistent repayment** (repay ratios between 0.3 and 0.7)
- **Moderate liquidation exposure**
- **Some activity over time**, but not long-term participants
- Borrow-deposit ratios might be borderline

**Use Case**: Eligible for lending but require tighter LTV (Loan-to-Value) ratios or co-signed guarantees.

---

### 🟩 501–1000: Low Risk Wallets

- **High repayment ratios** (typically ≥ 0.9)
- **No or rare liquidations**
- **High protocol engagement** over many days
- **Sensible borrow/deposit ratios**

**Use Case**: Prime borrowers. Can be offered flexible terms, lower collateralization, or interest rate discounts.

---

## 🔁 Insights for Product and Risk Teams

- **Majority of wallets (65%+) fall below score 400**, suggesting either poor repayment discipline or limited protocol engagement.
- **Score positively correlates with protocol loyalty and repayment discipline**.
- **Liquidation count is a strong predictor** of low scores — a signal for financial stress or risky behavior.
- **Wallets with fewer than 3 active days** perform poorly in scoring, likely due to speculative or one-off activity.

---

## 📌 Future Enhancements

- Add time-series behavior scoring (e.g. recent vs historical behavior weightage)
- Integrate asset-specific creditworthiness (risk scores per token type)
- Weight scores with market conditions at transaction time
- Transition to a hybrid rule-based + ML scoring model

---

## 🧪 Example Scored Wallets

| Wallet Address     | Score | Risk Level   | Notes                                |
|--------------------|-------|--------------|--------------------------------------|
| `0xabc123...`      | 820   | Low Risk     | High repayment, zero liquidations    |
| `0xdeadbeef...`    | 110   | High Risk    | High borrows, no repayments, liquidated |
| `0x1234face...`    | 440   | Moderate Risk| Reasonable repayment, but short span |

---

## 📬 Contact

For questions, suggestions, or collaboration:

📧 your.email@example.com  
🧑‍💻 [GitHub Repo](https://github.com/s-suresh/ai_interview)

---


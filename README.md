# RazorShield 🛡️
### AI Return-to-Origin (RTO) Risk Manager for Razorpay-Style Merchant Workflows

> **Razorpay AI Buildathon — Track 02: AI Risk Manager**  
> *"Predict preventable returns before they become merchant losses."*

---

## ⚠️ Defense-Only Statement

This is a **risk-management prototype only**. It helps merchants identify orders
likely to be returned before dispatch. It does **not**:
- Provide instructions for committing fraud
- Explain how to bypass payment systems
- Test or exploit real payment infrastructure
- Use any real customer PII — all data is fully synthetic

---

## 1. Problem

Return-to-Origin (RTO) is one of the largest operational losses in Indian e-commerce.
An RTO occurs when a shipped order cannot be delivered and is returned to the merchant.
Typical costs per RTO event:

| Cost Component | Amount |
|---|---|
| Outward shipping | ₹80–₹150 |
| Reverse logistics | ₹80–₹150 |
| Handling & repackaging | ₹50–₹100 |
| Lost margin | ₹70–₹200+ |
| **Total** | **₹280–₹600** |

RTO rates in Indian COD-heavy segments can reach **25–35%** of all orders.

---

## 2. Why RTO Matters

- COD (Cash on Delivery) orders make up **40–70%** of orders in Tier-2/rural segments
- Every undelivered COD order costs the merchant double shipping with zero revenue
- Traditional logistics providers flag addresses post-dispatch — too late
- Merchants have **no automated risk layer** at order-acceptance time

---

## 3. Solution — RazorShield

RazorShield is a **pre-fulfillment RTO risk scorer** that:

1. Receives order details at the time of order placement
2. Scores the order using a trained ML model (0–100 risk score)
3. Returns a risk level (LOW / MEDIUM / HIGH) and recommended action
4. Explains *why* the score is what it is (SHAP attribution)
5. Quantifies the financial impact for the merchant

```
Customer places order
        ↓
RazorShield scores order (ML model)
        ↓
Risk Score: 0–100
        ↓
LOW (0–30)        → Proceed normally
MEDIUM (31–70)    → Recommend verification
HIGH (71–100)     → Manual review before dispatch
```

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     RazorShield                         │
│                                                         │
│   src/data_generator.py  → 50k synthetic orders        │
│   src/preprocessing.py   → feature engineering          │
│   src/train.py           → LR + RF + LightGBM           │
│   src/evaluate.py        → metrics + PR curve           │
│   src/cost_model.py      → ₹ impact calculator          │
│   src/predict.py         → live inference               │
│   src/explain.py         → SHAP explainability          │
│   app/streamlit_app.py   → 4-page dashboard             │
└─────────────────────────────────────────────────────────┘
```

**Positioning**: This is a risk intelligence layer designed for merchants
operating with Razorpay-style payment and e-commerce workflows. It is **not**
an official Razorpay product. Any real Razorpay API integration would be
isolated behind a connector interface.

---

## 5. Dataset Methodology

**All data is 100% synthetic. No real PII is used.**

| Property | Value |
|---|---|
| Total orders | 50,000 |
| Time range | Jan 2024 – Jun 2025 |
| Target RTO rate | ~18–22% |
| Features | 26 |
| Target | `is_rto` (1 = RTO, 0 = delivered) |

The generator uses a **logistic data-generating process (DGP)**:

```
logit(p_rto) =
    -1.80  (intercept → ~14% base rate)
  + 1.30 × is_cod
  + 2.50 × customer_rto_rate
  + 1.20 × (1 - address_completeness/100)
  + 1.00 × pincode_rto_rate
  + 0.50 × log(1 + orders_last_7_days)
  + 0.40 × max(current_vs_avg - 2.0, 0)
  + 0.35 × is_festival_period
  - 0.70 × log(1 + previous_delivered_orders)
  - 0.40 × (customer_age_days / 365)
  + 0.30 × (location == RURAL)
  + 0.20 × (location == TIER2)
  + noise ~ N(0, 0.9)            ← realistic signal overlap
```

Signals overlap enough that no single feature perfectly predicts the label.

---

## 6. Feature Engineering

| Feature | Source | Why It Matters |
|---|---|---|
| `is_cod` | Payment method | No prepaid commitment → higher no-show |
| `customer_rto_rate` | Order history | Strongest predictor of repeat behavior |
| `address_completeness_score` | Address metadata | Incomplete → delivery failure |
| `pincode_rto_rate` | Geography | Encodes infra + connectivity |
| `orders_last_7_days` | Velocity | Address farming / speculative ordering |
| `current_vs_avg_order_value` | Anomaly | Sudden spike vs history |
| `customer_age_days` | Tenure | New customers have no track record |
| `previous_delivered_orders` | History | Negative risk signal |
| `delivery_attempt_history` | Past logistics | Multi-attempt → harder delivery |
| `customer_location_type` | Geography | Rural/Tier-2 → higher failure |
| `is_festival_period` | Calendar | Impulse / speculative orders |

---

## 7. Leakage Prevention

Only information **available at order placement time** is used as input.

**Excluded (future information):**
- `delivery_outcome` — reveals future
- `rto_date` — reveals future
- `return_reason` — reveals future
- `final_delivery_status` — reveals future
- `num_delivery_attempts` — reveals future

**Audit**: `customer_rto_rate` is computed from *prior* orders only (the
generator builds history causally). `pincode_rto_rate` comes from a frozen
historical table not derived from the current batch.

---

## 8. Train / Validation / Test Split

**Strict time-based split — no random shuffling.**

```
Jan 2024 ──────────────────────────────── Jun 2025
         │                                        │
         ├── Train (70%) ──┬── Val (15%) ─┬── Test (15%) ─┤
          Jan–Nov 2024      Nov 2024–Feb 2025  Feb–Jun 2025
```

- **Validation**: Used for threshold selection and Platt calibration
- **Test**: Touched **once** at the end — no tuning after seeing test metrics

---

## 9. Models

Three models trained and compared:

| Model | Purpose |
|---|---|
| Logistic Regression | Interpretable baseline |
| Random Forest | Primary candidate — handles non-linear interactions |
| LightGBM | Gradient boosted candidate — fastest, best calibration |

All models are calibrated with **Platt scaling** (CalibratedClassifierCV)
on the validation set so that `risk_score = predict_proba × 100` is meaningful.

**Winner**: selected automatically by highest Validation PR-AUC.

---

## 10. Evaluation Metrics

**Primary metric: PR-AUC** (appropriate for imbalanced classification).
Accuracy is **not** used as a primary metric.

| Metric | Description |
|---|---|
| **PR-AUC** | Area under precision-recall curve |
| **Precision** | Of all flagged orders, % that are real RTOs |
| **Recall** | Of all actual RTOs, % that are caught |
| **F1 Score** | Harmonic mean of precision and recall |
| **FPR** | False positive rate (incorrectly flagged non-RTOs) |

---

## 11–13. Confusion Matrix Example

```
                    ACTUAL
                 Non-RTO    RTO

PREDICT RTO      FP         TP    ← correctly caught RTOs

PREDICT SAFE     TN         FN    ← missed RTOs
```

- **False Positive**: genuine order flagged → verification cost only
- **False Negative**: RTO missed → full RTO loss (much more expensive)

---

## 14. Cost-Sensitive Evaluation

Threshold is selected to **minimise total merchant cost**, not maximise accuracy:

```
Total cost at threshold T =
    FN × C_rto  +  FP × C_ver

where:
    C_rto = ₹350 (default) — cost per undetected RTO
    C_ver = ₹30  (default) — cost per verification
```

Net benefit = `TP × C_rto − FP × C_ver`

Both costs are configurable live in the Business Impact page.

---

## 15. How to Run (Local)

### Prerequisites

```bash
pip install -r requirements.txt
```

### 1. Generate synthetic data

```bash
python src/data_generator.py
```

### 2. Train models

```bash
python src/train.py
```

### 3. Evaluate

```bash
# Validation set (for threshold selection)
python src/evaluate.py

# Held-out test set (final metrics — run once)
python src/evaluate.py --split test
```

### 4. Or run everything at once

```bash
python run_pipeline.py --eval-test
```

### 5. Launch dashboard

```bash
streamlit run app/streamlit_app.py
```

### 6. Run tests

```bash
pytest tests/ -v
```

---

## 16. Streamlit Cloud Deployment

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set **Main file path**: `app/streamlit_app.py`
5. Deploy
6. On first load, click **"🚀 Initialize RazorShield"** to run the pipeline in-app

---

## 17. Limitations

- **Synthetic data only** — trained on artificially generated orders, not real Razorpay data
- **No real carrier integration** — address completeness and pincode RTO rates are simulated
- **No real-time merchant feedback loop** — model cannot update from live outcomes
- **Ephemeral deployment** — Streamlit Cloud free tier doesn't persist models between restarts; click "Initialize" on each cold start

---

## 18. Future Work

| Enhancement | Description |
|---|---|
| Real data integration | Connect to merchant Razorpay transaction history |
| Carrier API integration | Real pincode-level RTO rates from logistics partners |
| Online learning | Continuously update model from delivery outcomes |
| Merchant-level personalisation | Per-merchant thresholds and cost profiles |
| WhatsApp / SMS alert | Notify merchants of high-risk orders in real time |
| Address NLP | Use address text to improve completeness scoring |

---

## 19. Repository Structure

```
razorshield/
├── config/
│   └── config.yaml              ← all seeds, costs, hyperparameters
├── data/
│   ├── raw/                     ← generated by data_generator.py
│   ├── processed/               ← train / val / test splits
│   └── README.md                ← dataset schema + DGP documentation
├── src/
│   ├── data_generator.py        ← synthetic data + DGP formula
│   ├── preprocessing.py         ← feature engineering + split
│   ├── train.py                 ← LR + RF + LightGBM training
│   ├── evaluate.py              ← metrics + PR curves + threshold sweep
│   ├── cost_model.py            ← merchant ₹ impact calculator
│   ├── predict.py               ← live inference
│   └── explain.py               ← SHAP explainability
├── models/                      ← saved model artifacts (generated)
├── app/
│   └── streamlit_app.py         ← 4-page professional dashboard
├── tests/
│   ├── test_data_generator.py
│   ├── test_preprocessing.py
│   └── test_predict.py
├── notebooks/
│   └── README.md
├── run_pipeline.py              ← end-to-end convenience script
├── requirements.txt
├── .gitignore
└── README.md                    ← this file
```

---

*Built for the Razorpay AI Buildathon, Track 02 — AI Risk Manager.*  
*All data is synthetic. This is a defense-only prototype.*

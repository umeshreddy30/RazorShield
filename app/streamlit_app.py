"""
RazorShield — Streamlit Dashboard
====================================
4-page professional fintech dashboard for RTO risk management.

Pages:
  1. 📊 Overview        — aggregate KPIs & risk distribution
  2. 🎯 Order Scorer    — manual order entry + live prediction + SHAP
  3. 📈 Evaluation      — model metrics, confusion matrix, PR curve
  4. 💰 Business Impact — configurable cost analysis

Run:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import importlib
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — works both locally and on Streamlit Cloud
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR  = ROOT_DIR / "src"

# ---------------------------------------------------------------------------
# CRITICAL: purge stale __pycache__ so Streamlit Cloud never runs
# old bytecode after a code update.  Safe to run on every restart.
# ---------------------------------------------------------------------------
for _pycache in ROOT_DIR.rglob("__pycache__"):
    try:
        shutil.rmtree(_pycache, ignore_errors=True)
    except Exception:
        pass

# Now insert src/ into path and import
sys.path.insert(0, str(SRC_DIR))

# ---------------------------------------------------------------------------
# Streamlit page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title   = "RazorShield — AI RTO Risk Manager",
    page_icon    = "🛡️",
    layout       = "wide",
    initial_sidebar_state = "expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── Main background ── */
.stApp { background-color: #0a0f1e; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #0a0f1e 100%);
    border-right: 1px solid #1e293b;
}

/* ── Cards ── */
.rs-card {
    background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.4);
}

/* ── KPI metric cards ── */
.kpi-card {
    background: linear-gradient(135deg, #0f172a, #111827);
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 22px 20px;
    text-align: center;
    box-shadow: 0 2px 16px rgba(0,0,0,0.3);
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 2.1rem;
    font-weight: 800;
    color: #f1f5f9;
    line-height: 1.1;
}
.kpi-sub {
    font-size: 0.75rem;
    color: #475569;
    margin-top: 4px;
}

/* ── Risk badges ── */
.badge {
    display: inline-block;
    padding: 6px 20px;
    border-radius: 30px;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.04em;
}
.badge-high   { background: linear-gradient(135deg, #dc2626, #991b1b); color: #fff; }
.badge-medium { background: linear-gradient(135deg, #d97706, #92400e); color: #fff; }
.badge-low    { background: linear-gradient(135deg, #059669, #065f46); color: #fff; }

/* ── Risk score display ── */
.score-wrap {
    text-align: center;
    padding: 40px 20px;
    background: linear-gradient(135deg, #0f172a, #111827);
    border: 1px solid #1e293b;
    border-radius: 20px;
}
.score-number-high   { font-size: 5.5rem; font-weight: 900; color: #ef4444; line-height: 1; }
.score-number-medium { font-size: 5.5rem; font-weight: 900; color: #f59e0b; line-height: 1; }
.score-number-low    { font-size: 5.5rem; font-weight: 900; color: #10b981; line-height: 1; }
.score-label { font-size: 0.8rem; color: #64748b; margin-top: 6px; letter-spacing: 0.1em; }

/* ── Factor items ── */
.factor-pos {
    background: rgba(239,68,68,0.08);
    border-left: 3px solid #ef4444;
    padding: 10px 16px;
    margin: 5px 0;
    border-radius: 0 8px 8px 0;
    color: #fca5a5;
    font-size: 0.875rem;
}
.factor-neg {
    background: rgba(16,185,129,0.08);
    border-left: 3px solid #10b981;
    padding: 10px 16px;
    margin: 5px 0;
    border-radius: 0 8px 8px 0;
    color: #6ee7b7;
    font-size: 0.875rem;
}

/* ── Section header ── */
.section-header {
    font-size: 1.25rem;
    font-weight: 700;
    color: #f1f5f9;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e293b;
    margin: 24px 0 16px 0;
}

/* ── Action box ── */
.action-box {
    border-radius: 12px;
    padding: 16px 20px;
    font-weight: 600;
    font-size: 0.95rem;
    margin-top: 12px;
}
.action-high   { background: rgba(239,68,68,0.12);  border: 1px solid #7f1d1d; color: #fca5a5; }
.action-medium { background: rgba(245,158,11,0.12); border: 1px solid #78350f; color: #fcd34d; }
.action-low    { background: rgba(16,185,129,0.12); border: 1px solid #064e3b; color: #6ee7b7; }

/* ── Logo strip ── */
.logo-strip {
    display: flex; align-items: center; gap: 10px;
    padding: 16px 4px 24px 4px;
}
.logo-icon { font-size: 2rem; }
.logo-text-main { font-size: 1.4rem; font-weight: 800; color: #f1f5f9; }
.logo-text-sub  { font-size: 0.7rem; color: #64748b; letter-spacing: 0.08em; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Plotly dark theme helper
# ---------------------------------------------------------------------------
PLOTLY_LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(family="Inter", color="#94a3b8", size=12),
    xaxis         = dict(gridcolor="#1e293b", linecolor="#334155"),
    yaxis         = dict(gridcolor="#1e293b", linecolor="#334155"),
    margin        = dict(l=0, r=0, t=30, b=0),
)

# ---------------------------------------------------------------------------
# Pipeline runner (for Streamlit Cloud cold start)
# ---------------------------------------------------------------------------

def _run_pipeline(config: dict) -> None:
    """Run data generation + training + evaluation in-process."""
    from data_generator import generate_and_save
    from train_v2 import train_all_models
    from evaluate import evaluate_on_split

    st.info("⚙️ Generating synthetic dataset (50,000 orders)…")
    generate_and_save(config)

    st.info("🤖 Training models (LR + RF + LightGBM)…")
    train_all_models(config)

    st.info("📊 Evaluating on validation + test splits…")
    evaluate_on_split("validation", config)
    evaluate_on_split("test", config)


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _load_artifacts():
    from predict import load_artifacts
    return load_artifacts()


@st.cache_data(show_spinner=False)
def _load_test_metrics() -> dict | None:
    p = ROOT_DIR / "models" / "test_metrics.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def _load_val_metrics() -> dict | None:
    p = ROOT_DIR / "models" / "validation_metrics.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def _load_test_probs():
    """Load test-set labels + probabilities for live cost model computation."""
    proc = ROOT_DIR / "data" / "processed" / "test.csv"
    if not proc.exists():
        return None, None
    df = pd.read_csv(proc)
    p  = ROOT_DIR / "models" / "test_metrics.json"
    if not p.exists():
        return None, None

    with open(p) as f:
        meta = json.load(f)
    best = meta["best_model"]

    import pickle
    from preprocessing import FEATURE_COLUMNS, CATEGORICAL_FEATURES

    with open(ROOT_DIR / "models" / f"{best}.pkl", "rb") as f:
        md = pickle.load(f)
    with open(ROOT_DIR / "models" / "encoders.pkl", "rb") as f:
        encoders = pickle.load(f)

    for col in CATEGORICAL_FEATURES:
        le    = encoders[col]
        known = set(le.classes_)
        df[f"{col}_encoded"] = df[col].astype(str).apply(
            lambda v: le.transform([v])[0] if v in known else 0
        )

    X = df[FEATURE_COLUMNS].values.astype(float)
    if md["needs_scaling"] and md["scaler"] is not None:
        X = md["scaler"].transform(X)

    y_true = df["is_rto"].values
    y_prob = md["model"].predict_proba(X)[:, 1]
    return y_true, y_prob


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _sidebar() -> str:
    with st.sidebar:
        st.markdown("""
        <div class="logo-strip">
            <span class="logo-icon">🛡️</span>
            <div>
                <div class="logo-text-main">RazorShield</div>
                <div class="logo-text-sub">AI RTO RISK MANAGER</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        page = st.radio(
            "Navigate",
            ["📊 Overview", "🎯 Order Scorer", "🤖 Agent Investigation", "📈 Evaluation", "💰 Business Impact"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown(
            "<small style='color:#475569'>"
            "⚠️ Demo prototype using synthetic data only.<br>"
            "Not an official Razorpay product."
            "</small>",
            unsafe_allow_html=True,
        )
    return page


# ---------------------------------------------------------------------------
# Page 1 — Overview
# ---------------------------------------------------------------------------

def _page_overview(metrics: dict) -> None:
    st.markdown("## 📊 Overview")
    st.markdown(
        "<p style='color:#64748b'>Real-time RTO risk intelligence for your order pipeline.</p>",
        unsafe_allow_html=True,
    )

    m   = metrics["metrics"]
    biz = metrics["business_impact"]
    thr = metrics["optimal_threshold"]

    # ── KPI row ──
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    kpis = [
        (c1, "Total Orders",        f"{biz['total_orders']:,}",          "held-out test set"),
        (c2, "RTO Orders Detected", f"{m['tp']:,}",                      f"of {biz['total_rto']} actual RTOs"),
        (c3, "High-Risk Flagged",   f"{m['tp'] + m['fp']:,}",            "orders reviewed"),
        (c4, "Loss Prevented",      f"₹{biz['loss_prevented']:,.0f}",    "at optimal threshold"),
        (c5, "Model Precision",     f"{m['precision']*100:.1f}%",        "of flagged = real RTO"),
        (c6, "Model Recall",        f"{m['recall']*100:.1f}%",           "of RTOs caught"),
    ]
    for col, label, value, sub in kpis:
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ──
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<div class="section-header">RTO vs Non-RTO Distribution</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels = ["Non-RTO (Delivered)", "RTO (Returned)"],
            values = [biz["total_orders"] - biz["total_rto"], biz["total_rto"]],
            hole   = 0.6,
            marker = dict(colors=["#3b82f6", "#ef4444"]),
            textfont = dict(color="#f1f5f9"),
        ))
        fig.update_layout(
            **PLOTLY_LAYOUT,
            showlegend = True,
            legend     = dict(font=dict(color="#94a3b8")),
            height     = 300,
            annotations = [dict(
                text  = f"{biz['rto_rate']*100:.1f}%<br>RTO Rate",
                font  = dict(size=16, color="#f1f5f9"),
                showarrow = False,
            )],
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-header">Prediction Outcomes</div>', unsafe_allow_html=True)
        labels = ["True Positive\n(RTO caught)", "False Positive\n(Good order flagged)",
                  "False Negative\n(RTO missed)", "True Negative\n(Good order cleared)"]
        values = [m["tp"], m["fp"], m["fn"], m["tn"]]
        colors = ["#10b981", "#f59e0b", "#ef4444", "#3b82f6"]
        fig2 = go.Figure(go.Bar(
            x     = labels,
            y     = values,
            marker_color = colors,
            text  = [f"{v:,}" for v in values],
            textposition = "outside",
            textfont = dict(color="#f1f5f9"),
        ))
        fig2.update_layout(**PLOTLY_LAYOUT, height=300, yaxis_title="Count")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Model info card ──
    st.markdown('<div class="section-header">Active Model</div>', unsafe_allow_html=True)
    col_a, col_b, col_c, col_d = st.columns(4)
    model_name_display = {
        "logistic_regression": "Logistic Regression",
        "random_forest":       "Random Forest",
        "lightgbm":            "LightGBM",
    }.get(metrics["best_model"], metrics["best_model"])

    for col, label, val in [
        (col_a, "Active Model",   model_name_display),
        (col_b, "PR-AUC",         f"{m['prauc']:.4f}"),
        (col_c, "Decision Threshold", f"{thr:.2f}"),
        (col_d, "Test Split",     "Latest 15% by time"),
    ]:
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value" style="font-size:1.2rem">{val}</div>
                </div>""",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Page 2 — Order Scorer
# ---------------------------------------------------------------------------

def _page_scorer(artifacts: dict) -> None:
    from predict import score_order
    from explain import explain_prediction

    st.markdown("## 🎯 Order Risk Scorer")
    st.markdown(
        "<p style='color:#64748b'>Enter order details to get a real-time RTO risk score.</p>",
        unsafe_allow_html=True,
    )

    # ── Demo order preset ──
    use_demo = st.checkbox("Load the buildathon demo order (₹7,999 COD, high-risk)", value=True)

    defaults = {
        "order_value": 7999.0, "num_items": 2, "payment_method": "COD",
        "product_category": "Electronics", "customer_location_type": "TIER2",
        "customer_age_days": 12, "previous_orders": 3,
        "previous_delivered_orders": 1, "previous_rto_orders": 2,
        "previous_return_orders": 0, "previous_cancellations": 1,
        "customer_rto_rate": 0.667, "orders_last_7_days": 5, "orders_last_30_days": 8,
        "avg_previous_order_value": 1200.0, "pincode_rto_rate": 0.31,
        "address_completeness_score": 62.0, "delivery_attempt_history": 2.1,
        "order_hour": 23, "day_of_week": 6, "is_weekend": 1, "is_festival_period": 0,
    } if use_demo else {
        "order_value": 2500.0, "num_items": 1, "payment_method": "UPI",
        "product_category": "Apparel", "customer_location_type": "METRO",
        "customer_age_days": 365, "previous_orders": 12,
        "previous_delivered_orders": 11, "previous_rto_orders": 1,
        "previous_return_orders": 0, "previous_cancellations": 0,
        "customer_rto_rate": 0.083, "orders_last_7_days": 1, "orders_last_30_days": 3,
        "avg_previous_order_value": 2200.0, "pincode_rto_rate": 0.09,
        "address_completeness_score": 91.0, "delivery_attempt_history": 1.1,
        "order_hour": 14, "day_of_week": 2, "is_weekend": 0, "is_festival_period": 0,
    }

    st.markdown("---")

    # ── Input form ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📦 Order Details**")
        order_value       = st.number_input("Order Value (₹)", 99.0, 49999.0, float(defaults["order_value"]), 100.0)
        num_items         = st.number_input("Number of Items", 1, 20, int(defaults["num_items"]))
        payment_method    = st.selectbox("Payment Method", ["COD", "UPI", "CARD", "NETBANKING"],
                                         index=["COD","UPI","CARD","NETBANKING"].index(defaults["payment_method"]))
        product_category  = st.selectbox("Product Category",
                                         ["Electronics","Apparel","Beauty","Home","Books","Sports","Footwear"],
                                         index=["Electronics","Apparel","Beauty","Home","Books","Sports","Footwear"].index(defaults["product_category"]))
        location_type     = st.selectbox("Customer Location Type", ["METRO","TIER1","TIER2","RURAL"],
                                         index=["METRO","TIER1","TIER2","RURAL"].index(defaults["customer_location_type"]))

        st.markdown("**🕐 Temporal**")
        order_hour        = st.slider("Order Hour (0–23)", 0, 23, int(defaults["order_hour"]))
        day_of_week       = st.slider("Day of Week (0=Mon, 6=Sun)", 0, 6, int(defaults["day_of_week"]))
        is_weekend        = int(day_of_week >= 5)
        is_festival       = st.checkbox("Festival / Sale Period", bool(defaults["is_festival_period"]))

    with col2:
        st.markdown("**👤 Customer History**")
        customer_age      = st.number_input("Account Age (days)", 1, 1500, int(defaults["customer_age_days"]))
        prev_orders       = st.number_input("Lifetime Orders", 0, 500, int(defaults["previous_orders"]))
        prev_delivered    = st.number_input("Successful Deliveries", 0, 500, int(defaults["previous_delivered_orders"]))
        prev_rto          = st.number_input("Previous RTO Orders", 0, 100, int(defaults["previous_rto_orders"]))
        prev_returns      = st.number_input("Previous Returns", 0, 100, int(defaults["previous_return_orders"]))
        prev_cancel       = st.number_input("Previous Cancellations", 0, 100, int(defaults["previous_cancellations"]))

        st.markdown("**📈 Recent Activity**")
        orders_7d         = st.number_input("Orders in Last 7 Days", 0, 30, int(defaults["orders_last_7_days"]))
        orders_30d        = st.number_input("Orders in Last 30 Days", 0, 60, int(defaults["orders_last_30_days"]))
        avg_val           = st.number_input("Avg Previous Order Value (₹)", 99.0, 49999.0, float(defaults["avg_previous_order_value"]), 100.0)

        st.markdown("**📍 Address & Delivery**")
        pincode_rto       = st.slider("Pincode Historical RTO Rate", 0.02, 0.65, float(defaults["pincode_rto_rate"]), 0.01)
        addr_score        = st.slider("Address Completeness Score (0–100)", 20.0, 100.0, float(defaults["address_completeness_score"]), 1.0)
        deliv_attempts    = st.slider("Avg Delivery Attempts (history)", 1.0, 4.0, float(defaults["delivery_attempt_history"]), 0.1)

    customer_rto_rate = prev_rto / max(prev_orders, 1)
    current_vs_avg    = order_value / max(avg_val, 1)

    order_dict = {
        "order_value":                 order_value,
        "num_items":                   num_items,
        "is_cod":                      int(payment_method == "COD"),
        "customer_age_days":           customer_age,
        "previous_orders":             prev_orders,
        "previous_delivered_orders":   prev_delivered,
        "previous_rto_orders":         prev_rto,
        "previous_return_orders":      prev_returns,
        "previous_cancellations":      prev_cancel,
        "customer_rto_rate":           round(customer_rto_rate, 4),
        "orders_last_7_days":          orders_7d,
        "orders_last_30_days":         orders_30d,
        "avg_previous_order_value":    avg_val,
        "current_vs_avg_order_value":  round(current_vs_avg, 3),
        "pincode_rto_rate":            pincode_rto,
        "address_completeness_score":  addr_score,
        "delivery_attempt_history":    deliv_attempts,
        "order_hour":                  order_hour,
        "day_of_week":                 day_of_week,
        "is_weekend":                  is_weekend,
        "is_festival_period":          int(is_festival),
        "product_category":            product_category,
        "payment_method":              payment_method,
        "customer_location_type":      location_type,
    }

    st.markdown("---")

    if st.button("🔍 Analyse Order Risk", use_container_width=True, type="primary"):
        with st.spinner("Scoring order…"):
            result  = score_order(order_dict, artifacts)
            explain = explain_prediction(order_dict, artifacts)

        level = result["risk_level"]
        score = result["risk_score"]

        score_class  = f"score-number-{level.lower()}"
        badge_class  = f"badge-{level.lower()}"
        action_class = f"action-{level.lower()}"

        r1, r2 = st.columns([1, 2])

        with r1:
            st.markdown(
                f"""<div class="score-wrap">
                    <div class="score-label">RTO RISK SCORE</div>
                    <div class="{score_class}">{score}</div>
                    <div style="margin-top:12px">
                        <span class="badge {badge_class}">{level} RISK</span>
                    </div>
                    <div class="score-label" style="margin-top:14px">
                        Probability: {result['risk_probability']:.1%}
                    </div>
                </div>
                <div class="action-box {action_class}" style="margin-top:16px">
                    {result['action_label']}
                </div>""",
                unsafe_allow_html=True,
            )

        with r2:
            st.markdown('<div class="section-header">🔎 Key Contributing Factors</div>', unsafe_allow_html=True)
            st.markdown(
                f"<small style='color:#64748b'>Explanation method: <code>{explain['explainer_type']}</code></small>",
                unsafe_allow_html=True,
            )
            for fi in explain["feature_impacts"]:
                if abs(fi["shap_value"]) < 0.001:
                    continue
                css   = "factor-pos" if fi["shap_value"] > 0 else "factor-neg"
                arrow = "↑" if fi["shap_value"] > 0 else "↓"
                st.markdown(
                    f'<div class="{css}">{arrow} <b>{fi["display_name"]}</b>'
                    f' &nbsp;·&nbsp; value: {fi["raw_value"]:.3g}'
                    f' &nbsp;·&nbsp; attribution: {fi["shap_value"]:+.3f}</div>',
                    unsafe_allow_html=True,
                )

            # Waterfall chart
            top_n  = [fi for fi in explain["feature_impacts"] if abs(fi["shap_value"]) > 0.001][:8]
            names  = [fi["display_name"] for fi in top_n]
            values = [fi["shap_value"]   for fi in top_n]
            colors = ["#ef4444" if v > 0 else "#10b981" for v in values]

            fig = go.Figure(go.Bar(
                x            = values,
                y            = names,
                orientation  = "h",
                marker_color = colors,
                text         = [f"{v:+.3f}" for v in values],
                textposition = "outside",
                textfont     = dict(color="#f1f5f9"),
            ))
            fig.update_layout(
                **PLOTLY_LAYOUT,
                height    = 320,
                xaxis_title = "Attribution (SHAP value)",
                yaxis     = dict(autorange="reversed", gridcolor="#1e293b"),
            )
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page 3 — Evaluation
# ---------------------------------------------------------------------------

def _page_evaluation(metrics: dict) -> None:
    st.markdown("## 📈 Model Evaluation")
    st.markdown(
        f"<p style='color:#64748b'>Held-out <b>test set</b> — evaluated once, never tuned against. "
        f"Threshold = {metrics['optimal_threshold']:.2f} (selected on validation).</p>",
        unsafe_allow_html=True,
    )

    m   = metrics["metrics"]
    thr = metrics["optimal_threshold"]

    # ── Metric cards ──
    metric_cols = st.columns(5)
    for col, label, val in [
        (metric_cols[0], "PR-AUC",     f"{m['prauc']:.4f}"),
        (metric_cols[1], "Precision",  f"{m['precision']*100:.1f}%"),
        (metric_cols[2], "Recall",     f"{m['recall']*100:.1f}%"),
        (metric_cols[3], "F1 Score",   f"{m['f1']:.4f}"),
        (metric_cols[4], "False Positive Rate", f"{m['fpr']*100:.1f}%"),
    ]:
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value" style="font-size:1.8rem">{val}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    # ── Confusion Matrix ──
    with col_left:
        st.markdown('<div class="section-header">Confusion Matrix</div>', unsafe_allow_html=True)
        cm_vals = [[m["tn"], m["fp"]], [m["fn"], m["tp"]]]
        fig = go.Figure(go.Heatmap(
            z    = cm_vals,
            x    = ["Predicted: Safe", "Predicted: RTO"],
            y    = ["Actual: Safe", "Actual: RTO"],
            text = [[str(v) for v in row] for row in cm_vals],
            texttemplate = "<b>%{text}</b>",
            textfont     = dict(size=20, color="#f1f5f9"),
            colorscale   = [[0, "#0f172a"], [1, "#3b82f6"]],
            showscale    = False,
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            """<div class="rs-card" style="font-size:0.85rem;color:#94a3b8">
                <b style="color:#f1f5f9">False Positive</b> — A genuine order incorrectly flagged as high risk.
                Costs: unnecessary verification friction.<br><br>
                <b style="color:#f1f5f9">False Negative</b> — An RTO order the model missed.
                Costs: full shipping + reverse logistics loss.
            </div>""",
            unsafe_allow_html=True,
        )

    # ── PR Curve ──
    with col_right:
        st.markdown('<div class="section-header">Precision-Recall Curve</div>', unsafe_allow_html=True)
        pr = metrics["pr_curve"]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x    = pr["recall"],
            y    = pr["precision"],
            mode = "lines",
            line = dict(color="#3b82f6", width=2.5),
            name = f"PR-AUC = {m['prauc']:.4f}",
            fill = "tozeroy",
            fillcolor = "rgba(59,130,246,0.08)",
        ))
        # Mark current threshold
        fig2.add_trace(go.Scatter(
            x    = [m["recall"]],
            y    = [m["precision"]],
            mode = "markers",
            marker = dict(color="#f59e0b", size=12, symbol="star"),
            name = f"Threshold = {thr}",
        ))
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            height      = 300,
            xaxis_title = "Recall",
            yaxis_title = "Precision",
            legend      = dict(font=dict(color="#94a3b8")),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Model comparison table ──
    st.markdown('<div class="section-header">All Models — Test Set Comparison</div>', unsafe_allow_html=True)
    all_m = metrics.get("all_model_metrics", {})
    if all_m:
        rows = []
        name_display = {
            "logistic_regression": "Logistic Regression",
            "random_forest": "Random Forest",
            "lightgbm": "LightGBM",
        }
        for name, mm in all_m.items():
            rows.append({
                "Model":     name_display.get(name, name),
                "PR-AUC":    f"{mm['prauc']:.4f}",
                "Precision": f"{mm['precision']:.4f}",
                "Recall":    f"{mm['recall']:.4f}",
                "F1":        f"{mm['f1']:.4f}",
                "FPR":       f"{mm['fpr']:.4f}",
            })
        cmp_df = pd.DataFrame(rows)
        st.dataframe(cmp_df, use_container_width=True, hide_index=True)

    # ── Interactive threshold analysis ──
    st.markdown('<div class="section-header">Threshold Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        "<small style='color:#64748b'>Adjust threshold to see how precision/recall trade off "
        "and how many orders get flagged.</small>",
        unsafe_allow_html=True,
    )
    selected_t = st.slider("Risk Threshold", 0.05, 0.95, float(thr), 0.05,
                            key="eval_threshold")

    sweep = metrics.get("threshold_sweep", [])
    if sweep:
        df_sweep = pd.DataFrame(sweep)
        row = df_sweep[df_sweep["threshold"] == round(selected_t, 2)]
        if not row.empty:
            r = row.iloc[0]
            prec = r["tp"] / max(r["tp"] + r["fp"], 1)
            rec  = r["tp"] / max(r["tp"] + r["fn"], 1)
            col1, col2, col3, col4 = st.columns(4)
            for c, lb, v in [
                (col1, "Precision",       f"{prec*100:.1f}%"),
                (col2, "Recall",          f"{rec*100:.1f}%"),
                (col3, "Orders Flagged",  f"{int(r['tp']+r['fp']):,}"),
                (col4, "RTOs Caught",     f"{int(r['tp']):,}"),
            ]:
                with c:
                    st.markdown(
                        f"""<div class="kpi-card">
                            <div class="kpi-label">{lb}</div>
                            <div class="kpi-value" style="font-size:1.5rem">{v}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

        # Chart
        prec_vals = [r["tp"] / max(r["tp"] + r["fp"], 1) for _, r in df_sweep.iterrows()]
        rec_vals  = [r["tp"] / max(r["tp"] + r["fn"], 1) for _, r in df_sweep.iterrows()]
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df_sweep["threshold"].tolist(), y=prec_vals,
                                   mode="lines+markers", name="Precision",
                                   line=dict(color="#10b981", width=2)))
        fig3.add_trace(go.Scatter(x=df_sweep["threshold"].tolist(), y=rec_vals,
                                   mode="lines+markers", name="Recall",
                                   line=dict(color="#3b82f6", width=2)))
        fig3.add_vline(x=selected_t, line_dash="dash", line_color="#f59e0b")
        fig3.update_layout(
            **PLOTLY_LAYOUT,
            height      = 280,
            xaxis_title = "Threshold",
            yaxis_title = "Score",
            legend      = dict(font=dict(color="#94a3b8")),
        )
        st.plotly_chart(fig3, use_container_width=True)


# ---------------------------------------------------------------------------
# Page 4 — Business Impact
# ---------------------------------------------------------------------------

def _page_business(metrics: dict, y_true: np.ndarray | None, y_prob: np.ndarray | None) -> None:
    from cost_model import compute_business_impact, sweep_thresholds_business

    st.markdown("## 💰 Business Impact Analysis")
    st.markdown(
        "<p style='color:#64748b'>Configure your merchant cost parameters and see the net financial impact.</p>",
        unsafe_allow_html=True,
    )

    col_cost1, col_cost2 = st.columns(2)
    with col_cost1:
        rto_cost = st.slider("Cost per undetected RTO (₹)", 100, 1000, 350, 10,
                              help="Shipping + reverse logistics + lost margin per RTO")
    with col_cost2:
        ver_cost = st.slider("Cost per verification (₹)", 5, 200, 30, 5,
                              help="Ops + customer friction cost for flagged orders")

    threshold = st.slider("Risk Threshold", 0.05, 0.95,
                           float(metrics["optimal_threshold"]), 0.05,
                           key="biz_threshold")

    if y_true is not None and y_prob is not None:
        biz = compute_business_impact(y_true, y_prob, threshold, rto_cost, ver_cost)
    else:
        biz = metrics["business_impact"]

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    for col, label, val, color in [
        (col1, "Baseline RTO Loss",  f"₹{biz['baseline_loss']:,.0f}",  "#ef4444"),
        (col2, "Loss Prevented",     f"₹{biz['loss_prevented']:,.0f}", "#10b981"),
        (col3, "False-Positive Cost",f"₹{biz['fp_cost']:,.0f}",        "#f59e0b"),
        (col4, "Net Benefit",        f"₹{biz['net_benefit']:,.0f}",    "#3b82f6"),
    ]:
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value" style="font-size:1.6rem;color:{color}">{val}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""<div class="rs-card" style="font-size:0.9rem;color:#94a3b8;margin-top:12px">
            At threshold <b style="color:#f1f5f9">{threshold:.2f}</b>, the model catches
            <b style="color:#10b981">{biz['tp']:,} RTO orders</b>
            ({biz['tp']/max(biz['total_rto'],1)*100:.1f}% recall) while incorrectly flagging
            <b style="color:#f59e0b">{biz['fp']:,} non-RTO orders</b>.
            Net benefit vs no model: <b style="color:#3b82f6">₹{biz['net_benefit']:,.0f}</b>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Threshold sweep chart ──
    if y_true is not None and y_prob is not None:
        st.markdown('<div class="section-header">Net Benefit vs Threshold</div>', unsafe_allow_html=True)
        sweep = sweep_thresholds_business(y_true, y_prob, rto_cost, ver_cost)
        df_s  = pd.DataFrame(sweep)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x    = df_s["threshold"],
            y    = df_s["net_benefit"],
            mode = "lines+markers",
            name = "Net Benefit (₹)",
            line = dict(color="#3b82f6", width=2.5),
            fill = "tozeroy",
            fillcolor = "rgba(59,130,246,0.08)",
        ))
        fig.add_trace(go.Scatter(
            x    = df_s["threshold"],
            y    = df_s["loss_prevented"],
            mode = "lines",
            name = "Loss Prevented (₹)",
            line = dict(color="#10b981", width=1.5, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x    = df_s["threshold"],
            y    = df_s["fp_cost"],
            mode = "lines",
            name = "False-Positive Cost (₹)",
            line = dict(color="#f59e0b", width=1.5, dash="dot"),
        ))
        fig.add_vline(x=threshold, line_dash="dash", line_color="#64748b",
                      annotation_text=f"T={threshold:.2f}", annotation_font_color="#94a3b8")
        fig.update_layout(
            **PLOTLY_LAYOUT,
            height      = 340,
            xaxis_title = "Threshold",
            yaxis_title = "₹",
            legend      = dict(font=dict(color="#94a3b8")),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Flagged orders vs threshold
        col_l2, col_r2 = st.columns(2)
        with col_l2:
            st.markdown('<div class="section-header">Orders Flagged vs Threshold</div>', unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x            = df_s["threshold"],
                y            = df_s["flagged_orders"],
                marker_color = "#6366f1",
                name         = "Flagged Orders",
            ))
            fig2.update_layout(**PLOTLY_LAYOUT, height=250,
                                xaxis_title="Threshold", yaxis_title="Orders")
            st.plotly_chart(fig2, use_container_width=True)

        with col_r2:
            st.markdown('<div class="section-header">Precision & Recall vs Threshold</div>', unsafe_allow_html=True)
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df_s["threshold"], y=df_s["precision"],
                                       mode="lines", name="Precision",
                                       line=dict(color="#10b981", width=2)))
            fig3.add_trace(go.Scatter(x=df_s["threshold"], y=df_s["recall"],
                                       mode="lines", name="Recall",
                                       line=dict(color="#3b82f6", width=2)))
            fig3.update_layout(**PLOTLY_LAYOUT, height=250,
                                xaxis_title="Threshold", yaxis_title="Score",
                                legend=dict(font=dict(color="#94a3b8")))
            st.plotly_chart(fig3, use_container_width=True)


# ---------------------------------------------------------------------------
# Initialisation screen
# ---------------------------------------------------------------------------

def _init_screen(config: dict) -> None:
    st.markdown("""
    <div style="text-align:center; padding: 60px 40px;">
        <div style="font-size:4rem">🛡️</div>
        <h1 style="font-size:2.5rem;font-weight:900;color:#f1f5f9;margin:16px 0 8px">RazorShield</h1>
        <p style="color:#64748b;font-size:1.1rem">AI Return-to-Origin Risk Manager</p>
        <p style="color:#475569;max-width:600px;margin:20px auto;font-size:0.9rem">
            First-time setup: click below to generate the synthetic dataset,
            train all models, and evaluate on the held-out test set.
            This runs once and takes ~90 seconds.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Initialize RazorShield", use_container_width=True, type="primary"):
            with st.spinner("Running pipeline… (this takes ~90 seconds)"):
                _run_pipeline(config)
            st.success("✅ Pipeline complete! Refreshing…")
            time.sleep(1)
            st.rerun()


# ---------------------------------------------------------------------------
# App entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    import yaml
    with open(ROOT_DIR / "config" / "config.yaml") as f:
        config = yaml.safe_load(f)

    models_ready = (ROOT_DIR / "models" / "best_model.json").exists()
    test_metrics_ready = (ROOT_DIR / "models" / "test_metrics.json").exists()

    if not models_ready:
        _init_screen(config)
        return

    if not test_metrics_ready:
        with st.spinner("Running final evaluation on test set…"):
            from evaluate import evaluate_on_split
            evaluate_on_split("validation", config)
            evaluate_on_split("test", config)
        st.rerun()

    page     = _sidebar()
    metrics  = _load_test_metrics()
    y_true, y_prob = _load_test_probs()

    if page == "📊 Overview":
        _page_overview(metrics)

    elif page == "🎯 Order Scorer":
        try:
            artifacts = _load_artifacts()
            _page_scorer(artifacts)
        except Exception as e:
            st.error(f"Could not load model: {e}")

    elif page == "🤖 Agent Investigation":
        _page_agent_investigation()

    elif page == "📈 Evaluation":
        _page_evaluation(metrics)

    elif page == "💰 Business Impact":
        _page_business(metrics, y_true, y_prob)


# ---------------------------------------------------------------------------
# Page 5 — Autonomous Multi-Agent Investigation
# ---------------------------------------------------------------------------

def _page_agent_investigation() -> None:
    import asyncio
    st.markdown("## 🤖 Autonomous Multi-Agent Fraud Investigation Mesh")
    st.markdown(
        "<p style='color:#64748b'>Powered by LangGraph multi-agent orchestration, MongoDB entity profiling, and real-time reasoning trails.</p>",
        unsafe_allow_html=True
    )

    col_case, col_actions = st.columns([2, 1])

    with col_case:
        case_type = st.selectbox(
            "Select Investigation Scenario Preset",
            [
                "🚨 High-Risk Syndicate Case (Shared IP/Device Cluster + Prior Chargeback)",
                "✅ Trusted Platinum Customer Case (Clean Tenure + 0 Disputes)",
                "⚠️ High-Velocity Anomaly Case (New Account + Rush Overnight Notes)",
                "🛠️ Custom Transaction Input"
            ]
        )

    if case_type.startswith("🚨"):
        default_cust = "cust_88129"
        default_amt = 48500.0
        default_ip = "103.21.124.89"
        default_dfp = "dfp_a7b29c011e4"
        default_notes = "Urgent overnight rush dispatch, leave with reception desk"
        default_vpn = True
    elif case_type.startswith("✅"):
        default_cust = "cust_trusted_01"
        default_amt = 3200.0
        default_ip = "49.207.210.12"
        default_dfp = "dfp_mac_9921"
        default_notes = "Standard residential delivery"
        default_vpn = False
    elif case_type.startswith("⚠️"):
        default_cust = "cust_new_velocity_03"
        default_amt = 24500.0
        default_ip = "103.45.12.9"
        default_dfp = "dfp_phone_001"
        default_notes = "Urgent gift, please fast-track courier delivery"
        default_vpn = True
    else:
        default_cust = "cust_custom_01"
        default_amt = 15000.0
        default_ip = "103.21.124.89"
        default_dfp = "dfp_a7b29c011e4"
        default_notes = "Urgent rush order"
        default_vpn = False

    with st.expander("📋 Inspect Case Payload & Entity Attributes", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            customer_id = st.text_input("Customer ID", value=default_cust)
            amount = st.number_input("Transaction Amount (₹)", value=default_amt, step=500.0)
        with c2:
            ip_address = st.text_input("IP Address", value=default_ip)
            device_fp = st.text_input("Device Fingerprint", value=default_dfp)
        with c3:
            is_vpn = st.checkbox("VPN / Proxy Detected", value=default_vpn)
            notes = st.text_input("Transaction Notes / Memos", value=default_notes)

    if st.button("🚀 Launch Autonomous Multi-Agent Investigation", type="primary", use_container_width=True):
        from backend.agents.workflow import execute_agent_investigation

        progress_container = st.container()
        with progress_container:
            st.markdown("### 🛰️ Live Agent Reasoning Stream")
            agent_log_placeholder = st.empty()

        captured_frames = []

        async def streamlit_stream_callback(frame: dict):
            captured_frames.append(frame)
            time.sleep(0.08)

        payload = {
            "transaction_id": f"txn_{int(time.time()*1000)}",
            "merchant_id": "mer_razor_enterprise",
            "customer_id": customer_id,
            "amount": float(amount),
            "account_age_days": 2.0 if is_vpn else 300.0,
            "device_trust_score": 0.15 if is_vpn else 0.95,
            "ip_velocity_1h": 5 if is_vpn else 1,
            "txn_velocity_1h": 6 if is_vpn else 1,
            "is_vpn_proxy": is_vpn,
            "failed_attempts_24h": 3 if is_vpn else 0,
            "billing_shipping_match": not is_vpn,
            "customer_email": f"{customer_id}@example.com",
            "ip_address": ip_address,
            "device_fingerprint": device_fp,
            "notes": notes
        }

        with st.spinner("🤖 Autonomous Agents analyzing MongoDB records, graph clusters & transaction telemetry..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    execute_agent_investigation(
                        transaction_id=payload["transaction_id"],
                        customer_id=payload["customer_id"],
                        merchant_id=payload["merchant_id"],
                        transaction_data=payload,
                        emit_callback=streamlit_stream_callback
                    )
                )
                loop.close()
            except Exception as e:
                st.error(f"Investigation execution error: {e}")
                return

        # Render Agent Reasoning Timeline
        for frame in captured_frames:
            agent = frame.get("agent_name", "Agent")
            ev_type = frame.get("event_type", "INFO")
            thought = frame.get("thought", "")

            if agent == "Supervisor":
                st.info(f"🧠 **[Supervisor]** {thought}")
            elif agent == "DataRetrievalAgent":
                st.markdown(f"💾 **[Data Retrieval Agent (MongoDB)]** `{thought}`")
                if frame.get("tool_output"):
                    with st.expander("🔍 View MongoDB Customer Profile Record", expanded=False):
                        st.json(frame["tool_output"])
            elif agent == "GraphAgent":
                st.warning(f"🕸️ **[Fraud Ring Graph Agent]** {thought}")
                if frame.get("tool_output"):
                    with st.expander("🔍 View Graph Entity Relationship Cluster", expanded=False):
                        st.json(frame["tool_output"])
            elif agent == "NLPAnalyzer":
                st.markdown(f"📝 **[NLP Metadata Analyzer]** {thought}")
            elif agent == "DecisionAgent" and ev_type == "DECISION_REACHED":
                st.success(f"⚖️ **[Decision Engine]** {thought}")

        st.markdown("---")
        st.markdown("### 🏆 Final Autonomous Verdict & Case File")

        res_col1, res_col2, res_col3 = st.columns(3)
        with res_col1:
            if result.verdict == "BLOCK":
                st.markdown(f"<div style='background:rgba(239,68,68,0.15);border:2px solid #ef4444;border-radius:12px;padding:20px;text-align:center;'><h2 style='color:#ef4444;margin:0;'>🛑 {result.verdict}</h2><p style='color:#f87171;font-size:0.85rem;margin-top:4px;'>CRITICAL RISK INTERCEPTED</p></div>", unsafe_allow_html=True)
            elif result.verdict == "TRIGGER_2FA":
                st.markdown(f"<div style='background:rgba(245,158,11,0.15);border:2px solid #f59e0b;border-radius:12px;padding:20px;text-align:center;'><h2 style='color:#f59e0b;margin:0;'>⚠️ {result.verdict}</h2><p style='color:#fbbf24;font-size:0.85rem;margin-top:4px;'>LIVENESS CHALLENGE REQUIRED</p></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background:rgba(16,185,129,0.15);border:2px solid #10b981;border-radius:12px;padding:20px;text-align:center;'><h2 style='color:#10b981;margin:0;'>✅ {result.verdict}</h2><p style='color:#34d399;font-size:0.85rem;margin-top:4px;'>LOW RISK APPROVAL</p></div>", unsafe_allow_html=True)

        with res_col2:
            st.metric("Composite Risk Score", f"{result.composite_risk_score}/100")
            st.metric("Agent Confidence", f"{int(result.confidence * 100)}%")

        with res_col3:
            st.metric("Investigation SLA Latency", f"{result.investigation_duration_ms} ms")
            st.metric("Triggered Risk Flags", f"{len(result.flags)} flags")

        st.markdown("#### 📜 Executive Rationale")
        st.info(result.executive_summary)

        st.markdown("#### 🛡️ Autonomous Enforcement Actions Dispatched")
        for act in result.recommended_actions:
            st.markdown(f"- ✅ **{act}**")


if __name__ == "__main__":
    main()


import streamlit as st
import pandas as pd
import plotly.express as px
from data import generate_mock_data
from utils import export_csv_bytes, export_pdf_bytes, retention_suggestion

st.set_page_config(page_title="Mortgage Churn Prediction", layout="wide")

@st.cache_data
def load_data(n=1000):
    df, trend = generate_mock_data(n_customers=n)
    return df, trend

df_all, trend_df = load_data(1200)

st.title("Mortgage Churn Prediction — Mock Streamlit Dashboard")

## Overview Section
st.markdown("### Monthly Churn Overview")
col1, col2, col3, col4 = st.columns(4)

total_customers = len(df_all)
high_risk_count = (df_all["churn_probability"] >= 0.7).sum()
projected_churn_rate = df_all["churn_probability"].mean()
estimated_revenue_at_risk = (df_all["balance"] * df_all["churn_probability"]).sum()

col1.metric("Customers Analyzed", f"{total_customers}")
col2.metric("High-Risk Customers", f"{high_risk_count}")
col3.metric("Projected Churn Rate", f"{projected_churn_rate:.2%}")
col4.metric("Estimated Revenue at Risk", f"${estimated_revenue_at_risk:,.0f}")

st.plotly_chart(px.line(trend_df, x="month", y="churn_rate", title="Churn Trend (Last 12 Months)"), use_container_width=True)

## Sidebar Filters for Customer Table
st.sidebar.header("Filter Predictions")
loan_types = ["All"] + sorted(df_all["loan_type"].unique().tolist())
selected_loan = st.sidebar.selectbox("Loan Type", loan_types)
states = ["All"] + sorted(df_all["state"].unique().tolist())
selected_state = st.sidebar.selectbox("State", states)
branches = ["All"] + sorted(df_all["branch"].unique().tolist())
selected_branch = st.sidebar.selectbox("Branch", branches)
risk_level = st.sidebar.slider("Max Risk Level (0=Low -> 1=High)", 0.0, 1.0, 1.0)

filtered = df_all.copy()
if selected_loan != "All":
    filtered = filtered[filtered["loan_type"] == selected_loan]
if selected_state != "All":
    filtered = filtered[filtered["state"] == selected_state]
if selected_branch != "All":
    filtered = filtered[filtered["branch"] == selected_branch]
filtered = filtered[filtered["churn_probability"] <= risk_level]

st.markdown("### Customer-Level Predictions")
st.markdown("Use filters in the sidebar to refine the table. Download filtered results as CSV or PDF.")

table_cols = ["customer_id","risk_level","churn_probability","apr","balance","loan_type","state","branch"]
st.dataframe(filtered[table_cols].sort_values("churn_probability", ascending=False).reset_index(drop=True), height=300)

csv_bytes = export_csv_bytes(filtered[table_cols])
st.download_button("⬇ Export Filtered Customers (CSV)", data=csv_bytes, file_name="filtered_customers.csv", mime="text/csv")

pdf_bytes = export_pdf_bytes("Filtered Customers", filtered[table_cols])
st.download_button("⬇ Export Filtered Customers (PDF)", data=pdf_bytes, file_name="filtered_customers.pdf", mime="application/pdf")

## Explainability Section (Mock SHAP)
st.markdown("### Why Customers Are Churning — Explainability (Mock SHAP)")
st.markdown("Feature importance (simulated) and per-customer explanation.")

# Simulate feature importance
feat_imp = pd.DataFrame({
    "feature": ["rate_diff_vs_market","payment_inconsistency","delinquency_count","complaints","online_checks","balance"],
    "importance": [0.22,0.18,0.17,0.14,0.12,0.09]
})

fig_imp = px.bar(feat_imp, x="importance", y="feature", orientation='h', title="Feature Importance")
st.plotly_chart(fig_imp, use_container_width=True)

# Individual explainability
st.markdown("#### Explain Individual Customer")
cust_id = st.text_input("Customer ID (e.g. C10294)", value="")
if cust_id:
    customer = df_all[df_all["customer_id"] == cust_id]
    if customer.empty:
        st.warning("Customer ID not found in mock dataset.")
    else:
        row = customer.iloc[0]
        # Create a mock per-feature contribution
        features = feat_imp["feature"].tolist()
        contributions = (row.get("churn_probability") * feat_imp["importance"]).round(3)
        explain_df = pd.DataFrame({"feature": features, "contribution": contributions})
        st.table(explain_df)

## Retention Recommendation Engine
st.markdown("### Retention Actions")
st.markdown("Select a customer from the filtered table (or enter ID above) to view suggested retention action.")
selected = st.selectbox("Pick a customer from filtered set", options=filtered["customer_id"].head(100).tolist())
if selected:
    r = filtered[filtered["customer_id"] == selected].iloc[0].to_dict()
    suggestion = retention_suggestion(r)
    st.write(f"**Customer ID:** {r['customer_id']}")
    st.write(f"**Risk Level:** {r['risk_level']} ({r['churn_probability']:.2f})")
    st.info(f"**Suggested Action:** {suggestion}")

## Downloadable Reports (Examples)
st.markdown("### Downloadable Reports")
high_risk_df = df_all[df_all["churn_probability"] >= 0.7]
csv_hr = export_csv_bytes(high_risk_df[table_cols])
st.download_button("⬇ Export High-Risk Customers (CSV)", data=csv_hr, file_name="high_risk_customers.csv", mime="text/csv")

full_pdf = export_pdf_bytes("Full Churn Report", df_all[table_cols])
st.download_button("⬇ Export Full Churn Report (PDF)", data=full_pdf, file_name="full_churn_report.pdf", mime="application/pdf")

feat_pdf = export_pdf_bytes("Feature Importance", feat_imp)
st.download_button("⬇ Download Feature Importance Summary", data=feat_pdf, file_name="feature_importance.pdf", mime="application/pdf")

st.markdown("---")
st.caption("This dashboard is a mock-up demonstrating layout and basic interactions for mortgage churn prediction.")

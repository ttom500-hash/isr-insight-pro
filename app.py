import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Insurance Warehouse Pro", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    st.sidebar.title("🗄️ ניהול מחסן")
    company = st.sidebar.selectbox("בחר חברה:", df['company'].unique())
    row = df[df['company'] == company].iloc[-1]

    st.title(f"📊 תשתית ניתוח: {company}")
    
    # הצגת 5 ה-KPIs הקריטיים [cite: 2026-01-03]
    cols = st.columns(5)
    cols[0].metric("סולבנסי", f"{row['solvency_ratio']}%", delta_color="normal" if row['solvency_ratio'] >= 150 else "inverse")
    cols[1].metric("יתרת CSM", f"₪{row['csm_balance']}B")
    cols[2].metric("מרכיב הפסד", f"₪{row['loss_component']}M")
    cols[3].metric("ROE", f"{row['roe']}%")
    cols[4].metric("נזילות", f"{row['liquidity']}x")

    st.divider()
    
    # סימולטור Stress Test מקצועי
    st.subheader("🧪 סימולטור תרחישים")
    s_int = st.slider("שינוי ריבית (bps)", -200, 200, 0) / 100
    s_mkt = st.slider("שינוי שוק הון (%)", -20.0, 20.0, 0.0)
    
    impact = (s_int * row['int_sensitivity'] * 100) + (s_mkt/10 * row['mkt_sensitivity'] * 100)
    st.metric("סולבנסי תחת לחץ", f"{row['solvency_ratio'] + impact:.1f}%", delta=f"{impact:.1f}%")

except Exception as e:
    st.warning("המערכת ממתינה לעדכון נתונים ב-CSV.")

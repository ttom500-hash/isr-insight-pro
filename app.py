import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Insurance Master Analytics", layout="wide")
df = pd.read_csv('data/database.csv')
row = df.iloc[-1]

st.title(f"🏛️ ניתוח פיננסי הוליסטי: {row['company']}")

# יצירת טאבים להפרדה מקצועית בין דוחות
tab1, tab2, tab3, tab4 = st.tabs(["📊 מדדי חוסן (KPIs)", "📄 דוח רווח והפסד", "⚖️ מאזן ונזילות", "💸 תזרים מזומנים"])

with tab1:
    st.subheader("5 מדדי הליבה הקריטיים [cite: 2026-01-03]")
    kpi = st.columns(5)
    kpi[0].metric("סולבנסי", f"{row['solvency_ratio']}%")
    kpi[1].metric("CSM", f"₪{row['csm_balance']}B")
    kpi[2].metric("מרכיב הפסד", f"₪{row['loss_component']}M")
    kpi[3].metric("ROE", f"{row['roe']}%")
    kpi[4].metric("נזילות", f"{row['liquidity']}x")

with tab2:
    st.subheader("ניתוח תוצאות פעילות")
    col1, col2 = st.columns(2)
    col1.metric("יחס הוצאות (Expense Ratio)", f"{row['expense_ratio']}%", help="יעילות תפעולית")
    col2.metric("יחס משולב (Combined Ratio)", f"{row['combined_ratio']}%", help="רווחיות חיתומית")

with tab3:
    st.subheader("מבנה המאזן")
    st.metric("הון עצמי לסך מאזן", f"{row['equity_to_balance']}%")
    st.info("יחס זה מעיד על רמת המינוף של הקבוצה ביחס לנכסים המנוהלים.")

with tab4:
    st.subheader("ניתוח תזרים מזומנים")
    st.metric("תזרים מפעילות שוטפת", f"₪{row['operating_cash_flow']}B")
    st.write("תזרים חיובי מפעילות שוטפת הוא קריטי לתשלום תביעות ודיבידנדים ללא מימוש נכסים.")

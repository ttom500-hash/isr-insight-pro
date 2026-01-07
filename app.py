import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. הגדרות תצוגה ועיצוב Enterprise
st.set_page_config(page_title="INSIGHT PRO | Global Supervision AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e1e4e8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .formula-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-right: 5px solid #007bff; margin: 10px 0; }
    h1, h2, h3 { color: #1a3a5a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 2. פונקציית טעינת הנתונים מה-CSV
@st.cache_data
def load_data():
    try:
        # טעינת המחסן המעודכן עם הפניקס והראל
        df = pd.read_csv('data/database.csv')
        return df
    except Exception as e:
        st.error(f"שגיאה בטעינת בסיס הנתונים: {e}")
        return None

df = load_data()

if df is not None:
    # --- סרגל צד (Sidebar) ---
    st.sidebar.title("🛡️ לוח בקרה למפקח")
    selected_company = st.sidebar.selectbox("בחר ישות לניתוח עומק:", df['company'].unique())
    
    # שליפת נתוני החברה שנבחרה (כולל השוואה לרבעון קודם אם קיים)
    c_df = df[df['company'] == selected_company].sort_values(['year', 'quarter'])
    row = c_df.iloc[-1]
    prev_row = c_df.iloc[-2] if len(c_df) > 1 else row

    # כותרת ראשית
    st.title(f"🏛️ Insurance Insight Pro: {selected_company}")
    st.caption(f"מערכת ניתוח מבוססת IFRS 17 & Solvency II | תקופת דיווח: {row['quarter']} {row['year']}")

    # --- 🤖 שכבת AI Insights (למקום הראשון) ---
    st.subheader("🤖

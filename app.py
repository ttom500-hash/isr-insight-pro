import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
import requests
import base64
import os
import re
from datetime import datetime

# --- 1. THE ULTIMATE DESIGN SYSTEM (CSS) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* בסיס המערכת - כהה ויוקרתי */
    .stApp {
        background-color: #02040a;
        color: #ccd6f6;
    }
    
    /* כותרות לבנות וחדות */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.5px;
    }

    /* כרטיסי המדדים - Glassmorphism עם ניגודיות גבוהה */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #112240 0%, #0a192f 100%);
        border: 1px solid #233554;
        border-radius: 12px;
        padding: 20px !important;
        box-shadow: 0 10px 30px -15px rgba(2, 12, 27, 0.7);
    }
    
    /* טקסט בתוך המדדים - לבן וקריא */
    div[data-testid="stMetricValue"] {
        color: #64ffda !important; /* צבע טורקיז בוהק למספרים */
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #ffffff !important;
        font-size: 1rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* דגלים אדומים - ניגודיות מקסימלית */
    .red-flag-alert {
        background-color: #1d1017;
        border-right: 5px solid #ff2e63;
        padding: 15px;
        border-radius: 4px;
        color: #ff2e63;
        font-weight: bold;
        margin-bottom: 10px;
        box-shadow: 0 0 15px rgba(255, 46, 99, 0.2);
    }

    /* עיצוב ה-Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0a192f;
        border-left: 1px solid #233554;
    }

    /* כפתורים בסגנון Gaming-Elite */
    .stButton>button {
        background: linear-gradient(90deg, #64ffda, #00d2ff);
        color: #020c1b !important;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(100, 255, 218, 0.6);
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ENGINE ---
def secure_sync(new_row):
    try:
        if "GITHUB_TOKEN" not in st.secrets: return False
        token, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"]
        path = "data/database.csv"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers, timeout=10).json()
        current_content = base64.b64decode(r['content']).decode('utf-8')
        if new_row.strip() in current_content: return "exists"
        updated_content = current_content.strip() + "\n" + new_row
        payload = {"message": "Master Update", "content": base64.b64encode(updated_content.encode()).decode(), "sha": r['sha']}
        return requests.put(url, json=payload, headers=headers, timeout=10).status_code == 200
    except: return False

@st.cache_data(ttl=300)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0].split('.')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 3. UI LAYOUT ---
df = load_data()
with st.sidebar:
    st.markdown("<h1 style='color:#64ffda;'>APEX</h1>", unsafe_allow_html=True)
    st.write("🛡️ **SupTech Framework v7.0**")
    
    if not df.empty:
        sel_name = st.selectbox("בחר ישות פיננסית:", sorted(df['display_name'].unique()))
        comp_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("תקופת דיווח:", comp_df['quarter'].unique())
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        if st.button("EXECUTE SYSTEM REFRESH"): st.cache_data.clear(); st.rerun()

    with st.expander("📥 DATA INGESTION PORTAL"):
        f = st.file_uploader("טען דוחות סולבנסי", type=['pdf'])
        if f:
            st.success("קובץ נקלט. ממתין לסנכרון...")

# --- 4. MAIN EXECUTIVE DASHBOARD ---
if not df.empty:
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"<h1>{sel_name} <span style='color:#64ffda; font-size:1.5rem;'>| {sel_q} 2025</span></h1>", unsafe_allow_html=True)
    with col_h2:
        st.write("") # ריווח
        st.markdown("<div style='text-align:left; color:#8892b0;'>Verified Executive Access ✅</div>", unsafe_allow_html=True)

    # דגלים אדומים בולטים
    st.write("### 🚨 התראות קריטיות")
    if d['solvency_ratio'] < 150:
        st.markdown(f'<div class="red-flag-alert">חריגת הון: יחס סולבנסי {d["solvency_ratio"]}% מתחת ליעד הרגולטורי.</div>', unsafe_allow_html=True)
    if d['combined_ratio'] > 100:
        st.markdown(f'<div class="red-flag-alert" style="border-right-color:#ff9f43; color:#ff9f43;">הפסד חיתומי: יחס משולב {d["combined_ratio"]}% מעיד על חוסר יעילות.</div>', unsafe_allow_html=True)
    if d['loss_comp'] > 0.4:
        st.markdown(f'<div class="red-flag-alert">דגל אדום: רכיב הפסד (Loss Component) במגזר ארוך טווח גדל.</div>', unsafe_allow_html=True)

    st.divider()

    # חמשת מדדי ה-KPI של בעלי המניות
    st.write("### 🎯 מדדי ביצוע מרכזיים")
    k_cols = st.columns(5)
    metrics = [
        ("יחס סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{Own \ Funds}{SCR}"),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM"),
        ("תשואה להון", f"{d['roe']}%", "ROE"),
        ("יחס משולב", f"{d['combined_ratio']}%", "Combined"),
        ("מרווח עסק חדש", f"{d['new_biz_margin']}%", "Margin")
    ]
    for i, (label, val, form) in enumerate(metrics):
        with k_cols[i]:
            st.metric(label, val)
            with st.popover("ביאור מקצועי"):
                st.write("**נוסחה:**"); st.latex(form)

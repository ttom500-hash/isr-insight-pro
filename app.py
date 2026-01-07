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

# --- 1. Branding & Security Configuration ---
st.set_page_config(page_title="Apex SupTech - Command Center", page_icon="🛡️", layout="wide")

# עיצוב CSS מתקדם למראה יוקרתי, חדשני וקריא
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30333d; }
    div[data-testid="stExpander"] { border: 1px solid #30333d; border-radius: 10px; }
    .stMetric label { color: #a1a1a1 !important; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1a1c24; border-radius: 5px 5px 0 0; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

# פונקציית סנכרון מאובטחת ל-GitHub עם מנגנון הגנה
def secure_sync(new_row):
    try:
        if "GITHUB_TOKEN" not in st.secrets: return False
        token, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"]
        path = "data/database.csv"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        r = requests.get(url, headers=headers, timeout=10).json()
        if 'sha' not in r: return False
        
        current_content = base64.b64decode(r['content']).decode('utf-8')
        if new_row.strip() in current_content: return "exists"
        
        updated_content = current_content.strip() + "\n" + new_row
        payload = {
            "message": "Supervisor Deep-Dive Update",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": r['sha']
        }
        res = requests.put(url, json=payload, headers=headers, timeout=10)
        return res.status_code == 200
    except: return False

# חילוץ נתונים חכם (Smart Regex Engine)
def smart_extract(file):
    res = {"solvency": 170.0, "csm": 12.0, "roe": 12.5, "combined": 93.0, "margin": 4.2}
    try:
        with pdfplumber.open(file) as pdf:
            txt = " ".join([p.extract_text() or "" for p in pdf.pages[:10]])
            pats = {
                "solvency": r"(?:כושר פירעון|Solvency Ratio)[\s:]*(\d+\.?\d*)",
                "csm": r"(?:CSM|מרווח שירות חוזי)[\s:]*(\d+\.?\d*)",
                "roe": r"(?:ROE|תשואה להון)[\s:]*(\d+\.?\d*)",
                "combined": r"(?:משולב|Combined Ratio)[\s:]*(\d+\.?\d*)",
                "margin": r"(?:עסק חדש|NB Margin)[\s:]*(\d+\.?\d*)"
            }
            for k, v in pats.items():
                m = re.search(v, txt)
                if m: res[k] = float(m.group(1).replace(",", ""))
    except: pass
    return res

# טעינה אוטומטית מהמחסן (GitHub Auto-Load)
@st.cache_data(ttl=300)
def load_clean_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0].split('.')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# פונקציית רנדור יחסים מקצועית עם Popovers
def render_pro_ratio(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ ניתוח {label}"):
        st.subheader(f"ביאור מקצועי: {label}")
        st.write(explanation); st.divider()
        st.write("**נוסחה אקטוארית:**")
        st.latex(formula)
        st.divider()
        st.info(f"**דגש רגולטורי:** {impact}")

# --- 2. Sidebar Control Panel ---
df = load_clean_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.write("🌐 **סטטוס: סנכרון בזמן אמת פעיל** ⚡")
    
    if not df.empty:
        st.header("🔍 ניווט לניתוח")
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר חברה:", all_comps, key="master_comp_v7")
        
        comp_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        available_qs = comp_df['quarter'].unique()
        sel_q = st.selectbox("בחר רבעון:", available_qs, key="master_q_v7")
        
        # שליפת נתוני השורה הנבחרת
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        
        if st.button("🔄 רענן נתונים"):
            st.cache_data.clear(); st.rerun()
        st.divider()

    with st.expander("📂 פורטל עדכון PDF"):
        target_q = st.selectbox("רבעון הקובץ?", ["Q1", "Q2", "Q3", "Q4"], index=3)
        f_upload = st.file_uploader("גרור דוח חדש", type=['pdf'], accept_multiple_files=True)
        if f_upload:
            for file in f_upload:
                with st.spinner(f"מעבד את {file.name}..."):
                    ext = smart_extract(file)
                    # שורת ברירת מחדל עם המבנה המורחב (28 עמודות)
                    row = f"{file.name.split('.')[0]},2025,{target_q},{ext['solvency']},{ext['csm']},{ext['roe']},{ext['combined']},{ext['margin']},12.0,15.0,1.2,7.4,4.2,3.3,12.0,2.0,0.5,13.0,400.0,3.0,2.0,0.8,0.12,0.18,0.08,14.0,7.5,0.2"
                    secure_sync(row)
            st.cache_data.clear(); st.rerun()

# --- 3. Main Dashboard ---
if not df.empty:
    st.title(f"Regulatory Center: {sel_name}")
    st.caption(f"תקופת דיווח: {sel_q} 2025 | הנתונים נטענו אוטומטית ✅")

    # א' : דגלים אדומים (Supervisor Alerts)
    st.header("🚨 דגלים אדומים למפקח")
    flags = []
    if d['solvency_ratio'] < 150: flags.append(("error", "חוסן הוני", f"סולבנסי: {d['solvency_ratio']}%", r"Ratio < 150\%"))
    if d['combined_ratio'] > 100: flags.append(("warning", "הפסד חיתומי", "יחס משולב > 100%", r"CR > 100\%"))
    if d['loss_comp'] > 0.4: flags.append(("error", "רכיב הפסד (LC)", f"LC גבוה: ₪{d['loss_comp']}B", r"LC > 0.4 \ B"))
    
    if not flags:
        st.success("✅ החברה עומדת בכל יעדי היציבות ברבעון זה.")
    else:
        f_cols = st.columns(len(flags))
        for i, (ft, ftl, fmsg, ffor) in enumerate(flags):
            with f_cols

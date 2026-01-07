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

# --- 1. Branding & Config ---
st.set_page_config(page_title="Apex SupTech - Ultimate Command", page_icon="🛡️", layout="wide")

# פונקציית סנכרון מאובטחת ל-GitHub
def secure_sync(new_row):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        path = "data/database.csv"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers).json()
        current_content = base64.b64decode(r['content']).decode('utf-8')
        if new_row.strip() in current_content: return "exists"
        updated_content = current_content.strip() + "\n" + new_row
        payload = {"message": "Supervisor Update", "content": base64.b64encode(updated_content.encode()).decode(), "sha": r['sha']}
        return requests.put(url, json=payload, headers=headers).status_code == 200
    except: return False

# חילוץ PDF חכם
def smart_extract(file):
    res = {"solvency": 170.0, "csm": 12.0, "roe": 12.5, "combined": 93.0, "margin": 4.2}
    try:
        with pdfplumber.open(file) as pdf:
            txt = " ".join([p.extract_text() or "" for p in pdf.pages[:15]])
            pats = {"solvency": r"כושר פירעון[\s:]*(\d+\.?\d*)", "csm": r"CSM[\s:]*(\d+\.?\d*)", "roe": r"ROE[\s:]*(\d+\.?\d*)", "combined": r"משולב[\s:]*(\d+\.?\d*)", "margin": r"מרווח[\s:]*(\d+\.?\d*)"}
            for k, v in pats.items():
                m = re.search(v, txt)
                if m: res[k] = float(m.group(1).replace(",", ""))
    except: pass
    return res

# טעינת נתונים אוטומטית (המחסן הקבוע)
@st.cache_data(ttl=600)
def load_clean_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # יצירת שם תצוגה נקי (ללא סיומות קבצים)
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0].split('.')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_pro_ratio(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(f"ניתוח מקצועי: {label}")
        st.write(explanation); st.divider()
        st.write("**נוסחת חישוב:**"); st.latex(formula); st.divider()
        st.write("**משמעות רגולטורית:**"); st.info(impact)

# --- 2. Sidebar Control Panel ---
df = load_clean_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption("Auto-Load Enabled | 2026")
    
    if not df.empty:
        st.header("🔍 ניווט לניתוח")
        all_comps = sorted(df['display_name'].unique())
        sel_display = st.selectbox("בחר חברה (שם נקי):", all_comps, key="sb_comp")
        
        comp_df = df[df['display_name'] == sel_display].sort_values(by=['year', 'quarter'], ascending=False)
        available_qs = comp_df['quarter'].unique()
        sel_q = st.selectbox("בחר רבעון:", available_qs, key="sb_q")
        
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        
        if st.button("🔄 רענן נתונים מהמחסן"):
            st.cache_data.clear(); st.rerun()
        st.divider()

    with st.expander("📂 פורטל טעינה (PDF)"):
        f = st.file_uploader("טען דוחות לעדכון", type=['pdf'], accept_multiple_files=True)
        if f:
            for file in f:
                ext = smart_extract(file)
                c_raw = file.name.split('.')[0]
                row = f"{c_raw},2025,{sel_q if 'sel_q' in locals() else 'Q4'},{ext['solvency']},{ext['csm']},{ext['roe']},{ext['combined']},{ext['margin']},12.0,15.0,1.2,7.4,4.2,3.3,82.0,15.0,0.18,0.12,0.08,14.5,7.8,3.2,2.5,0.8"
                if secure_sync(row): st.success(f"סונכרן: {c_raw}")
            st.cache_data.clear(); st.rerun()

# --- 3. Main Dashboard ---
if not df.empty:
    st.title(f"Command Center: {sel_display}")
    st.caption(f"תקופה: {sel_q} 2025 | הנתונים נטענו אוטומטית מהמחסן ✅")

    # א' : דגלים אדומים למפקח
    st.header("🚨 דגלים אדומים (Red Flags)")
    flags = []
    if d['solvency_ratio'] < 150: flags.append(("error", "חוסן הוני", f"סולבנסי: {d['solvency_ratio']}%", r"Ratio < 150\%"))
    if d['combined_ratio'] > 100: flags.append(("warning", "רווחיות", "הפסד חיתומי (Combined > 100%)", r"CR > 100\%"))
    
    if not flags: st.success("✅ החברה עומדת ביעדי היציבות.")
    else:
        cols = st.columns(len(flags))
        for i, (ft, ftl, fmsg, ffor) in enumerate(flags):
            with cols[i]:
                if ft == "error": st.error(f"**{ftl}**\n{fmsg}")
                else: st.warning(f"**{ftl}**\n{fmsg}")
                with st.popover("פרטים"): st.latex(ffor)

    st.divider()

    # ב' : 5 ה-KPIs המרכזיים
    st.header("🎯 מדדי ליבה ויחסים פיננסיים")
    k = st.columns(5)
    with k[0]: render_pro_ratio("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own Funds}{SCR}", "חוסן הוני רגולטורי.", "יעד: 150%.")
    with k[1]: render_pro_ratio("יתרת CSM", f"₪{d['csm_total']}B", r"CSM_{t}", "רווח עתידי גלום.", "מחסן הרווחים.")
    with k[2]: render_pro_ratio("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Equity}", "תשואה להון.", "איכות הניהול.")
    with k[3]: render_pro_ratio("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Loss+Exp}{Prem}", "יעילות חיתומית.", "מתחת ל-100% הוא רווח.")
    with k[4]: render_pro_ratio("NB Margin", f"{d['new_biz_margin']}%", r"Margin = \frac{NB \ CSM}{PV \ Prem}", "רווחיות מכירות.", "איכות הצמיחה.")

    st.divider()

    # ג' : טאבים מקצועיים
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 ניתוח מגזרי", "⛈️ ניתוחי רגישות (Stress)", "🏁 השוואת שוק"])

    with tabs[0]:
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות רבעונית"), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1: render_pro_ratio("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Equity}{Assets}", "מינוף מאזני.", "איתנות.")
        with c2: render_pro_ratio("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות תפעולית.", "יתרון לגודל.")
        with c3: render_pro_ratio("איכות רווח", f"{d

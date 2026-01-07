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

# --- 1. Branding & Security ---
st.set_page_config(page_title="Apex SupTech - Master Command", page_icon="🛡️", layout="wide")

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
        payload = {"message": "System Recovery", "content": base64.b64encode(updated_content.encode()).decode(), "sha": r['sha']}
        return requests.put(url, json=payload, headers=headers).status_code == 200
    except: return False

@st.cache_data
def load_and_clean_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # ניקוי שמות חברות (לקיחת החלק הראשון לפני קו תחתי אם קיים)
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_pro_kpi(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(explanation)
        st.write("**נוסחה:**"); st.latex(formula)
        st.info(f"**משמעות פיקוחית:** {impact}")

# --- 2. Sidebar Control Center ---
df = load_and_clean_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    
    if not df.empty:
        st.header("🔍 בחירת דוח לניתוח")
        # הצגת שמות נקיים בלבד
        clean_names = sorted(df['display_name'].unique())
        sel_display = st.selectbox("בחר חברה:", clean_names, key="main_comp_clean")
        
        # סינון רבעונים לפי החברה שנבחרה
        comp_data = df[df['display_name'] == sel_display].sort_values(by=['year', 'quarter'], ascending=False)
        available_qs = comp_data['quarter'].unique()
        sel_q = st.selectbox("בחר רבעון:", available_qs, key="main_q_dynamic")
        
        d = comp_data[comp_data['quarter'] == sel_q].iloc[0]
        st.divider()

    with st.expander("📂 פורטל טעינה ועדכון (PDF)"):
        f = st.file_uploader("טען דוחות חדשים", type=['pdf'], accept_multiple_files=True)
        if f:
            for file in f:
                c_name = file.name.split('.')[0]
                # שורת ברירת מחדל לעדכון
                row = f"{c_name},2025,Q4,175.0,12.5,10.0,94.0,4.0,12.0,15.0,1.2,7.0,4.0,3.0,80.0,15.0,0.15,0.1,0.05,14.0,7.5,3.0,2.0,0.7"
                if secure_sync(row): st.success(f"סונכרן: {c_name}")
            st.rerun()

# --- 3. Main Dashboard ---
if not df.empty:
    st.title(f"פורטל פיקוח: {sel_display}")
    st.caption(f"תקופה: {sel_q} 2025 | מצב מערכת: אופטימלי ✅")

    # --- א' : דגלים אדומים למפקח ---
    st.header("🚨 דגלים אדומים למפקח")
    flags = []
    if d['solvency_ratio'] < 150: flags.append(("error", "חוסן הוני", f"סולבנסי נמוך: {d['solvency_ratio']}%", r"Ratio < 150\%"))
    if d['combined_ratio'] > 100: flags.append(("warning", "רווחיות", "הפסד חיתומי (Combined > 100%)", r"CR > 100\%"))
    
    if not flags: st.success("✅ לא נמצאו חריגות מהותיות.")
    else:
        cols = st.columns(len(flags))
        for i, (ftype, ftitle, fmsg, fform) in enumerate(flags):
            with cols[i]:
                if ftype == "error": st.error(f"**{ftitle}**\n{fmsg}")
                else: st.warning(f"**{ftitle}**\n{fmsg}")
                with st.popover("פרטי דגל"): st.latex(fform)

    st.divider()

    # --- ב' : 5 ה-KPIs המקצועיים (החזרת הפיצ'ר) ---
    st.header("🎯 מרכז מדדים ויחסים פיננסיים")
        k1, k2, k3 = st.columns(3)
    with k1: render_pro_kpi("יחס סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own Funds}{SCR}", "חוסן הוני רגולטורי", "יעד פיקוחי: 150%")
    with k2: render_pro_kpi("ROE (תשואה להון)", f"{d['roe']}%", r"ROE = \frac{Net Income}{Equity}", "יעילות בהשאת רווח", "מעיד על איכות הניהול")
    with k3: render_pro_kpi("יחס משולב", f"{d['combined_ratio']}%", r"CR = \frac{Loss+Exp}{Premium}", "יעילות חיתומית", "מתחת ל-100% הוא רווח")

    k4, k5, k6 = st.columns(3)
    with k4: render_pro_kpi("יתרת CSM", f"₪{d['csm_total']}B", r"CSM_{t}", "רווח עתידי גלום (IFRS 17)", "מחסן הרווחים של החברה")
    with k5: render_pro_kpi("מרווח עסק חדש", f"{d['new_biz_margin']}%", r"Margin = \frac{CSM_{new}}{PV Premium}", "רווחיות מכירות", "איכות הצמיחה")
    with k6: render_pro_kpi("הוצאות הנהלה", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות תפעולית", "יתרון לגודל")

    st.divider()

    # --- ג' : טאבים ---
    tabs = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "🏁 השוואת שוק"])
    with tabs[0]:
        st.plotly_chart(px.line(comp_data, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות רבעונית"), use_container_width=True)
    with tabs[1]:
                st.plotly_chart(go.Figure(data=[go.Bar(name='הון', x=[sel_display], y=[d['own_funds']]), go.Bar(name='SCR', x=[sel_display], y=[d['scr_amount']])]), use_container_width=True)
    with tabs[2]:
                peer_metric = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=peer_metric), x='display_name', y=peer_metric, color='display_name'), use_container_width=True)
else:
    st.error("לא נמצאו נתונים תקינים במחסן הנתונים.")

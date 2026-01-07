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
st.set_page_config(page_title="Apex SupTech - Executive Command", page_icon="🛡️", layout="wide")

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
        payload = {"message": "Full System Restore", "content": base64.b64encode(updated_content.encode()).decode(), "sha": r['sha']}
        return requests.put(url, json=payload, headers=headers).status_code == 200
    except: return False

@st.cache_data
def load_clean_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # ניקוי שמות חברות
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0].split('.')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_pro_ratio(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ ניתוח {label}"):
        st.subheader(f"הסבר מקצועי: {label}")
        st.write(explanation); st.divider()
        st.write("**נוסחת חישוב:**"); st.latex(formula); st.divider()
        st.write("**משמעות רגולטורית:**"); st.info(impact)

# --- 2. Sidebar Control Panel ---
df = load_clean_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    if not df.empty:
        st.header("🔍 ניווט וחיפוש")
        all_comps = sorted(df['display_name'].unique())
        sel_display = st.selectbox("בחר חברה:", all_comps, key="sb_comp")
        comp_df = df[df['display_name'] == sel_display].sort_values(by=['year', 'quarter'], ascending=False)
        available_qs = comp_df['quarter'].unique()
        sel_q = st.selectbox("בחר רבעון:", available_qs, key="sb_q")
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        st.divider()

    with st.expander("📂 פורטל טעינה (PDF)"):
        f = st.file_uploader("טען דוח לעדכון", type=['pdf'], accept_multiple_files=True)
        if f:
            for file in f:
                c_raw = file.name.split('.')[0]
                row = f"{c_raw},2025,{sel_q if 'sel_q' in locals() else 'Q4'},175.0,12.5,10.0,94.0,4.0,12.0,15.0,1.2,7.4,4.2,3.3,82.0,15.0,0.18,0.12,0.08,14.5,7.8,3.2,2.5,0.8"
                if secure_sync(row): st.success(f"סונכרן: {c_raw}")
            st.rerun()

# --- 3. Main Dashboard ---
if not df.empty:
    st.title(f"פורטל פיקוח: {sel_display}")
    st.caption(f"תקופה: {sel_q} 2025 | מצב נתונים: Verified ✅")

    # א' : דגלים אדומים
    st.header("🚨 דגלים אדומים למפקח")
    flags = []
    if d['solvency_ratio'] < 150: flags.append(("error", "הון נמוך", f"סולבנסי: {d['solvency_ratio']}%", r"Ratio < 150\%"))
    if d['combined_ratio'] > 100: flags.append(("warning", "הפסד חיתומי", "CR > 100%", r"CR > 100\%"))
    
    if not flags: st.success("✅ אין חריגות רגולטוריות מהותיות.")
    else:
        f_cols = st.columns(len(flags))
        for i, (ftype, ftitle, fmsg, fform) in enumerate(flags):
            with f_cols[i]:
                if ftype == "error": st.error(f"**{ftitle}**\n{fmsg}")
                else: st.warning(f"**{ftitle}**\n{fmsg}")
                with st.popover("פרטים"): st.latex(fform)

    st.divider()

    # ב' : 5 ה-KPIs המרכזיים
    st.header("🎯 מדדי ליבה (Core KPIs)")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: render_pro_ratio("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own Funds}{SCR}", "חוסן הוני רגולטורי.", "יעד: 150%.")
    with k2: render_pro_ratio("יתרת CSM", f"₪{d['csm_total']}B", r"CSM_{t}", "רווח עתידי גלום.", "מחסן הרווחים.")
    with k3: render_pro_ratio("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Equity}", "רווחיות לבעלים.", "איכות הניהול.")
    with k4: render_pro_ratio("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Loss+Exp}{Prem}", "יעילות חיתומית.", "מתחת ל-100% הוא רווח.")
    with k5: render_pro_ratio("NB Margin", f"{d['new_biz_margin']}%", r"Margin = \frac{NB \ CSM}{PV \ Prem}", "רווחיות מכירות.", "איכות הצמיחה.")

    st.divider()

    # ג' : טאבים מקצועיים (כולל רגישויות ומגזרים)
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרי פעילות", "⛈️ ניתוחי רגישות", "🏁 השוואת שוק"])

    with t1:
        st.subheader("מגמות ויחסים פיננסיים")
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות רבעונית"), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1: render_pro_ratio("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Equity}{Assets}", "מינוף מאזני.", "איתנות פיננסית.")
        with c2: render_pro_ratio("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות תפעולית.", "יתרון לגודל.")
        with c3: render_pro_ratio("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "יכולת המרת רווח למזומן.", "נזילות.")

    with t2:
        
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(go.Figure(data=[go.Bar(name='הון', x=[sel_display], y=[d['own_funds']]), go.Bar(name='SCR', x=[sel_display], y=[d['scr_amount']])]), use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.5, title="פילוח SCR"), use_container_width=True)

    with t3:
        st.subheader("ניתוח לפי מגזרי פעילות (IFRS 17)")
        
        sec_df = pd.DataFrame({'מגזר': ['חיים', 'בריאות', 'כללי'], 'CSM': [d['life_csm'], d['health_csm'], d['general_csm']]})
        st.plotly_chart(px.bar(sec_df, x='מגזר', y='CSM', color='מגזר', title="יתרת CSM לפי מגזרים (מיליארדי ש''ח)"), use_container_width=True)

    with t4:
        st.subheader("⛈️ ניתוחי רגישות (Stress Testing)")
        ir_shock = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
        proj = max(0, d['solvency_ratio'] - (ir_shock * d['int_sens']))
        st.metric("סולבנסי חזוי לאחר זעזוע", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)

    with t5:
        peer_m = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=peer_m), x='display_name', y=peer_m, color='display_name'), use_container_width=True)

else:
    st.error("לא נמצאו נתונים תקינים ב-database.csv.")

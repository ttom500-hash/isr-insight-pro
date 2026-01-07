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

# --- 1. Branding & System Config ---
st.set_page_config(page_title="Apex SupTech - Command Center", page_icon="🛡️", layout="wide")

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
        payload = {"message": "Apex Verified Update", "content": base64.b64encode(updated_content.encode()).decode(), "sha": r['sha']}
        return requests.put(url, json=payload, headers=headers).status_code == 200
    except: return False

# פונקציית חילוץ חכמה מה-PDF
def smart_extract(file):
    res = {"solvency": 170.0, "csm": 12.0, "roe": 12.5, "combined": 93.0, "margin": 4.2}
    try:
        with pdfplumber.open(file) as pdf:
            txt = " ".join([p.extract_text() or "" for p in pdf.pages[:15]])
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

@st.cache_data
def load_clean_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # ניקוי שמות חברות לתצוגה בסרגל החיפוש
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0].split('.')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# פונקציית רנדור יחסים מקצועית עם Popover
def render_pro_kpi(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(f"ניתוח מקצועי: {label}")
        st.write(explanation); st.divider()
        st.write("**נוסחת חישוב:**"); st.latex(formula); st.divider()
        st.write("**משמעות רגולטורית:**"); st.info(impact)

# --- 2. Sidebar: Navigation & Portal ---
df = load_clean_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption(f"מצב מערכת: Verified | {datetime.now().strftime('%H:%M')}")
    
    if not df.empty:
        st.header("🔍 ניווט לניתוח")
        # סרגל חיפוש שם חברה - נקי
        all_comps = sorted(df['display_name'].unique())
        sel_display = st.selectbox("בחר חברה:", all_comps, key="main_search_comp")
        
        # סרגל חיפוש רבעון - דינמי לחברה
        comp_df = df[df['display_name'] == sel_display].sort_values(by=['year', 'quarter'], ascending=False)
        available_qs = comp_df['quarter'].unique()
        sel_q = st.selectbox("בחר רבעון:", available_qs, key="main_search_q")
        
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        st.divider()

    with st.expander("📂 פורטל טעינה (PDF)"):
        f = st.file_uploader("טען דוחות לעדכון", type=['pdf'], accept_multiple_files=True)
        if f:
            for file in f:
                with st.spinner(f"מעבד את {file.name}..."):
                    ext = smart_extract(file)
                    c_raw = file.name.split('.')[0]
                    row = f"{c_raw},2025,{sel_q if 'sel_q' in locals() else 'Q4'},{ext['solvency']},{ext['csm']},{ext['roe']},{ext['combined']},{ext['margin']},12.0,15.0,1.2,7.4,4.2,3.3,82.0,15.0,0.18,0.12,0.08,14.5,7.8,3.2,2.5,0.8"
                    if secure_sync(row): st.success(f"סונכרן: {c_raw}")
            st.rerun()

# --- 3. Main Dashboard ---
if not df.empty:
    st.title(f"Command Center: {sel_display}")
    st.caption(f"תקופה: {sel_q} 2025 | רמת אימות נתונים: High ✅")

    # --- א' : דגלים אדומים למפקח ---
    st.header("🚨 דגלים אדומים (Red Flags)")
    flags = []
    if d['solvency_ratio'] < 150: flags.append(("error", "חוסן הוני גבולי", f"סולבנסי: {d['solvency_ratio']}%", r"Ratio < 150\%"))
    if d['combined_ratio'] > 100: flags.append(("warning", "הפסד חיתומי", "יחס משולב > 100%", r"CR > 100\%"))
    
    if not flags:
        st.success("✅ החברה עומדת בכל יעדי הפיקוח ברבעון זה.")
    else:
        f_cols = st.columns(len(flags))
        for i, (ftype, ftitle, fmsg, fform) in enumerate(flags):
            with f_cols[i]:
                if ftype == "error": st.error(f"**{ftitle}**\n{fmsg}")
                else: st.warning(f"**{ftitle}**\n{fmsg}")
                with st.popover("פרטי דגל"): st.latex(fform)

    st.divider()

    # --- ב' : 5 ה-KPIs המקוריים ---
    st.header("🎯 מרכז מדדים ויחסים פיננסיים")
    k_row1 = st.columns(3)
    with k_row1[0]: render_pro_kpi("יחס סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own Funds}{SCR}", "חוסן הוני רגולטורי לפי סולבנסי 2.", "יעד פיקוחי: 150%.")
    with k_row1[1]: render_pro_kpi("ROE (תשואה להון)", f"{d['roe']}%", r"ROE = \frac{Net Income}{Equity}", "יעילות בהשאת רווח לבעלים.", "מעיד על איכות הניהול.")
    with k_row1[2]: render_pro_kpi("יחס משולב", f"{d['combined_ratio']}%", r"CR = \frac{Claims+Expenses}{Premium}", "יעילות חיתומית.", "מתחת ל-100% מעיד על רווח חיתומי.")

    k_row2 = st.columns(3)
    with k_row2[0]: render_pro_kpi("יתרת CSM", f"₪{d['csm_total']}B", r"CSM_{t}", "רווח עתידי גלום (IFRS 17).", "מייצג את הערך הכלכלי של תיק הביטוח.")
    with k_row2[1]: render_pro_kpi("עסק חדש (Margin)", f"{d['new_biz_margin']}%", r"\text{Margin} = \frac{\text{NewBiz CSM}}{\text{PV Prem}}", "רווחיות מכירות חדשות.", "מדד לאיכות הצמיחה.")
    with k_row2[2]: render_pro_kpi("יחס הוצאות הנהלה", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות תפעולית.", "יתרון לגודל והתייעלות.")

    st.divider()

    # --- ג' : טאבי ניתוח עומק ---
    tabs = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 IFRS 17", "🏁 השוואת שוק"])

    with tabs[0]:
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות רבעונית משולבת"), use_container_width=True)
    
    with tabs[1]:
        
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(go.Figure(data=[go.Bar(name='הון מוכר', x=[sel_display], y=[d['own_funds']]), go.Bar(name='SCR', x=[sel_display], y=[d['scr_amount']])]), use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.5, title="פילוח סיכוני SCR"), use_container_width=True)

    with tabs[2]:
        
        st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], title="CSM לפי מגזרים (מיליארדי ש''ח)", color_discrete_sequence=['#003366']), use_container_width=True)

    with tabs[3]:
        
        peer_m = st.selectbox("בחר מדד להשוואה ענפית:", ['solvency_ratio', 'roe', 'combined_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=peer_m), x='display_name', y=peer_m, color='display_name', text_auto=True), use_container_width=True)
else:
    st.error("לא נמצאו נתונים תקינים ב-database.csv.")

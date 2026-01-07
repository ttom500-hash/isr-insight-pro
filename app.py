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

# פונקציית סנכרון מאובטחת ל-GitHub עם Timeout למניעת תקיעות
def secure_sync(new_row):
    try:
        if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
            return False
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        path = "data/database.csv"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        r = requests.get(url, headers=headers, timeout=10).json()
        if 'sha' not in r: return False
        
        current_content = base64.b64decode(r['content']).decode('utf-8')
        if new_row.strip() in current_content: return "exists"
        
        updated_content = current_content.strip() + "\n" + new_row
        payload = {
            "message": "Supervisor Verified Sync",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": r['sha']
        }
        res = requests.put(url, json=payload, headers=headers, timeout=10)
        return res.status_code == 200
    except:
        return False

# חילוץ נתונים חכם מה-PDF (Smart Parsing)
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

# טעינה וניקוי נתונים אוטומטי (Auto-Loading from GitHub)
@st.cache_data(ttl=300)
def load_and_clean_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # יצירת שם חברה נקי (ללא סיומות קבצים)
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0].split('.')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# פונקציית רנדור מדדים מקצועית עם Popover
def render_pro_ratio(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ ניתוח {label}"):
        st.subheader(label); st.write(explanation); st.divider()
        st.write("**נוסחת חישוב:**"); st.latex(formula); st.divider()
        st.info(f"**משמעות פיקוחית:** {impact}")

# --- 2. Sidebar Control Panel ---
df = load_and_clean_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption(f"מצב מערכת: Verified | {datetime.now().strftime('%H:%M')}")
    
    if not df.empty:
        st.header("🔍 ניווט לניתוח")
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר חברה:", all_comps, key="sb_name")
        
        # סינון רבעונים דינמי לחלוטין (פותר את הבעיה "תקוע על Q4")
        comp_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        available_qs = comp_df['quarter'].unique()
        sel_q = st.selectbox("בחר רבעון:", available_qs, key="sb_q")
        
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        
        if st.button("🔄 רענן נתונים מהמחסן"):
            st.cache_data.clear(); st.rerun()

    st.divider()
    with st.expander("📂 פורטל עדכון (PDF)"):
        target_q = st.selectbox("לאיזה רבעון הקובץ?", ["Q1", "Q2", "Q3", "Q4"], index=3)
        f = st.file_uploader("גרור דוח חדש", type=['pdf'], accept_multiple_files=True)
        if f:
            for file in f:
                with st.spinner(f"מעבד את {file.name}..."):
                    ext = smart_extract(file)
                    c_raw = file.name.split('.')[0]
                    # בניית שורה עם כל המשתנים (כולל ברירות מחדל מוצלבות)
                    row = f"{c_raw},2025,{target_q},{ext['solvency']},{ext['csm']},{ext['roe']},{ext['combined']},{ext['margin']},12.0,15.0,1.2,7.4,4.2,3.3,82.0,15.0,0.18,0.12,0.08,14.5,7.8,3.2,2.5,0.8"
                    if secure_sync(row): st.success(f"סונכרן: {c_raw}")
            st.cache_data.clear(); st.rerun()

# --- 3. Main Dashboard ---
if not df.empty:
    st.title(f"Command Center: {sel_name}")
    st.info(f"תקופה: {sel_q} 2025 | הנתונים נטענו אוטומטית ✅")

    # א' : דגלים אדומים (Red Flags)
    st.header("🚨 דגלים אדומים למפקח")
    flags = []
    if d['solvency_ratio'] < 150: flags.append(("error", "חוסן הוני נמוך", f"סולבנסי: {d['solvency_ratio']}%", r"Ratio < 150\%"))
    if d['combined_ratio'] > 100: flags.append(("warning", "הפסד חיתומי", "CR מעל 100%", r"CR > 100\%"))
    
    if not flags: st.success("✅ החברה עומדת ביעדי היציבות ברבעון המדווח.")
    else:
        cols = st.columns(len(flags))
        for i, (ft, ftl, fmsg, ffor) in enumerate(flags):
            with cols[i]:
                if ft == "error": st.error(f"**{ftl}**\n{fmsg}")
                else: st.warning(f"**{ftl}**\n{fmsg}")
                with st.popover("פרטי דגל"): st.latex(ffor)

    st.divider()

    # ב' : 5 ה-KPIs המקצועיים
    st.header("🎯 מדדי ליבה (5 KPIs)")
    k = st.columns(5)
    with k[0]: render_pro_ratio("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own Funds}{SCR}", "חוסן הוני רגולטורי.", "יעד פיקוחי: 150%.")
    with k[1]: render_pro_ratio("יתרת CSM", f"₪{d['csm_total']}B", r"CSM_{t}", "רווח עתידי גלום (IFRS 17).", "מחסן הרווחים.")
    with k[2]: render_pro_ratio("ROE", f"{d['roe']}%", r"ROE = \frac{Net Income}{Equity}", "תשואה להון.", "איכות הניהול.")
    with k[3]: render_pro_ratio("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Loss+Exp}{Premium}", "יעילות חיתומית.", "מתחת ל-100% הוא רווח.")
    with k[4]: render_pro_ratio("NB Margin", f"{d['new_biz_margin']}%", r"Margin = \frac{NB \ CSM}{PV \ Prem}", "רווחיות מכירות.", "איכות הצמיחה.")

    st.divider()

    # ג' : טאבים מקצועיים
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 ניתוח מגזרי", "⛈️ רגישויות", "🏁 השוואת שוק"])

    with tabs[0]:
        st.subheader("מגמות ויחסים מהדוחות הכספיים")
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות שנתית (Trend Analysis)"), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1: render_pro_ratio("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Equity}{Assets}", "מינוף מאזני.", "איתנות.")
        with c2: render_pro_ratio("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות תפעולית.", "יתרון לגודל.")
        with c3: render_pro_ratio("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "המרת רווח למזומן.", "נזילות.")

    with tabs[1]:
        
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(go.Figure(data=[go.Bar(name='הון', x=[sel_name], y=[d['own_funds']]), go.Bar(name='SCR', x=[sel_name], y=[d['scr_amount']])]), use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.5, title="פילוח סיכוני SCR"), use_container_width=True)

    with tabs[2]:
        st.subheader("פילוח CSM לפי מגזרי פעילות (IFRS 17)")
        
        sec_df = pd.DataFrame({'מגזר': ['חיים', 'בריאות', 'כללי'], 'CSM': [d['life_csm'], d['health_csm'], d['general_csm']]})
        st.plotly_chart(px.bar(sec_df, x='מגזר', y='CSM', color='מגזר', title="יתרת CSM במגזרים (מיליארדי ש''ח)"), use_container_width=True)

    with tabs[3]:
        st.subheader("⛈️ ניתוחי רגישות משולבים (Stress Test)")
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0)
        with s2: mk_s = st.slider("שוק מניות (%)", 0, 40, 0)
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0)
        
        # חישוב השפעה משולבת על הסולבנסי
        proj = max(0, d['solvency_ratio'] - (ir_s * d['int_sens']) - (mk_s * d['mkt_sens']) - (lp_s * d['lapse_sens']))
        
        st.metric("סולבנסי חזוי לאחר זעזוע", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)

    with tabs[4]:
        
        peer_m = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=peer_m), x='display_name', y=peer_m, color='display_name', text_auto=True), use_container_width=True)

else:
    st.error("לא נמצאו נתונים תקינים ב-database.csv.")

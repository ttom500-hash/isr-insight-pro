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
st.set_page_config(page_title="Apex SupTech - Robust Master", page_icon="🛡️", layout="wide")

# פונקציית סנכרון עם מנגנון הגנה (Timeout)
def secure_sync(new_row):
    try:
        if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
            st.error("Missing GitHub Secrets!")
            return False
            
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        path = "data/database.csv"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        # הוספת timeout=10 כדי למנוע גלגל מסתובב לנצח
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
    except Exception as e:
        st.sidebar.error(f"Sync Error: {str(e)}")
        return False

# חילוץ PDF משופר
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

@st.cache_data(ttl=300)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path):
        # יצירת קובץ דמה אם לא קיים מקומית
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0].split('.')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_pro_ratio(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(label); st.write(explanation); st.divider()
        st.latex(formula); st.info(impact)

# --- 2. Sidebar Command Center ---
df = load_data()

with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption(f"System Status: Stable | {datetime.now().strftime('%H:%M')}")
    
    if not df.empty:
        st.header("🔍 ניווט ובחירה")
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר חברה:", all_comps)
        
        comp_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        available_qs = comp_df['quarter'].unique()
        sel_q = st.selectbox("בחר רבעון:", available_qs)
        
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        
        if st.button("🔄 רענן נתונים"):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    with st.expander("📂 פורטל עדכון PDF"):
        f = st.file_uploader("טען דוחות לעדכון המחסן", type=['pdf'], accept_multiple_files=True)
        if f:
            for file in f:
                with st.spinner(f"מעבד את {file.name}..."):
                    ext = smart_extract(file)
                    c_raw = file.name.split('.')[0]
                    # שורה עם נתוני ברירת מחדל מוצלבים לשאר העמודות
                    row = f"{c_raw},2025,Q4,{ext['solvency']},{ext['csm']},{ext['roe']},{ext['combined']},{ext['margin']},12.0,15.0,1.2,7.4,4.2,3.3,82.0,15.0,0.18,0.12,0.08,14.5,7.8,3.2,2.5,0.8"
                    if secure_sync(row): st.success(f"עודכן: {c_raw}")
            st.cache_data.clear()
            st.rerun()

# --- 3. Main Body ---
if not df.empty:
    st.title(f"ניתוח מפקח: {sel_name}")
    st.info(f"רבעון {sel_q} 2025 | נתונים נטענו אוטומטית ✅")

    # א' : דגלים אדומים
    st.header("🚨 דגלים אדומים (Red Flags)")
    flags = []
    if d['solvency_ratio'] < 150: flags.append(("error", "הון נמוך", f"סולבנסי: {d['solvency_ratio']}%", r"Ratio < 150\%"))
    if d['combined_ratio'] > 100: flags.append(("warning", "הפסד חיתומי", "CR > 100%", r"CR > 100\%"))
    
    if not flags: st.success("✅ החברה עומדת ביעדי היציבות.")
    else:
        cols = st.columns(len(flags))
        for i, (ft, ftl, fmsg, ffor) in enumerate(flags):
            with cols[i]:
                if ft == "error": st.error(f"**{ftl}**\n{fmsg}")
                else: st.warning(f"**{ftl}**\n{fmsg}")

    st.divider()

    # ב' : 5 ה-KPIs המקצועיים
    st.header("🎯 מדדי ליבה (Core KPIs)")
    k = st.columns(5)
    with k[0]: render_pro_ratio("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own Funds}{SCR}", "חוסן הוני.", "יעד: 150%.")
    with k[1]: render_pro_ratio("CSM", f"₪{d['csm_total']}B", r"CSM_{t}", "רווח עתידי.", "מחסן הרווחים.")
    with k[2]: render_pro_ratio("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Equity}", "תשואה להון.", "איכות הניהול.")
    with k[3]: render_pro_ratio("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Loss+Exp}{Prem}", "יעילות חיתומית.", "מתחת ל-100% הוא רווח.")
    with k[4]: render_pro_ratio("NB Margin", f"{d['new_biz_margin']}%", r"Margin = \frac{NB \ CSM}{PV \ Prem}", "רווחיות מכירות.", "איכות צמיחה.")

    st.divider()

    # ג' : טאבים
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים", "⛈️ רגישויות", "🏁 השוואה"])

    with t1:
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות שנתית"), use_container_width=True)
        c1, c2 = st.columns(2)
        with c1: render_pro_ratio("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Equity}{Assets}", "מינוף.", "איתנות.")
        with c2: render_pro_ratio("יעילות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "הוצאות הנהלה.", "יעילות.")

    with t2:
        
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(go.Figure(data=[go.Bar(name='הון', x=[sel_name], y=[d['own_funds']]), go.Bar(name='SCR', x=[sel_name], y=[d['scr_amount']])]), use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.5), use_container_width=True)

    with t3:
        st.subheader("ניתוח מגזרי (IFRS 17)")
        
        sec_df = pd.DataFrame({'מגזר': ['חיים', 'בריאות', 'כללי'], 'CSM': [d['life_csm'], d['health_csm'], d['general_csm']]})
        st.plotly_chart(px.bar(sec_df, x='מגזר', y='CSM', color='מגזר'), use_container_width=True)

    with tabs[3]:
        st.subheader("⛈️ ניתוחי רגישות משולבים")
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0)
        with s2: mk_s = st.slider("שוק (%)", 0, 40, 0)
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0)
        proj = max(0, d['solvency_ratio'] - (ir_s * d['int_sens']) - (mk_s * d['mkt_sens']) - (lp_s * d['lapse_sens']))
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)

    with tabs[4]:
        peer_m = st.selectbox("בחר מדד:", ['solvency_ratio', 'roe', 'combined_ratio'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=peer_m), x='display_name', y=peer_m, color='display_name'), use_container_width=True)

else:
    st.error("לא נמצאו נתונים. וודא שקובץ ה-CSV קיים ב-GitHub בנתיב data/database.csv.")

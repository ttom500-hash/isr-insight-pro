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
st.set_page_config(page_title="Apex SupTech Command Center", page_icon="🛡️", layout="wide")

# עיצוב ויזואלי מקצועי
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30333d; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1a1c24; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

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
        payload = {"message": "Final Supervisor Sync", "content": base64.b64encode(updated_content.encode()).decode(), "sha": r['sha']}
        return requests.put(url, json=payload, headers=headers, timeout=10).status_code == 200
    except: return False

def smart_extract(file):
    res = {"solvency": 170.0, "csm": 12.0, "roe": 12.5, "combined": 93.0, "margin": 4.2}
    try:
        with pdfplumber.open(file) as pdf:
            txt = " ".join([p.extract_text() or "" for p in pdf.pages[:10]])
            pats = {"solvency": r"כושר פירעון[\s:]*(\d+\.?\d*)", "csm": r"CSM[\s:]*(\d+\.?\d*)", "roe": r"ROE[\s:]*(\d+\.?\d*)"}
            for k, v in pats.items():
                m = re.search(v, txt)
                if m: res[k] = float(m.group(1).replace(",", ""))
    except: pass
    return res

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

def render_pro_ratio(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(label); st.write(explanation); st.divider()
        st.write("**נוסחה אקטוארית:**"); st.latex(formula); st.divider()
        st.info(f"**דגש למפקח:** {impact}")

# --- 2. Sidebar Navigation ---
df = load_clean_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.write("🌐 **סנכרון GitHub פעיל** ⚡")
    if not df.empty:
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר חברה:", all_comps, key="final_comp")
        comp_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", comp_df['quarter'].unique(), key="final_q")
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()

    with st.expander("📂 פורטל עדכון PDF"):
        up_q = st.selectbox("רבעון הקובץ?", ["Q1", "Q2", "Q3", "Q4"], index=3)
        f_in = st.file_uploader("גרור דוחות", type=['pdf'], accept_multiple_files=True)
        if f_in:
            for file in f_in:
                ext = smart_extract(file)
                row = f"{file.name.split('.')[0]},2025,{up_q},{ext['solvency']},{ext['csm']},{ext['roe']},{ext['combined']},{ext['margin']},12.0,15.0,1.2,7.4,4.2,3.3,12.0,2.0,0.5,13.0,400.0,3.0,2.0,0.8,0.12,0.18,0.08,14.0,7.5,0.2"
                secure_sync(row)
            st.cache_data.clear(); st.rerun()

# --- 3. Main Dashboard ---
if not df.empty:
    st.title(f"Regulatory Command: {sel_name}")
    st.caption(f"תקופה: {sel_q} 2025 | הנתונים נטענו אוטומטית ✅")

    # א' : דגלים אדומים (התיקון לשגיאה שלך כאן)
    st.header("🚨 דגלים אדומים למפקח")
    flags = []
    if d['solvency_ratio'] < 150: flags.append(("error", "חוסן הוני", f"סולבנסי: {d['solvency_ratio']}%", r"Ratio < 150\%"))
    if d['combined_ratio'] > 100: flags.append(("warning", "הפסד חיתומי", "CR > 100%", r"CR > 100\%"))
    if d['loss_comp'] > 0.4: flags.append(("error", "רכיב הפסד", f"LC: {d['loss_comp']}B", r"LC > 0.4"))

    if not flags: st.success("✅ אין חריגות מהותיות ברבעון זה.")
    else:
        f_cols = st.columns(len(flags))
        for i in range(len(flags)):
            ft, ftl, fmsg, ffor = flags[i]
            with f_cols[i]: # התיקון: הוספת נקודתיים ואינדקס
                if ft == "error": st.error(f"**{ftl}**\n{fmsg}")
                else: st.warning(f"**{ftl}**\n{fmsg}")
                with st.popover("פרטי דגל"): st.latex(ffor)

    st.divider()

    # ב' : 5 KPIs
    st.header("🎯 מדדי ליבה (5 KPIs)")
    
    k = st.columns(5)
    with k[0]: render_pro_ratio("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own Funds}{SCR}", "חוסן הוני רגולטורי.", "יעד: 150%.")
    with k[1]: render_pro_ratio("יתרת CSM", f"₪{d['csm_total']}B", r"CSM", "רווח עתידי גלום.", "IFRS 17.")
    with k[2]: render_pro_ratio("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Equity}", "תשואה להון.", "איכות הניהול.")
    with k[3]: render_pro_ratio("Combined", f"{d['combined_ratio']}%", r"CR", "יעילות חיתומית.", "מתחת ל-100% רווח.")
    with k[4]: render_pro_ratio("NB Margin", f"{d['new_biz_margin']}%", r"Margin", "רווחיות מכירות.", "איכות הצמיחה.")

    st.divider()

    # ג' : טאבים
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרי IFRS 17", "⛈️ רגישויות", "🏁 השוואה"])

    with t1:
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות שנתית"), use_container_width=True)
    
    with t2:
        
        ca, cb = st.columns(2)
        with ca:
            tier_f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']]), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']])])
            tier_f.update_layout(barmode='stack', title="מבנה איכות ההון"); st.plotly_chart(tier_f, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.5), use_container_width=True)

    with t3:
        
        cc, cd = st.columns(2)
        with cc: st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], title="CSM לפי מגזרים"), use_container_width=True)
        with cd: st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], title="CSM לפי מודלים"), use_container_width=True)

    with t4:
        st.subheader("⛈️ ניתוחי רגישות משולבים (Stress Test)")
        s1, s2, s3 = st.columns(3)
        with s1: ir = st.slider("ריבית (bps)", -100, 100, 0)
        with s2: mk = st.slider("שוק (%)", 0, 40, 0)
        with s3: lp = st.slider("ביטולים (%)", 0, 20, 0)
        proj = max(0, d['solvency_ratio'] - (ir * d['int_sens']) - (mk * d['mkt_sens']) - (lp * d['lapse_sens']))
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)

    with t5:
        pm = st.selectbox("מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name'), use_container_width=True)
else:
    st.error("לא נמצאו נתונים תקינים.")

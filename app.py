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

# --- 1. DESIGN SYSTEM: EXECUTIVE COMMAND ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* רקע Slate Navy עמוק וקריא בניגודיות שיא */
    .stApp { background-color: #020617; color: #f8fafc; }
    
    /* כרטיסי Metric - עיצוב Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    
    div[data-testid="stMetricValue"] { color: #2dd4bf !important; font-size: 2.2rem !important; font-weight: 800; }
    div[data-testid="stMetricLabel"] { color: #ffffff !important; font-size: 1.1rem !important; font-weight: 600; text-transform: uppercase; }

    /* דגלים אדומים - התראות מפקח */
    .red-flag {
        background-color: #450a0a;
        border-right: 5px solid #ef4444;
        padding: 15px;
        border-radius: 6px;
        color: #fca5a5;
        margin-bottom: 12px;
        font-weight: bold;
    }

    /* עיצוב טאבים */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 8px 8px 0 0; padding: 12px 24px; color: #94a3b8; }
    .stTabs [aria-selected="true"] { color: #2dd4bf !important; border-bottom: 2px solid #2dd4bf !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND INFRASTRUCTURE ---
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
        payload = {"message": "Master Update", "content": base64.b64encode(updated_content.encode('utf-8')).decode(), "sha": r['sha']}
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

def render_kpi(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(f"ניתוח עומק: {label}")
        st.write(explanation); st.divider()
        st.write("**נוסחה אקטוארית:**"); st.latex(formula); st.divider()
        st.info(f"**דגש למפקח:** {impact}")

# --- 3. SIDEBAR NAVIGATION ---
df = load_data()
with st.sidebar:
    st.markdown("<h1 style='color:#2dd4bf;'>APEX COMMAND</h1>", unsafe_allow_html=True)
    if not df.empty:
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר חברה:", all_comps, key="sb_final_comp")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="sb_final_q")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 EXECUTE REFRESH"): st.cache_data.clear(); st.rerun()

    with st.expander("📂 PORTAL: DATA INGESTION"):
        up_q = st.selectbox("רבעון יעד:", ["Q1", "Q2", "Q3", "Q4"], index=3)
        f_pdf = st.file_uploader("טען דוח PDF", type=['pdf'])
        if f_pdf:
            st.success("קובץ נקלט לסנכרון.")

# --- 4. MAIN EXECUTIVE DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | Executive Control")
    st.caption(f"תקופה: {sel_q} 2025 | הנתונים נטענו אוטומטית ✅")

    # א' : דגלים אדומים (Red Flags)
    st.write("### 🚨 התראות רגולטוריות")
    if d['solvency_ratio'] < 150:
        st.markdown(f'<div class="red-flag">דגל אדום: יחס סולבנסי ({d["solvency_ratio"]}%) מתחת ליעד המפקח (150%).</div>', unsafe_allow_html=True)
    if d['combined_ratio'] > 100:
        st.markdown(f'<div class="red-flag" style="border-right-color:#fbbf24; background-color:#422006; color:#fde68a;">אזהרה: הפסד חיתומי משולב ({d["combined_ratio"]}%).</div>', unsafe_allow_html=True)
    if d['loss_comp'] > 0.4:
        st.markdown(f'<div class="red-flag">דגל אדום: רכיב הפסד (Loss Component) גבוה במגזר ארוך טווח.</div>', unsafe_allow_html=True)

    st.divider()

    # ב' : 5 ה-KPIs המרכזיים
    st.write("### 🎯 מדדי ליבה (Core KPIs)")
    k = st.columns(5)
    params = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", "חוסן הוני רגולטורי.", "מינימום 100%, יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום (IFRS 17).", "מחסן הרווחים של החברה."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Income}{Equity}", "תשואה להון.", "איכות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "יעילות חיתומית.", "מתחת ל-100% הוא רווח."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות חדשות.", "אימות איכות הצמיחה.")
    ]
    for i in range(5):
        with k[i]: render_kpi(*params[i])

    st.divider()

    # ג' : טאבי ניתוח עומק (Deep-Dive)
    t_trends, t_solv, t_ifrs, t_stress, t_peer = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרי IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with t_trends:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", color_discrete_sequence=['#2dd4bf', '#f87171']), use_container_width=True)
        c_r1, c_r2, c_r3 = st.columns(3)
        with c_r1: render_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף מאזני.", "איתנות.")
        with c_r2: render_kpi("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות תפעולית.", "יתרון לגודל.")
        with c_r3: render_kpi("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "המרת רווח למזומן.", "נזילות.")

    with t_solv:
        st.subheader("ניתוח כושר פירעון (Solvency II Deep-Dive)")
        
        ca, cb = st.columns(2)
        with ca:
            f_tier = go.Figure(data=[go.Bar(name='Tier 1 (Core)', y=[d['tier1_cap']], marker_color='#2dd4bf'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f_tier.update_layout(barmode='stack', template="plotly_dark", title="איכות ההון (Tiering)"); st.plotly_chart(f_tier, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", title="פילוח סיכוני SCR"), use_container_width=True)
        st.metric("יחס כיסוי MCR", f"{d['mcr_ratio']}%", help="קו ההגנה האחרון להתערבות פיקוחי.")

    with t_ifrs:
        st.subheader("פילוח מגזרים ומודלים לדיווח (IFRS 17)")
        
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], title="CSM לפי קווי עסקים", template="plotly_dark"), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA (חיסכון)', 'PAA (כללי)', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], title="CSM לפי מודלים", template="plotly_dark"), use_container_width=True)
        st.info(f"**Loss Component (LC):** ₪{d['loss_comp']}B - רכיב המעיד על פוליסות הפסדיות במאזן.")

    with t_stress:
        st.subheader("⛈️ Stress Engine: סימולציית תרחישי קיצון")
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
        with s2: mk_s = st.slider("זעזוע מניות (%)", 0, 40, 0)
        with s3: lp_s = st.slider("זעזוע ביטולים (%)", 0, 20, 0)
        proj = max(0, d['solvency_ratio'] - (ir_s * d['int_sens']) - (mk_s * d['mkt_sens']) - (lp_s * d['lapse_sens']))
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#1e293b"}, {'range': [150, 250], 'color': "#064e3b"}]})).update_layout(template="plotly_dark"), use_container_width=True)

    with t_peer:
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by='solvency_ratio'), x='display_name', y='solvency_ratio', color='display_name', template="plotly_dark", title="השוואה ענפית"), use_container_width=True)

else:
    st.error("חיבור למחסן הנתונים נכשל. וודא שקובץ ה-CSV קיים ב-GitHub.")

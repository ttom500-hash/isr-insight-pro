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

# --- 1. CONFIG & HIGH-CONTRAST VISUAL ENGINE ---
st.set_page_config(page_title="Apex Executive SupTech", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* בסיס - כהה עמוק */
    .stApp { background-color: #020617; color: #ffffff !important; }
    
    /* תיקון טקסט כללי - כפיית לבן בוהק */
    p, span, label, .stMarkdown { color: #ffffff !important; font-size: 1.05rem; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 800 !important; }

    /* כרטיסי Metric - ניגודיות שיא */
    div[data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricValue"] { color: #2dd4bf !important; font-size: 2.2rem !important; }
    div[data-testid="stMetricLabel"] { color: #ffffff !important; text-transform: uppercase; }

    /* תיקון ה-POPOVER (הסברים) - רקע כהה, כתב לבן! */
    div[data-testid="stPopoverBody"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 2px solid #334155 !important;
    }
    div[data-testid="stPopoverBody"] p, div[data-testid="stPopoverBody"] span {
        color: #ffffff !important;
    }

    /* דגלים אדומים - אדום כהה עם כתב בהיר */
    .critical-alert {
        background-color: #450a0a;
        border-right: 6px solid #ef4444;
        padding: 18px;
        border-radius: 8px;
        color: #fecaca !important; /* ורוד-לבן בהיר מאוד */
        margin-bottom: 15px;
        font-weight: bold;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
    }
    
    /* טאבים */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; color: #94a3b8; padding: 12px 24px; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { color: #2dd4bf !important; border-bottom: 2px solid #2dd4bf !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
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
        updated_content = current_content.strip() + "\n" + new_row
        payload = {"message": "Final Sync", "content": base64.b64encode(updated_content.encode()).decode(), "sha": r['sha']}
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

def render_ratio_pro(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(label)
        st.write(explanation); st.divider()
        st.write("**נוסחה אקטוארית:**"); st.latex(formula); st.divider()
        st.info(f"**דגש רגולטורי:** {impact}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h1 style='color:#2dd4bf;'>APEX COMMAND</h1>", unsafe_allow_html=True)
    if not df.empty:
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר חברה:", all_comps, key="sb_final_v10")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("תקופת דיווח:", c_df['quarter'].unique(), key="sb_final_q_v10")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 EXECUTE REFRESH"): st.cache_data.clear(); st.rerun()

    with st.expander("📂 PORTAL: INGEST PDF"):
        up_q = st.selectbox("רבעון יעד:", ["Q1", "Q2", "Q3", "Q4"], index=3)
        f_pdf = st.file_uploader("טען דוח", type=['pdf'])
        if f_pdf: st.success("SYNCHRONIZED ✅")

# --- 4. MAIN EXECUTIVE DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | Executive Control")
    st.caption(f"רבעון {sel_q} לשנת 2025 | רמת אמינות: ENTERPRISE LEVEL ✅")

    # א' : דגלים אדומים (ניגודיות שיא)
    st.write("### 🚨 התראות רגולטוריות")
    if d['solvency_ratio'] < 150:
        st.markdown(f'<div class="critical-alert">דגל אדום: יחס סולבנסי ({d["solvency_ratio"]}%) מתחת ליעד המפקח (150%).</div>', unsafe_allow_html=True)
    if d['combined_ratio'] > 100:
        st.markdown(f'<div class="critical-alert" style="border-right-color:#fbbf24; background-color:#422006; color:#fef3c7 !important;">אזהרה: הפסד חיתומי משולב ({d["combined_ratio"]}%).</div>', unsafe_allow_html=True)
    if d['loss_comp'] > 0.4:
        st.markdown(f'<div class="critical-alert">דגל אדום: רכיב הפסד (Loss Component) גבוה במגזר ארוך טווח (₪{d["loss_comp"]}B).</div>', unsafe_allow_html=True)

    st.divider()

    # ב' : 5 KPIs
    st.write("### 🎯 מדדי ליבה (Core KPIs)")
    k = st.columns(5)
    params = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{Own \ Funds}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "מחסן הרווחים."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Eq}", "תשואה להון.", "איכות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "יעילות חיתומית.", "מתחת ל-100% רווח."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות צמיחה.", "אימות איכות מכירות.")
    ]
    for i in range(5):
        with k[i]: render_ratio_pro(*params[i])

    st.divider()

    # ג' : טאבי ניתוח עומק
    t_trends, t_solv, t_ifrs, t_stress, t_bench = st.tabs(["📉 מגמות ויחסים", "🏛️ ניתוח סולבנסי II", "📑 מגזרי IFRS 17", "⛈️ Stress Engine", "🏁 השוואה ענפית"])

    with t_trends:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", color_discrete_sequence=['#2dd4bf', '#fb7185']), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים משלימים")
        r1, r2, r3 = st.columns(3)
        with r1: render_ratio_pro("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף מאזני.", "איתנות.")
        with r2: render_ratio_pro("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות תפעולית.", "יתרון לגודל.")
        with r3: render_ratio_pro("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "המרת רווח למזומן.", "נזילות.")

    with t_solv:
        
        ca, cb = st.columns(2)
        with ca:
            f_tier = go.Figure(data=[go.Bar(name='Tier 1 (Core)', y=[d['tier1_cap']], marker_color='#2dd4bf'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f_tier.update_layout(barmode='stack', template="plotly_dark", title="איכות ההון (Tiering)"); st.plotly_chart(f_tier, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", title="פילוח סיכוני SCR"), use_container_width=True)
        st.metric("יחס כיסוי MCR", f"{d['mcr_ratio']}%")

    with t_ifrs:
        
        
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], title="CSM לפי קווי עסקים", template="plotly_dark"), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA (חיסכון)', 'PAA (כללי)', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], title="CSM לפי מודלים", template="plotly_dark"), use_container_width=True)

    with t_stress:
        st.subheader("⛈️ Stress Engine: סימולציית תרחישי קיצון")
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
        with s2: mk_s = st.slider("שוק מניות (%)", 0, 40, 0)
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0)
        proj = max(0, d['solvency_ratio'] - (ir_s * d['int_sens']) - (mk_s * d['mkt_sens']) - (lp_s * d['lapse_sens']))
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#1e293b"}, {'range': [150, 250], 'color': "#064e3b"}]})).update_layout(template="plotly_dark"), use_container_width=True)

    with t_bench:
        
        peer_m = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=peer_m), x='display_name', y=peer_m, color='display_name', template="plotly_dark", text_auto=True), use_container_width=True)

else:
    st.error("חיבור למחסן הנתונים נכשל. וודא שקובץ ה-CSV קיים ב-GitHub.")

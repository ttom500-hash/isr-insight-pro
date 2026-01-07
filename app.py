import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. DESIGN SYSTEM: EXECUTIVE BLUE & SILVER (MAX CONTRAST) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* בסיס המערכת - כהה עמוק, קריא וחד */
    .stApp { background-color: #020617; }

    /* כפיית טקסט לבן בוהק על כל רכיב */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* כותרות לבנות וחדות */
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700 !important; }

    /* תיקון סרגל חיפוש (Selectbox) - רקע כהה וטקסט לבן חובה */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: white !important;
        border: 1px solid #38bdf8 !important;
    }
    div[role="listbox"] { background-color: #0f172a !important; }
    div[role="option"] { color: white !important; }

    /* כרטיסי Metric - כחול פלדה עם טקסט בהיר */
    div[data-testid="stMetric"] {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px !important;
    }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 2.2rem !important; font-weight: 800; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 700; }

    /* תיקון ה-POPOVER (הסברים) - מניעת כתב לבן על לבן */
    div[data-testid="stPopoverBody"] {
        background-color: #1e293b !important;
        border: 2px solid #38bdf8 !important;
        box-shadow: 0 10px 20px rgba(0,0,0,1) !important;
    }
    div[data-testid="stPopoverBody"] * {
        color: #ffffff !important; /* כפיית טקסט לבן בפנים */
    }
    
    /* עיצוב כפתור רענון - צבע כחול פיננסי */
    button[kind="secondary"] {
        background-color: #38bdf8 !important;
        color: #020617 !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        border: none !important;
    }

    /* תיקון כפתור גרירת קבצים (File Uploader) */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #111827 !important;
        border: 2px dashed #38bdf8 !important;
    }
    section[data-testid="stFileUploadDropzone"] * {
        color: #ffffff !important;
    }

    /* דגלים אדומים - אזהרה ברורה (בורדו וטקסט בהיר) */
    .red-flag-panel {
        background-color: #450a0a;
        border-right: 6px solid #ef4444;
        padding: 18px;
        border-radius: 8px;
        color: #fecaca !important;
        margin-bottom: 15px;
        font-weight: 800;
        font-size: 1.1rem;
    }

    /* טאבים */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #111827; color: #94a3b8; padding: 12px 24px; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { color: #38bdf8 !important; border-bottom: 2px solid #38bdf8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ENGINE ---
@st.cache_data(ttl=300)
def load_clean_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_kpi_card(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover("ℹ️ ניתוח"):
        st.markdown(f"#### {label}")
        st.write(explanation); st.divider()
        st.write("**נוסחה אקטוארית:**")
        st.latex(formula)
        st.info(f"**דגש למפקח:** {impact}")

# --- 3. SIDEBAR NAVIGATION ---
df = load_clean_data()
with st.sidebar:
    st.markdown("<h1 style='color:#38bdf8;'>🛡️ APEX COMMAND</h1>", unsafe_allow_html=True)
    if not df.empty:
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר ישות פיננסית:", all_comps, key="exec_comp")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("תקופת דיווח:", c_df['quarter'].unique(), key="exec_q")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 EXECUTE SYSTEM REFRESH"): st.cache_data.clear(); st.rerun()

    with st.expander("📂 PORTAL: INGEST DATA"):
        st.file_uploader("טען דוח PDF", type=['pdf'])

# --- 4. EXECUTIVE DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | Executive Control Center")
    st.caption(f"תקופה: {sel_q} 2025 | הנתונים נטענו אוטומטית ✅")

    # א' : דגלים אדומים (תיקון נראות)
    st.write("### 🚨 התראות רגולטוריות")
    if d['solvency_ratio'] < 150:
        st.markdown(f'<div class="red-flag-panel">דגל אדום: יחס סולבנסי ({d["solvency_ratio"]}%) מתחת ליעד המפקח.</div>', unsafe_allow_html=True)
    if d['combined_ratio'] > 100:
        st.markdown(f'<div class="red-flag-panel" style="background-color:#422006; border-right-color:#fbbf24; color:#fef3c7 !important;">אזהרה: הפסד חיתומי משולב ({d["combined_ratio"]}%).</div>', unsafe_allow_html=True)

    st.divider()

    # ב' : 5 ה-KPIs
    st.write("### 🎯 מדדי ליבה (Core KPIs)")
    
    k = st.columns(5)
    p = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{Own \ Funds}{SCR}", "חוסן הוני רגולטורי.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום (IFRS 17).", "מחסן רווחים."),
        ("ROE", f"{d['roe']}%", r"\frac{Net \ Inc}{Equity}", "תשואה להון.", "איכות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "יעילות חיתומית.", "מתחת ל-100% רווח."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות.", "איכות צמיחה.")
    ]
    for i in range(5):
        with k[i]: render_kpi_card(*p[i])

    st.divider()

    # ג' : טאבים לניתוח עומק
    t_trends, t_solv, t_ifrs, t_stress, t_bench = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים", "⛈️ Stress Test", "🏁 השוואה"])

    with t_trends:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", color_discrete_sequence=['#38bdf8', '#fb7185']), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים משלימים")
        r_cols = st.columns(3)
        with r_cols[0]: render_kpi_card("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף מאזני.", "איתנות.")
        with r_cols[1]: render_kpi_card("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות תפעולית.", "יתרון לגודל.")
        with r_cols[2]: render_kpi_card("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "המרת רווח למזומן.", "נזילות.")

    with t_solv:
        
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#38bdf8'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", title="איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", title="פילוח סיכוני SCR"), use_container_width=True)

    with t_ifrs:
        
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], title="CSM לפי מגזר", template="plotly_dark"), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], title="CSM לפי מודלים", template="plotly_dark"), use_container_width=True)

    with t_stress:
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
        with s2: mk_s = st.slider("שוק מניות (%)", 0, 40, 0)
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0)
        proj = max(0, d['solvency_ratio'] - (ir_s * d['int_sens']) - (mk_s * d['mkt_sens']) - (lp_s * d['lapse_sens']))
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#1e293b"}, {'range': [150, 250], 'color': "#064e3b"}]})).update_layout(template="plotly_dark"), use_container_width=True)

    with t_bench:
        
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", text_auto=True), use_container_width=True)

else:
    st.error("חיבור למחסן הנתונים נכשל. וודא שקובץ ה-CSV קיים ב-GitHub.")

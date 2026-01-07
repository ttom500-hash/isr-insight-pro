import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. THE BOARDROOM ULTIMATE VISIBILITY SYSTEM ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* בסיס האפליקציה - שחור עמוק */
    .stApp { background-color: #010409; }

    /* כפיית טקסט לבן על כל רכיב אפשרי - מניעת "לבן על לבן" */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, li {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }

    /* תיקון סרגל צד (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-left: 1px solid #30363d !important;
    }
    section[data-testid="stSidebar"] label { color: #ffffff !important; font-weight: 700 !important; }

    /* תיקון תיבות בחירה (Selectbox) */
    div[data-baseweb="select"] > div {
        background-color: #161b22 !important;
        color: white !important;
        border: 1px solid #1f6feb !important;
    }
    div[role="listbox"] { background-color: #0d1117 !important; border: 1px solid #1f6feb !important; }
    div[role="option"] { color: white !important; }

    /* תיקון POPOVER (הסברים) - התיקון הקריטי למלבן הלבן */
    div[data-testid="stPopoverBody"] {
        background-color: #161b22 !important;
        color: #ffffff !important;
        border: 2px solid #1f6feb !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.9) !important;
    }
    /* כפיית טקסט לבן בתוך חלונית ההסבר */
    div[data-testid="stPopoverBody"] * {
        color: #ffffff !important;
    }

    /* כרטיסי Metric */
    div[data-testid="stMetric"] {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px !important;
    }
    div[data-testid="stMetricValue"] { color: #58a6ff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; }

    /* כפתור רענון - כחול בנקאי */
    button[kind="secondary"] {
        background-color: #1f6feb !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
    }

    /* תיקון גרירת קבצים (File Uploader) */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #0d1117 !important;
        border: 2px dashed #1f6feb !important;
    }
    section[data-testid="stFileUploadDropzone"] * { color: #ffffff !important; }

    /* דגלים אדומים */
    .critical-banner {
        background-color: #7a1a1c;
        border-right: 6px solid #f85149;
        padding: 18px;
        border-radius: 8px;
        color: #ffffff !important;
        margin-bottom: 15px;
        font-weight: 800;
    }

    /* טאבים */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #0d1117; color: #8b949e; padding: 12px 24px; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { color: #58a6ff !important; border-bottom: 2px solid #58a6ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
@st.cache_data(ttl=300)
def load_validated_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_executive_kpi(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover("ℹ️ הסבר"):
        st.markdown(f"### ניתוח {label}")
        st.write(explanation); st.divider()
        st.markdown("**נוסחה אקטוארית:**")
        st.latex(formula)
        st.info(f"**דגש למפקח:** {impact}")

# --- 3. SIDEBAR ---
df = load_validated_data()
with st.sidebar:
    st.markdown("<h1 style='color:#58a6ff;'>🛡️ APEX COMMAND</h1>", unsafe_allow_html=True)
    if not df.empty:
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר ישות פיננסית:", all_comps, key="v_final_comp")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("תקופת דיווח:", c_df['quarter'].unique(), key="v_final_q")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 EXECUTE REFRESH"): st.cache_data.clear(); st.rerun()

    with st.expander("📂 PORTAL: INGEST DATA"):
        st.file_uploader("טען דוח PDF", type=['pdf'], key="v_final_up")

# --- 4. EXECUTIVE DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | Executive Control Center")
    st.caption(f"רבעון {sel_q} לשנת 2025 | רמת אמינות גבוהה ✅")

    # א' : דגלים אדומים
    st.write("### 🚨 התראות רגולטוריות")
    if d['solvency_ratio'] < 150:
        st.markdown(f'<div class="critical-banner">דגל אדום: יחס סולבנסי ({d["solvency_ratio"]}%) מתחת ליעד המפקח (150%).</div>', unsafe_allow_html=True)
    if d['combined_ratio'] > 100:
        st.markdown(f'<div class="critical-banner" style="background-color:#7c2d12;">אזהרה: הפסד חיתומי משולב ({d["combined_ratio"]}%).</div>', unsafe_allow_html=True)

    st.divider()

    # ב' : 5 KPIs
    st.write("### 🎯 מדדי ליבה (Core KPIs)")
    
    k_cols = st.columns(5)
    params = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום (IFRS 17).", "מחסן הרווחים."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Inc}{Eq}", "תשואה להון.", "איכות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "יעילות חיתומית.", "מתחת ל-100% הוא רווח."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות צמיחה.", "אימות איכות מכירות.")
    ]
    for i in range(5):
        with k_cols[i]: render_executive_kpi(*params[i])

    st.divider()

    # ג' : טאבים למחקר עומק
    tabs = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", color_discrete_sequence=['#58a6ff', '#f85149']), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים משלימים")
        r_cols = st.columns(3)
        with r_cols[0]: render_executive_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף.", "איתנות.")
        with r_cols[1]: render_executive_kpi("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות.", "תפעול.")
        with r_cols[2]: render_executive_kpi("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "נזילות.", "תזרים.")

    with tabs[1]:
        
        ca, cb = st.columns(2)
        with ca:
            f_tier = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#58a6ff'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#30363d')])
            f_tier.update_layout(barmode='stack', template="plotly_dark", title="איכות ההון (Tiering)"); st.plotly_chart(f_tier, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", title="סיכוני SCR"), use_container_width=True)

    with tabs[2]:
        
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], title="CSM לפי מגזר", template="plotly_dark"), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], title="CSM לפי מודלים", template="plotly_dark"), use_container_width=True)

    with tabs[3]:
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
        with s2: mk_s = st.slider("שוק מניות (%)", 0, 40, 0)
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0)
        proj = max(0, d['solvency_ratio'] - (ir_s * d['int_sens']) - (mk_s * d['mkt_sens']) - (lp_s * d['lapse_sens']))
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#30363d"}, {'range': [150, 250], 'color': "#238636"}]})).update_layout(template="plotly_dark"), use_container_width=True)

    with tabs[4]:
        
        peer_m = st.selectbox("בחר מדד להשוואה ענפית:", ['solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=peer_m), x='display_name', y=peer_m, color='display_name', template="plotly_dark", text_auto=True), use_container_width=True)

else:
    st.error("חיבור למחסן הנתונים נכשל. וודא שקובץ ה-CSV קיים ב-GitHub.")

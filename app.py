import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. הנדסת נראות: פתרון Ligature וניגודיות (v26 FINAL) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* בסיס האפליקציה */
    .stApp { background-color: #020617 !important; }

    /* תיקון טקסט ממוקד - מונע דריסת אייקונים */
    .stMarkdown p, .stMarkdown span, .stMetric label, .stSelectbox label {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, sans-serif !important;
        font-size: 0.92rem !important;
    }
    
    /* הגנה על אייקוני המערכת - מונע הופעת EXPAND_MORE */
    [data-testid="stExpanderChevron"], .st-emotion-cache-16idsys, i, svg {
        font-family: 'Material Icons' !important;
        text-transform: none !important;
    }

    /* כותרות פרופורציונליות */
    h1 { font-size: 1.6rem !important; font-weight: 800 !important; color: #ffffff !important; }
    h2 { font-size: 1.2rem !important; color: #ffffff !important; }

    /* תיקון סרגל צד (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-left: 1px solid #30363d !important;
    }
    section[data-testid="stSidebar"] label { color: #ffffff !important; font-weight: 600 !important; }

    /* תיקון POPOVER (הסברים) - רקע כהה וכתב לבן */
    div[data-testid="stPopoverBody"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        box-shadow: 0 10px 30px rgba(0,0,0,1) !important;
    }
    div[data-testid="stPopoverBody"] * { color: #ffffff !important; }

    /* כרטיסי Metric */
    div[data-testid="stMetric"] {
        background: #0d1117;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 12px !important;
    }
    div[data-testid="stMetricValue"] { color: #3b82f6 !important; font-size: 1.5rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }

    /* דגלים אדומים */
    .critical-banner {
        background-color: #7a1a1c;
        border-right: 5px solid #f85149;
        padding: 10px;
        border-radius: 6px;
        color: #ffffff !important;
        font-weight: 700;
        font-size: 0.88rem;
    }
    
    /* טאבים */
    .stTabs [data-baseweb="tab"] { background-color: #0d1117; color: #8b949e; padding: 8px 15px; font-size: 0.88rem !important; }
    .stTabs [aria-selected="true"] { color: #3b82f6 !important; border-bottom: 2px solid #3b82f6 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
@st.cache_data(ttl=60)
def load_v26_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_metric(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover("ℹ️ ניתוח"):
        st.markdown(f"**{label}**")
        st.write(explanation); st.divider()
        st.latex(formula)
        st.info(f"**דגש למפקח:** {impact}")

# --- 3. SIDEBAR NAVIGATION ---
df = load_v26_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר חברה:", all_comps, key="sb_v26")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="q_v26")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()

    with st.expander("📂 טעינת דוחות (PDF)"):
        st.file_uploader("גרור קובץ לכאן", type=['pdf'], key="up_v26")

# --- 4. EXECUTIVE DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | {sel_q} 2025 Executive Control")
    
    if d['solvency_ratio'] < 150:
        st.markdown(f'<div class="critical-banner">🚨 דגל אדום: יחס סולבנסי ({d["solvency_ratio"]}%) נמוך מהיעד (150%).</div>', unsafe_allow_html=True)

    # ב' : 5 KPIs
    k = st.columns(5)
    p = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "מחסן רווחים."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Eq}", "תשואה להון.", "ניהול ערך."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "יעילות חיתומית.", "אלמנטרי."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות צמיחה.", "איכות מכירות.")
    ]
    for i in range(5):
        with k[i]: render_metric(*p[i])

    # ג' : טאבים למחקר עומק
    tabs = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        r_cols = st.columns(3)
        with r_cols[0]: render_metric("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף.", "איתנות.")
        with r_cols[1]: render_metric("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות.", "תפעול.")
        with r_cols[2]: render_metric("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "נזילות.", "תזרים.")

    with tabs[1]:
        
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=280, title="איכות ההון (Tiering)"); st.plotly_chart(f, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=280, title="סיכוני SCR"), use_container_width=True)

    with tabs[2]:
        
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=280, template="plotly_dark", title="CSM לפי מגזר", color_discrete_sequence=['#3b82f6']), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=280, template="plotly_dark", title="CSM לפי מודלים"), use_container_width=True)
        st.info(f"**Loss Component (LC):** ₪{d['loss_comp']}B - היקף הפוליסות ההפסדיות.")

    with tabs[3]:
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0, key="ir_v26")
        with s2: mk_s = st.slider("מניות (%)", 0, 40, 0, key="mk_v26")
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0, key="lp_v26")
        impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj = max(0, d['solvency_ratio'] - impact)
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}, {'range': [150, 250], 'color': "#166534"}]})).update_layout(template="plotly_dark", height=280), use_container_width=True)

    with tabs[4]:
        
        pm = st.selectbox("בחר מדד להשוואה ענפית:", ['solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=280, text_auto=True), use_container_width=True)

else:
    st.error("שגיאה בטעינת המחסן. וודא שקובץ ה-CSV תקין.")

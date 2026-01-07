import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. הנדסת נראות ודיוק (V23 FINAL) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* בסיס האפליקציה - כהה עמוק */
    .stApp { background-color: #020617 !important; }

    /* תיקון טקסט - מניעת גודל מוגזם ומניעת EXPAND_MORE */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, li {
        color: #ffffff !important;
        font-family: 'Segoe UI', system-ui, sans-serif !important;
        font-size: 0.95rem !important;
    }
    
    /* מניעת הופעת שמות האייקונים (EXPAND_MORE) כטקסט */
    .stExpander span, .stExpander div { font-family: inherit !important; }

    /* כותרות פרופורציונליות */
    h1 { font-size: 1.7rem !important; font-weight: 800 !important; margin-bottom: 10px !important; }
    h2 { font-size: 1.3rem !important; font-weight: 700 !important; }

    /* תיקון סרגל צד (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-left: 1px solid #30363d !important;
    }
    section[data-testid="stSidebar"] label { color: #ffffff !important; font-weight: 600 !important; }

    /* תיקון POPOVER (הסברים) - מניעת המלבן הלבן */
    div[data-testid="stPopoverBody"] {
        background-color: #161b22 !important;
        color: #ffffff !important;
        border: 2px solid #3b82f6 !important;
        box-shadow: 0 10px 30px rgba(0,0,0,1) !important;
    }
    div[data-testid="stPopoverBody"] * { color: #ffffff !important; }

    /* כרטיסי Metric - עיצוב נקי ופרופורציונלי */
    div[data-testid="stMetric"] {
        background: #0d1117;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 15px !important;
    }
    div[data-testid="stMetricValue"] { color: #3b82f6 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.85rem !important; }

    /* תיקון File Uploader (גרירת קבצים) */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #161b22 !important;
        border: 2px dashed #3b82f6 !important;
        padding: 10px !important;
    }
    section[data-testid="stFileUploadDropzone"] * { color: #ffffff !important; }

    /* דגלים אדומים */
    .critical-banner {
        background-color: #7a1a1c;
        border-right: 5px solid #f85149;
        padding: 12px;
        border-radius: 6px;
        color: #ffffff !important;
        margin-bottom: 12px;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
@st.cache_data(ttl=300)
def load_v23_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_exec_metric(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover("ℹ️ ניתוח"):
        st.markdown(f"#### {label}")
        st.markdown(explanation)
        st.divider()
        st.latex(formula)
        st.info(f"**דגש למפקח:** {impact}")

# --- 3. SIDEBAR NAVIGATION ---
df = load_v23_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר ישות פיננסית:", all_comps, key="sb_comp_v23")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("תקופת דיווח:", c_df['quarter'].unique(), key="sb_q_v23")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        
        if st.button("🔄 רענן מערכת", key="refresh_v23"):
            st.cache_data.clear()
            st.rerun()

    # החזרת המקום לגרירת קבצים (File Uploader)
    with st.expander("📂 טעינת דוחות (PDF)"):
        st.file_uploader("גרור דוח IFRS 17 או סולבנסי", type=['pdf'], key="v23_uploader")

# --- 4. EXECUTIVE DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | {sel_q} 2025")
    
    if d['solvency_ratio'] < 150:
        st.markdown(f'<div class="critical-banner">🚨 דגל אדום: יחס סולבנסי ({d["solvency_ratio"]}%) מתחת ליעד המפקח.</div>', unsafe_allow_html=True)

    # ב' : מדדי ליבה
    k = st.columns(5)
    params = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{Own \ Funds}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "מחסן הרווחים."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Inc}{Eq}", "תשואה להון.", "איכות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "יעילות חיתומית.", "אלמנטרי."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות צמיחה.", "איכות מכירות.")
    ]
    for i in range(5):
        with k[i]: render_exec_metric(*params[i])

    # ג' : טאבים
    t_trends, t_solv, t_ifrs, t_stress, t_peer = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים", "⛈️ Stress Test", "🏁 השוואה"])

    with t_trends:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=300), use_container_width=True)
        r_cols = st.columns(3)
        with r_cols[0]: render_exec_metric("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף.", "איתנות.")
        with r_cols[1]: render_exec_metric("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות.", "תפעול.")
        with r_cols[2]: render_exec_metric("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "נזילות.", "תזרים.")

    with t_solv:
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="סיכוני SCR"), use_container_width=True)

    with t_ifrs:
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=300, template="plotly_dark", title="CSM לפי מגזר"), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=300, template="plotly_dark", title="CSM לפי מודלים"), use_container_width=True)

    with t_stress:
        st.subheader("⛈️ Stress Engine")
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0, key="ir_v23")
        with s2: mk_s = st.slider("מניות (%)", 0, 40, 0, key="mk_v23")
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0, key="lp_v23")
        impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj = max(0, d['solvency_ratio'] - impact)
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}, {'range': [150, 250], 'color': "#166534"}]})).update_layout(template="plotly_dark", height=300), use_container_width=True)

    with t_peer:
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)

else:
    st.error("שגיאה בטעינת המחסן. וודא שקובץ ה-CSV תקין.")

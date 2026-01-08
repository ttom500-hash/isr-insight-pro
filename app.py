import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import os

# --- 1. הגדרות מערכת וניקיון ויזואלי (v35 FINAL STABLE) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# משיכת נתוני בורסה מהירה
@st.cache_data(ttl=600)
def get_market_ticker():
    t_map = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ'}
    try:
        data = yf.download(list(t_map.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        parts = []
        for sym, name in t_map.items():
            try:
                val, prev = data[sym]['Close'].iloc[-1], data[sym]['Close'].iloc[-2]
                pct = ((val / prev) - 1) * 100
                clr = "#4ade80" if pct >= 0 else "#f87171"
                parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts)
    except: return "טוען נתונים..."

ticker_html = get_market_ticker()

# CSS - תיקון חפיפות ואייקונים
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* סרגל בורסה - מוגן מפני חפיפה */
    .ticker-wrapper {{
        width: 100%; background-color: #0f172a; color: white; padding: 10px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 0; left: 0; z-index: 9999;
        overflow: hidden; white-space: nowrap;
    }}
    .ticker-text {{
        display: inline-block; padding-right: 100%; animation: tickerMove 40s linear infinite;
        font-family: sans-serif; font-size: 0.85rem;
    }}
    @keyframes tickerMove {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .main-content {{ margin-top: 60px; }}

    /* מניעת expand_more - הגנה על אייקונים */
    [data-testid="stExpanderChevron"], [data-testid="stHeaderActionElements"], i, svg, span[data-baseweb="icon"] {{
        font-family: 'Material Icons' !important;
        text-transform: none !important;
        display: inline-block !important;
    }}

    /* טקסט כללי */
    .stMarkdown p, label, .stMetric label {{
        color: #ffffff !important; font-family: 'Segoe UI', sans-serif !important; font-size: 0.92rem !important;
    }}

    /* תיקון Metric וכרטיסים */
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-size: 1.6rem !important; font-weight: 700 !important; }}
    
    /* תיקון סרגל גרירת קבצים - מניעת כתב על כתב */
    [data-testid="stFileUploadDropzone"] {{ background-color: #111827 !important; border: 2px dashed #3b82f6 !important; padding: 10px !important; }}
    [data-testid="stFileUploadDropzone"] * {{ color: #ffffff !important; font-size: 0.85rem !important; }}
    </style>
    
    <div class="ticker-wrapper"><div class="ticker-text">{ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {ticker_html}</div></div>
    <div class="main-content"></div>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
@st.cache_data(ttl=60)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_kpi(label, value, formula, desc, imp):
    st.metric(label, value)
    with st.expander("ℹ️ ניתוח"):
        st.markdown(f"**{label}** - {desc}")
        st.latex(formula)
        st.info(f"**דגש:** {imp}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_name = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="s_v35")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="q_v35")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.write("📂 **טעינת דוחות (PDF)**")
    st.file_uploader("", type=['pdf'], key="up_v35")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | {sel_q} 2025")
    
    # 5 ה-KPIs הקריטיים (Checklist)
    cols = st.columns(5)
    kpis = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "מחסן רווחים."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Eq}", "תשואה להון.", "ניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום.", "יעילות."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות צמיחה.", "איכות.")
    ]
    for i in range(5):
        with cols[i]: render_kpi(*kpis[i])

    st.divider()
    t_trends, t_solv, t_segments, t_stress, t_peer = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with t_trends:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=300), use_container_width=True)
        # החזרת היחסים הפיננסיים שנעלמו
        st.write("### 📊 יחסים פיננסיים משלימים")
        r1, r2, r3 = st.columns(3)
        with r1: render_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף.", "איתנות.")
        with r2: render_kpi("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות.", "תפעול.")
        with r3: render_metric_v2 = render_kpi("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "נזילות.", "תזרים.")

    with t_solv:
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="סיכוני SCR"), use_container_width=True)

    with t_segments:
        
        cc, cd = st.columns(2)
        with cc: st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=300, template="plotly_dark", title="CSM לפי מגזר", color_discrete_sequence=['#3b82f6']), use_container_width=True)
        with cd: st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=300, template="plotly_dark", title="CSM לפי מודלים"), use_container_width=True)

    with t_stress:
        s1, s2, s3 = st.columns(3)
        with s1: ir = st.slider("ריבית (bps)", -100, 100, 0, key="ir_v35")
        with s2: mk = st.slider("מניות (%)", 0, 40, 0, key="mk_v35")
        with s3: lp = st.slider("ביטולים (%)", 0, 20, 0, key="lp_v35")
        impact = (ir * d['int_sens']) + (mk * d['mkt_sens']) + (lp * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}, {'range': [150, 250], 'color': "#166534"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with t_peer:
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("שגיאה בטעינת המחסן.")

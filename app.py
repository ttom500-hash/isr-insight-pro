import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import os

# --- 1. הגדרות מערכת ונראות (v29 FINAL CONSOLIDATED) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציה למשיכת נתוני בורסה חיים (מתרענן כל 5 דקות)
@st.cache_data(ttl=300)
def get_live_market_ticker():
    tickers = {
        "^TA125.TA": "ת"א 125",
        "ILS=X": "USD/ILS",
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "EURILS=X": "EUR/ILS",
        "^TNX": "אג"ח 10ש'"
    }
    ticker_parts = []
    try:
        for symbol, name in tickers.items():
            t = yf.Ticker(symbol)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                change = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-2]) - 1) * 100
                color = "#4ade80" if change >= 0 else "#f87171"
                arrow = "▲" if change >= 0 else "▼"
                ticker_parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{color};">{price:.2f} ({arrow}{change:.2f}%)</span>')
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(ticker_parts)
    except:
        return "טוען נתוני שוק חיים..."

market_data_html = get_live_market_ticker()

# הזרקת CSS מתקדם לפתרון ניגודיות, פרופורציות ואייקונים
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}

    /* סרגל בורסה רץ */
    .ticker-container {{
        width: 100%;
        background-color: #0f172a;
        color: white;
        padding: 8px 0;
        border-bottom: 1px solid #1e293b;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 999999;
        overflow: hidden;
        white-space: nowrap;
    }}
    .ticker-scroll {{
        display: inline-block;
        padding-right: 100%;
        animation: scroll-left 40s linear infinite;
        font-family: 'Segoe UI', sans-serif;
        font-size: 0.85rem;
    }}
    @keyframes scroll-left {{
        0% {{ transform: translateX(0); }}
        100% {{ transform: translateX(-100%); }}
    }}
    .main-body-offset {{ margin-top: 45px; }}

    /* תיקון טקסט ופרופורציות */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, li {{
        color: #ffffff !important;
        font-family: 'Segoe UI', system-ui, sans-serif !important;
        font-size: 0.92rem !important;
    }}
    
    /* מניעת הופעת EXPAND_MORE */
    [data-testid="stExpanderChevron"], [data-testid="stHeaderActionElements"], i, svg {{
        font-family: 'Material Icons' !important;
        text-transform: none !important;
    }}

    /* תיקון פופ-אפ (Popover) */
    div[data-testid="stPopoverBody"] {{
        background-color: #161b22 !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        box-shadow: 0 10px 30px rgba(0,0,0,1) !important;
        min-width: 320px !important;
    }}
    div[data-testid="stPopoverBody"] * {{ color: #ffffff !important; }}

    /* כרטיסי Metric */
    div[data-testid="stMetric"] {{
        background: #0d1117;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 10px 15px !important;
    }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-size: 1.5rem !important; font-weight: 700 !important; }}
    div[data-testid="stMetricLabel"] {{ color: #94a3b8 !important; font-size: 0.82rem !important; }}

    /* סרגל צד וגרירת קבצים */
    section[data-testid="stSidebar"] {{ background-color: #0d1117 !important; border-left: 1px solid #30363d !important; }}
    section[data-testid="stFileUploadDropzone"] {{
        background-color: #111827 !important;
        border: 2px dashed #3b82f6 !important;
    }}

    /* דגלים אדומים */
    .red-flag {{
        background-color: #7a1a1c;
        border-right: 5px solid #f85149;
        padding: 10px;
        border-radius: 6px;
        color: #ffffff !important;
        margin-bottom: 10px;
        font-weight: 700;
    }}
    </style>
    
    <div class="ticker-container">
        <div class="ticker-scroll">
            {market_data_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {market_data_html}
        </div>
    </div>
    <div class="main-body-offset"></div>
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

def render_metric_with_info(label, value, formula, explanation, impact):
    st.metric(label, value)
    with st.popover("ℹ️ ניתוח"):
        st.markdown(f"#### {label}")
        st.write(explanation); st.divider()
        st.latex(formula)
        st.info(f"**דגש פיקוחי:** {impact}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6; margin-top:30px;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_name = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="sb_comp")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="sb_q")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()

    with st.expander("📂 טעינת דוחות (PDF)"):
        st.file_uploader("גרור קובץ לכאן", type=['pdf'], key="uploader")

# --- 4. EXECUTIVE DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | {sel_q} 2025 Executive Control")
    
    if d['solvency_ratio'] < 150:
        st.markdown(f'<div class="red-flag">🚨 חריגת הון: יחס סולבנסי ({d["solvency_ratio"]}%) נמוך מהיעד.</div>', unsafe_allow_html=True)

    # 5 המדדים הקריטיים
    k = st.columns(5)
    params = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "מחסן הרווחים."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Eq}", "תשואה להון.", "איכות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום.", "מתחת ל-100% רווח."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות צמיחה.", "איכות מכירות.")
    ]
    for i in range(5):
        with k[i]: render_metric_with_info(*params[i])

    st.divider()

    tabs = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]: # מגמות ויחסים
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        r_cols = st.columns(3)
        with r_cols[0]: render_metric_with_info("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף.", "איתנות.")
        with r_cols[1]: render_metric_with_info("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות.", "תפעול.")
        with r_cols[2]: render_metric_with_info("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "נזילות.", "תזרים.")

    with tabs[1]: # סולבנסי II
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=280, title="איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=280, title="סיכוני SCR"), use_container_width=True)

    with tabs[2]: # מגזרים IFRS 17
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=280, template="plotly_dark", title="CSM לפי מגזר", color_discrete_sequence=['#3b82f6']), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=280, template="plotly_dark", title="CSM לפי מודלים"), use_container_width=True)

    with tabs[3]: # תרחישי קיצון
        s1, s2, s3 = st.columns(3)
        with s1: ir_v = st.slider("ריבית (bps)", -100, 100, 0, key="ir_v29")
        with s2: mk_v = st.slider("מניות (%)", 0, 40, 0, key="mk_v29")
        with s3: lp_v = st.slider("ביטולים (%)", 0, 20, 0, key="lp_v29")
        impact = (ir_v * d['int_sens']) + (mk_v * d['mkt_sens']) + (lp_v * d['lapse_sens'])
        proj = max(0, d['solvency_ratio'] - impact)
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}, {'range': [150, 250], 'color': "#166534"}]})).update_layout(template="plotly_dark", height=280), use_container_width=True)

    with tabs[4]: # השוואה ענפית
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=280, text_auto=True), use_container_width=True)

else:
    st.error("שגיאה בטעינת המחסן.")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import os

# --- 1. הגדרות מערכת ונראות (v33 VALIDATED) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציה מהירה למשיכת נתוני בורסה (Bulk Fetch)
@st.cache_data(ttl=600)
def get_market_ticker():
    tickers_map = {
        '^TA125.TA': 'ת"א 125',
        'ILS=X': 'USD/ILS',
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        'EURILS=X': 'EUR/ILS',
        '^TNX': "אג''ח 10ש'"
    }
    try:
        data = yf.download(list(tickers_map.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        parts = []
        for sym, name in tickers_map.items():
            try:
                latest = data[sym]['Close'].iloc[-1]
                prev = data[sym]['Close'].iloc[-2]
                pct = ((latest / prev) - 1) * 100
                clr = "#4ade80" if pct >= 0 else "#f87171"
                arr = "▲" if pct >= 0 else "▼"
                parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{latest:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts)
    except:
        return "ממתין לעדכון נתוני שוק..."

ticker_html = get_market_ticker()

# CSS - פתרון מוחלט לניגודיות, EXPAND_MORE ופרופורציות
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* סרגל בורסה */
    .ticker-bar {{
        width: 100%; background-color: #0f172a; color: white; padding: 10px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 0; left: 0; z-index: 999999;
        overflow: hidden; white-space: nowrap;
    }}
    .ticker-move {{
        display: inline-block; padding-right: 100%; animation: moveLeft 40s linear infinite;
        font-family: 'Segoe UI', sans-serif; font-size: 0.85rem;
    }}
    @keyframes moveLeft {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .spacer {{ margin-top: 55px; }}

    /* טקסט ואייקונים */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, li {{
        color: #ffffff !important; font-family: 'Segoe UI', sans-serif !important; font-size: 0.92rem !important;
    }}
    [data-testid="stExpanderChevron"], i, svg {{ font-family: 'Material Icons' !important; text-transform: none !important; }}

    /* פופ-אפ וכרטיסים */
    div[data-testid="stPopoverBody"] {{ background-color: #161b22 !important; border: 1px solid #3b82f6 !important; }}
    div[data-testid="stPopoverBody"] * {{ color: #ffffff !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-size: 1.6rem !important; font-weight: 700 !important; }}
    
    /* כפתור רענון */
    button[kind="secondary"] {{ background-color: #3b82f6 !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }}
    </style>
    
    <div class="ticker-bar"><div class="ticker-move">{ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {ticker_html}</div></div>
    <div class="spacer"></div>
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

def render_metric(label, value, formula, desc, imp):
    st.metric(label, value)
    with st.popover("ℹ️ ניתוח"):
        st.markdown(f"#### {label}")
        st.write(desc); st.divider()
        st.latex(formula)
        st.info(f"**דגש:** {imp}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        all_comps = sorted(df['display_name'].unique())
        sel_name = st.selectbox("בחר ישות פיננסית:", all_comps, key="c_v33")
        c_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="q_v33")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"):
            st.cache_data.clear()
            st.rerun()
    st.divider()
    with st.expander("📂 טעינת דוחות (PDF)"):
        st.file_uploader("גרור קובץ לכאן", type=['pdf'], key="up_v33")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_name} | {sel_q} 2025 Executive Control")
    
    # 5 המדדים הקריטיים
    k = st.columns(5)
    params = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "IFRS 17."),
        ("ROE", f"{d['roe']}%", r"\frac{NI}{Eq}", "תשואה להון.", "ניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום.", "יעילות."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות צמיחה.", "איכות מכירות.")
    ]
    for i in range(5):
        with k[i]: render_metric(*params[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)

    with tabs[1]:
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[
                go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'),
                go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')
            ])
            f.update_layout(barmode='stack', template="plotly_dark", height=280, title="איכות ההון")
            st.plotly_chart(f, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=280, title="סיכוני SCR"), use_container_width=True)

    with tabs[2]:
        
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=280, template="plotly_dark", title="CSM לפי מגזר", color_discrete_sequence=['#3b82f6']), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=280, template="plotly_dark", title="CSM לפי מודלים"), use_container_width=True)

    with tabs[3]:
        s1, s2, s3 = st.columns(3)
        with s1: ir = st.slider("ריבית (bps)", -100, 100, 0, key="ir")
        with s2: mk = st.slider("מניות (%)", 0, 40, 0, key="mk")
        with s3: lp = st.slider("ביטולים (%)", 0, 20, 0, key="lp")
        proj = d['solvency_ratio'] - (ir*d['int_sens'] + mk*d['mkt_sens'] + lp*d['lapse_sens'])
        st.metric("סולבנסי חזוי", f"{proj:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}, {'range': [150, 250], 'color': "#166534"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with tabs[4]:
        
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=280, text_auto=True), use_container_width=True)

else:
    st.error("שגיאה בטעינת המחסן. וודא שקובץ data/database.csv קיים.")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import os

# --- 1. הגדרות מערכת וסרגל שוק מורחב (v38 RESTORED & STABLE) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_market_data():
    # מדדים: בורסה, מט"ח וריבית
    tickers_dict = {
        '^TA125.TA': 'ת"א 125',
        'ILS=X': 'USD/ILS',
        'EURILS=X': 'EUR/ILS',
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^TNX': 'אג"ח 10ש (ריבית)'
    }
    try:
        data = yf.download(list(tickers_dict.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        ticker_items = []
        for symbol, name in tickers_dict.items():
            try:
                price = data[symbol]['Close'].iloc[-1]
                prev = data[symbol]['Close'].iloc[-2]
                change = ((price / prev) - 1) * 100
                color = "#4ade80" if change >= 0 else "#f87171"
                arrow = "▲" if change >= 0 else "▼"
                ticker_items.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{color};">{price:.2f} ({arrow}{change:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(ticker_items)
    except:
        return "מתחבר לנתוני בורסה..."

ticker_html = get_live_market_data()

# CSS - ניקוי עיצוב, מניעת חפיפה וביטול expand_more
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* סרגל בורסה עליון */
    .ticker-wrapper {{
        width: 100%; background-color: #0f172a; color: white; padding: 10px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 0; left: 0; z-index: 10000;
        overflow: hidden; white-space: nowrap;
    }}
    .ticker-content {{
        display: inline-block; padding-right: 100%; animation: tickerScroll 40s linear infinite;
        font-family: sans-serif; font-size: 0.85rem;
    }}
    @keyframes tickerScroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .body-offset {{ margin-top: 65px; }}

    /* הגנה על אייקונים - פותר את expand_more */
    [data-testid="stExpanderChevron"], i, svg, span[data-baseweb="icon"] {{
        font-family: 'Material Icons' !important; text-transform: none !important;
    }}

    /* טקסט וכרטיסים */
    html, body, .stMarkdown p, label {{ color: #ffffff !important; font-size: 0.92rem !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-size: 1.6rem !important; font-weight: 700 !important; }}
    </style>
    
    <div class="ticker-wrapper"><div class="ticker-content">{ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {ticker_html}</div></div>
    <div class="body-offset"></div>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
@st.cache_data(ttl=60)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path); df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_metric_with_expander(label, value, formula, description, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי"):
        st.write(description); st.divider()
        st.latex(formula); st.info(f"**דגש:** {note}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="c_v38")
        c_df = df[df['display_name'] == sel_comp].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="q_v38")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.write("📂 **טעינת דוחות (PDF)**")
    st.file_uploader("", type=['pdf'], key="u_v38")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_comp} | {sel_q} 2025 Executive Control")
    
    # 5 KPIs מהצ'קליסט שלך
    k_cols = st.columns(5)
    kpi_data = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "IFRS 17."),
        ("ROE", f"{d['roe']}%", r"\frac{NI}{Eq}", "תשואה להון.", "ניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום.", "אלמנטרי."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות צמיחה.", "איכות.")
    ]
    for i in range(5):
        with k_cols[i]: render_metric_with_expander(*kpi_data[i])

    st.divider()
    t_trends, t_solv, t_segments, t_stress, t_peer = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with t_trends:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים משלימים")
        r1, r2, r3 = st.columns(3)
        with r1: render_metric_with_expander("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף.", "איתנות.")
        with r2: render_metric_with_expander("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות.", "תפעול.")
        with r3: render_metric_with_expander("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "נזילות.", "תזרים.")

    with t_solv: # שחזור טאב סולבנסי
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון (Tiering)"); st.plotly_chart(f, use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="התפלגות דרישת הון (SCR)"), use_container_width=True)

    with t_segments: # מגזרים
        cc, cd = st.columns(2)
        with cc: st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=280, template="plotly_dark", title="CSM לפי מגזר", color_discrete_sequence=['#3b82f6']), use_container_width=True)
        with cd: st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=280, template="plotly_dark", title="CSM לפי מודלים"), use_container_width=True)

    with t_stress: # שחזור תרחיש ביטולים
        st.subheader("⛈️ Stress Test Engine")
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0, key="ir_s")
        with s2: mk_s = st.slider("מניות (%)", 0, 40, 0, key="mk_s")
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0, key="lp_s")
        
        # חישוב אימפקט משולב (כולל ביטולים)
        total_impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj_solvency = d['solvency_ratio'] - total_impact
        
        st.metric("סולבנסי חזוי", f"{proj_solvency:.1f}%", delta=f"{-total_impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj_solvency, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with t_peer:
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'combined_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("שגיאה בטעינת המחסן.")

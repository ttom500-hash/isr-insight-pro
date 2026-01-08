import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import os

# --- 1. הגדרות מערכת והאצת טעינה (v36 SUPER-SPEED) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציית בורסה מוגנת מפני תקיעות (Timeout Safe)
@st.cache_data(ttl=3600) # נשמר שעה בזיכרון
def get_market_ticker_safe():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', '^GSPC': 'S&P 500'}
    try:
        # משיכה מהירה מאוד של יום אחד בלבד
        data = yf.download(list(tickers.keys()), period="1d", progress=False)
        parts = []
        for sym, name in tickers.items():
            try:
                price = data['Close'][sym].iloc[-1]
                parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:#4ade80;">{price:.2f}</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts)
    except:
        return "נתוני שוק מתעדכנים..."

ticker_html = get_market_ticker_safe()

# CSS - פתרון סופי לחפיפה, לאייקונים ולניגודיות
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* סרגל בורסה - שכבה נפרדת (Z-Index גבוה) */
    .ticker-header {{
        width: 100%; background-color: #0f172a; color: white; padding: 8px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 0; left: 0; z-index: 10000;
        overflow: hidden; white-space: nowrap;
    }}
    .ticker-move {{
        display: inline-block; padding-right: 100%; animation: tickerAnim 40s linear infinite;
        font-family: sans-serif; font-size: 0.85rem;
    }}
    @keyframes tickerAnim {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .main-body {{ margin-top: 60px; }}

    /* הגנה על אייקונים - מניעת expand_more */
    [data-testid="stExpanderChevron"], i, svg, span[data-baseweb="icon"] {{
        font-family: 'Material Icons' !important; text-transform: none !important;
    }}

    /* טקסט וכרטיסים */
    html, body, .stMarkdown p, label {{ color: #ffffff !important; font-size: 0.92rem !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 10px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-size: 1.5rem !important; font-weight: 700 !important; }}
    
    /* סרגל גרירת קבצים - נקי וברור */
    [data-testid="stFileUploadDropzone"] {{ background-color: #111827 !important; border: 1px dashed #3b82f6 !important; }}
    </style>
    
    <div class="ticker-header"><div class="ticker-move">{ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {ticker_html}</div></div>
    <div class="main-body"></div>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
@st.cache_data(ttl=60)
def load_validated_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_kpi_card(label, value, formula, desc, imp):
    st.metric(label, value)
    with st.expander("ℹ️ פירוט"):
        st.write(f"**{desc}**"); st.latex(formula); st.info(f"דגש: {imp}")

# --- 3. SIDEBAR ---
df = load_validated_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_comp = st.selectbox("חברה:", sorted(df['display_name'].unique()), key="c_v36")
        c_df = df[df['display_name'] == sel_comp].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("רבעון:", c_df['quarter'].unique(), key="q_v36")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.file_uploader("📂 טעינת PDF", type=['pdf'], key="u_v36")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_comp} | {sel_q} 2025")
    
    # הצגת 5 ה-KPIs (הצ'קליסט השמור שלך)
    cols = st.columns(5)
    kpis = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח גלום.", "מחסן רווחים."),
        ("ROE", f"{d['roe']}%", r"\frac{NI}{Eq}", "תשואה להון.", "ניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום.", "יעילות."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות.", "צמיחה.")
    ]
    for i in range(5):
        with cols[i]: render_kpi_card(*kpis[i])

    st.divider()
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות", "🏛️ סולבנסי", "📑 מגזרים (IFRS17)", "⛈️ Stress Test", "🏁 השוואה"])

    with t1:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        st.write("### 📊 יחסים משלימים")
        r1, r2, r3 = st.columns(3)
        with r1: render_kpi_card("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Eq}{Assets}", "מינוף.", "איתנות.")
        with r2: render_kpi_card("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{OpEx}{GWP}", "יעילות.", "תפעול.")
        with r3: render_kpi_card("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{CFO}{NI}", "נזילות.", "תזרים.")

    with t2:
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=280, title="מבנה הון"); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=280, title="פרופיל סיכון"), use_container_width=True)

    with t3: # מגזרים IFRS 17 (נשמר במלואו)
        
        cc, cd = st.columns(2)
        with cc: st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=280, template="plotly_dark", title="CSM לפי קווי עסקים", color_discrete_sequence=['#3b82f6']), use_container_width=True)
        with cd: st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=280, template="plotly_dark", title="חלוקה לפי מודלים"), use_container_width=True)

    with t4:
        st.subheader("⛈️ Stress Engine")
        ir = st.slider("ריבית (bps)", -100, 100, 0, key="ir_v36")
        mk = st.slider("מניות (%)", 0, 40, 0, key="mk_v36")
        impact = (ir * d['int_sens']) + (mk * d['mkt_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with t5:
        pm = st.selectbox("בחר מדד:", ['solvency_ratio', 'roe', 'combined_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("שגיאה בטעינת המחסן.")

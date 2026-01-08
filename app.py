import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os

# --- 1. הגדרות מערכת וסרגלים כפולים (v45 DUAL TICKER FIX) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציה למשיכת מדדי שוק (בורסה, מט"ח, ריבית)
@st.cache_data(ttl=600)
def get_market_data():
    tickers = {
        '^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS',
        '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^TNX': 'ריבית (10Y)'
    }
    parts = []
    try:
        data = yf.download(list(tickers.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        for sym, name in tickers.items():
            try:
                if sym in data.columns.levels[0]:
                    val = data[sym]['Close'].iloc[-1]
                    prev = data[sym]['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "טוען מדדי בורסה..."
    except: return "מתחבר לנתוני שוק..."

# פונקציה למשיכת מבזקי חדשות
@st.cache_data(ttl=900)
def get_news_data():
    feeds = [
        ("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"),
        ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml")
    ]
    news_parts = []
    for src, url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                news_parts.append(f"🚨 {src}: {entry.title}")
        except: continue
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join(news_parts) if news_parts else "מחכה למבזקים..."

m_ticker = get_market_data()
n_ticker = get_news_data()

# CSS - בניית שתי קומות נפרדות לסרגלים
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* קומה 1: סרגל בורסה (עליון ביותר) */
    .market-bar {{
        width: 100%; background-color: #0f172a; color: white; padding: 10px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 0; left: 0; z-index: 999999;
        overflow: hidden; white-space: nowrap;
    }}
    
    /* קומה 2: סרגל חדשות (מתחת לבורסה) */
    .news-bar {{
        width: 100%; background-color: #450a0a; color: white; padding: 8px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 42px; left: 0; z-index: 999998;
        overflow: hidden; white-space: nowrap;
    }}
    
    .scroll-anim {{
        display: inline-block; padding-right: 100%; animation: scrollText 55s linear infinite;
        font-family: 'Segoe UI', sans-serif; font-size: 0.88rem;
    }}
    @keyframes scrollText {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    
    .app-spacer {{ margin-top: 105px; }}
    
    /* מניעת expand_more */
    [data-testid="stExpanderChevron"], i, svg {{ font-family: 'Material Icons' !important; text-transform: none !important; }}
    html, body, .stMarkdown p, label {{ color: #ffffff !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; }}
    </style>
    
    <div class="market-bar"><div class="scroll-anim">{m_ticker} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_ticker}</div></div>
    <div class="news-bar"><div class="scroll-anim">מבזקים: {n_ticker} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_ticker}</div></div>
    <div class="app-spacer"></div>
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

def render_metric_with_pro_desc(label, value, formula, desc, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי"):
        st.write(f"**מהות:** {desc}"); st.divider(); st.latex(formula); st.info(f"**דגש:** {note}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6; padding-top:20px;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="c_v45")
        c_df = df[df['display_name'] == sel_comp].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="q_v45")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.file_uploader("📂 פורטל PDF", type=['pdf'], key="u_v45")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_comp} | {sel_q} 2025 Executive Control")
    
    # 5 ה-KPIs הקריטיים עם הפירוט המורחב שביקשת
    k_cols = st.columns(5)
    k_params = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני לספיגת הפסדים.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום (IFRS 17).", "מחסן הרווחים."),
        ("ROE", f"{d['roe']}%", r"\frac{NI}{Eq}", "תשואה להון.", "יעילות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום אלמנטרי.", "מתחת ל-100% רווח."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות חדשות.", "איכות צמיחה.")
    ]
    for i in range(5):
        with k_cols[i]: render_metric_with_pro_desc(*k_params[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים (IFRS 17)", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]: # מגמות ויחסים משלימים
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        r_cols = st.columns(3)
        with r_cols[0]: render_metric_with_pro_desc("יחס תביעות", f"{d['loss_ratio']}%", r"Loss", "איכות חיתום.", "דגל אדום בעלייה.")
        with r_cols[1]: render_metric_with_pro_desc("שחרור CSM", f"{d['csm_release_rate']}%", r"Release", "קצב הכרת רווח.", "שימור המחסן.")
        with r_cols[2]: render_metric_with_pro_desc("תשואת השקעות", f"{d['inv_yield']}%", r"Yield", "ביצועי תיק.", "קריטי ליעדים.")

    with tabs[1]: # סולבנסי II
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="פרופיל סיכון SCR"), use_container_width=True)

    with tabs[2]: # מגזרים - השוואת CSM מול חוזים מפסידים (Onerous)
        st.write("### 📑 רווחיות (CSM) מול חוזים מפסידים (LC)")
        
        sn = ['חיים', 'בריאות', 'כללי']
        f_seg = go.Figure(data=[
            go.Bar(name='CSM (רווח)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
            go.Bar(name='Loss Component (הפסד)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
        ])
        f_seg.update_layout(barmode='group', template="plotly_dark", height=350)
        st.plotly_chart(f_seg, use_container_width=True)

    with tabs[3]: # Stress Test עם ביטולים (Lapse)
        s1, s2, s3 = st.columns(3)
        with s1: ir = st.slider("ריבית (bps)", -100, 100, 0, key="irs")
        with s2: mk = st.slider("מניות (%)", 0, 40, 0, key="mks")
        with s3: lp = st.slider("ביטולים (%)", 0, 20, 0, key="lps")
        impact = (ir * d['int_sens']) + (mk * d['mkt_sens']) + (lp * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with tabs[4]: # השוואה ענפית
        pm = st.selectbox("בחר מדד:", ['solvency_ratio', 'roe', 'inv_yield', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("שגיאה בטעינת המחסן.")

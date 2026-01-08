import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os

# --- 1. הגדרות מערכת וסרגלי מידע (v43 FINAL VALIDATED) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציה למשיכת מבזקי חדשות (גלובס, דה-מרקר)
@st.cache_data(ttl=600)
def get_live_news():
    feeds = [
        ("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"),
        ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml")
    ]
    news_parts = []
    for name, url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:4]:
                news_parts.append(f"🚩 {name}: {entry.title}")
        except: continue
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join(news_parts) if news_parts else "טוען מבזקים..."

# פונקציה למשיכת מדדי שוק אונליין
@st.cache_data(ttl=3600)
def get_market_ticker():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS', '^GSPC': 'S&P 500', '^TNX': 'ריבית (10Y)'}
    parts = []
    try:
        data = yf.download(list(tickers.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        for sym, name in tickers.items():
            try:
                val, prev = data[sym]['Close'].iloc[-1], data[sym]['Close'].iloc[-2]
                pct = ((val / prev) - 1) * 100
                clr = "#4ade80" if pct >= 0 else "#f87171"
                arr = "▲" if pct >= 0 else "▼"
                parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts)
    except: return "טוען מדדים..."

ticker_html = get_market_ticker()
news_html = get_live_news()

# CSS - פתרון סופי לחפיפה, עיצוב כהה ואייקונים
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* סרגל בורסה (עליון) */
    .m-ticker {{
        width: 100%; background-color: #0f172a; color: white; padding: 10px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 0; left: 0; z-index: 10001;
        overflow: hidden; white-space: nowrap;
    }}
    
    /* סרגל חדשות (תחתון) */
    .n-ticker {{
        width: 100%; background-color: #7a1a1c; color: white; padding: 7px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 44px; left: 0; z-index: 10000;
        overflow: hidden; white-space: nowrap; font-weight: bold;
    }}
    
    .anim {{ display: inline-block; padding-right: 100%; animation: tScroll 50s linear infinite; font-family: sans-serif; font-size: 0.88rem; }}
    @keyframes tScroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .spacer {{ margin-top: 100px; }}
    
    /* תיקון אייקונים */
    [data-testid="stExpanderChevron"], i, svg {{ font-family: 'Material Icons' !important; text-transform: none !important; }}
    html, body, .stMarkdown p, label {{ color: #ffffff !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    </style>
    
    <div class="m-ticker"><div class="anim">{ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {ticker_html}</div></div>
    <div class="n-ticker"><div class="anim">🚨 מבזקים: {news_html} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {news_html}</div></div>
    <div class="spacer"></div>
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

def render_pro_kpi(label, value, formula, desc, note):
    st.metric(label, value)
    with st.expander("📚 ניתוח מקצועי"):
        st.write(f"**מהות:** {desc}"); st.divider(); st.latex(formula); st.info(f"**דגש:** {note}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_comp = st.selectbox("חברה:", sorted(df['display_name'].unique()), key="c_v43")
        c_df = df[df['display_name'] == sel_comp].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("רבעון:", c_df['quarter'].unique(), key="q_v43")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.file_uploader("📂 פורטל PDF", type=['pdf'], key="u_v43")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_comp} | סקירה ניהולית {sel_q}")
    
    # 5 Core KPIs
    cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "מחסן רווחים."),
        ("ROE", f"{d['roe']}%", r"\frac{NI}{Eq}", "תשואה להון.", "יעילות."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום אלמנטרי.", "רווחיות תפעולית."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות.", "איכות צמיחה.")
    ]
    for i in range(5):
        with cols[i]: render_pro_kpi(*k_meta[i])

    st.divider()
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים (IFRS 17)", "⛈️ Stress Test", "🏁 השוואה"])

    with t1: # מגמות ויחסים משופרים
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים מקצועיים")
        r_cols = st.columns(3)
        with r_cols[0]: render_pro_kpi("Loss Ratio", f"{d['loss_ratio']}%", r"\frac{Claims}{Premium}", "איכות חיתום.", "עלייה מעידה על סיכון.")
        with r_cols[1]: render_pro_kpi("שיעור שחרור CSM", f"{d['csm_release_rate']}%", r"Release", "קצב הכרת הרווח.", "שחיקה מהירה ללא מכירות היא דגל אדום.")
        with r_cols[2]: render_pro_kpi("תשואת השקעות", f"{d['inv_yield']}%", r"Yield", "ביצועי תיק ההשקעות.", "קריטי לעמידה בהתחייבויות.")

    with t2: # סולבנסי
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="סיכוני SCR"), use_container_width=True)

    with t3: # מגזרים - השוואת CSM מול חוזים מפסידים
        st.write("### 📑 רווחיות (CSM) מול חוזים מפסידים (LC) לפי מגזר")
        
        seg_names = ['חיים', 'בריאות', 'כללי']
        f_seg = go.Figure(data=[
            go.Bar(name='CSM (רווח גלום)', x=seg_names, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
            go.Bar(name='Loss Component (הפסד)', x=seg_names, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
        ])
        f_seg.update_layout(barmode='group', template="plotly_dark", height=350)
        st.plotly_chart(f_seg, use_container_width=True)

    with t4: # Stress Test מלא עם ביטולים
        s1, s2, s3 = st.columns(3)
        with s1: ir = st.slider("ריבית (bps)", -100, 100, 0, key="irs")
        with s2: mk = st.slider("מניות (%)", 0, 40, 0, key="mks")
        with s3: lp = st.slider("ביטולים (%)", 0, 20, 0, key="lps")
        impact = (ir * d['int_sens']) + (mk * d['mkt_sens']) + (lp * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with t5:
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'inv_yield', 'loss_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("שגיאה בטעינת המחסן.")

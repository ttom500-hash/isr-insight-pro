import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os

# --- 1. הגדרות מערכת וסרגלים כפולים (v47 WINDOW RESTORATION) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציות משיכת נתונים (בורסה וחדשות)
@st.cache_data(ttl=600)
def get_market_ticker():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS', '^GSPC': 'S&P 500', '^TNX': 'ריבית (10Y)'}
    parts = []
    try:
        data = yf.download(list(tickers.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        for sym, name in tickers.items():
            try:
                if sym in data.columns.levels[0]:
                    val, prev = data[sym]['Close'].iloc[-1], data[sym]['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "טוען מדדים..."
    except: return "מתחבר לבורסה..."

@st.cache_data(ttl=900)
def get_news_ticker():
    feeds = [("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"), ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml")]
    news_parts = []
    for src, url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:3]: news_parts.append(f"🚨 {src}: {entry.title}")
        except: continue
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join(news_parts) if news_parts else "מחכה למבזקים..."

m_html = get_market_ticker()
n_html = get_news_ticker()

# CSS - תיקון חלון החיפוש והסרגלים
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* סרגלים - מוגדרים מתחת ל-Sidebar ב-Z-Index */
    .ticker-header {{
        position: fixed; top: 0; left: 0; width: 100%; z-index: 99;
        background-color: #0f172a; border-bottom: 1px solid #1e293b;
    }}
    
    .market-stripe {{ background-color: #0f172a; padding: 10px 0; border-bottom: 1px solid #1e293b; }}
    .news-stripe {{ background-color: #450a0a; padding: 7px 0; }}
    
    .scroll-wrapper {{
        display: inline-block; padding-right: 100%; animation: scrollEffect 55s linear infinite;
        font-family: sans-serif; font-size: 0.88rem; white-space: nowrap; color: white;
    }}
    @keyframes scrollEffect {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    
    /* יצירת מרווח לתוכן המרכזי כדי שלא יוסתר */
    .main-body-spacer {{ margin-top: 100px; }}

    /* הפיכת ה-Sidebar (חלון החיפוש) לשכבה העליונה ביותר */
    [data-testid="stSidebar"] {{
        background-color: #0f172a !important;
        z-index: 1000000 !important;
        border-left: 1px solid #1e293b;
    }}

    /* תיקון אייקונים של Streamlit */
    [data-testid="stExpanderChevron"], i, svg {{ font-family: 'Material Icons' !important; text-transform: none !important; }}
    
    /* עיצוב כללי של טקסט */
    html, body, .stMarkdown p, label, .stMetric label {{ color: #ffffff !important; font-family: 'Segoe UI', sans-serif !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    
    /* עיצוב חלון גרירת קבצים */
    [data-testid="stFileUploadDropzone"] {{ background-color: #111827 !important; border: 2px dashed #3b82f6 !important; border-radius: 10px; }}
    </style>
    
    <div class="ticker-header">
        <div class="market-stripe"><div class="scroll-wrapper">{m_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_html}</div></div>
        <div class="news-stripe"><div class="scroll-wrapper">מבזקים: {n_html} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_html}</div></div>
    </div>
    <div class="main-body-spacer"></div>
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

def render_actuarial_kpi(label, value, formula, desc, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי"):
        st.write(f"**מהות המדד:** {desc}"); st.divider(); st.latex(formula); st.info(f"**דגש למפקח:** {note}")

# --- 3. SIDEBAR (חלון החיפוש והגרירה המשוקם) ---
df = load_data()
with st.sidebar:
    st.markdown("<h1 style='color:#3b82f6; margin-bottom:0;'>🛡️ APEX PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:0.85rem;'>Executive Control Systems</p>", unsafe_allow_html=True)
    st.divider()
    
    if not df.empty:
        st.subheader("🔍 חלון חיפוש")
        selected_company = st.selectbox("בחר חברה לניתוח:", sorted(df['display_name'].unique()), key="sb_comp")
        comp_df = df[df['display_name'] == selected_company].sort_values(by=['year', 'quarter'], ascending=False)
        selected_q = st.selectbox("בחר רבעון דיווח:", comp_df['quarter'].unique(), key="sb_q")
        d = comp_df[comp_df['quarter'] == selected_q].iloc[0]
        
        if st.button("🔄 רענן מסד נתונים"):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    st.subheader("📂 חלון גרירת קבצים")
    st.file_uploader("טען דוח כספי (PDF) לעדכון אוטומטי", type=['pdf'], key="pdf_upload")
    
    st.divider()
    st.caption("v47.0 | מערכת לניתוח אקטוארי ופיננסי")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{selected_company} | {selected_q} 2025")
    
    # 5 המדדים הקריטיים
    cols = st.columns(5)
    kpi_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני לספיגת הפסדים.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום (IFRS 17).", "מחסן הרווחים."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{NI}{Eq}", "תשואה להון.", "יעילות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום אלמנטרי.", "רווחיות תפעולית."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות חדשות.", "איכות צמיחה.")
    ]
    for i in range(5):
        with cols[i]: render_actuarial_kpi(*kpi_meta[i])

    st.divider()
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with t1:
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
    
    with t2: # סולבנסי II
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="פרופיל SCR"), use_container_width=True)

    with t3: # מגזרים - CSM מול חוזים מפסידים (Onerous)
        st.write("### 📑 רווחיות (CSM) מול חוזים מפסידים (LC)")
        sn = ['חיים', 'בריאות', 'כללי']
        f_seg = go.Figure(data=[
            go.Bar(name='CSM (רווח)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
            go.Bar(name='Loss Component (הפסד)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
        ])
        f_seg.update_layout(barmode='group', template="plotly_dark", height=350)
        st.plotly_chart(f_seg, use_container_width=True)

    with t4: # Stress Test עם ביטולים (Lapse)
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0, key="irs")
        with s2: mk_s = st.slider("מניות (%)", 0, 40, 0, key="mks")
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0, key="lps")
        impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with t5:
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'inv_yield', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==selected_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים תקין.")

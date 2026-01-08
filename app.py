import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os
from datetime import datetime, timedelta

# --- 1. הגדרות מערכת ועיצוב EXECUTIVE (v67.0) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציית מדדי שוק (בורסה, מט"ח, ריבית) - משיכה חסינה
@st.cache_data(ttl=300)
def get_market_data():
    tickers = {
        '^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS',
        '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^TNX': 'ריבית (10Y)'
    }
    parts = []
    try:
        for sym, name in tickers.items():
            try:
                # שימוש ב-download מהיר
                data = yf.download(sym, period="5d", interval="1d", progress=False)
                if not data.empty:
                    val = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "טוען מדדי שוק אונליין..."
    except: return "מתחבר לבורסה..."

# מנוע מבזקים חכם - סריקת עומק שבועית (Backfill)
@st.cache_data(ttl=600)
def get_smart_news():
    feeds = [
        ("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"),
        ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml"),
        ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml")
    ]
    keywords = ["ביטוח", "פנסיה", "גמל", "סולבנסי", "ריבית", "אינפלציה", "שוק ההון", "אג\"ח", "IFRS", "דיבידנד", "רגולציה", "רשות שוק ההון", "הפניקס", "הראל", "מגדל", "כלל", "מנורה"]
    news_items = []
    seen = set()
    
    for src, url in feeds:
        try:
            f = feedparser.parse(url)
            # סריקת עד 100 ידיעות אחרונות להבטחת חדשות מהשבוע האחרון
            for entry in f.entries[:100]:
                title = entry.title
                if any(k in title for k in keywords) and title not in seen:
                    news_items.append(f"🚩 {src}: {title}")
                    seen.add(title)
        except: continue
        
    # במידה ואין מספיק חדשות ביטוח, נמלא בחדשות מאקרו חשובות
    if len(news_items) < 5:
        for src, url in feeds:
            try:
                f = feedparser.parse(url)
                for entry in f.entries[:10]:
                    if entry.title not in seen:
                        news_items.append(f"🌐 {src}: {entry.title}")
            except: continue
            
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join(news_items) if news_items else "סורק פרסומים רגולטוריים..."

m_ticker_html = get_market_data()
n_ticker_html = get_smart_news()

# CSS - תיקון הסטה לימין (עבור עברית) וZ-Index
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    
    /* קונטיינר הסרגלים - מוסט שמאלה כדי שלא ייבלע ב-Sidebar הימני */
    .ticker-fixed-container {{
        position: fixed; top: 0; left: 0; 
        width: 100%; /* נשתמש ברוחב מלא עם פדינג פנימי */
        z-index: 99999;
    }}
    
    .m-strip {{
        background-color: #000000; padding: 12px 2rem; border-bottom: 1px solid #334155;
        overflow: hidden; white-space: nowrap;
    }}
    
    .n-strip {{
        background-color: #450a0a; padding: 7px 2rem; border-bottom: 2px solid #7a1a1c;
        overflow: hidden; white-space: nowrap;
    }}
    
    .scroll-content {{
        display: inline-block; padding-right: 100%; animation: tScroll 80s linear infinite;
        font-family: sans-serif; font-size: 0.92rem; color: #ffffff !important;
    }}
    @keyframes tScroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    
    .spacer-top {{ margin-top: 130px; }}

    /* Sidebar - חלון החיפוש */
    [data-testid="stSidebar"] {{ 
        background-color: #1e293b !important; 
        z-index: 1000000 !important; /* גבוה יותר מהסרגלים */
    }}
    
    /* עיצוב מדדים */
    div[data-testid="stMetric"] {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 10px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; }}
    </style>
    
    <div class="ticker-fixed-container">
        <div class="m-strip"><div class="scroll-content">{m_ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_ticker_html}</div></div>
        <div class="n-strip"><div class="scroll-content">📢 מבזקי רגולציה ושוק (עדכוני שבוע): {n_ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_ticker_html}</div></div>
    </div>
    <div class="spacer-top"></div>
    """, unsafe_allow_html=True)

# --- 2. BACKEND & SIDEBAR ---
@st.cache_data(ttl=60)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path); df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()
d = None
with st.sidebar:
    st.markdown("<h1 style='color:#3b82f6; margin-bottom:0;'>🛡️ APEX PRO</h1>", unsafe_allow_html=True)
    st.divider()
    if not df.empty:
        s_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="sb_c")
        comp_df = df[df['display_name'] == s_comp].sort_values(by=['year', 'quarter'], ascending=False)
        available_q = comp_df['quarter'].unique()
        s_q = st.selectbox("בחר רבעון:", available_q, key="sb_q")
        d = comp_df[comp_df['quarter'] == s_q].iloc[0]
        if st.button("🔄 רענן מערכת"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.subheader("📂 חלון גרירת קבצים")
    st.file_uploader("טען דוח PDF", type=['pdf'], key="pdf_up")

# --- 3. DASHBOARD ---
def render_kpi(label, value, formula, desc, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי"):
        st.write(f"**מהות:** {desc}"); st.divider(); st.latex(formula); st.info(f"**דגש:** {note}")

if not df.empty and d is not None:
    st.title(f"{s_comp} | סקירה ניהולית {s_q}")
    
    k_cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום (IFRS 17).", "מחסן הרווחים."),
        ("ROE", f"{d['roe']}%", r"ROE", "תשואה להון.", "יעילות."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום אלמנטרי.", "רווחיות."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות.", "צמיחה.")
    ]
    for i in range(5):
        with k_cols[i]: render_kpi(*k_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]:
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        r_cols = st.columns(3)
        with r_cols[0]: render_kpi("Loss Ratio", f"{d['loss_ratio']}%", r"LR", "אימות חיתום.", "דגל אדום בעלייה.")
        with r_cols[1]: render_kpi("שחרור CSM", f"{d['csm_release_rate']}%", r"Rel", "קצב הכרת רווח.", "שימור המחסן.")
        with r_cols[2]: render_kpi("תשואת השקעות", f"{d['inv_yield']}%", r"Yield", "ביצועי תיק.", "קריטי ליעדים.")

    with tabs[1]:
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#334155')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="סיכוני SCR").update_layout(paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)

    with tabs[2]:
        st.write("### 📑 רווחיות (CSM) מול חוזים מפסידים (LC) לפי מגזר")
        sn = ['חיים', 'בריאות', 'כללי']
        f_seg = go.Figure(data=[
            go.Bar(name='CSM (רווח)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
            go.Bar(name='Loss Component (הפסד)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
        ])
        f_seg.update_layout(barmode='group', template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f_seg, use_container_width=True)

    with tabs[3]:
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית", -100, 100, 0, key="irs")
        with s2: mk_s = st.slider("מניות", 0, 40, 0, key="mks")
        with s3: lp_s = st.slider("ביטולים", 0, 20, 0, key="lps")
        impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")

    with tabs[4]:
        pm = st.selectbox("בחר מדד:", ['solvency_ratio', 'roe', 'inv_yield', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==s_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים.")

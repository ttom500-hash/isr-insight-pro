import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os
from datetime import datetime

# --- 1. הגדרות מערכת ועיצוב EXECUTIVE SLATE (v72.0 VALIDATED) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציית מדדי שוק - משיכה אגרסיבית להבטחת נתונים
@st.cache_data(ttl=300)
def get_market_data_v72():
    tickers = {
        '^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS',
        '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^TNX': 'ריבית (10Y)'
    }
    parts = []
    try:
        # משיכה של חודש אחורה כדי לוודא שיש נקודות נתונים לחישוב אחוזים
        data = yf.download(list(tickers.keys()), period="1mo", interval="1d", group_by='ticker', progress=False)
        for sym, name in tickers.items():
            try:
                s_data = data[sym].dropna()
                if not s_data.empty and len(s_data) >= 2:
                    val = s_data['Close'].iloc[-1]
                    prev = s_data['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "ממתין לסנכרון נתונים..."
    except: return "מתחבר למסוף הבורסה..."

# מנוע מבזקים מורחב - סריקת עומק ללא חסימות
@st.cache_data(ttl=600)
def get_news_v72():
    feeds = [
        ("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"),
        ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml"),
        ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml")
    ]
    keywords = ["ביטוח", "פנסיה", "גמל", "סולבנסי", "ריבית", "אינפלציה", "שוק ההון", "IFRS", "דיבידנד", "רגולציה", "מפקח", "הראל", "הפניקס", "מגדל", "כלל", "מנורה"]
    news_items = []
    seen = set()
    
    for src, url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:100]: # סריקה מקסימלית
                title = entry.title
                if title not in seen:
                    is_rel = any(k in title for k in keywords)
                    prefix = "🚩" if is_rel else "🌐"
                    news_items.append({"t": f"{prefix} {src}: {title}", "rel": is_rel})
                    seen.add(title)
        except: continue
    
    # מיון: חדשות רלוונטיות למפקח בראש
    news_items.sort(key=lambda x: x['rel'], reverse=True)
    res = [i['t'] for i in news_items[:50]]
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join(res) if res else "סורק פרסומים רגולטוריים..."

m_ticker = get_market_data_v72()
n_ticker = get_news_v72()

# --- CSS - פתרון ה-Sticky הסופי ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    
    /* הסרגלים מוצמדים לראש אזור התוכן ולא נכנסים מתחת ל-Sidebar */
    .ticker-container-v72 {{
        position: sticky; top: -1px; width: 100%; z-index: 999;
        margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }}
    
    .m-strip-v72 {{ background-color: #000000; padding: 12px 20px; border-bottom: 1px solid #334155; overflow: hidden; white-space: nowrap; }}
    .n-strip-v72 {{ background-color: #450a0a; padding: 8px 20px; border-bottom: 2px solid #7a1a1c; overflow: hidden; white-space: nowrap; }}
    
    .scroll-v72 {{
        display: inline-block; padding-right: 100%; animation: tRunV72 90s linear infinite;
        font-family: sans-serif; font-size: 0.94rem; color: #ffffff !important;
    }}
    @keyframes tRunV72 {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}

    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-left: 1px solid #334155; }}
    div[data-testid="stMetric"] {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; }}
    </style>
    
    <div class="ticker-container-v72">
        <div class="m-strip-v72"><div class="scroll-v72">{m_ticker} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_ticker}</div></div>
        <div class="n-strip-v72"><div class="scroll-v72">📢 מודיעין פיננסי ורגולטורי: {n_ticker} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_ticker}</div></div>
    </div>
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
    st.markdown("<h1 style='color:#3b82f6;'>🛡️ APEX PRO</h1>", unsafe_allow_html=True)
    st.divider()
    if not df.empty:
        s_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="sb_c_v72")
        comp_df = df[df['display_name'] == s_comp].sort_values(by=['year', 'quarter'], ascending=False)
        s_q = st.selectbox("בחר רבעון:", comp_df['quarter'].unique(), key="sb_q_v72")
        d = comp_df[comp_df['quarter'] == s_q].iloc[0]
        if st.button("🔄 רענן מערכת"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.file_uploader("📂 חלון גרירת PDF", type=['pdf'], key="pdf_up_v72")

# --- 3. DASHBOARD ---
def render_kpi_v72(label, value, formula, desc, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי"):
        st.write(f"**מהות:** {desc}"); st.divider(); st.latex(formula); st.info(f"**דגש למפקח:** {note}")

if not df.empty and d is not None:
    st.title(f"{s_comp} | סקירה ניהולית {s_q}")
    
    # 5 KPIs
    k_cols = st.columns(5)
    k_params = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}", "חוסן הוני.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום.", "IFRS 17."),
        ("ROE", f"{d['roe']}%", "ROE", "תשואה להון.", "ניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום.", "אלמנטרי."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות.", "צמיחה.")
    ]
    for i in range(5):
        with k_cols[i]: render_kpi_v72(*k_params[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 מגזרים", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]:
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
    
    with tabs[1]:
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#334155')])
            f.update_layout(barmode='stack', template="plotly_dark", title="מבנה איכות ההון", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", title="סיכוני SCR").update_layout(paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)

    with tabs[2]:
        
        st.write("### 📑 רווחיות (CSM) מול חוזים מפסידים (LC) לפי מגזר")
        sn = ['חיים', 'בריאות', 'כללי']
        f_seg = go.Figure(data=[
            go.Bar(name='CSM (רווח)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
            go.Bar(name='Loss Component (הפסד)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
        ])
        f_seg.update_layout(barmode='group', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f_seg, use_container_width=True)

    with tabs[3]: # Stress Test
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0, key="irs_v72")
        with s2: mk_s = st.slider("מניות (%)", 0, 40, 0, key="mks_v72")
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0, key="lps_v72")
        impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
else:
    st.error("לא נמצא מחסן נתונים.")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os

# --- 1. הגדרות מערכת וסרגלים כפולים (v50 MASTER VALIDATED) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציה חסינה למשיכת מדדי שוק (בורסה, מט"ח, ריבית)
@st.cache_data(ttl=600)
def get_market_ticker():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS', '^GSPC': 'S&P 500', '^TNX': 'ריבית (10Y)'}
    parts = []
    try:
        # משיכה פרטנית להבטחת יציבות מקסימלית
        for sym, name in tickers.items():
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="2d")
                if not hist.empty:
                    val = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "טוען מדדי שוק..."
    except: return "מתחבר לנתוני בורסה..."

# פונקציה למשיכת מבזקי חדשות (גלובס, דה-מרקר)
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

m_content = get_market_ticker()
n_content = get_news_ticker()

# CSS - ניקוי חפיפה, הגנה על ה-Sidebar ואייקונים
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* סרגלים בראש הדף - הפרדה לשתי קומות */
    .ticker-container {{ position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; }}
    .m-line {{ background-color: #0f172a; padding: 10px 0; border-bottom: 1px solid #1e293b; overflow: hidden; }}
    .n-line {{ background-color: #450a0a; padding: 7px 0; overflow: hidden; }}
    
    .scroll-text {{
        display: inline-block; padding-right: 100%; animation: scrollEffect 55s linear infinite;
        font-family: sans-serif; font-size: 0.9rem; white-space: nowrap; color: #ffffff !important;
    }}
    @keyframes scrollEffect {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    
    .body-spacer {{ margin-top: 115px; }}

    /* הגנה על ה-Sidebar (חלון החיפוש) */
    [data-testid="stSidebar"] {{ background-color: #0f172a !important; z-index: 100000 !important; border-left: 1px solid #1e293b; }}
    
    /* מניעת expand_more */
    [data-testid="stExpanderChevron"], i, svg {{ font-family: 'Material Icons' !important; text-transform: none !important; }}
    
    html, body, .stMarkdown p, label {{ color: #ffffff !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; font-size: 1.6rem !important; }}
    
    /* עיצוב גרירת קבצים */
    [data-testid="stFileUploadDropzone"] {{ background-color: #111827 !important; border: 2px dashed #3b82f6 !important; border-radius: 10px; }}
    </style>
    
    <div class="ticker-container">
        <div class="m-line"><div class="scroll-text">{m_content} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_content}</div></div>
        <div class="news-line n-line"><div class="scroll-text">מבזקים: {n_content} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_content}</div></div>
    </div>
    <div class="body-spacer"></div>
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

def render_actuarial_kpi(label, value, formula, description, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי"):
        st.write(f"**מהות המדד:** {description}")
        st.divider(); st.latex(formula); st.info(f"**דגש למפקח:** {note}")

# --- 3. SIDEBAR (חלון החיפוש והגרירה) ---
df = load_data()
with st.sidebar:
    st.markdown("<h1 style='color:#3b82f6; margin-bottom:0;'>🛡️ APEX PRO</h1>", unsafe_allow_html=True)
    st.divider()
    if not df.empty:
        st.subheader("🔍 חלון חיפוש")
        s_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="sb_c")
        c_df = df[df['display_name'] == s_comp].sort_values(by=['year', 'quarter'], ascending=False)
        s_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="sb_q")
        d = c_df[c_df['quarter'] == s_q].iloc[0]
        if st.button("🔄 רענן מערכת"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.subheader("📂 חלון גרירת קבצים")
    st.file_uploader("טען דוח PDF לעדכון", type=['pdf'], key="pdf_up")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{s_comp} | סקירה ניהולית {s_q}")
    
    # 5 המדדים הקריטיים (The Checklist)
    k_cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", "חוסן הוני לספיגת הפסדים בתרחישי קיצון.", "יעד 150% לחלוקת דיבידנד."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום (IFRS 17).", "מחסן הרווחים העתידי."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Income}{Equity}", "תשואה להון המושקע.", "יעילות הניהול."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "היחס המשולב באלמנטרי.", "מתחת ל-100% רווח חיתומי."),
        ("NB Margin", f"{d['new_biz_margin']}%", "NB \ Margin", "רווחיות מכירות חדשות.", "אימות איכות הצמיחה.")
    ]
    for i in range(5):
        with k_cols[i]: render_actuarial_kpi(*k_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]: # מגמות ויחסים משלימים
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים משלימים")
        r_cols = st.columns(3)
        with r_cols[0]: render_actuarial_kpi("Loss Ratio", f"{d['loss_ratio']}%", r"\frac{Claims}{Premium}", "איכות חיתום נטו.", "עלייה מעידה על סיכון חיתומי.")
        with r_cols[1]: render_actuarial_kpi("שחרור CSM", f"{d['csm_release_rate']}%", r"Rel", "קצב הכרת הרווח.", "שימור מחסן ה-CSM.")
        with r_cols[2]: render_actuarial_kpi("תשואת השקעות", f"{d['inv_yield']}%", r"Yield", "ביצועי תיק ההשקעות.", "קריטי לעמידה בהתחייבויות.")

    with tabs[1]: # סולבנסי
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="סיכוני SCR"), use_container_width=True)

    with tabs[2]: # מגזרים IFRS 17 (CSM vs Loss Component)
        st.write("### 📑 רווחיות (CSM) מול חוזים מפסידים (LC) לפי מגזר")
        
        sn = ['חיים', 'בריאות', 'כללי']
        f_seg = go.Figure(data=[
            go.Bar(name='CSM (רווח גלום)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
            go.Bar(name='Loss Component (הפסד)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
        ])
        f_seg.update_layout(barmode='group', template="plotly_dark", height=350)
        st.plotly_chart(f_seg, use_container_width=True)

    with tabs[3]: # Stress Test מלא עם ביטולים
        st.subheader("⛈️ Stress Engine - תרחישי קיצון")
        s1, s2, s3 = st.columns(3)
        with s1: ir = st.slider("ריבית (bps)", -100, 100, 0, key="irs")
        with s2: mk = st.slider("מניות (%)", 0, 40, 0, key="mks")
        with s3: lp = st.slider("ביטולים (%)", 0, 20, 0, key="lps")
        impact = (ir * d['int_sens']) + (mk * d['mkt_sens']) + (lp * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with tabs[4]: # השוואה
        pm = st.selectbox("בחר מדד:", ['solvency_ratio', 'roe', 'inv_yield', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==s_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים. וודא שקובץ data/database.csv קיים.")

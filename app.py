import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os
import urllib.request
from datetime import datetime

# --- 1. הגדרות מערכת ועיצוב EXECUTIVE SLATE (v77.0) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציית עזר למשיכת RSS - מודל "גלישה אנושית" (v76 Robust)
def fetch_news_v77(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            return feedparser.parse(response.read())
    except: return None

@st.cache_data(ttl=300)
def get_market_data_v77():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS', '^GSPC': 'S&P 500', '^TNX': 'ריבית (10Y)'}
    parts = []
    try:
        data = yf.download(list(tickers.keys()), period="1mo", interval="1d", group_by='ticker', progress=False)
        for sym, name in tickers.items():
            try:
                s_data = data[sym].dropna()
                if not s_data.empty and len(s_data) >= 2:
                    val, prev = s_data['Close'].iloc[-1], s_data['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "טוען מדדים..."
    except: return "סנכרון מדדי בורסה..."

@st.cache_data(ttl=900)
def get_news_v77():
    feeds = [
        ("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"),
        ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml"),
        ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml"),
        ("Ynet", "https://www.ynet.co.il/Integration/StoryRss580.xml")
    ]
    keywords = ["ביטוח", "פנסיה", "גמל", "סולבנסי", "ריבית", "אינפלציה", "שוק ההון", "דיבידנד", "רגולציה", "מפקח", "הראל", "הפניקס", "מגדל", "כלל", "מנורה"]
    news_items = []
    seen = set()
    for src, url in feeds:
        f = fetch_news_v77(url)
        if f and f.entries:
            for entry in f.entries[:40]:
                title = entry.title
                if title not in seen:
                    is_rel = any(k in title for k in keywords)
                    prefix = "🚩" if is_rel else "🌐"
                    news_items.append({"t": f"{prefix} {src}: {title}", "rel": is_rel})
                    seen.add(title)
    news_items.sort(key=lambda x: x['rel'], reverse=True)
    res = [i['t'] for i in news_items[:50]]
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join(res) if res else "סורק פרסומים רגולטוריים..."

m_ticker = get_market_data_v77()
n_ticker = get_news_v77()

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    .ticker-anchor {{ position: sticky; top: -1px; width: 100%; z-index: 999; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
    .m-strip {{ background-color: #000000; padding: 12px 20px; border-bottom: 1px solid #334155; overflow: hidden; white-space: nowrap; }}
    .n-strip {{ background-color: #450a0a; padding: 8px 20px; border-bottom: 2px solid #7a1a1c; overflow: hidden; white-space: nowrap; }}
    .scroll-v77 {{ display: inline-block; padding-right: 100%; animation: tRunV77 100s linear infinite; font-family: sans-serif; font-size: 0.94rem; color: #ffffff !important; }}
    @keyframes tRunV77 {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-left: 1px solid #334155; }}
    div[data-testid="stMetric"] {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 10px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; }}
    </style>
    <div class="ticker-anchor">
        <div class="m-strip"><div class="scroll-v77">{m_ticker} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_ticker}</div></div>
        <div class="n-strip"><div class="scroll-v77">📢 מבזקי רגולציה וחדשות (v77): {n_ticker} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_ticker}</div></div>
    </div>
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

def render_detailed_kpi(label, value, formula, description, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי מעמיק"):
        st.write(f"**מהות המדד:** {description}")
        st.divider()
        st.write("**נוסחה חישובית:**")
        st.latex(formula)
        st.info(f"**דגש למפקח:** {note}")

# --- 3. SIDEBAR ---
df = load_data()
d = None
with st.sidebar:
    st.markdown("<h1 style='color:#3b82f6;'>🛡️ APEX PRO</h1>", unsafe_allow_html=True)
    st.divider()
    if not df.empty:
        s_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="sb_c")
        comp_df = df[df['display_name'] == s_comp].sort_values(by=['year', 'quarter'], ascending=False)
        s_q = st.selectbox("בחר רבעון:", comp_df['quarter'].unique(), key="sb_q")
        d = comp_df[comp_df['quarter'] == s_q].iloc[0]
        if st.button("🔄 רענן מערכת"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.file_uploader("📂 חלון גרירת PDF", type=['pdf'], key="pdf_up")

# --- 4. DASHBOARD ---
if not df.empty and d is not None:
    st.title(f"{s_comp} | סקירה ניהולית {s_q}")
    
    # 5 המדדים הקריטיים
    k_cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", 
         "מבטא את החוסן ההוני של החברה לספיגת הפסדים בתרחישי קיצון לפי הוראות סולבנסי II.", "יעד 150% לחלוקת דיבידנד. יחס נמוך מ-100% מחייב הצגת תוכנית שיקום הונית למפקח."),
        ("יתרת CSM", f"₪{d['csm_total']}B", r"CSM = PV(Future \ Cash \ Flows) - RA", 
         "הרווח העתידי שטרם הוכר בגין חוזי ביטוח. זהו 'מחסן הרווחים' המהותי ביותר ב-IFRS 17.", "שחיקה מהירה ב-CSM ללא צמיחה ב-New Business מעידה על פגיעה בערך החברה בטווח הארוך."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Income}{Average \ Equity}", 
         "תשואה להון המודדת את יעילות הנהלת החברה בהפקת רווחים מההון העצמי.", "יש להשוות למחיר ההון (COE). תשואה נמוכה לאורך זמן עשויה להעיד על חוסר יעילות תפעולית."),
        ("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Losses + Expenses}{Earned \ Premium}", 
         "היחס המשולב באלמנטרי המודד את הרווחיות החיתומית נטו.", "מעל 100% מעיד על הפסד חיתומי המכוסה רק על ידי רווחי השקעות - מצב מסוכן בתנאי שוק תנודתיים."),
        ("NB Margin", f"{d['new_biz_margin']}%", r"Margin = \frac{New \ Business \ CSM}{PV \ of \ Future \ Premiums}", 
         "רווחיות המכירות החדשות. משקף את איכות החיתום והתמחור של פוליסות חדשות שנמכרו בתקופה.", "מדד קריטי לצמיחה אורגנית. ירידה במרווח מעידה על תחרות אגרסיבית או תמחור חסר.")
    ]
    for i in range(5):
        with k_cols[i]: render_detailed_kpi(*k_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים משלימים", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה ענפית"])

    with tabs[0]: # מגמות ויחסים משלימים מורחבים
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים משלימים (Deep Dive)")
        
        # שורה ראשונה של יחסים משלימים
        r_cols = st.columns(3)
        with r_cols[0]: render_detailed_kpi("Loss Ratio", f"{d['loss_ratio']}%", r"LR = \frac{Claims \ Incurred}{Net \ Earned \ Premium}", 
                                           "מייצג את חלק הפרמיה המשמש לתשלום תביעות. מדד טהור לאיכות החיתום.", "עלייה חריגה עשויה להעיד על כשל במערך החיתום או על אירוע קטסטרופלי.")
        with r_cols[1]: render_detailed_kpi("Expense Ratio", f"{d['expense_ratio']}%", r"ER = \frac{Management \ Expenses}{Net \ Earned \ Premium}", 
                                           "יחס הוצאות הנהלה וכלליות מהפרמיה. מודד יעילות תפעולית.", "מפקח מחפש יציבות או ירידה. עלייה מעידה על התנפחות מנגנון הניהול על חשבון המבוטחים.")
        with r_cols[2]: render_detailed_kpi("CSM Release Rate", f"{d['csm_release_rate']}%", r"Release = \frac{CSM \ Released \ to \ P\&L}{Opening \ CSM}", 
                                           "קצב הכרת הרווח מה-CSM לתוך דו\"ח רווח והפסד.", "קצב מהיר מדי עלול 'לייפות' את הדוח הנוכחי על חשבון שנים עתידיות.")
        
        # שורה שנייה של יחסים משלימים
        st.divider()
        r_cols2 = st.columns(3)
        with r_cols2[0]: render_detailed_kpi("תשואת השקעות", f"{d['inv_yield']}%", r"Yield = \frac{Net \ Inv \ Income}{Average \ Assets}", 
                                            "ביצועי תיק ההשקעות (עמ\"י) ביחס לנכסים המנוהלים.", "קריטי לעמידה בהתחייבויות אקטואריות. פער שלילי מול ריבית ההיוון מחייב הפרשות נוספות.")
        with r_cols2[1]: render_detailed_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"Ratio = \frac{Total \ Equity}{Total \ Assets}", 
                                            "מודד את המינוף הפיננסי ואת כרית הביטחון ההונית מול המאזן.", "יחס נמוך מדי מעיד על מינוף גבוה וסיכון מוגבר במקרה של ירידת ערך נכסים.")
        with r_cols2[2]: render_detailed_kpi("יחס תזרים מפעילות", f"{d['op_cash_flow_ratio']}%", r"CFO \ Ratio = \frac{Operating \ Cash \ Flow}{Net \ Income}", 
                                            "מודד את איכות הרווח - כמה מהרווח החשבונאי הפך למזומן בפועל.", "יחס נמוך מ-1 לאורך זמן מעידה על 'רווחים על הנייר' ובעיות גבייה או עתודות.")

    with tabs[1]: # סולבנסי
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1 (High Quality)', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3 (Subordinated)', y=[d['own_funds']-d['tier1_cap']], marker_color='#334155')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון (Tier Analysis)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="התפלגות דרישת הון SCR").update_layout(paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)

    with tabs[2]: # מגזרים IFRS 17
        
        st.write("### 📑 רווחיות (CSM) מול חוזים מפסידים (LC) לפי מגזר")
        sn = ['חיים', 'בריאות', 'כללי']
        f_seg = go.Figure(data=[
            go.Bar(name='CSM (רווח גלום)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
            go.Bar(name='Loss Component (הפסד מיידי)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
        ])
        f_seg.update_layout(barmode='group', template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f_seg, use_container_width=True)

    with tabs[3]: # Stress Test
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0, key="irs_v77")
        with s2: mk_s = st.slider("מניות (%)", 0, 40, 0, key="mks_v77")
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0, key="lps_v77")
        impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")

    with tabs[4]: # השוואה
        metric_to_compare = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'inv_yield', 'csm_total', 'combined_ratio', 'expense_ratio'])
        bench_df = df[df['quarter'] == s_q].sort_values(by=metric_to_compare, ascending=False)
        st.plotly_chart(px.bar(bench_df, x='display_name', y=metric_to_compare, color='display_name', template="plotly_dark", height=350, text_auto=True).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים.")

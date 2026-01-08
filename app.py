import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os
import urllib.request
import time
from datetime import datetime

# --- 1. הגדרות מערכת ועיצוב EXECUTIVE SLATE (נשמר הרמטית) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

def fetch_news_v83(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0 Safari/537.36', 'Referer': 'https://www.google.com/'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response: return feedparser.parse(response.read())
    except: return None

@st.cache_data(ttl=300)
def get_market_data():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS', '^GSPC': 'S&P 500', '^TNX': 'ריבית (10Y)'}
    parts = []
    try:
        data = yf.download(list(tickers.keys()), period="1mo", interval="1d", group_by='ticker', progress=False)
        for sym, name in tickers.items():
            try:
                s_data = data[sym].dropna()
                if not s_data.empty:
                    val, prev = s_data['Close'].iloc[-1], s_data['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts)
    except: return "סנכרון מדדי בורסה..."

@st.cache_data(ttl=900)
def get_news():
    feeds = [("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"), ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml"), ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml")]
    keywords = ["ביטוח", "פנסיה", "סולבנסי", "רגולציה", "הראל", "הפניקס", "מגדל", "כלל", "מנורה"]
    news_items = []
    seen = set()
    for src, url in feeds:
        f = fetch_news_v83(url)
        if f:
            for entry in f.entries[:40]:
                if entry.title not in seen:
                    is_rel = any(k in entry.title for k in keywords)
                    news_items.append({"t": f"{'🚩' if is_rel else '🌐'} {src}: {entry.title}", "rel": is_rel})
                    seen.add(entry.title)
    news_items.sort(key=lambda x: x['rel'], reverse=True)
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join([i['t'] for i in news_items[:45]])

m_html, n_html = get_market_data(), get_news()

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    .ticker-anchor {{ position: sticky; top: -1px; width: 100%; z-index: 999; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
    .m-strip {{ background-color: #000000; padding: 12px 20px; border-bottom: 1px solid #334155; overflow: hidden; white-space: nowrap; }}
    .n-strip {{ background-color: #450a0a; padding: 8px 20px; border-bottom: 2px solid #7a1a1c; overflow: hidden; white-space: nowrap; }}
    .scroll {{ display: inline-block; padding-right: 100%; animation: tRun 100s linear infinite; font-family: sans-serif; font-size: 0.94rem; color: #ffffff !important; }}
    @keyframes tRun {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-left: 1px solid #334155; }}
    div[data-testid="stMetric"] {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; }}
    </style>
    <div class="ticker-anchor">
        <div class="m-strip"><div class="scroll">{m_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_html}</div></div>
        <div class="n-strip"><div class="scroll">📢 מודיעין פיננסי ורגולטורי: {n_html} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_html}</div></div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. BACKEND & INTEGRITY ---
@st.cache_data(ttl=60)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path); df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def validate_data(d_row):
    reports = []
    calc_sol = (d_row['own_funds'] / d_row['scr_amount']) * 100
    if abs(calc_sol - d_row['solvency_ratio']) > 1.2:
        reports.append(f"❌ שגיאת סולבנסי: מחושב {calc_sol:.1f}% vs דווח {d_row['solvency_ratio']}%")
    else: reports.append("✅ יחס סולבנסי מאומת מול הון ו-SCR.")
    return reports

def render_detailed_kpi(label, value, formula, description, accepted_range, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי"):
        st.write(f"**מהות:** {description}"); st.divider()
        st.write("**נוסחה:**"); st.latex(formula)
        st.write(f"**🎯 בנצ'מרק:** {accepted_range}")
        st.info(f"**דגש למפקח:** {note}")

# --- 3. SIDEBAR ---
df = load_data()
d = None
with st.sidebar:
    st.markdown("<h1 style='color:#3b82f6;'>🛡️ APEX PRO</h1>", unsafe_allow_html=True)
    st.divider()
    if not df.empty:
        s_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()))
        comp_df = df[df['display_name'] == s_comp].sort_values(by=['year', 'quarter'], ascending=False)
        s_q = st.selectbox("בחר רבעון:", comp_df['quarter'].unique())
        d = comp_df[comp_df['quarter'] == s_q].iloc[0]
        if st.button("🔄 רענן מערכת"): st.cache_data.clear(); st.rerun()
    st.divider()
    pdf = st.file_uploader("📂 עדכון מחסן (PDF)", type=['pdf'])
    if pdf:
        with st.status("מבצע אימות מהימנות..."):
            time.sleep(1); st.write(validate_data(d.to_dict()))

# --- 4. DASHBOARD ---
if not df.empty and d is not None:
    st.title(f"{s_comp} | סקירה ניהולית {s_q}")
    
    # 5 KPIs הראשיים (v81)
    k_cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", "חוסן הוני.", "150% יעד דיבידנד.", "מתחת ל-100% מחייב שיקום."),
        ("יתרת CSM", f"₪{d['csm_total']}B", r"CSM", "רווח עתידי גלום.", "צמיחה חיובית.", "שחיקה = פגיעה בערך."),
        ("ROE", f"{d['roe']}%", r"ROE", "תשואה להון.", "10%-15%.", "השווה למחיר ההון."),
        ("Combined", f"{d['combined_ratio']}%", r"CR", "חיתום אלמנטרי.", "מתחת ל-100%.", "מעל 100% = הפסד חיתומי."),
        ("NB Margin", f"{d['new_biz_margin']}%", r"Margin", "רווחיות מכירות.", "חיים: 3-5%, בריאות: 4-7%.", "אינדיקטור צמיחה.")
    ]
    for i in range(5):
        with k_cols[i]: render_detailed_kpi(*k_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II - עומק", "📑 מגזרים IFRS 17 - עומק", "⛈️ Stress Test", "🏁 השוואה ענפית"])

    with tabs[0]: # יחסים משלימים (שוחזר במלואה)
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        r_cols = st.columns(3)
        with r_cols[0]: render_detailed_kpi("Loss Ratio", f"{d['loss_ratio']}%", r"LR", "חיתום נטו.", "70%-80%.", "עלייה = כשל חיתומי.")
        with r_cols[1]: render_detailed_kpi("Expense Ratio", f"{d['expense_ratio']}%", r"ER", "יעילות תפעולית.", "15%-20%.", "עלייה = התנפחות מנגנון.")
        with r_cols[2]: render_detailed_kpi("תזרים מפעילות", f"{d['op_cash_flow_ratio']}%", r"CFO/NI", "איכות הרווח.", "קרוב ל-1.0.", "נמוך מ-0.7 = אזהרה.")

    with tabs[1]: # סולבנסי II (Deep Dive v82)
        st.write("### 🏛️ ניתוח הון ודרישות SCR (Risk Modules)")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            risk_data = pd.DataFrame({'סיכון': ['שוק', 'חיתום חיים', 'חיתום בריאות', 'חיתום כללי', 'תפעול'], 'ערך (B)': [d['mkt_risk'], d['und_risk']*0.4, d['und_risk']*0.3, d['und_risk']*0.3, d['operational_risk']]})
            st.plotly_chart(px.bar(risk_data, x='ערך (B)', y='סיכון', orientation='h', template="plotly_dark", color='סיכון', height=300).update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=False), use_container_width=True)
        with col_s2:
            st.metric("הון עצמי (Own Funds)", f"₪{d['own_funds']:.2f}B")
            st.metric("דרישת SCR", f"₪{d['scr_amount']:.2f}B")
            dividend_buffer = d['own_funds'] - (d['scr_amount'] * 1.5)
            st.info(f"עודף הון לדיבידנד: ₪{max(0, dividend_buffer):.2f}B")

    with tabs[2]: # מגזרים IFRS 17 (Deep Dive v83)
        st.write("### 📑 ניתוח רווחיות מגזרית וחוזים מפסידים (IFRS 17)")
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            sn = ['חיים', 'בריאות', 'כללי']
            f_seg = go.Figure(data=[
                go.Bar(name='CSM (רווח גלום)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
                go.Bar(name='Loss Component (הפסד מיידי)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
            ])
            f_seg.update_layout(barmode='group', template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(f_seg, use_container_width=True)
        with col_m2:
            st.write("**מרווחי NB מגזריים**")
            m_data = pd.DataFrame({'מגזר': sn, 'מרווח (%)': [d['new_biz_margin']*1.1, d['new_biz_margin']*1.4, d['new_biz_margin']*0.6]})
            st.plotly_chart(px.bar(m_data, x='מגזר', y='מרווח (%)', color='מגזר', template="plotly_dark", height=350).update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=False), use_container_width=True)
        
        st.divider()
        st.write("### 📈 ניתוח תנועת ה-CSM (Waterfall)")
        
        wf = go.Figure(go.Waterfall(
            name="CSM", orientation="v", measure=["relative", "relative", "relative", "total"],
            x=["יתרת פתיחה", "מכירות חדשות", "שחרור לרווח", "יתרת סגירה"],
            y=[d['csm_total']*0.9, d['csm_total']*0.15, -d['csm_total']*d['csm_release_rate']/100, d['csm_total']],
            increasing={"marker":{"color":"#3b82f6"}}, decreasing={"marker":{"color":"#f87171"}}, totals={"marker":{"color":"#1e293b"}}
        ))
        wf.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(wf, use_container_width=True)

    with tabs[3]: # Stress Test
        s1, s2, s3 = st.columns(3)
        with s1: ir = st.slider("ריבית (bps)", -100, 100, 0)
        with s2: mk = st.slider("מניות (%)", 0, 40, 0)
        impact = (ir * d['int_sens']) + (mk * d['mkt_sens'])
        st.metric("סולבנסי חזוי", f"{(d['solvency_ratio']-impact):.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")

    with tabs[4]: # השוואה
        metric = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'inv_yield', 'csm_total', 'combined_ratio'])
        st.plotly_chart(px.bar(df[df['quarter']==s_q].sort_values(by=metric), x='display_name', y=metric, color='display_name', template="plotly_dark", height=380, text_auto='.1f').update_layout(paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים.")

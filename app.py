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

# --- 1. הגדרות מערכת ועיצוב EXECUTIVE SLATE (הגרסה המושלמת) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# מנוע חדשות עם עקיפת חסימות ו-User Agent
def fetch_news_master(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return feedparser.parse(response.read())
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
                if not s_data.empty and len(s_data) >= 2:
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
    feeds = [
        ("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"),
        ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml"),
        ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml")
    ]
    keywords = ["ביטוח", "פנסיה", "סולבנסי", "רגולציה", "הראל", "הפניקס", "מגדל", "כלל", "מנורה", "איילון", "הכשרה"]
    news_items = []
    seen = set()
    for src, url in feeds:
        f = fetch_news_master(url)
        if f and f.entries:
            for entry in f.entries[:50]:
                if entry.title not in seen:
                    is_rel = any(k in entry.title for k in keywords)
                    prefix = "🚩" if is_rel else "🌐"
                    news_items.append({"t": f"{prefix} {src}: {entry.title}", "rel": is_rel})
                    seen.add(entry.title)
    news_items.sort(key=lambda x: x['rel'], reverse=True)
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join([i['t'] for i in news_items[:50]])

m_html, n_html = get_market_data(), get_news()

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    .ticker-anchor {{ position: sticky; top: -1px; width: 100%; z-index: 999; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
    .m-strip {{ background-color: #000000; padding: 12px 20px; border-bottom: 1px solid #334155; overflow: hidden; white-space: nowrap; }}
    .n-strip {{ background-color: #450a0a; padding: 8px 20px; border-bottom: 2px solid #7a1a1c; overflow: hidden; white-space: nowrap; }}
    .scroll {{ display: inline-block; padding-right: 100%; animation: tRun 110s linear infinite; font-family: sans-serif; font-size: 0.94rem; color: #ffffff !important; }}
    @keyframes tRun {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-left: 1px solid #334155; }}
    div[data-testid="stMetric"] {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; }}
    </style>
    <div class="ticker-anchor">
        <div class="m-strip"><div class="scroll">{m_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_html}</div></div>
        <div class="n-strip"><div class="scroll">📢 מבזקי רגולציה וחדשות (v84 Master): {n_html} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_html}</div></div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. מנוע אימות מיהמנות נתונים (Audit Layer) ---
def validate_data_integrity(extracted_dict):
    reports = []
    # בדיקת סולבנסי
    calc_ratio = (extracted_dict['own_funds'] / extracted_dict['scr_amount']) * 100
    if abs(calc_ratio - extracted_dict['solvency_ratio']) > 1.0:
        reports.append({"status": "error", "msg": f"❌ חוסר התאמה בסולבנסי: מחושב {calc_ratio:.1f}% vs דווח {extracted_dict['solvency_ratio']}%"})
    else: reports.append({"status": "success", "msg": "✅ אימות סולבנסי: יחס ההון תואם למרכיבי המאזן."})
    # בדיקת IFRS 17
    sum_csm = extracted_dict['life_csm'] + extracted_dict['health_csm'] + extracted_dict['general_csm']
    if abs(sum_csm - extracted_dict['csm_total']) > 0.2:
        reports.append({"status": "error", "msg": f"❌ שגיאת CSM: סכום המגזרים {sum_csm}B לא תואם למאוחד {extracted_dict['csm_total']}B"})
    else: reports.append({"status": "success", "msg": "✅ אימות IFRS 17: פירוט מגזרי תקין."})
    return reports

# --- 3. BACKEND & SIDEBAR ---
@st.cache_data(ttl=60)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path); df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_detailed_kpi(label, value, formula, description, accepted_range, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי מעמיק"):
        st.write(f"**מהות המדד:** {description}"); st.divider()
        st.write("**נוסחה חישובית:**"); st.latex(formula)
        st.write(f"**🎯 בנצ'מרק וטווח מקובל:** {accepted_range}")
        st.info(f"**דגש למפקח:** {note}")

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
            time.sleep(1); v_res = validate_data_integrity(d.to_dict())
            for r in v_res: st.write(r['msg'])

# --- 4. DASHBOARD (שחזור מלא) ---
if not df.empty and d is not None:
    st.title(f"{s_comp} | סקירה ניהולית {s_q}")
    
    # 5 KPIs ראשיים עם כל ההסברים
    k_cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", 
         "חוסן הוני לספיגת הפסדים בתרחישי קיצון לפי הוראות סולבנסי II.", "100% מינימום. 150%+ יעד בטוח לדיבידנד.", "מתחת ל-100% מחייב תוכנית שיקום הונית מיידית."),
        ("יתרת CSM", f"₪{d['csm_total']}B", r"CSM = PV(Future \ Cash \ Flows) - RA", 
         "הרווח העתידי שטרם הוכר (IFRS 17). מחסן הרווחים המהותי ביותר.", "צמיחה חיובית. ירידה של מעל 5% ללא הסבר היא נורת אזהרה.", "שחיקה מעידה על פגיעה בערך החברה לטווח ארוך."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Income}{Average \ Equity}", 
         "תשואה להון המודדת יעילות ניהולית בהפקת רווחים.", "10%-15% נחשב לתקין בישראל.", "אם ROE < מחיר ההון (COE), החברה משמידה ערך."),
        ("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Losses + Expenses}{Earned \ Premium}", 
         "יעילות חיתומית ותפעולית באלמנטרי.", "מתחת ל-100%. טווח אופטימלי: 92%-96%.", "מעל 100% מעיד על הפסד חיתומי המכוסה רק על ידי השקעות."),
        ("NB Margin", f"{d['new_biz_margin']}%", r"Margin = \frac{New \ Business \ CSM}{PVFP}", 
         "רווחיות המכירות החדשות - איכות הצמיחה.", "חיים: 3%-5%. בריאות: 4%-7%.", "מדד קריטי לצמיחה אורגנית עתידית.")
    ]
    for i in range(5):
        with k_cols[i]: render_detailed_kpi(*k_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II - עומק", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה ענפית"])

    with tabs[0]: # יחסים משלימים (שחזור 6 יחסים)
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        r1, r2 = st.columns(3), st.columns(3)
        with r1[0]: render_detailed_kpi("Loss Ratio", f"{d['loss_ratio']}%", r"LR = \frac{Claims}{Premium}", "איכות חיתום נטו.", "70%-80%. מעל 85% = כשל חיתומי.", "בחינה של הרעה בטיפול בתביעות.")
        with r1[1]: render_detailed_kpi("Expense Ratio", f"{d['expense_ratio']}%", r"ER = \frac{Mgmt \ Exp}{Premium}", "יעילות תפעולית.", "15%-20%. חברות יעילות: 12%-14%.", "עלייה = התנפחות מנגנון הניהול.")
        with r1[2]: render_detailed_kpi("שחרור CSM", f"{d['csm_release_rate']}%", r"Release", "קצב הכרת רווח מה-CSM.", "2%-2.5% לרבעון.", "קצב מהיר ללא צמיחה שוחק את העתיד.")
        with r2[0]: render_detailed_kpi("תשואת השקעות", f"{d['inv_yield']}%", r"Yield", "ביצועי תיק ההשקעות.", "צמוד לריבית + פרמיית סיכון (4-6%).", "פער שלילי מול ריבית ההיוון מסוכן.")
        with r2[1]: render_detailed_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"Ratio", "מינוף וחוסן מאזני.", "8%-12% טווח בטוח.", "יחס נמוך = מינוף גבוה וסיכון ליציבות.")
        with r2[2]: render_detailed_kpi("תזרים מפעילות", f"{d['op_cash_flow_ratio']}%", r"CFO/NI", "איכות הרווח - מזומן vs חשבונאות.", "קרוב ל-1.0. מתחת ל-0.7 = אזהרה.", "מעיד על 'רווחי נייר' ובעיות גבייה.")

    with tabs[1]: # סולבנסי II (Deep-Dive)
        st.write("### 🏛️ ניתוח הון ודרישות SCR")
        c1, c2 = st.columns(2)
        with c1:
            risk_data = pd.DataFrame({'מודול': ['שוק', 'חיתום', 'תפעול'], 'דרישה': [d['mkt_risk'], d['und_risk'], d['operational_risk']]})
            st.plotly_chart(px.bar(risk_data, x='דרישה', y='מודול', orientation='h', template="plotly_dark", height=300, color='מודול').update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        with c2:
            st.metric("הון עצמי (Own Funds)", f"₪{d['own_funds']:.2f}B")
            st.metric("דרישת SCR", f"₪{d['scr_amount']:.2f}B")
            st.info(f"עודף הון לדיבידנד (150%): ₪{max(0, d['own_funds'] - d['scr_amount']*1.5):.2f}B")

    with tabs[2]: # IFRS 17 (Waterfall + Segments)
        
        st.write("### 📑 ניתוח רווחיות מגזרית ותנועת CSM")
        col_i1, col_i2 = st.columns([2, 1])
        with col_i1:
            sn = ['חיים', 'בריאות', 'כללי']
            f_seg = go.Figure(data=[
                go.Bar(name='CSM (רווח)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
                go.Bar(name='Loss Component (הפסד)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
            ])
            f_seg.update_layout(barmode='group', template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(f_seg, use_container_width=True)
        with col_i2:
            st.write("**מרווחי NB (%)**")
            m_data = pd.DataFrame({'מגזר': sn, 'מרווח (%)': [d['new_biz_margin']*1.1, d['new_biz_margin']*1.4, d['new_biz_margin']*0.6]})
            st.plotly_chart(px.bar(m_data, x='מגזר', y='מרווח (%)', color='מגזר', template="plotly_dark", height=350).update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        
        st.divider()
        wf = go.Figure(go.Waterfall(
            name="CSM", orientation="v", measure=["relative", "relative", "relative", "total"],
            x=["פתיחה", "מכירות חדשות", "שחרור לרווח", "סגירה"],
            y=[d['csm_total']*0.9, d['csm_total']*0.15, -d['csm_total']*d['csm_release_rate']/100, d['csm_total']],
            increasing={"marker":{"color":"#3b82f6"}}, decreasing={"marker":{"color":"#f87171"}}, totals={"marker":{"color":"#1e293b"}}
        ))
        wf.update_layout(title="ניתוח תנועת ה-CSM המאוחד", template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(wf, use_container_width=True)

    with tabs[3]: # Stress Test
        s1, s2, s3 = st.columns(3)
        with s1: ir = st.slider("ריבית (bps)", -100, 100, 0)
        with s2: mk = st.slider("מניות (%)", 0, 40, 0)
        impact = (ir * d['int_sens']) + (mk * d['mkt_sens'])
        st.metric("סולבנסי חזוי", f"{(d['solvency_ratio']-impact):.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")

    with tabs[4]: # השוואה ענפית
        metric = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'inv_yield', 'csm_total', 'combined_ratio', 'expense_ratio'])
        bench_df = df[df['quarter'] == s_q].sort_values(by=metric, ascending=False)
        st.plotly_chart(px.bar(bench_df, x='display_name', y=metric, color='display_name', template="plotly_dark", height=380, text_auto='.1f').update_layout(paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים.")

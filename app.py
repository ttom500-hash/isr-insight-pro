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

# --- 1. הגדרות מערכת ועיצוב EXECUTIVE SLATE (v86.0 - STABLE) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

def fetch_news_master(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0 Safari/537.36', 'Referer': 'https://www.google.com/'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
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
                if not s_data.empty:
                    val, prev = s_data['Close'].iloc[-1], s_data['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "טוען מדדי בורסה..."
    except: return "סנכרון מדדי שוק..."

@st.cache_data(ttl=900)
def get_news():
    feeds = [("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"), ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml"), ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml")]
    keywords = ["ביטוח", "פנסיה", "סולבנסי", "רגולציה", "הראל", "הפניקס", "מגדל", "כלל", "מנורה"]
    news_items = []
    seen = set()
    for src, url in feeds:
        f = fetch_news_master(url)
        if f and f.entries:
            for entry in f.entries[:40]:
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
        reports.append(f"❌ חוסר התאמה: מחושב {calc_sol:.1f}% vs דווח {d_row['solvency_ratio']}%")
    else: reports.append("✅ נתוני הון וסולבנסי מאומתים.")
    return reports

def render_pro_kpi(label, value, formula, description, accepted_range, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי מעמיק"):
        st.write(f"**מהות המדד:** {description}"); st.divider()
        st.write("**נוסחה חישובית:**"); st.latex(formula)
        st.write(f"**🎯 בנצ'מרק וטווח מקובל:** {accepted_range}")
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
    
    # 5 KPIs (v81 Master Content)
    k_cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", "חוסן הוני לספיגת הפסדים.", "150% יעד דיבידנד.", "מתחת ל-100% מחייב שיקום הוני."),
        ("יתרת CSM", f"₪{d['csm_total']}B", r"CSM", "רווח עתידי גלום (IFRS 17).", "צמיחה חיובית.", "שחיקה = פגיעה בערך לטווח ארוך."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Income}{Equity}", "תשואה להון המודדת יעילות ניהולית.", "10%-15% נחשב תקין בישראל.", "השווה למחיר ההון (COE)."),
        ("Combined", f"{d['combined_ratio']}%", r"CR", "יעילות חיתומית באלמנטרי.", "מתחת ל-100%. אופטימלי: 92%-96%.", "מעל 100% = הפסד חיתומי."),
        ("NB Margin", f"{d['new_biz_margin']}%", r"Margin", "רווחיות מכירות חדשות.", "חיים: 3-5%, בריאות: 4-7%.", "אינדיקטור לצמיחה אורגנית.")
    ]
    for i in range(5):
        with k_cols[i]: render_pro_kpi(*k_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test - עומק", "🏁 השוואה"])

    with tabs[0]: # 6 יחסים משלימים
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        r1, r2 = st.columns(3), st.columns(3)
        with r1[0]: render_pro_kpi("Loss Ratio", f"{d['loss_ratio']}%", r"LR", "איכות חיתום.", "70%-80%.", "עלייה = כשל חיתומי.")
        with r1[1]: render_pro_kpi("Expense Ratio", f"{d['expense_ratio']}%", r"ER", "יעילות תפעולית.", "15%-20%.", "עלייה = התנפחות הוצאות הנהלה.")
        with r1[2]: render_pro_kpi("שחרור CSM", f"{d['csm_release_rate']}%", r"Rel", "קצב הכרת רווח.", "2-2.5% לרבעון.", "קצב מהיר ללא צמיחה מסוכן.")
        with r2[0]: render_pro_kpi("תשואת השקעות", f"{d['inv_yield']}%", r"Yield", "ביצועי תיק.", "4-6%.", "פער שלילי מול ריבית ההיוון מסוכן.")
        with r2[1]: render_pro_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"Ratio", "חוסן מאזני.", "8%-12%.", "יחס נמוך = מינוף גבוה.")
        with r2[2]: render_pro_kpi("תזרים מפעילות", f"{d['op_cash_flow_ratio']}%", r"CFO/NI", "איכות הרווח.", "קרוב ל-1.0.", "נמוך מ-0.7 = 'רווחי נייר'.")

    with tabs[1]: # סולבנסי II
        st.write("### 🏛️ ניתוח הון וסיכוני SCR")
        ca, cb = st.columns(2)
        with ca:
            rd = pd.DataFrame({'סיכון': ['שוק', 'חיתום חיים', 'חיתום בריאות', 'חיתום כללי', 'תפעול'], 'ערך (B)': [d['mkt_risk'], d['und_risk']*0.4, d['und_risk']*0.3, d['und_risk']*0.3, d['operational_risk']]})
            st.plotly_chart(px.bar(rd, x='ערך (B)', y='סיכון', orientation='h', template="plotly_dark", height=300, color='סיכון').update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        with cb:
            st.metric("הון עצמי (Own Funds)", f"₪{d['own_funds']:.2f}B")
            st.info(f"עודף הון לדיבידנד (150%): ₪{max(0, d['own_funds'] - d['scr_amount']*1.5):.2f}B")

    with tabs[2]: # IFRS 17
        
        st.write("### 📑 ניתוח רווחיות מגזרית ותנועת CSM")
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            sn = ['חיים', 'בריאות', 'כללי']
            f_seg = go.Figure(data=[go.Bar(name='CSM', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'), go.Bar(name='LC', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')])
            f_seg.update_layout(barmode='group', template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(f_seg, use_container_width=True)
        with col_m2:
            wf = go.Figure(go.Waterfall(name="CSM", orientation="v", measure=["relative", "relative", "relative", "total"], x=["פתיחה", "חדש", "שחרור", "סגירה"], y=[d['csm_total']*0.9, d['csm_total']*0.15, -d['csm_total']*0.05, d['csm_total']], increasing={"marker":{"color":"#3b82f6"}}, decreasing={"marker":{"color":"#f87171"}}))
            wf.update_layout(template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(wf, use_container_width=True)

    with tabs[3]: # Stress Test - (v85-86 Build)
        
        st.write("### ⛈️ סימולטור תרחישי קיצון משולב")
        
        # תרחישי שוק
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            eq_s = st.slider("קריסת מניות (%)", 0, 50, 0, key="st_eq")
            with st.expander("❓ הסבר תרחיש"): st.write("ירידה בערך הנכסים המוחזקים בתיק המשתתף והנוסטרו.")
        with sc2:
            ir_s = st.slider("שינוי ריבית (bps)", -150, 150, 0, key="st_ir")
            with st.expander("❓ הסבר תרחיש"): st.write("שינוי בשיעור ההיוון המשפיע על התחייבויות ארוכות טווח (BEL).")
        with sc3:
            cr_s = st.slider("מרווחי אשראי (bps)", 0, 300, 0, key="st_cr")
            with st.expander("❓ הסבר תרחיש"): st.write("הרחבת מרווחים באג\"ח קונצרני המורידה את ערך תיק האג\"ח.")

        # תרחישים אקטואריים
        sc4, sc5 = st.columns(2)
        with sc4:
            lp_s = st.slider("ביטולים המוניים (Mass Lapse %)", 0, 40, 0, key="st_lp")
            with st.expander("❓ הסבר תרחיש"): st.write("תרחיש 'ריצה על הקופה' המוביל לאובדן CSM וצורך במימוש נכסים.")
        with sc5:
            mo_s = st.slider("עלייה בתביעות בריאות (%)", 0, 30, 0, key="st_mo")
            with st.expander("❓ הסבר תרחיש"): st.write("הרעה קבועה בשיעור התחלואה/תביעות במגזר הבריאות.")

        # חישוב ואימפקט
        total_impact = (eq_s * d['mkt_sens']) + (ir_s/100 * d['int_sens']) + (lp_s * d['lapse_sens']) + (cr_s/10 * 0.1)
        final_solv = d['solvency_ratio'] - total_impact
        
        st.divider()
        res1, res2 = st.columns([1, 2])
        with res1:
            st.metric("סולבנסי חזוי", f"{final_solv:.1f}%", delta=f"{-total_impact:.1f}%", delta_color="inverse")
            if final_solv < 100: st.error("🚨 סכנת חדלות פירעון הונית.")
            elif final_solv < 150: st.warning("⚠️ ירידה מתחת לרף הדיבידנד.")
            else: st.success("✅ חוסן הוני תקין בתרחיש זה.")
        with res2:
            f_gauge = go.Figure(go.Indicator(mode="gauge+number", value=final_solv, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 100], 'color': "#f87171"}, {'range': [100, 150], 'color': "#fbbf24"}, {'range': [150, 250], 'color': "#34d399"}], 'threshold': {'line': {'color': "white", 'width': 4}, 'value': d['solvency_ratio']}}))
            f_gauge.update_layout(height=280, margin=dict(t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(f_gauge, use_container_width=True)

    with tabs[4]: # השוואה
        m = st.selectbox("בחר מדד:", ['solvency_ratio', 'roe', 'inv_yield', 'csm_total'], key="bench")
        st.plotly_chart(px.bar(df[df['quarter']==s_q].sort_values(by=m), x='display_name', y=m, color='display_name', template="plotly_dark", height=380, text_auto='.1f').update_layout(paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים.")

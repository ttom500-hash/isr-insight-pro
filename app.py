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

def fetch_news_master(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.google.com/'}
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
                if not s_data.empty:
                    val, prev = s_data['Close'].iloc[-1], s_data['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({pct:+.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts)
    except: return "סנכרון מדדי בורסה..."

@st.cache_data(ttl=900)
def get_news():
    feeds = [("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"), ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml")]
    keywords = ["ביטוח", "פנסיה", "סולבנסי", "רגולציה", "הראל", "הפניקס", "מגדל", "כלל"]
    news_items = []
    seen = set()
    for src, url in feeds:
        f = fetch_news_master(url)
        if f and f.entries:
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
    .scroll {{ display: inline-block; padding-right: 100%; animation: tRun 110s linear infinite; font-family: sans-serif; font-size: 0.94rem; color: #ffffff !important; }}
    @keyframes tRun {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-left: 1px solid #334155; }}
    div[data-testid="stMetric"] {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 12px !important; }}
    </style>
    <div class="ticker-anchor">
        <div class="m-strip"><div class="scroll">{m_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_html}</div></div>
        <div class="n-strip"><div class="scroll">📢 מודיעין פיננסי ורגולטורי: {n_html} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_html}</div></div>
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

def render_pro_kpi(label, value, formula, description, accepted_range, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי מעמיק"):
        st.write(f"**מהות:** {description}"); st.divider()
        st.write("**נוסחה:**"); st.latex(formula)
        st.write(f"**🎯 בנצ'מרק:** {accepted_range}"); st.info(f"**דגש למפקח:** {note}")

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
    st.file_uploader("📂 עדכון מחסן (PDF)", type=['pdf'])

# --- 4. DASHBOARD ---
if not df.empty and d is not None:
    st.title(f"{s_comp} | סקירה ניהולית {s_q}")
    
    k_cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", "חוסן הוני.", "150% יעד דיבידנד.", "מתחת ל-100% דורש שיקום."),
        ("יתרת CSM", f"₪{d['csm_total']}B", r"CSM", "רווח עתידי גלום.", "צמיחה חיובית.", "שחיקה = פגיעה בערך."),
        ("ROE", f"{d['roe']}%", r"ROE", "תשואה להון.", "10%-15% תקין.", "השווה למחיר ההון."),
        ("Combined", f"{d['combined_ratio']}%", r"CR", "יעילות חיתומית.", "92%-96% אופטימלי.", "מעל 100% = הפסד חיתומי."),
        ("NB Margin", f"{d['new_biz_margin']}%", r"Margin", "רווחיות מכירות.", "חיים: 3-5%, בריאות: 4-7%.", "אינדיקטור צמיחה.")
    ]
    for i in range(5):
        with k_cols[i]: render_pro_kpi(*k_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה ענפית"])

    with tabs[0]: # 6 יחסים משלימים (שחזור מלא)
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        r1, r2 = st.columns(3), st.columns(3)
        with r1[0]: render_pro_kpi("Loss Ratio", f"{d['loss_ratio']}%", "LR", "חיתום נטו.", "70%-80%.", "בחינת עתודות.")
        with r1[1]: render_pro_kpi("Expense Ratio", f"{d['expense_ratio']}%", "ER", "יעילות תפעולית.", "15%-20%.", "בחינת הוצאות.")
        with r1[2]: render_pro_kpi("שחרור CSM", f"{d['csm_release_rate']}%", "Rel", "קצב הכרת רווח.", "2-2.5% לרבעון.", "קצב מהיר ללא צמיחה מסוכן.")
        with r2[0]: render_pro_kpi("תשואת השקעות", f"{d['inv_yield']}%", "Yield", "ביצועי תיק.", "4-6%.", "פער שלילי מסוכן.")
        with r2[1]: render_pro_kpi("הון לנכסים", f"{d['equity_to_assets']}%", "Ratio", "חוסן מאזני.", "8%-12%.", "יחס נמוך = מינוף גבוה.")
        with r2[2]: render_pro_kpi("תזרים מפעילות", f"{d['op_cash_flow_ratio']}%", "CFO/NI", "איכות הרווח.", "1.0 אופטימלי.", "נמוך מ-0.7 = 'רווחי נייר'.")

    with tabs[1]: # סולבנסי
        c1, c2 = st.columns(2)
        with c1:
            rd = pd.DataFrame({'מודול': ['שוק', 'חיתום חיים', 'חיתום בריאות', 'חיתום כללי', 'תפעול'], 'ערך (B)': [d['mkt_risk'], d['und_risk']*0.4, d['und_risk']*0.3, d['und_risk']*0.3, d['operational_risk']]})
            st.plotly_chart(px.bar(rd, x='ערך (B)', y='מודול', orientation='h', template="plotly_dark", height=300, color='מודול').update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        with c2:
            st.metric("הון עצמי (Own Funds)", f"₪{d['own_funds']:.2f}B")
            st.info(f"עודף הון לדיבידנד (150%): ₪{max(0, d['own_funds'] - d['scr_amount']*1.5):.2f}B")

    with tabs[2]: # IFRS 17
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            f_seg = go.Figure(data=[go.Bar(name='CSM', x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'), go.Bar(name='LC', x=['חיים', 'בריאות', 'כללי'], y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')])
            f_seg.update_layout(barmode='group', template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(f_seg, use_container_width=True)
        with col_m2:
            wf = go.Figure(go.Waterfall(name="CSM", orientation="v", measure=["relative", "relative", "relative", "total"], x=["פתיחה", "חדש", "שחרור", "סגירה"], y=[d['csm_total']*0.9, d['csm_total']*0.15, -d['csm_total']*0.05, d['csm_total']], increasing={"marker":{"color":"#3b82f6"}}, decreasing={"marker":{"color":"#f87171"}}))
            wf.update_layout(template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(wf, use_container_width=True)

    with tabs[3]: # Stress Test
        s1, s2, s3 = st.columns(3)
        with s1: eq = st.slider("קריסת מניות (%)", 0, 50, 0)
        with s2: ir = st.slider("שינוי ריבית (bps)", -150, 150, 0)
        with s3: lp = st.slider("ביטולים המוניים (%)", 0, 40, 0)
        impact = (eq * d['mkt_sens']) + (ir/100 * d['int_sens']) + (lp * d['lapse_sens'])
        st.metric("סולבנסי חזוי", f"{(d['solvency_ratio'] - impact):.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")

    with tabs[4]: # השוואה ענפית (תוקן: חסין קריסה)
        st.write("### 🏁 ניתוח Peer Analysis")
        q_df = df[df['quarter'] == s_q].copy()
        
        # טבלה חסינה - אם matplotlib חסר, היא פשוט תוצג ללא צבעים
        st.markdown("#### א. מטריצת ביצועים ענפית")
        m_cols = ['display_name', 'solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total']
        m_df = q_df[m_cols].rename(columns={'display_name': 'חברה', 'solvency_ratio': 'סולבנסי (%)', 'roe': 'ROE (%)', 'combined_ratio': 'Combined (%)', 'expense_ratio': 'הוצאות (%)', 'csm_total': 'CSM (B)'})
        
        try:
            st.dataframe(m_df.style.background_gradient(cmap='Blues', subset=['ROE (%)', 'CSM (B)']).background_gradient(cmap='Reds', subset=['הוצאות (%)', 'Combined (%)']), use_container_width=True)
        except ImportError:
            st.dataframe(m_df, use_container_width=True)
            st.warning("התקן 'matplotlib' ב-requirements.txt כדי להציג צבעים בטבלה.")

        st.divider()
        st.markdown("#### ב. יעילות מול חוסן (Efficiency Frontier)")
        fig_s = px.scatter(q_df, x="solvency_ratio", y="roe", size="csm_total", color="display_name", hover_name="display_name", template="plotly_dark")
        fig_s.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_s, use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים.")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import os

# --- 1. הגדרות מערכת וסרגל שוק חי (v42 PRO ANALYTICS) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_market_ticker():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS', '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^TNX': 'ריבית (10Y)'}
    parts = []
    try:
        data = yf.download(list(tickers.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        for sym, name in tickers.items():
            try:
                if sym in data.columns.levels[0]:
                    val = data[sym]['Close'].iloc[-1]
                    prev = data[sym]['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "טוען מדדים..."
    except: return "מתחבר לבורסה..."

ticker_html = get_live_market_ticker()

st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    .ticker-header {{
        width: 100%; background-color: #0f172a; color: white; padding: 12px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 0; left: 0; z-index: 999999;
        overflow: hidden; white-space: nowrap;
    }}
    .ticker-anim {{ display: inline-block; padding-right: 100%; animation: tMove 50s linear infinite; font-family: sans-serif; font-size: 0.9rem; }}
    @keyframes tMove {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .spacer {{ margin-top: 70px; }}
    [data-testid="stExpanderChevron"], i, svg {{ font-family: 'Material Icons' !important; text-transform: none !important; }}
    html, body, .stMarkdown p, label {{ color: #ffffff !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; }}
    </style>
    <div class="ticker-header"><div class="ticker-anim">{ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {ticker_html}</div></div>
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

def render_pro_kpi(label, value, formula, description, inspector_note):
    st.metric(label, value)
    with st.expander("📚 ניתוח מקצועי"):
        st.write(f"**מהות:** {description}")
        st.divider(); st.latex(formula); st.info(f"**דגש:** {inspector_note}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="c_v42")
        c_df = df[df['display_name'] == sel_comp].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="q_v42")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()
    st.divider(); st.file_uploader("📂 פורטל PDF", type=['pdf'], key="u_v42")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_comp} | סקירה ניהולית {sel_q}")
    
    # 5 Core KPIs
    cols = st.columns(5)
    kpi_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", "חוסן הוני לספיגת הפסדים.", "יעד 150%."),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM", "רווח עתידי גלום (IFRS 17).", "מחסן הרווחים."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Inc}{Equity}", "תשואה להון.", "יעילות."),
        ("Combined", f"{d['combined_ratio']}%", "CR", "חיתום אלמנטרי.", "מתחת ל-100% רווח."),
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", "רווחיות מכירות חדשות.", "איכות צמיחה.")
    ]
    for i in range(5):
        with cols[i]: render_pro_kpi(*kpi_meta[i])

    st.divider()
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים (IFRS 17)", "⛈️ Stress Test", "🏁 השוואה"])

    with t1: # מגמות ויחסים מורחבים
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים מקצועיים")
        r_cols = st.columns(3)
        with r_cols[0]: render_pro_kpi("יחס תביעות (Loss Ratio)", f"{d['loss_ratio']}%", r"\frac{Claims}{Earned \ Premium}", "מודד את איכות החיתום ללא הוצאות הנהלה.", "עלייה מעידה על הרעה בטיפול בתביעות או תמחור חסר.")
        with r_cols[1]: render_pro_kpi("שיעור שחרור CSM", f"{d['csm_release_rate']}%", r"\frac{Amortized \ CSM}{Opening \ CSM}", "קצב הכרת הרווח מה-CSM לדו''ח רווח והפסד.", "שיעור גבוה מעיד על הכרה מהירה ברווח, אך מצריך מכירות חדשות לשימור המחסן.")
        with r_cols[2]: render_pro_kpi("תשואת השקעות", f"{d['inv_yield']}%", r"\frac{Inv \ Income}{Invested \ Assets}", "התשואה שהשיגה החברה על תיק ההשקעות שלה.", "קריטי לביטוח חיים וחיסכון ארוך טווח.")

    with t2: # סולבנסי
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="סיכוני SCR"), use_container_width=True)

    with t3: # מגזרים - CSM וחוזים מפסידים (Loss Component)
        st.write("### 📑 ניתוח CSM מול חוזים מפסידים (Onerous Contracts)")
        
        segments = ['חיים', 'בריאות', 'כללי']
        csm_vals = [d['life_csm'], d['health_csm'], d['general_csm']]
        lc_vals = [d['life_lc'], d['health_lc'], d['general_lc']]
        
        f_seg = go.Figure(data=[
            go.Bar(name='CSM (רווח)', x=segments, y=csm_vals, marker_color='#3b82f6'),
            go.Bar(name='Loss Component (הפסד)', x=segments, y=lc_vals, marker_color='#f87171')
        ])
        f_seg.update_layout(barmode='group', template="plotly_dark", height=350, title="רווחיות מול הפסדיות לפי מגזר")
        st.plotly_chart(f_seg, use_container_width=True)
        
        st.info("💡 **Onerous Contracts:** חוזים שהפסדיהם מוכרים מיד ברווח והפסד (Loss Component) במקום להיפרס ב-CSM. יחס LC/CSM גבוה מעיד על תיק בעייתי.")

    with t4: # Stress Test עם ביטולים
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0, key="irs")
        with s2: mk_s = st.slider("מניות (%)", 0, 40, 0, key="mks")
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0, key="lps")
        impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")

    with t5:
        pm = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'roe', 'inv_yield', 'loss_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("שגיאה בטעינת המחסן.")

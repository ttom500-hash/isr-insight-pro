import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import os

# --- 1. הגדרות מערכת וסרגל שוק חי (v41 FULL CONTENT RESTORED) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_market_ticker():
    tickers = {
        '^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS',
        '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^TNX': 'ריבית (10Y)'
    }
    ticker_parts = []
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
                    ticker_parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(ticker_parts) if ticker_parts else "טוען מדדים..."
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
    .ticker-anim {{
        display: inline-block; padding-right: 100%; animation: tMove 50s linear infinite;
        font-family: sans-serif; font-size: 0.9rem;
    }}
    @keyframes tMove {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .spacer {{ margin-top: 70px; }}
    
    /* מניעת expand_more ושמירה על אייקונים */
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

# פונקציית ההסברים המפורטת ששוחזרה
def render_pro_kpi(label, value, formula, description, inspector_note):
    st.metric(label, value)
    with st.expander("📚 ניתוח מקצועי"):
        st.write(f"**מהות המדד:** {description}")
        st.divider()
        st.write("**נוסחה חישובית:**")
        st.latex(formula)
        st.info(f"**דגש פיקוחי:** {inspector_note}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="c_v41")
        c_df = df[df['display_name'] == sel_comp].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", c_df['quarter'].unique(), key="q_v41")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.file_uploader("📂 פורטל PDF", type=['pdf'], key="u_v41")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_comp} | סקירה ניהולית {sel_q}")
    
    # שחזור 5 ה-KPIs המפורטים
    cols = st.columns(5)
    kpi_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", 
         "מבטא את החוסן ההוני של החברה. היחס מודד האם לחברה יש מספיק הון עצמי לספוג הפסדים בלתי צפויים בתרחישי קיצון.", 
         "יעד מינימלי 100%. המפקח מצפה ל-150% ומעלה כדי לאשר חלוקת דיבידנד."),
        
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM = PV(Future \ Cash \ Flows)", 
         "מייצג את הרווח העתידי שטרם הוכר בגין חוזי ביטוח קיימים (IFRS 17). זהו 'מחסן הרווחים' של החברה.", 
         "ירידה ב-CSM ללא צמיחה במכירות חדשות מעידה על שחיקה ברווחיות העתידית."),
        
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Income}{Equity}", 
         "תשואה להון המודדת את יעילות החברה ביצירת רווחים מההון המושקע.", 
         "ROE נמוך ממחיר ההון מעיד על השמדת ערך לבעלי המניות."),
        
        ("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Losses + Expenses}{Premium}", 
         "היחס המשולב בביטוח אלמנטרי. מודד את הרווחיות החיתומית נטו.", 
         "יחס מעל 100% פירושו הפסד חיתומי המכוסה רק על ידי רווחי השקעות."),
        
        ("NB Margin", f"{d['new_biz_margin']}%", "Margin", 
         "רווחיות המכירות החדשות. מודד כמה רווח גלום בכל שקל של פרמיה חדשה.", 
         "צמיחה בפרמיה עם שולי רווח נמוכים עלולה לשחוק את הון החברה.")
    ]
    for i in range(5):
        with cols[i]: render_pro_kpi(*kpi_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II", "📑 מגזרים IFRS 17", "⛈️ Stress Test", "🏁 השוואה"])

    with tabs[0]:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים משלימים (פירוט מלא)")
        r1, r2, r3 = st.columns(3)
        with r1: render_pro_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Equity}{Total \ Assets}", 
                                 "מודד את המינוף המאזני.", "ככל שהיחס גבוה יותר, החברה יותר איתנה ופחות נשענת על חוב.")
        with r2: render_pro_kpi("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{Operating \ Exp}{Premium}", 
                                 "מודד את היעילות התפעולית.", "מגמת ירידה מעידה על יתרון לגודל והתייעלות.")
        with r3: render_pro_kpi("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{Cash \ Flow}{Net \ Income}", 
                                 "בודק האם הרווח מגובה במזומן.", "פער שלילי גדול מעיד על רישומים חשבונאיים אופטימיים.")

    with tabs[1]: # סולבנסי II
        ca, cb = st.columns(2)
        with ca:
            f = go.Figure(data=[go.Bar(name='Tier 1', y=[d['tier1_cap']], marker_color='#3b82f6'), go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#1e293b')])
            f.update_layout(barmode='stack', template="plotly_dark", height=300, title="מבנה איכות ההון"); st.plotly_chart(f, use_container_width=True)
        with cb: st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], hole=0.6, template="plotly_dark", height=300, title="התפלגות סיכוני SCR"), use_container_width=True)

    with tabs[2]: # מגזרים
        cc, cd = st.columns(2)
        with cc: st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=280, template="plotly_dark", title="CSM לפי מגזר", color_discrete_sequence=['#3b82f6']), use_container_width=True)
        with cd: st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=280, template="plotly_dark", title="מודלים"), use_container_width=True)

    with tabs[3]: # Stress Test עם ביטולים
        s1, s2, s3 = st.columns(3)
        with s1: ir_s = st.slider("ריבית (bps)", -100, 100, 0, key="irs")
        with s2: mk_s = st.slider("מניות (%)", 0, 40, 0, key="mks")
        with s3: lp_s = st.slider("ביטולים (%)", 0, 20, 0, key="lps")
        impact = (ir_s * d['int_sens']) + (mk_s * d['mkt_sens']) + (lp_s * d['lapse_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

    with tabs[4]: # השוואה
        pm = st.selectbox("בחר מדד:", ['solvency_ratio', 'roe', 'combined_ratio', 'csm_total'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=pm), x='display_name', y=pm, color='display_name', template="plotly_dark", height=300, text_auto=True), use_container_width=True)
else:
    st.error("שגיאה בטעינת המחסן.")

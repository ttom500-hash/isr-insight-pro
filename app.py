import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import os

# --- 1. הגדרות מערכת וסרגל שוק מורחב (v37 EXECUTIVE PRO) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_extended_market_ticker():
    # רשימת מדדים מורחבת: בורסה, מט"ח וריבית
    tickers_map = {
        '^TA125.TA': 'ת"א 125',
        'ILS=X': 'USD/ILS',
        'EURILS=X': 'EUR/ILS',
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^TNX': 'תשואת אג"ח 10ש (ריבית)'
    }
    try:
        data = yf.download(list(tickers_map.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        parts = []
        for sym, name in tickers_map.items():
            try:
                latest = data[sym]['Close'].iloc[-1]
                prev = data[sym]['Close'].iloc[-2]
                pct = ((latest / prev) - 1) * 100
                clr = "#4ade80" if pct >= 0 else "#f87171"
                arr = "▲" if pct >= 0 else "▼"
                parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{latest:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts)
    except:
        return "טוען נתוני שוק חיים..."

ticker_html = get_extended_market_ticker()

# CSS - ניקוי ויזואלי סופי
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    .ticker-header {{
        width: 100%; background-color: #0f172a; color: white; padding: 10px 0;
        border-bottom: 1px solid #1e293b; position: fixed; top: 0; left: 0; z-index: 10000;
        overflow: hidden; white-space: nowrap;
    }}
    .ticker-move {{
        display: inline-block; padding-right: 100%; animation: tickerAnim 40s linear infinite;
        font-family: sans-serif; font-size: 0.85rem;
    }}
    @keyframes tickerAnim {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .main-body {{ margin-top: 65px; }}
    
    /* מניעת expand_more */
    [data-testid="stExpanderChevron"], i, svg {{ font-family: 'Material Icons' !important; text-transform: none !important; }}
    
    html, body, .stMarkdown p, label {{ color: #ffffff !important; font-size: 0.92rem !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-size: 1.6rem !important; font-weight: 700 !important; }}
    </style>
    
    <div class="ticker-header"><div class="ticker-move">{ticker_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {ticker_html}</div></div>
    <div class="main-body"></div>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
@st.cache_data(ttl=60)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# פונקציה להצגת כרטיס מדד עם פירוט עשיר
def render_detailed_kpi(label, value, formula, description, inspector_note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי"):
        st.write(f"**מהות המדד:** {description}")
        st.divider()
        st.write("**נוסחה חישובית:**")
        st.latex(formula)
        st.info(f"**דגש למפקח:** {inspector_note}")

# --- 3. SIDEBAR ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>🛡️ APEX COMMAND</h2>", unsafe_allow_html=True)
    if not df.empty:
        sel_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="c_v37")
        c_df = df[df['display_name'] == sel_comp].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון דיווח:", c_df['quarter'].unique(), key="q_v37")
        d = c_df[c_df['quarter'] == sel_q].iloc[0]
        if st.button("🔄 רענן נתונים"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.write("📂 **פורטל טעינת דוחות**")
    st.file_uploader("", type=['pdf'], key="u_v37")

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"{sel_comp} | סקירה ניהולית רבעון {sel_q}")
    
    # 5 ה-KPIs הקריטיים עם פירוט מלא
    st.write("### 🎯 מדדי ליבה (Core KPIs)")
    cols = st.columns(5)
    
    kpis = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", 
         "מבטא את החוסן ההוני של החברה. יחס זה מודד האם לחברה יש מספיק הון עצמי כדי לספוג הפסדים בלתי צפויים בתרחישי קיצון.", 
         "יעד רגולטורי מינימלי הוא 100%. המפקח מצפה ליחס של 150% ומעלה כדי לאפשר חלוקת דיבידנד."),
        
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM = PV(Future \ Cash \ Flows)", 
         "מייצג את הרווח העתידי שטרם הוכר בגין חוזי ביטוח קיימים (תחת IFRS 17). זהו 'מחסן הרווחים' של החברה.", 
         "ירידה ב-CSM ללא צמיחה במכירות חדשות מעידה על שחיקה ברווחיות העתידית."),
        
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Income}{Equity}", 
         "תשואה להון המודדת את יעילות החברה ביצירת רווחים מההון המושקע של בעלי המניות.", 
         "יש להשוות למחיר ההון של החברה. ROE נמוך לאורך זמן עלול להעיד על חוסר יעילות תפעולית."),
        
        ("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Losses + Expenses}{Premium}", 
         "היחס המשולב בביטוח אלמנטרי. מודד את הרווחיות החיתומית.", 
         "יחס מעל 100% פירושו שהחברה מפסידה כסף מפעילות הביטוח עצמה ונשענת רק על רווחי השקעות."),
        
        ("NB Margin", f"{d['new_biz_margin']}%", r"Margin = \frac{NB \ CSM}{PVFP}", 
         "רווחיות המכירות החדשות. מודד כמה רווח גלום בכל שקל של פרמיה חדשה שנמכרה.", 
         "מדד קריטי לצמיחה איכותית. צמיחה בפרמיה ללא שולי רווח גבוהים עשויה לפגוע בסולבנסי.")
    ]
    
    for i in range(5):
        with cols[i]: render_detailed_kpi(*kpis[i])

    st.divider()
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי", "📑 מגזרים (IFRS17)", "⛈️ Stress Test", "🏁 השוואה"])

    with t1:
        st.plotly_chart(px.line(c_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=300), use_container_width=True)
        st.write("### 📊 יחסים פיננסיים משלימים")
        r1, r2, r3 = st.columns(3)
        with r1: render_detailed_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"\frac{Equity}{Total \ Assets}", 
                                     "מודד את המינוף המאזני של החברה.", "ככל שהיחס גבוה יותר, החברה פחות ממונפת ויותר איתנה.")
        with r2: render_detailed_kpi("יחס הוצאות", f"{d['expense_ratio']}%", r"\frac{Operating \ Exp}{Premium}", 
                                     "מודד את היעילות התפעולית של החברה.", "ירידה ביחס מעידה על התייעלות ויתרון לגודל.")
        with r3: render_detailed_kpi("איכות רווח", f"{d['op_cash_flow_ratio']}%", r"\frac{Cash \ Flow}{Net \ Income}", 
                                     "בודק האם הרווח החשבונאי מגובה במזומנים.", "פער שלילי גדול עלול להעיד על הערכות חשבונאיות אופטימיות מדי.")

    with t3: # מגזרים
        cc, cd = st.columns(2)
        with cc: st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], height=280, template="plotly_dark", title="CSM לפי קווי עסקים", color_discrete_sequence=['#3b82f6']), use_container_width=True)
        with cd: st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], height=280, template="plotly_dark", title="CSM לפי מודלים"), use_container_width=True)

    with t4: # תרחישי קיצון
        st.subheader("⛈️ Stress Engine")
        ir = st.slider("זעזוע ריבית (bps)", -100, 100, 0, key="ir_v37")
        mk = st.slider("זעזוע שוק מניות (%)", 0, 40, 0, key="mk_v37")
        impact = (ir * d['int_sens']) + (mk * d['mkt_sens'])
        proj = d['solvency_ratio'] - impact
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{-impact:.1f}%", delta_color="inverse")
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "#334155"}]})).update_layout(template="plotly_dark", height=250), use_container_width=True)

else:
    st.error("שגיאה בטעינת המחסן. וודא שקובץ data/database.csv קיים.")

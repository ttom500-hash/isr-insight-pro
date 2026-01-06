import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time

# --- 1. הגדרת עמוד (חייב להיות ראשון) ---
st.set_page_config(page_title="ISR-TITAN FINAL", layout="wide", page_icon="🏛️")

# --- 2. טיפול בשגיאות יבוא (Safety Check) ---
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

# --- 3. עיצוב CSS אגרסיבי (תיקון הצבעים) ---
def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
        
        /* רקע כללי */
        .stApp {
            background-color: #0e1117;
            font-family: 'Assistant', sans-serif;
        }
        
        /* טקסטים - הכל לבן */
        h1, h2, h3, h4, p, label, span, div {
            color: #ffffff !important;
            text-align: right;
        }
        
        /* --- תיקון קריטי לתיבת החיפוש (Selectbox) --- */
        /* הרקע של התיבה */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 2px solid #00d4ff !important;
        }
        /* הטקסט בתוך התיבה */
        div[data-baseweb="select"] div {
            color: #000000 !important;
            font-weight: bold;
        }
        /* התפריט שנפתח */
        ul[data-baseweb="menu"] {
            background-color: #ffffff !important;
        }
        ul[data-baseweb="menu"] li {
            color: #000000 !important;
            background-color: #ffffff !important;
        }
        /* ----------------------------------------------- */

        /* כרטיסי KPI */
        .metric-card {
            background-color: #1f2937;
            border: 1px solid #374151;
            padding: 15px;
            border-radius: 8px;
            border-right: 5px solid #00d4ff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 10px;
        }
        .metric-val { font-size: 1.8rem; font-weight: 800; color: #ffffff !important; }
        .metric-lbl { font-size: 0.85rem; color: #9ca3af !important; }
        
        /* טבלאות */
        div[data-testid="stDataFrame"] { background-color: #1f2937; border: 1px solid #374151; }
        
        /* סרגל צד */
        section[data-testid="stSidebar"] { background-color: #111827; border-left: 1px solid #374151; }
        
        /* סליידרים */
        .stSlider > div > div > div > div { background-color: #00d4ff; }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==========================================
# 4. לוגיקה עסקית ונתונים
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA", "ביטוח ישיר": "DIDI.TA",
    "איילון אחזקות": "AYAL.TA", "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE"
}

@st.cache_data
def get_company_data(name):
    # נתונים גנריים למקרה של כשל
    equity = 5000000000
    market_cap = 4000000000
    change = 0.0
    source = "Model"
    
    # ניסיון להביא נתונים אמיתיים
    symbol = TICKERS.get(name)
    if YF_AVAILABLE and symbol != "PRIVATE":
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if 'marketCap' in info:
                market_cap = info['marketCap']
                equity = market_cap / info.get('priceToBook', 0.85)
                source = "Live API"
        except:
            pass # Fallback שקט

    # בניית מודל אקטוארי
    np.random.seed(abs(hash(name)) % (2**32))
    
    # מאזן
    assets = equity * np.random.uniform(7.5, 9.0)
    liabilities = assets - equity
    
    # IFRS 17 CSM
    csm_opening = equity * 0.45
    csm_new = csm_opening * 0.1
    csm_interest = csm_opening * 0.03
    csm_release = csm_opening * -0.08
    csm_closing = csm_opening + csm_new + csm_interest + csm_release
    
    # תזרימים (P&L Inputs)
    gwp = assets * 0.15
    nwp = gwp * 0.85
    claims = nwp * 0.72
    expenses = nwp * 0.24
    
    # מגזרים
    segments = {
        "כללי (P&C)": csm_closing * 0.15,
        "בריאות": csm_closing * 0.30,
        "חיסכון ופנסיה": csm_closing * 0.55
    }
    
    return {
        "equity": equity, "assets": assets, "liabilities": liabilities,
        "market_cap": market_cap, "source": source,
        "csm": {"open": csm_opening, "new": csm_new, "int": csm_interest, "rel": csm_release, "close": csm_closing},
        "pnl": {"nwp": nwp, "claims": claims, "expenses": expenses, "gwp": gwp},
        "segments": segments,
        "base_scr": equity * 0.75
    }

def calculate_scenario(data, shocks, factor):
    # 1. השפעת שוק
    eq_shock = data['equity'] * (shocks['equity']/100) * 0.6
    final_equity = data['equity'] - eq_shock
    
    # 2. השפעת ריבית
    liab_shock = data['liabilities'] * (shocks['interest']/100) * -6.0
    
    # 3. השפעת ביטולים
    lapse_shock = data['csm']['close'] * (shocks['lapse']/100)
    final_csm = data['csm']['close'] - lapse_shock
    
    # 4. Solvency II
    own_funds = final_equity + (final_csm * 0.7)
    if shocks['cat']: own_funds -= 400000000
    
    scr = data['base_scr'] + (liab_shock * 0.5)
    scr = max(1, scr)
    solvency = (own_funds / scr) * 100
    
    # 5. יחסים פיננסיים
    cat_loss = 350000000 if shocks['cat'] else 0
    final_claims = data['pnl']['claims'] + cat_loss
    
    uw_profit = (data['pnl']['nwp']*factor) - (final_claims*factor) - (data['pnl']['expenses']*factor)
    inv_profit = (data['assets']*0.04*factor) - (eq_shock*0.1)
    net_income = uw_profit + inv_profit
    
    combined = ((final_claims + data['pnl']['expenses']) / data['pnl']['nwp']) * 100
    loss_r = (final_claims / data['pnl']['nwp']) * 100
    exp_r = (data['pnl']['expenses'] / data['pnl']['nwp']) * 100
    retention = (data['pnl']['nwp'] / data['pnl']['gwp']) * 100
    leverage = (data['assets'] - eq_shock) / final_equity
    roe = (net_income / final_equity) * 100 * (1/factor)
    
    return {
        "Equity": final_equity, "Solvency": solvency, "CSM": final_csm,
        "Net_Income": net_income, "Combined": combined, "Loss_R": loss_r,
        "Exp_R": exp_r, "Retention": retention, "Leverage": leverage, "ROE": roe,
        "Lapse_Impact": lapse_shock
    }

# ==========================================
# 5. ממשק משתמש (UI)
# ==========================================

# סרגל צד
with st.sidebar:
    st.header("🎛️ חדר בקרה")
    st.info("הגדרות רגולציה וסימולציה")
    
    per = st.radio("תקופה:", ["שנתי", "רבעוני"])
    factor = 0.25 if per == "רבעוני" else 1.0
    
    st.markdown("---")
    s_eq = st.slider("📉 נפילת שוק (%)", 0, 50, 0)
    s_int = st.slider("🏦 שינוי ריבית (%)", -2.0, 2.0, 0.0, step=0.1)
    s_lap = st.slider("🏃 ביטולים (%)", 0, 40, 0)
    s_cat = st.checkbox("🌪️ קטסטרופה")
    
    shocks = {'equity': s_eq, 'interest': s_int, 'lapse': s_lap, 'cat': s_cat}
    
    if st.button("🔄 אפס"):
        st.rerun()

# כותרת ראשית
c1, c2 = st.columns([3,1])
with c1:
    st.title("ISR-TITAN REGULATOR")
    st.caption("מערכת תומכת החלטה | IFRS 17 & Solvency II")
with c2:
    mode = "STRESS MODE" if (s_eq > 0 or s_cat) else "LIVE MODE"
    color = "#ff4b4b" if (s_eq > 0 or s_cat) else "#00ff9d"
    st.markdown(f"""
    <div style="border:1px solid {color}; padding:10px; border-radius:8px; text-align:center; color:{color}; font-weight:bold;">
        {mode}<br>{datetime.now().strftime('%H:%M')}
    </div>""", unsafe_allow_html=True)

st.divider()

# תיבת חיפוש (המתוקנת)
comp_name = st.selectbox("בחר חברה:", list(TICKERS.keys()))

# חישובים
base_data = get_company_data(comp_name)
sim_res = calculate_scenario(base_data, shocks, factor)

def fmt(v): return f"₪{v/1e9:.2f}B" if v >= 1e9 else f"₪{v/1e6:.0f}M"

# --- KPIs ---
k1, k2, k3, k4 = st.columns(4)

def kpi(col, title, val, sub):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">{title}</div>
        <div class="metric-val">{val}</div>
        <div style="font-size:0.8rem; color:#9ca3af;">{sub}</div>
    </div>""", unsafe_allow_html=True)

kpi(k1, "הון עצמי (Equity)", fmt(sim_res['Equity']), f"Source: {base_data['source']}")
kpi(k2, "יחס סולבנסי", f"{sim_res['Solvency']:.1f}%", "Target: >100%")
kpi(k3, "רווח גלום (CSM)", fmt(sim_res['CSM']), "Future Value")
kpi(k4, "רווח נקי", fmt(sim_res['Net_Income']), f"ROE: {sim_res['ROE']:.1f}%")

# --- יחסים פיננסיים ---
st.markdown("### 📈 יחסים פיננסיים")
r1, r2, r3, r4, r5 = st.columns(5)
r1.metric("Combined Ratio", f"{sim_res['Combined']:.1f}%", delta=None)
r2.metric("Loss Ratio", f"{sim_res['Loss_R']:.1f}%")
r3.metric("Expense Ratio", f"{sim_res['Exp_R']:.1f}%")
r4.metric("Retention", f"{sim_res['Retention']:.1f}%")
r5.metric("Leverage", f"{sim_res['Leverage']:.1f}x")

st.markdown("---")

# --- גרפים ---
t1, t2 = st.tabs(["🧬 ניתוח CSM", "⚖️ מאזן ודוחות"])

with t1:
    c_l, c_r = st.columns([2, 1])
    with c_l:
        st.markdown("#### גשר CSM")
        c = base_data['csm']
        fig = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v", measure = ["relative", "relative", "relative", "relative", "relative", "total"],
            x = ["פתיחה", "חדש", "ריבית", "שחרור", "השפעת סטרס", "סגירה"],
            textposition = "outside",
            y = [c['open'], c['new'], c['int'], c['rel'], -sim_res['Lapse_Impact'], 0],
            connector = {"line":{"color":"white"}}
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with c_r:
        st.markdown("#### פילוח מגזרי")
        segs = base_data['segments']
        fig_pie = px.pie(names=list(segs.keys()), values=list(segs.values()), hole=0.4)
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

with t2:
    st.markdown("#### תמונת מאזן")
    df_b = pd.DataFrame({
        "פריט": ["נכסים", "התחייבויות", "הון עצמי"],
        "ערך": [sim_res['Equity'] + base_data['liabilities'], base_data['liabilities'], sim_res['Equity']]
    })
    st.bar_chart(df_b.set_index("פריט"), color="#00d4ff")
    
    st.markdown("#### ייצוא נתונים")
    df_ex = pd.DataFrame([sim_res])
    st.dataframe(df_ex.T, use_container_width=True)

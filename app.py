import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. הגדרות מערכת ועיצוב (High Contrast & Black Input)
# ==========================================
st.set_page_config(page_title="ISR-TITAN REGULATOR", layout="wide", page_icon="⚖️")

def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
        
        /* 1. רקע כהה וטקסט לבן גלובלי */
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
            font-family: 'Heebo', sans-serif;
        }
        
        h1, h2, h3, h4, p, label, span, div {
            color: #ffffff;
            text-align: right;
        }
        
        /* 2. תיקון אגרסיבי לתיבת החיפוש - שחור על לבן */
        /* הרקע של התיבה עצמה */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 2px solid #00d4ff !important;
            color: #000000 !important;
        }
        /* הטקסט שנבחר בתוך התיבה */
        div[data-baseweb="select"] span {
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
        ul[data-baseweb="menu"] li:hover {
            background-color: #e0e0e0 !important;
        }
        /* ------------------------------------------- */

        /* 3. כרטיסי KPI */
        .metric-box {
            background-color: #1f2937;
            border: 1px solid #374151;
            padding: 20px;
            border-radius: 8px;
            border-right: 5px solid #00d4ff;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .metric-title { font-size: 0.85rem; color: #9ca3af !important; text-transform: uppercase; }
        .metric-value { font-size: 1.8rem; font-weight: 800; color: #ffffff !important; }
        .metric-sub { font-size: 0.8rem; color: #00d4ff !important; }

        /* 4. כרטיסי יחסים פיננסיים (קטנים) */
        .ratio-box {
            background-color: rgba(31, 41, 55, 0.7);
            border: 1px solid #374151;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
        }
        .ratio-val { font-size: 1.3rem; font-weight: bold; color: #00d4ff !important; }
        .ratio-lbl { font-size: 0.8rem; color: #d1d5db !important; }

        /* 5. טבלאות וטאבים */
        div[data-testid="stDataFrame"] { background-color: #1f2937; border: 1px solid #374151; }
        div[data-testid="stDataFrame"] * { color: #ffffff !important; background-color: #1f2937 !important; }
        
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { background-color: #1f2937; color: #9ca3af; border: 1px solid #374151; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #00d4ff; color: #000000 !important; font-weight: bold; }
        
        /* 6. סליידרים */
        .stSlider > div > div > div > div { background-color: #00d4ff !important; }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==========================================
# 2. מנוע נתונים מלא (Full Engine)
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA", "ביטוח ישיר": "DIDI.TA",
    "איילון אחזקות": "AYAL.TA", "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE", "ליברה": "LBRA.TA"
}

@st.cache_data(ttl=600)
def fetch_data(ticker_name):
    symbol = TICKERS[ticker_name]
    is_live = False
    
    # ברירות מחדל
    market_cap = 4000000000
    equity = 5000000000
    change_pct = 0.0
    
    # שאיבה מהבורסה
    if symbol != "PRIVATE":
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            if 'marketCap' in info and info['marketCap']:
                market_cap = info['marketCap']
                equity = market_cap / info.get('priceToBook', 0.85)
                if 'currentPrice' in info and 'previousClose' in info:
                    prev = info['previousClose']
                    if prev > 0:
                        change_pct = ((info['currentPrice'] - prev) / prev) * 100
                is_live = True
        except:
            pass # Fallback

    np.random.seed(abs(hash(ticker_name)) % (2**32))
    
    # מאזן בסיס
    assets = equity * np.random.uniform(7.5, 9.5)
    liabilities = assets - equity
    
    # רכיבי P&L
    gwp = assets * 0.15
    nwp = gwp * 0.85
    claims_base = nwp * 0.70
    expenses = nwp * 0.25
    
    # רכיבי IFRS 17 CSM
    csm_opening = equity * 0.45
    csm_new_biz = csm_opening * 0.10
    csm_interest = csm_opening * 0.03
    csm_release = csm_opening * -0.08
    csm_changes = csm_opening * 0.01
    csm_closing = csm_opening + csm_new_biz + csm_interest + csm_release + csm_changes
    
    segments = {
        "ביטוח כללי": csm_closing * 0.15,
        "בריאות": csm_closing * 0.30,
        "חיסכון ופנסיה": csm_closing * 0.55
    }

    return {
        "is_live": is_live,
        "market_cap": market_cap,
        "equity": equity,
        "assets": assets,
        "liabilities": liabilities,
        "change_pct": change_pct,
        "csm_data": {
            "opening": csm_opening, "new": csm_new_biz, "interest": csm_interest,
            "release": csm_release, "changes": csm_changes, "closing": csm_closing
        },
        "segments": segments,
        "pnl": {"nwp": nwp, "claims": claims_base, "expenses": expenses},
        "base_scr": equity * 0.75
    }

def run_simulation(data, shocks, period_factor):
    # 1. זעזוע שוק
    equity_impact = data['equity'] * (shocks['equity']/100.0) * 0.6
    final_equity = data['equity'] - equity_impact
    
    # 2. זעזוע ריבית
    liab_impact = data['liabilities'] * (shocks['interest']/100.0) * -6.0
    new_liabilities = data['liabilities'] + liab_impact
    
    # שמירת משוואת מאזן (Equity = Assets - Liabilities)
    # נכסים יורדים בגלל שוק ההון
    asset_drop = equity_impact
    new_assets = data['assets'] - asset_drop
    
    # הון סופי מתוקן לפי המאזן החדש
    final_equity = new_assets - new_liabilities
    
    # 3. זעזוע ביטולים
    lapse_impact = data['csm_data']['closing'] * (shocks['lapse']/100.0)
    final_csm = data['csm_data']['closing'] - lapse_impact
    
    # 4. Solvency II
    own_funds = final_equity + (final_csm * 0.7)
    if shocks['catastrophe']: own_funds -= 400000000
    
    scr = data['base_scr'] + (liab_impact * 0.5)
    scr = max(1, scr)
    solvency_ratio = (own_funds / scr) * 100
    
    # 5. P&L ו-Ratios
    cat_loss = 350000000 if shocks['catastrophe'] else 0
    final_claims = data['pnl']['claims'] + cat_loss
    
    underwriting_profit = (data['pnl']['nwp'] * period_factor) - (final_claims * period_factor) - (data['pnl']['expenses'] * period_factor)
    inv_profit = (data['assets'] * 0.04 * period_factor) - (equity_impact * 0.1) # הפסד מניות
    net_income = underwriting_profit + inv_profit
    
    combined_ratio = ((final_claims + data['pnl']['expenses']) / data['pnl']['nwp']) * 100
    loss_ratio = (final_claims / data['pnl']['nwp']) * 100
    expense_ratio = (data['pnl']['expenses'] / data['pnl']['nwp']) * 100
    
    # Leverage
    leverage = new_assets / max(1, final_equity)
    
    # ROE
    roe = (net_income / max(1, final_equity)) * 100 * (1/period_factor)
    
    return {
        "Equity": final_equity,
        "Solvency": solvency_ratio,
        "CSM_Final": final_csm,
        "Net_Income": net_income,
        "Combined_Ratio": combined_ratio,
        "Loss_Ratio": loss_ratio,
        "Expense_Ratio": expense_ratio,
        "Leverage": leverage,
        "ROE": roe,
        "Lapse_Impact": lapse_impact
    }

# ==========================================
# 3. ממשק משתמש (UI)
# ==========================================

# --- סרגל צד ---
with st.sidebar:
    st.header("🎛️ בקרת רגולטור")
    p_type = st.radio("", ["שנתי", "רבעוני"], horizontal=True)
    factor = 0.25 if p_type == "רבעוני" else 1.0
    
    st.divider()
    
    st.markdown("### 📉 תרחישי קיצון")
    s_eq = st.slider("נפילת מניות (%)", 0, 50, 0, format="-%d%%")
    s_int = st.slider("שינוי ריבית (%)", -2.0, 2.0, 0.0, step=0.1, format="%+.1f%%")
    s_lap = st.slider("ביטולים (%)", 0, 40, 0, format="-%d%%")
    s_cat = st.checkbox("אירוע קטסטרופה")
    
    if st.button("🔄 אפס הכל", type="primary"):
        st.rerun()
        
    shocks = {'equity': s_eq, 'interest': s_int, 'lapse': s_lap, 'catastrophe': s_cat}

# --- דף ראשי ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("ISR-TITAN REGULATOR")
    st.caption("מערכת ניתוח עומק למבטחים | IFRS 17 & Solvency II")
with c2:
    status = "STRESS MODE" if (s_eq > 0 or s_cat) else "LIVE MODE"
    color = "#ff4b4b" if (s_eq > 0 or s_cat) else "#00ff9d"
    st.markdown(f"""
    <div style="border:1px solid {color}; padding:10px; border-radius:8px; text-align:center; color:{color}; font-weight:bold;">
        {status}<br>{datetime.now().strftime('%H:%M')}
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- מנוע חיפוש (המתוקן) ---
comp = st.selectbox("בחר גוף מפוקח (Search):", list(TICKERS.keys()))

# הפעלת לוגיקה
base = fetch_data(comp)
sim = run_simulation(base, shocks, factor)

def fmt(v): return f"₪{v/1e9:.2f}B" if v >= 1e9 else f"₪{v/1e6:.0f}M"

# --- שורת KPIs ראשית ---
k1, k2, k3, k4 = st.columns(4)

def kpi_box(col, title, val, sub):
    col.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{val}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

kpi_box(k1, "הון עצמי (Equity)", fmt(sim['Equity']), f"שינוי יומי: {base['change_pct']:.2f}%")
kpi_box(k2, "יחס סולבנסי", f"{sim['Solvency']:.1f}%", "יעד רגולטורי: >100%")
kpi_box(k3, "רווח גלום (CSM)", fmt(sim['CSM_Final']), "IFRS 17 Stock")
kpi_box(k4, "רווח נקי", fmt(sim['Net_Income']), f"ROE: {sim['ROE']:.1f}%")

# --- יחסים פיננסיים (Ratios) ---
st.markdown("### 📈 יחסים פיננסיים")
r1, r2, r3, r4, r5 = st.columns(5)

def ratio_box(col, title, val, suffix):
    col.markdown(f"""
    <div class="ratio-box">
        <div class="ratio-lbl">{title}</div>
        <div class="ratio-val">{val:.1f}{suffix}</div>
    </div>
    """, unsafe_allow_html=True)

ratio_box(r1, "Combined Ratio", sim['Combined_Ratio'], "%")
ratio_box(r2, "Loss Ratio", sim['Loss_Ratio'], "%")
ratio_box(r3, "Expense Ratio", sim['Expense_Ratio'], "%")
ratio_box(r4, "Leverage", sim['Leverage'], "x")
ratio_box(r5, "Lapse Cost", sim['Lapse_Impact']/1e6, "M")

st.divider()

# --- גרפים וניתוח ---
t1, t2 = st.tabs(["🧬 ניתוח CSM ומגזרים", "⚖️ מאזן ודוחות"])

with t1:
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.markdown("#### גשר ה-CSM (Waterfall)")
        csm = base['csm_data']
        fig = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
            x = ["פתיחה", "חדש", "ריבית", "שחרור", "שינוי הנחות", "סטרס", "סגירה"],
            textposition = "outside",
            y = [csm['opening'], csm['new'], csm['interest'], csm['release'], csm['changes'], -sim['Lapse_Impact'], 0],
            connector = {"line":{"color":"white"}},
            decreasing = {"marker":{"color":"#ff4b4b"}}, increasing = {"marker":{"color":"#00ff9d"}}, totals = {"marker":{"color":"#00d4ff"}}
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with c_right:
        st.markdown("#### תרומה למגזר")
        fig_sun = px.sunburst(
            names=list(base['segments'].keys()), 
            parents=[""]*len(base['segments']), 
            values=list(base['segments'].values())
        )
        fig_sun.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_sun, use_container_width=True)

with t2:
    st.markdown("#### ניתוח מאזן (Assets vs Liabilities)")
    df_bal = pd.DataFrame({
        "פריט": ["נכסים", "התחייבויות", "הון עצמי"],
        "ערך": [sim['Equity']+base['liabilities'], base['liabilities'], sim['Equity']]
    })
    st.bar_chart(df_bal.set_index("פריט"), color="#00d4ff")
    
    st.markdown("#### ייצוא נתונים")
    df_exp = pd.DataFrame([sim])
    st.dataframe(df_exp.T, use_container_width=True)
    st.download_button("📥 הורד דוח CSV", df_exp.to_csv().encode('utf-8'), "report.csv", "text/csv")

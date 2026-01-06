import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. הגדרות מערכת ועיצוב (Regulator UI)
# ==========================================
st.set_page_config(page_title="ISR-TITAN PRO", layout="wide", page_icon="⚖️")

# הזרקת CSS לתיקון צבעים ותיבת חיפוש
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    
    /* איפוס כללי למצב כהה */
    .stApp { background-color: #0b0f19; color: #ffffff; font-family: 'Heebo', sans-serif; }
    h1, h2, h3, h4, p, span, label, div { color: #ffffff; text-align: right; }
    
    /* --- תיקון קריטי לתיבת החיפוש (Selectbox) --- */
    /* רקע לבן, מסגרת תכולה */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 2px solid #38bdf8 !important;
        color: #000000 !important;
    }
    /* טקסט שחור בתוך התיבה */
    div[data-baseweb="select"] span {
        color: #000000 !important;
        font-weight: 700;
    }
    /* התפריט שנפתח */
    ul[data-baseweb="menu"] { background-color: #ffffff !important; }
    ul[data-baseweb="menu"] li {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    /* ------------------------------------------- */

    /* כרטיסי KPI */
    .kpi-card {
        background-color: #151e2e;
        border: 1px solid #334155;
        border-right: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .kpi-val { font-size: 1.8rem; font-weight: 800; color: #ffffff; }
    .kpi-lbl { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; }
    .kpi-sub { font-size: 0.75rem; color: #38bdf8; }

    /* יחסים פיננסיים */
    .ratio-box {
        background: rgba(255,255,255,0.05);
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
    }
    .ratio-val { color: #38bdf8; font-weight: bold; font-size: 1.2rem; }
    .ratio-lbl { font-size: 0.8rem; color: #cbd5e0; }
    
    /* טבלאות וגרפים */
    div[data-testid="stDataFrame"] { background-color: #151e2e; border: 1px solid #334155; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #151e2e; color: #94a3b8; border: 1px solid #334155; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #38bdf8; color: #000000 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. נתונים ומנוע חישוב (Logic Engine)
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA", "ביטוח ישיר": "DIDI.TA",
    "איילון אחזקות": "AYAL.TA", "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE", "ליברה": "LBRA.TA"
}

@st.cache_data
def get_insurer_data(name):
    """ מייצר את נתוני הבסיס (חשבונאי + אקטוארי) """
    # ברירת מחדל
    equity = 5500000000.0
    source = "Model"
    
    # ניסיון שאיבה אמיתי (מוגן משגיאות)
    sym = TICKERS.get(name)
    if sym != "PRIVATE":
        try:
            import yfinance as yf
            info = yf.Ticker(sym).info
            if 'marketCap' in info:
                equity = info['marketCap'] / info.get('priceToBook', 0.9)
                source = "Hybrid API"
        except:
            pass

    # בניה סטוכסטית של המודל הפנימי
    np.random.seed(abs(hash(name)) % (2**32))
    
    assets = equity * np.random.uniform(7.5, 9.0)
    liabilities = assets - equity
    
    # גשר CSM
    csm_open = equity * 0.45
    csm_flows = {
        "open": csm_open,
        "new": csm_open * 0.12,
        "int": csm_open * 0.03,
        "rel": csm_open * -0.09,
        "var": csm_open * 0.01
    }
    csm_flows["close"] = sum(csm_flows.values())
    
    # P&L Base
    gwp = assets * 0.16
    nwp = gwp * 0.88
    pnl = {
        "nwp": nwp, "gwp": gwp,
        "claims": nwp * 0.70,
        "expenses": nwp * 0.24
    }
    
    # סגמנטים
    segments = {
        "כללי (P&C)": csm_flows["close"] * 0.15,
        "בריאות": csm_flows["close"] * 0.30,
        "חיסכון": csm_flows["close"] * 0.55
    }
    
    return {
        "equity": equity, "assets": assets, "liabilities": liabilities,
        "source": source, "csm": csm_flows, "pnl": pnl, "segments": segments,
        "base_scr": equity * 0.7
    }

def run_simulation(data, shocks, factor):
    """ מנוע הסימולציה עם חישובי סולבנסי וקמירות """
    # 1. Asset Shock (Equity Drop + Bond Convexity)
    eq_shock = data['assets'] * 0.15 * (shocks['eq']/100.0)
    
    # Bond Convexity approx
    dur, conv = 6.0, 50.0
    dy = shocks['int'] / 100.0
    bond_chg = (-dur * dy) + (0.5 * conv * (dy**2))
    bond_shock = data['assets'] * 0.85 * bond_chg
    
    total_asset_hit = eq_shock - bond_shock # bond_shock is negative if rates rise
    new_assets = data['assets'] - total_asset_hit
    
    # 2. Liability Shock (Convexity)
    l_dur, l_conv = 7.5, 65.0
    l_chg = (-l_dur * dy) + (0.5 * l_conv * (dy**2))
    new_liabs = data['liabilities'] * (1 + l_chg)
    
    # 3. CSM Shock (Lapse)
    lapse_hit = data['csm']['close'] * (shocks['lap']/100.0)
    new_csm = data['csm']['close'] - lapse_hit
    
    # 4. Solvency II Calculation
    new_equity = new_assets - new_liabs
    own_funds = new_equity + (new_csm * 0.7)
    if shocks['cat']: own_funds -= 400000000
    
    # Dynamic SCR (Capital Requirement increases with risk)
    scr = data['base_scr'] * (1 + abs(dy)*0.5 + (shocks['eq']/200.0))
    scr = max(1000, scr) # מניעת חלוקה ב-0
    solvency = (own_funds / scr) * 100
    
    # 5. P&L & Ratios
    cat_loss = 350000000 if shocks['cat'] else 0
    final_claims = data['pnl']['claims'] + cat_loss
    
    uw_res = (data['pnl']['nwp']*factor) - (final_claims*factor) - (data['pnl']['expenses']*factor)
    inv_res = (new_assets * 0.035 * factor) - (total_asset_hit * 0.15) # מימוש חלקי של הפסד הון
    net_income = uw_res + inv_res
    
    # Ratios
    combined = ((final_claims + data['pnl']['expenses']) / data['pnl']['nwp']) * 100
    loss_r = (final_claims / data['pnl']['nwp']) * 100
    exp_r = (data['pnl']['expenses'] / data['pnl']['nwp']) * 100
    retention = (data['pnl']['nwp'] / data['pnl']['gwp']) * 100
    leverage = new_assets / max(1, new_equity)
    roe = (net_income / max(1, new_equity)) * 100 * (1/factor)
    
    return {
        "Equity": new_equity, "Solvency": solvency, "CSM": new_csm, "Net": net_income,
        "Combined": combined, "Loss_R": loss_r, "Exp_R": exp_r,
        "Retention": retention, "Leverage": leverage, "ROE": roe,
        "Lapse_Hit": lapse_hit, "Assets": new_assets, "Liabilities": new_liabs
    }

# ==========================================
# 3. ממשק משתמש (UI)
# ==========================================

# Sidebar Controls
with st.sidebar:
    st.header("🎛️ חדר בקרה")
    per = st.radio("תקופה:", ["שנתי", "רבעוני"], horizontal=True)
    f = 0.25 if per == "רבעוני" else 1.0
    st.divider()
    s_eq = st.slider("📉 מניות (%)", 0, 50, 0)
    s_int = st.slider("🏦 ריבית (%)", -2.0, 2.0, 0.0, step=0.1)
    s_lap = st.slider("🏃 פדיונות (%)", 0, 40, 0)
    s_cat = st.checkbox("🌪️ קטסטרופה")
    if st.button("🔄 אפס נתונים", type="primary"): st.rerun()
    shocks = {'eq': s_eq, 'int': s_int, 'lap': s_lap, 'cat': s_cat}

# Main Header
c1, c2 = st.columns([3, 1])
with c1:
    st.title("ISR-TITAN PRO 🛡️")
    st.caption("מערכת ניהול סיכונים רגולטורית | IFRS 17 & Solvency II")
with c2:
    stress = any(shocks.values())
    bg = "#ef4444" if stress else "#10b981"
    st.markdown(f"""
    <div style='background:{bg}; padding:10px; border-radius:8px; text-align:center; font-weight:bold;'>
        {'STRESS MODE' if stress else 'LIVE MONITOR'}<br>{datetime.now().strftime('%H:%M')}
    </div>""", unsafe_allow_html=True)

st.divider()

# Search Box (The Fix)
comp_name = st.selectbox("בחר גוף מפוקח:", list(TICKERS.keys()))

# Run Calculation
base = get_insurer_data(comp_name)
sim = run_simulation(base, shocks, f)

def fmt(v): return f"₪{v/1e9:.2f}B" if abs(v) >= 1e9 else f"₪{v/1e6:.0f}M"

# Top KPIs
k1, k2, k3, k4 = st.columns(4)
def kpi(c, t, v, s):
    c.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-lbl'>{t}</div>
        <div class='kpi-val'>{v}</div>
        <div class='kpi-sub'>{s}</div>
    </div>""", unsafe_allow_html=True)

kpi(k1, "הון עצמי (Equity)", fmt(sim['Equity']), f"Leverage: {sim['Leverage']:.1f}x")
kpi(k2, "יחס סולבנסי", f"{sim['Solvency']:.1f}%", "Target: >100%")
kpi(k3, "ערך גלום (CSM)", fmt(sim['CSM']), "Future Profits")
kpi(k4, "רווח נקי", fmt(sim['Net']), f"ROE: {sim['ROE']:.1f}%")

# Ratios Grid
st.markdown("### 📊 יחסים פיננסיים")
r1, r2, r3, r4, r5 = st.columns(5)
def ratio(c, t, v):
    c.markdown(f"""<div class='ratio-box'><div class='ratio-lbl'>{t}</div><div class='ratio-val'>{v}</div></div>""", unsafe_allow_html=True)

ratio(r1, "Combined Ratio", f"{sim['Combined']:.1f}%")
ratio(r2, "Loss Ratio", f"{sim['Loss_R']:.1f}%")
ratio(r3, "Expense Ratio", f"{sim['Exp_R']:.1f}%")
ratio(r4, "Retention", f"{sim['Retention']:.1f}%")
ratio(r5, "Lapse Cost", fmt(sim['Lapse_Hit']))

st.divider()

# Charts Tabs
t1, t2 = st.tabs(["🧬 גשר CSM", "⚖️ מאזן"])

with t1:
    c_l, c_r = st.columns([2, 1])
    with c_l:
        st.markdown("#### גשר ה-CSM (Waterfall)")
        c = base['csm']
        fig = go.Figure(go.Waterfall(
            name="CSM", orientation="v",
            measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"],
            x=["פתיחה", "עסקים חדשים", "ריבית", "שחרור", "שינוי הנחות", "סטרס", "סגירה"],
            y=[c['open'], c['new'], c['int'], c['rel'], c['var'], -sim['Lapse_Hit'], 0],
            connector={"line":{"color":"#94a3b8"}},
            decreasing={"marker":{"color":"#ef4444"}}, increasing={"marker":{"color":"#10b981"}}, totals={"marker":{"color":"#38bdf8"}}
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with c_r:
        st.markdown("#### פילוח מגזרי")
        segs = base['segments']
        fig_pie = px.pie(names=list(segs.keys()), values=list(segs.values()), hole=0.4)
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

with t2:
    st.markdown("#### ניתוח מאזן (Assets vs Liabilities)")
    df_bal = pd.DataFrame({
        "פריט": ["נכסים", "התחייבויות", "הון עצמי"],
        "ערך": [sim['Assets'], sim['Liabilities'], sim['Equity']]
    })
    st.bar_chart(df_bal.set_index("פריט"), color="#38bdf8")
    
    st.markdown("#### ייצוא נתונים")
    df_ex = pd.DataFrame([sim]).T
    st.dataframe(df_ex, use_container_width=True)

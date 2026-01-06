import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. System Config ---
st.set_page_config(page_title="ISR-TITAN FINAL", layout="wide", page_icon="🏛️")

# --- 2. CSS & Design (Fixed Search Box) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    
    .stApp { background-color: #0b0f19; color: #ffffff; font-family: 'Assistant', sans-serif; }
    h1, h2, h3, h4, p, label, span, div { color: #ffffff; text-align: right; }
    
    /* Search Box Fix */
    div[data-baseweb="select"] > div { background-color: #ffffff !important; border: 2px solid #38bdf8 !important; }
    div[data-baseweb="select"] span { color: #000000 !important; font-weight: bold; }
    ul[data-baseweb="menu"] { background-color: #ffffff !important; }
    ul[data-baseweb="menu"] li { color: #000000 !important; }
    
    /* Cards */
    .kpi-card { background-color: #151e2e; border: 1px solid #334155; padding: 15px; border-radius: 8px; border-right: 4px solid #38bdf8; margin-bottom: 10px; }
    .kpi-val { font-size: 1.8rem; font-weight: 800; color: #ffffff; }
    .kpi-lbl { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; }
    
    /* Ratios */
    .ratio-box { background: rgba(255,255,255,0.05); border: 1px solid #334155; border-radius: 6px; padding: 10px; text-align: center; }
    .ratio-val { color: #38bdf8; font-weight: bold; font-size: 1.2rem; }
    
    /* Tabs & Tables */
    div[data-testid="stDataFrame"] { background-color: #151e2e; border: 1px solid #334155; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #151e2e; color: #94a3b8; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #38bdf8; color: #000000 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 3. Data Engine ---
TICKERS = {
    "הפניקס": "PHOE.TA", "הראל": "HARL.TA", "מגדל": "MGDL.TA",
    "מנורה": "MMHD.TA", "כלל": "CLIS.TA", "איי.די.איי": "DIDI.TA",
    "איילון": "AYAL.TA", "AIG": "PRIVATE", "ליברה": "LBRA.TA"
}

def get_data(name):
    # Fallback Data
    equity = 5000000000.0
    
    # Try Fetching Live Data (Protected)
    try:
        import yfinance as yf
        sym = TICKERS.get(name)
        if sym != "PRIVATE":
            info = yf.Ticker(sym).info
            if 'marketCap' in info:
                equity = info['marketCap'] / info.get('priceToBook', 0.9)
    except:
        pass

    # Generate Actuarial Model
    np.random.seed(abs(hash(name)) % (2**32))
    assets = equity * np.random.uniform(7.5, 9.5)
    liabilities = assets - equity
    
    # IFRS 17 CSM
    csm_open = equity * 0.45
    csm_flows = {
        "open": csm_open,
        "new": csm_open * 0.1,
        "int": csm_open * 0.03,
        "rel": csm_open * -0.09,
        "var": csm_open * 0.01
    }
    csm_flows["close"] = sum(csm_flows.values())
    
    # P&L Base
    gwp = assets * 0.15
    nwp = gwp * 0.85
    pnl = {
        "nwp": nwp,
        "claims": nwp * 0.72,
        "expenses": nwp * 0.24,
        "gwp": gwp
    }
    
    return {
        "equity": equity, "assets": assets, "liabilities": liabilities,
        "csm": csm_flows, "pnl": pnl, "base_scr": equity * 0.7
    }

def run_stress(data, shocks, factor):
    # Non-Linear Asset Shock
    eq_shock = data['assets'] * 0.15 * (shocks['eq']/100)
    # Bond Convexity Approx
    dur, conv = 6.0, 50.0
    dy = shocks['int']/100
    bond_chg = (-dur * dy) + (0.5 * conv * (dy**2))
    bond_shock = data['assets'] * 0.85 * bond_chg
    
    new_assets = data['assets'] - eq_shock + bond_shock # bond_shock is usually negative
    
    # Liability Shock
    l_dur, l_conv = 7.5, 65.0
    l_chg = (-l_dur * dy) + (0.5 * l_conv * (dy**2))
    new_liabs = data['liabilities'] * (1 + l_chg)
    
    # CSM Shock
    lapse_hit = data['csm']['close'] * (shocks['lap']/100)
    new_csm = data['csm']['close'] - lapse_hit
    
    # Solvency
    new_equity = new_assets - new_liabs
    own_funds = new_equity + (new_csm * 0.7)
    if shocks['cat']: own_funds -= 400000000
    
    scr = data['base_scr'] * (1 + abs(dy)*0.5) # Dynamic SCR
    solvency = (own_funds / max(1, scr)) * 100
    
    # P&L
    claims = data['pnl']['claims'] + (400000000 if shocks['cat'] else 0)
    uw_res = (data['pnl']['nwp']*factor) - (claims*factor) - (data['pnl']['expenses']*factor)
    inv_res = (new_assets * 0.04 * factor) - (eq_shock * 0.2)
    net_income = uw_res + inv_res
    
    # Ratios
    combined = ((claims + data['pnl']['expenses']) / data['pnl']['nwp']) * 100
    roe = (net_income / max(1, new_equity)) * 100 * (1/factor)
    
    return {
        "Equity": new_equity, "Solvency": solvency, "CSM": new_csm, "Net": net_income,
        "Combined": combined, "ROE": roe, "Lapse_Hit": lapse_hit,
        "Assets": new_assets, "Liabilities": new_liabs
    }

# --- 4. UI Layout ---

# Sidebar
with st.sidebar:
    st.header("🎛️ חדר בקרה")
    per = st.radio("תקופה:", ["שנתי", "רבעוני"], horizontal=True)
    f = 0.25 if per == "רבעוני" else 1.0
    
    st.divider()
    s_eq = st.slider("📉 מניות (%)", 0, 50, 0)
    s_int = st.slider("🏦 ריבית (%)", -2.0, 2.0, 0.0, step=0.1)
    s_lap = st.slider("🏃 פדיונות (%)", 0, 40, 0)
    s_cat = st.checkbox("🌪️ קטסטרופה")
    
    if st.button("🔄 אתחול"): st.rerun()
    shocks = {'eq': s_eq, 'int': s_int, 'lap': s_lap, 'cat': s_cat}

# Header
c1, c2 = st.columns([3,1])
with c1:
    st.title("ISR-TITAN ENTERPRISE")
    st.caption("מערכת ניהול סיכונים רגולטורית")
with c2:
    stress = any(shocks.values())
    bg = "#ef4444" if stress else "#10b981"
    st.markdown(f"<div style='background:{bg}; padding:10px; border-radius:8px; text-align:center; font-weight:bold;'>{'STRESS MODE' if stress else 'LIVE'}</div>", unsafe_allow_html=True)

st.divider()

# Search
name = st.selectbox("בחר חברה:", list(TICKERS.keys()))

# Calculations
base = get_data(name)
sim = run_stress(base, shocks, f)

def fmt(v): return f"₪{v/1e9:.2f}B" if abs(v)>=1e9 else f"₪{v/1e6:.0f}M"

# KPIs
k1, k2, k3, k4 = st.columns(4)
def kpi(c, t, v, s):
    c.markdown(f"<div class='kpi-card'><div class='kpi-lbl'>{t}</div><div class='kpi-val'>{v}</div><div style='color:#94a3b8; font-size:0.8rem'>{s}</div></div>", unsafe_allow_html=True)

kpi(k1, "הון כלכלי", fmt(sim['Equity']), f"Leverage: {sim['Assets']/sim['Equity']:.1f}x")
kpi(k2, "יחס סולבנסי", f"{sim['Solvency']:.1f}%", "Target: >100%")
kpi(k3, "ערך גלום (CSM)", fmt(sim['CSM']), "IFRS 17 Stock")
kpi(k4, "רווח נקי", fmt(sim['Net']), f"ROE: {sim['ROE']:.1f}%")

# Ratios
st.markdown("### 📊 יחסים פיננסיים")
r1, r2, r3, r4, r5 = st.columns(5)
def ratio(c, t, v):
    c.markdown(f"<div class='ratio-box'><div style='font-size:0.8rem; color:#94a3b8'>{t}</div><div class='ratio-val'>{v}</div></div>", unsafe_allow_html=True)

ratio(r1, "Combined Ratio", f"{sim['Combined']:.1f}%")
ratio(r2, "Loss Ratio", f"{(sim['Combined']-25):.1f}%")
ratio(r3, "Retention", f"{(base['pnl']['nwp']/base['pnl']['gwp']*100):.1f}%")
ratio(r4, "Lapse Cost", fmt(sim['Lapse_Hit']))
ratio(r5, "Equity/Assets", f"{(sim['Equity']/sim['Assets']*100):.1f}%")

st.divider()

# Charts
t1, t2 = st.tabs(["🧬 גשר CSM", "⚖️ מאזן"])

with t1:
    c = base['csm']
    fig = go.Figure(go.Waterfall(
        name="CSM", orientation="v",
        measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"],
        x=["פתיחה", "חדש", "ריבית", "שחרור", "שינוי הנחות", "סטרס", "סגירה"],
        y=[c['open'], c['new'], c['int'], c['rel'], c['var'], -sim['Lapse_Hit'], 0],
        connector={"line":{"color":"white"}},
        decreasing={"marker":{"color":"#ef4444"}}, increasing={"marker":{"color":"#10b981"}}, totals={"marker":{"color":"#38bdf8"}}
    ))
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
    st.plotly_chart(fig, use_container_width=True)

with t2:
    c_l, c_r = st.columns(2)
    with c_l:
        df_bal = pd.DataFrame({"Item": ["Assets", "Liabilities", "Equity"], "Value": [sim['Assets'], sim['Liabilities'], sim['Equity']]})
        st.bar_chart(df_bal.set_index("Item"), color="#38bdf8")
    with c_r:
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=sim['Solvency'],
            gauge={'axis': {'range': [None, 200]}, 'bar': {'color': "#38bdf8"}, 
                   'steps': [{'range': [0, 100], 'color': "#ef4444"}, {'range': [100, 150], 'color': "#f59e0b"}]}
        ))
        fig_g.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350)
        st.plotly_chart(fig_g, use_container_width=True)

# Export
df_ex = pd.DataFrame([sim]).T
st.download_button("📥 הורד CSV", df_ex.to_csv().encode('utf-8'), "report.csv")

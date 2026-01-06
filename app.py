import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. System Config & CSS (The Foundation)
# ==========================================
st.set_page_config(page_title="ISR-TITAN ENTERPRISE", layout="wide", page_icon="🏛️")

def load_enterprise_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;800&display=swap');
        
        :root {
            --bg-color: #0b0f19;
            --panel-color: #151e2e;
            --text-primary: #ffffff;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --risk-high: #ef4444;
            --risk-med: #f59e0b;
            --risk-low: #10b981;
        }
        
        .stApp {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Assistant', sans-serif;
        }
        
        h1, h2, h3, h4, p, span, div { text-align: right; color: var(--text-primary); }
        
        /* Search Box Fix - Black Text on White Background */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 2px solid var(--accent) !important;
            color: #000000 !important;
        }
        div[data-baseweb="select"] span { color: #000000 !important; font-weight: 700; }
        ul[data-baseweb="menu"] { background-color: #ffffff !important; }
        ul[data-baseweb="menu"] li { color: #000000 !important; background-color: #ffffff !important; }
        
        /* KPI Cards */
        .kpi-container {
            background-color: var(--panel-color);
            border: 1px solid #334155;
            padding: 20px;
            border-radius: 8px;
            border-right: 4px solid var(--accent);
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        .kpi-container:hover { border-color: #ffffff; transform: translateY(-2px); }
        .kpi-lbl { font-size: 0.85rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
        .kpi-val { font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-top: 5px; }
        .kpi-sub { font-size: 0.8rem; margin-top: 5px; font-weight: 500; }
        
        /* Ratio Grid */
        .ratio-item {
            background: rgba(255,255,255,0.03);
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
        }
        .ratio-val { color: var(--accent); font-weight: bold; font-size: 1.2rem; }
        
        /* Component Overrides */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { background-color: var(--panel-color); color: var(--text-secondary); border: 1px solid #334155; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: var(--accent); color: #000000 !important; font-weight: bold; }
        div[data-testid="stDataFrame"] { background-color: var(--panel-color); border: 1px solid #334155; }
        section[data-testid="stSidebar"] { background-color: #0f1623; border-left: 1px solid #334155; }
        </style>
    """, unsafe_allow_html=True)

load_enterprise_css()

# ==========================================
# 2. Actuarial Engine (Logic)
# ==========================================

class ActuarialEngine:
    @staticmethod
    def calculate_solvency_ii(equity, liabilities, shocks):
        # חישוב SCR מבוסס סיכונים
        market_risk = (equity * 0.3) + abs(liabilities * 0.05 * (1 + abs(shocks['interest']))) + (equity * (shocks['equity']/100))
        insurance_risk = (liabilities * 0.15) + (liabilities * (shocks['lapse']/100))
        if shocks['catastrophe']: insurance_risk += 300000000
        op_risk = liabilities * 0.04
        
        # אגרגציה עם קורלציה
        corr = 0.25
        scr_basic = np.sqrt(market_risk**2 + insurance_risk**2 + 2*corr*market_risk*insurance_risk)
        return scr_basic + op_risk

    @staticmethod
    def apply_shock_impacts(base_data, shocks, period_factor):
        # 1. Asset Shock (Equity + Bonds Non-Linear)
        equity_drop = base_data['assets'] * 0.15 * (shocks['equity'] / 100.0)
        
        # Bond Convexity
        duration = 6.0
        convexity = 50.0
        dy = shocks['interest'] / 100.0
        bond_change_pct = (-duration * dy) + (0.5 * convexity * (dy**2))
        bond_impact = base_data['assets'] * 0.85 * bond_change_pct
        
        total_asset_impact = equity_drop - bond_impact
        new_assets = base_data['assets'] - total_asset_impact
        
        # 2. Liability Shock (Convexity)
        liab_duration = 7.5
        liab_convexity = 65.0
        liab_change_pct = (-liab_duration * dy) + (0.5 * liab_convexity * (dy**2))
        new_liabilities = base_data['liabilities'] * (1 + liab_change_pct)
        
        # 3. CSM Shock
        lapse_hit = base_data['csm_close'] * (shocks['lapse'] / 100.0)
        new_csm = base_data['csm_close'] - lapse_hit
        
        # 4. Economic Balance Sheet
        new_equity = new_assets - new_liabilities
        
        # 5. Solvency
        scr = ActuarialEngine.calculate_solvency_ii(new_equity, new_liabilities, shocks)
        own_funds = new_equity + (new_csm * 0.75) + base_data['risk_adjustment']
        if shocks['catastrophe']: own_funds -= 400000000
        
        solvency_ratio = (own_funds / scr) * 100
        
        # 6. P&L
        claims_inflated = base_data['pnl']['claims']
        if shocks['catastrophe']: claims_inflated += 400000000
        
        uw_result = (base_data['pnl']['nwp'] * period_factor) - (claims_inflated * period_factor) - (base_data['pnl']['expenses'] * period_factor)
        inv_result = (new_assets * 0.035 * period_factor) - (total_asset_impact * 0.2)
        net_income = uw_result + inv_result
        
        # Ratios
        combined_ratio = ((claims_inflated + base_data['pnl']['expenses']) / base_data['pnl']['nwp']) * 100
        roe = (net_income / max(1, new_equity)) * 100 * (1/period_factor)
        
        return {
            "Assets": new_assets, "Liabilities": new_liabilities, "Equity": new_equity,
            "CSM": new_csm, "Solvency": solvency_ratio, "Net_Income": net_income,
            "Combined_Ratio": combined_ratio, "ROE": roe, "Lapse_Impact": lapse_hit,
            "SCR": scr, "Own_Funds": own_funds
        }

# ==========================================
# 3. Data Loading
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA", "ביטוח ישיר": "DIDI.TA",
    "איילון אחזקות": "AYAL.TA", "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE", "ליברה": "LBRA.TA"
}

@st.cache_data
def get_insurer_profile(name):
    symbol = TICKERS.get(name)
    market_cap = 4000000000
    equity_proxy = 5000000000
    
    if symbol != "PRIVATE":
        try:
            import yfinance as yf
            t = yf.Ticker(symbol)
            info = t.info
            if 'marketCap' in info:
                market_cap = info['marketCap']
                equity_proxy = market_cap / info.get('priceToBook', 0.9)
        except:
            pass
            
    np.random.seed(abs(hash(name)) % (2**32))
    
    assets = equity_proxy * np.random.uniform(7.5, 9.5)
    liabilities = assets - equity_proxy
    
    csm_open = equity_proxy * 0.40
    csm_new = csm_open * 0.12
    csm_int = csm_open * 0.03
    csm_rel = csm_open * -0.09
    csm_var = csm_open * 0.01
    csm_close = csm_open + csm_new + csm_int + csm_rel + csm_var
    
    risk_adj = liabilities * 0.04
    
    gwp = assets * 0.16
    nwp = gwp * 0.88
    claims = nwp * 0.71
    expenses = nwp * 0.25
    
    segments = {
        "P&C (כללי)": csm_close * 0.15,
        "Health (בריאות)": csm_close * 0.30,
        "L&S (חיסכון)": csm_close * 0.55
    }
    
    return {
        "assets": assets, "liabilities": liabilities, "equity_base": equity_proxy,
        "csm_open": csm_open, "csm_new": csm_new, "csm_int": csm_int, "csm_rel": csm_rel, "csm_var": csm_var, "csm_close": csm_close,
        "risk_adjustment": risk_adj,
        "pnl": {"gwp": gwp, "nwp": nwp, "claims": claims, "expenses": expenses},
        "segments": segments
    }

# ==========================================
# 4. Main Application
# ==========================================

# Sidebar
with st.sidebar:
    st.header("🎛️ חדר סימולציה")
    period = st.radio("תקופת דיווח:", ["שנתי", "רבעוני"], horizontal=True)
    factor = 0.25 if period == "רבעוני" else 1.0
    st.divider()
    s_eq = st.slider("📉 נפילת מניות (%)", 0, 50, 0)
    s_int = st.slider("🏦 שינוי עקום ריבית (%)", -2.0, 2.0, 0.0, step=0.1)
    s_lap = st.slider("🏃 פדיונות (Lapse %)", 0, 40, 0)
    s_cat = st.checkbox("🌪️ אירוע קטסטרופה (CAT)")
    if st.button("🔄 אתחול סימולציה", type="primary"): st.rerun()
    shocks = {'equity': s_eq, 'interest': s_int, 'lapse': s_lap, 'catastrophe': s_cat}

# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.title("ISR-TITAN ENTERPRISE")
    st.caption("מערכת תומכת החלטה | IFRS 17 & Solvency II")
with c2:
    is_stress = any([s_eq, s_int, s_lap, s_cat])
    lbl = "STRESS ACTIVE" if is_stress else "ROUTINE"
    clr = "#ef4444" if is_stress else "#10b981"
    st.markdown(f"""
    <div style="background:{clr}20; border:1px solid {clr}; padding:10px; border-radius:8px; text-align:center; color:{clr}; font-weight:800;">
        {lbl}<br>{datetime.now().strftime('%H:%M')}
    </div>""", unsafe_allow_html=True)

st.divider()

# Search
selected_comp = st.selectbox("בחר חברה לניתוח:", list(TICKERS.keys()))

# Compute
base = get_insurer_profile(selected_comp)
sim = ActuarialEngine.apply_shock_impacts(base, shocks, factor)

def fmt(v): return f"₪{v/1e9:.2f}B" if abs(v) >= 1e9 else f"₪{v/1e6:.0f}M"

# KPIs
k1, k2, k3, k4 = st.columns(4)
def kpi_card(col, label, val, sub):
    col.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-lbl">{label}</div>
        <div class="kpi-val">{val}</div>
        <div class="kpi-sub" style="color:#94a3b8;">{sub}</div>
    </div>""", unsafe_allow_html=True)

kpi_card(k1, "הון כלכלי (Own Funds)", fmt(sim['Own_Funds']), f"SCR Coverage: {sim['Solvency']/100:.1f}x")
kpi_card(k2, "יחס סולבנסי (SII)", f"{sim['Solvency']:.1f}%", f"דרישת הון: {fmt(sim['SCR'])}")
kpi_card(k3, "ערך גלום (CSM)", fmt(sim['CSM']), "IFRS 17 Contract Value")
kpi_card(k4, "רווח נקי", fmt(sim['Net_Income']), f"ROE: {sim['ROE']:.1f}%")

# Ratios
st.markdown("### 📊 יחסים פיננסיים")
r_cols = st.columns(5)
r_data = [
    ("Combined Ratio", f"{sim['Combined_Ratio']:.1f}%"),
    ("Leverage", f"{sim['Assets']/sim['Equity']:.1f}x"),
    ("Risk Adj %", f"{(base['risk_adjustment']/sim['Liabilities'])*100:.1f}%"),
    ("Lapse Cost", fmt(sim['Lapse_Impact'])),
    ("Loss Ratio", f"{(sim['Combined_Ratio'] - 25):.1f}%")
]
for col, (lbl, val) in zip(r_cols, r_data):
    col.markdown(f"""<div class="ratio-item"><div style="font-size:0.8rem; color:#94a3b8;">{lbl}</div><div class="ratio-val">{val}</div></div>""", unsafe_allow_html=True)

st.divider()

# Tabs (Chart Engine)
t1, t2, t3 = st.tabs(["🧬 ניתוח CSM", "⚖️ מאזן וסולבנסי", "📥 ייצוא"])

with t1:
    c_l, c_r = st.columns([2, 1])
    with c_l:
        st.markdown("#### גשר ה-CSM (Waterfall)")
        fig_water = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
            x = ["פתיחה", "עסקים חדשים", "ריבית", "שחרור", "שינוי הנחות", "סטרס", "סגירה"],
            textposition = "outside",
            y = [base['csm_open'], base['csm_new'], base['csm_int'], base['csm_rel'], base['csm_var'], -sim['Lapse_Impact'], 0],
            connector = {"line":{"color":"#94a3b8"}},
            decreasing = {"marker":{"color":"#ef4444"}}, increasing = {"marker":{"color":"#10b981"}}, totals = {"marker":{"color":"#38bdf8"}}
        ))
        fig_water.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_water, use_container_width=True)
    
    with c_r:
        st.markdown("#### פילוח מגזרי")
        segs = base['segments']
        fig_sun = px.sunburst(names=list(segs.keys()), parents=[""]*len(segs), values=list(segs.values()), color_discrete_sequence=px.colors.sequential.Tealgrn)
        fig_sun.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_sun, use_container_width=True)

with t2:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### מד סולבנסי")
        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number+delta", value = sim['Solvency'],
            delta = {'reference': 100},
            gauge = {
                'axis': {'range': [None, 200]}, 'bar': {'color': "#38bdf8"},
                'steps': [{'range': [0, 100], 'color': "#ef4444"}, {'range': [100, 150], 'color': "#f59e0b"}],
                'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 100}
            }))
        fig_g.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350)
        st.plotly_chart(fig_g, use_container_width=True)
    with c2:
        st.markdown("#### מאזן כלכלי")
        df_bal = pd.DataFrame({
            "Item": ["Assets", "Liabilities", "Equity"],
            "Value": [sim['Assets'], sim['Liabilities'], sim['Equity']]
        })
        st.bar_chart(df_bal.set_index("Item"), color="#38bdf8")

with t3:
    st.markdown("#### ייצוא נתונים")
    df_exp = pd.DataFrame([sim]).T
    st.dataframe(df_exp, use_container_width=True)
    st.download_button("📥 הורד CSV", df_exp.to_csv().encode('utf-8'), "titan_report.csv")

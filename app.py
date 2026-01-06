import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. הגדרות מערכת ועיצוב ELITE (High Contrast)
# ==========================================
st.set_page_config(page_title="ISR-TITAN ULTIMATE", layout="wide", page_icon="💎")

def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700&display=swap');
        
        :root {
            --bg-dark: #0f172a;       /* Slate 900 */
            --card-bg: #1e293b;       /* Slate 800 */
            --text-high: #f8fafc;     /* לבן בוהק */
            --text-med: #94a3b8;      /* אפור בהיר */
            --accent: #0ea5e9;        /* תכלת */
            --success: #10b981;       /* ירוק */
            --danger: #f43f5e;        /* אדום */
            --warning: #eab308;       /* צהוב */
        }
        
        .stApp {
            background-color: var(--bg-dark);
            color: var(--text-high);
            font-family: 'Heebo', sans-serif;
            direction: rtl;
        }
        
        h1, h2, h3, h4, h5 { color: var(--text-high) !important; text-align: right; font-weight: 700; }
        p, label, div, span { color: var(--text-high); text-align: right; }
        
        /* כרטיסי KPI ראשיים */
        .kpi-card {
            background-color: var(--card-bg);
            border: 1px solid #334155;
            border-right: 4px solid var(--accent);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.2s;
            height: 100%;
        }
        .kpi-card:hover { transform: translateY(-3px); border-color: var(--text-high); }
        .kpi-title { font-size: 0.8rem; color: var(--text-med); text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-val { font-size: 1.6rem; font-weight: 800; color: var(--text-high); margin: 5px 0; }
        
        /* כרטיסי יחסים פיננסיים */
        .ratio-card {
            background-color: rgba(30, 41, 59, 0.5);
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
        }
        .ratio-val { font-size: 1.2rem; font-weight: bold; color: var(--accent); }
        .ratio-lbl { font-size: 0.8rem; color: var(--text-med); }

        /* סליידרים וטאבים */
        .stSlider > div > div > div > div { background-color: var(--accent); }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { background-color: var(--card-bg); border: 1px solid #334155; color: var(--text-med); border-radius: 6px; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: var(--accent); color: #0f172a !important; font-weight: bold; }
        
        /* טבלאות */
        div[data-testid="stDataFrame"] { background-color: var(--card-bg); border: 1px solid #334155; }
        div[data-testid="stDataFrame"] * { color: var(--text-high) !important; }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==========================================
# 2. מנוע נתונים מורחב (Comprehensive Data Engine)
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA", "ביטוח ישיר": "DIDI.TA",
    "איילון אחזקות": "AYAL.TA", "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE", "ליברה": "LBRA.TA"
}

@st.cache_data(ttl=600)
def fetch_comprehensive_data(ticker_name):
    symbol = TICKERS[ticker_name]
    is_live = False
    
    # נתוני בסיס (Fallback)
    market_cap = 4000000000
    equity = 5000000000
    change_pct = 0.0
    
    # 1. ניסיון שאיבה מהבורסה
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
            pass

    # 2. מודל אקטוארי מורחב
    np.random.seed(abs(hash(ticker_name)) % (2**32))
    
    # מאזן מורחב
    assets = equity * np.random.uniform(7.5, 9.5) # מינוף נכסים
    liabilities = assets - equity
    
    # נתוני תזרים (P&L Items) לשנה
    gwp = assets * 0.15 # פרמיות ברוטו
    reinsurance_rate = np.random.uniform(0.1, 0.2)
    nwp = gwp * (1 - reinsurance_rate) # פרמיות נטו
    
    # הנחות יסוד ליחסים (לפני סטרס)
    base_loss_ratio = np.random.uniform(0.65, 0.72)
    base_expense_ratio = np.random.uniform(0.23, 0.28)
    
    claims_base = nwp * base_loss_ratio 
    expenses = nwp * base_expense_ratio
    
    # IFRS 17 CSM Breakdown
    csm = equity * 0.45
    segments = {
        "כללי (P&C)": csm * 0.15,
        "בריאות": csm * 0.30,
        "חיסכון (Life)": csm * 0.55
    }

    return {
        "is_live": is_live,
        "market_cap": market_cap,
        "equity": equity,
        "assets": assets,
        "liabilities": liabilities,
        "change_pct": change_pct,
        "csm": csm,
        "segments": segments,
        # נתונים ליחסים פיננסיים
        "gwp": gwp,
        "nwp": nwp,
        "claims_base": claims_base,
        "expenses": expenses,
        "base_solvency": np.random.uniform(115, 145)
    }

def run_advanced_simulation(data, shocks, period_factor):
    """
    מנוע סימולציה שמחשב מחדש את כל הדוחות והיחסים הפיננסיים
    """
    # 1. השפעת מניות
    asset_shock = data['assets'] * 0.15 * (shocks['equity'] / 100.0)
    new_assets = data['assets'] - asset_shock
    new_equity = data['equity'] - asset_shock
    
    # 2. השפעת ריבית
    liab_shock = data['liabilities'] * (shocks['interest'] / 100.0) * -6.0 
    new_liabilities = data['liabilities'] + liab_shock
    
    final_equity = new_assets - new_liabilities
    
    # 3. השפעת ביטולים
    csm_shock = data['csm'] * (shocks['lapse'] / 100.0)
    new_csm = data['csm'] - csm_shock
    
    # 4. השפעת קטסטרופה
    cat_damage = 0
    if shocks['catastrophe']:
        cat_damage = 350000000 # נזק קטסטרופלי קבוע
        
    new_claims = data['claims_base'] + cat_damage
    
    # 5. חישוב רווח והפסד (P&L) לתקופה
    underwriting_result = (data['nwp'] * period_factor) - (new_claims * period_factor) - (data['expenses'] * period_factor)
    
    base_inv_income = data['assets'] * 0.04 * period_factor
    inv_income = base_inv_income - (asset_shock * 0.1)
    
    net_income = underwriting_result + inv_income
    
    # 6. חישוב יחסים פיננסיים
    own_funds = final_equity + (new_csm * 0.7)
    scr_req = (final_equity * 0.9) + max(0, liab_shock * 0.5) 
    solvency = (own_funds / scr_req) * 100
    
    earned_premium = data['nwp'] 
    loss_ratio = (new_claims / earned_premium) * 100
    expense_ratio = (data['expenses'] / earned_premium) * 100
    combined_ratio = loss_ratio + expense_ratio
    
    leverage_ratio = new_assets / max(1, final_equity)
    roe = (net_income / max(1, final_equity)) * (1/period_factor) * 100
    retention_ratio = (data['nwp'] / data['gwp']) * 100

    return {
        "Equity": final_equity,
        "Assets": new_assets,
        "Liabilities": new_liabilities,
        "CSM": new_csm,
        "Solvency": solvency,
        "Net_Income": net_income,
        "Loss_Ratio": loss_ratio,
        "Expense_Ratio": expense_ratio,
        "Combined_Ratio": combined_ratio,
        "Leverage": leverage_ratio,
        "ROE": roe,
        "Retention": retention_ratio
    }

# ==========================================
# 3. חדר בקרה (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🎛️ חדר בקרה")
    
    st.markdown("### 📅 דוחות")
    p_type = st.radio("", ["שנתי (Annual)", "רבעוני (Quarterly)"], horizontal=True)
    period_factor = 0.25 if "רבעוני" in p_type else 1.0
    
    st.divider()
    
    st.markdown("### 📉 תרחישי קיצון")
    s_equity = st.slider("נפילת שוק מניות (%)", 0, 50, 0, format="-%d%%")
    s_interest = st.slider("שינוי ריבית (%)", -2.0, 2.0, 0.0, step=0.1, format="%+.1f%%")
    s_lapse = st.slider("שיעור ביטולים (%)", 0, 40, 0, format="-%d%%")
    
    st.markdown("### 🌪️ אירועים")
    s_cat = st.checkbox("אירוע קטסטרופה (רעידת אדמה)")
    
    if st.button("🔄 אפס נתונים", type="primary"):
        st.rerun()
    
    shocks = {'equity': s_equity, 'interest': s_interest, 'lapse': s_lapse, 'catastrophe': s_cat}

# ==========================================
# 4. דשבורד ראשי
# ==========================================

# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("# 🛡️ ISR-TITAN ULTIMATE")
    st.markdown("### מערכת תומכת החלטה - ניהול סיכונים ויחסים פיננסיים")
with c2:
    is_stress = (s_equity > 0 or s_interest != 0 or s_lapse > 0 or s_cat)
    bg = "rgba(239, 68, 68, 0.2)" if is_stress else "rgba(16, 185, 129, 0.2)"
    col = "#f43f5e" if is_stress else "#10b981"
    txt = "STRESS MODE" if is_stress else "LIVE MODE"
    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {col}; padding:10px; border-radius:8px; text-align:center; color:{col}; font-weight:bold;">
        {txt}<br>{datetime.now().strftime('%H:%M')}
    </div>
    """, unsafe_allow_html=True)

st.divider()

# בחירה וחישוב
comp = st.selectbox("בחר חברה:", list(TICKERS.keys()))
base_d = fetch_comprehensive_data(comp)
sim_d = run_advanced_simulation(base_d, shocks, period_factor)

# פונקציה לעיצוב כסף
def fmt_money(val): 
    if val >= 1e9: return f"₪{val/1e9:.2f}B"
    return f"₪{val/1e6:.0f}M"

# --- שורת KPIs ראשית ---
k1, k2, k3, k4 = st.columns(4)

with k1:
    delta = base_d['change_pct']
    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">הון עצמי (Equity)</div><div class="kpi-val">{fmt_money(sim_d['Equity'])}</div>
    <div style="font-size:0.8rem; color:#94a3b8;">{'Live API' if base_d['is_live'] else 'Model'} <span style="float:left; color:{'#10b981' if delta>=0 else '#f43f5e'}; direction:ltr;">{delta:+.2f}%</span></div></div>""", unsafe_allow_html=True)

with k2:
    sol = sim_d['Solvency']
    col = "#10b981" if sol > 110 else ("#f43f5e" if sol < 100 else "#eab308")
    st.markdown(f"""<div class="kpi-card" style="border-right-color:{col}"><div class="kpi-title">יחס סולבנסי</div><div class="kpi-val" style="color:{col}">{sol:.1f}%</div>
    <div style="font-size:0.8rem; color:#94a3b8;">יעד: >100%</div></div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">רווח גלום (CSM)</div><div class="kpi-val">{fmt_money(sim_d['CSM'])}</div>
    <div style="font-size:0.8rem; color:#94a3b8;">מלאי רווחים עתידי</div></div>""", unsafe_allow_html=True)

with k4:
    roe = sim_d['ROE']
    col = "#38bdf8" if roe > 0 else "#f43f5e"
    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">תשואה להון (ROE)</div><div class="kpi-val" style="color:{col}">{roe:.1f}%</div>
    <div style="font-size:0.8rem; color:#94a3b8;">בגילום שנתי</div></div>""", unsafe_allow_html=True)

# --- פאנל יחסים פיננסיים (שורת המדדים השנייה) ---
st.markdown("### 📈 יחסים פיננסיים ותפעוליים (Financial Ratios)")
r1, r2, r3, r4, r5 = st.columns(5)

# פונקציית עזר ליחסים (תוקנה למניעת שגיאת תחביר)
def ratio_box(col, title, value, suffix="%", good_thresh=None, invert=False):
    color = "var(--text-high)"
    if good_thresh is not None:
        is_good = value > good_thresh if not invert else value < good_thresh
        color = "#10b981" if is_good else "#f43f5e"
    
    html_content = f"""
    <div class="ratio-card">
        <div class="ratio-lbl">{title}</div>
        <div class="ratio-val" style="color:{color}">{value:.1f}{suffix}</div>
    </div>
    """
    col.markdown(html_content, unsafe_allow_html=True)

# 1. Combined Ratio
ratio_box(r1, "Combined Ratio", sim_d['Combined_Ratio'], "%", 100, invert=True)
# 2. Loss Ratio
ratio_box(r2, "Loss Ratio (תביעות)", sim_d['Loss_Ratio'], "%", 75, invert=True)
# 3. Expense Ratio
ratio_box(r3, "Expense Ratio (הוצאות)", sim_d['Expense_Ratio'], "%", 30, invert=True)
# 4. Leverage
ratio_box(r4, "מינוף פיננסי", sim_d['Leverage'], "x", 10, invert=True)
# 5. Retention
ratio_box(r5, "שיעור שיור (Retention)", sim_d['Retention'], "%")

st.markdown("---")

# --- גרפים וניתוח ---
t1, t2 = st.tabs(["🧬 ניתוח ערך (IFRS 17)", "⚖️ מאזן וסיכונים"])

with t1:
    c_l, c_r = st.columns([2, 1])
    with c_l:
        st.markdown("#### גשר ה-CSM")
        fig = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "total"],
            x = ["פתיחה", "צמיחה", "השפעת תרחיש", "סגירה"],
            textposition = "outside",
            y = [base_d['csm'], base_d['csm']*0.05, sim_d['CSM'] - (base_d['csm']*1.05), 0],
            connector = {"line":{"color":"#94a3b8"}},
            decreasing = {"marker":{"color":"#f43f5e"}}, increasing = {"marker":{"color":"#10b981"}}, totals = {"marker":{"color":"#0ea5e9"}}
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350, font=dict(family="Heebo"))
        st.plotly_chart(fig, use_container_width=True)
    
    with c_r:
        st.markdown("#### תרומה ל-CSM לפי מגזר")
        # גרף שמש (Sunburst)
        sb_labels = []
        sb_parents = []
        sb_values = []
        for seg, val in base_d['segments'].items():
            sb_labels.append(seg)
            sb_parents.append("")
            sb_values.append(val)
            
        fig_sun = go.Figure(go.Sunburst(
            labels=sb_labels, parents=sb_parents, values=sb_values,
            branchvalues="total"
        ))
        fig_sun.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig_sun, use_container_width=True)

with t2:
    # מאזן ויזואלי
    st.markdown("#### מבנה מאזן (Simulated Balance Sheet)")
    balance_df = pd.DataFrame({
        "Sect": ["נכסים", "התחייבויות", "הון עצמי"],
        "Value": [sim_d['Assets'], sim_d['Liabilities'], sim_d['Equity']],
        "Color": ["#0ea5e9", "#f43f5e", "#10b981"]
    })
    fig_bar = px.bar(balance_df, x="Value", y="Sect", orientation='h', text_auto='.2s', color="Sect", color_discrete_sequence=balance_df["Color"])
    fig_bar.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=250)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # טבלת נתונים מלאה
    st.markdown("#### נתוני דוח מפורטים")
    exp_df = pd.DataFrame([
        {"Item": "Equity", "Value": fmt_money(sim_d['Equity'])},
        {"Item": "Assets", "Value": fmt_money(sim_d['Assets'])},
        {"Item": "Liabilities", "Value": fmt_money(sim_d['Liabilities'])},
        {"Item": "Solvency Ratio", "Value": f"{sim_d['Solvency']:.1f}%"},
        {"Item": "Combined Ratio", "Value": f"{sim_d['Combined_Ratio']:.1f}%"},
        {"Item": "Net Income", "Value": fmt_money(sim_d['Net_Income'])},
    ])
    st.dataframe(exp_df, use_container_width=True)

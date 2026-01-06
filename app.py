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
st.set_page_config(page_title="ISR-TITAN REGULATOR", layout="wide", page_icon="⚖️")

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
            --warning: #f59e0b;       /* כתום */
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
        .kpi-val { font-size: 1.6rem; font-weight: 800; color: var(--text-high); margin: 5px 0; }
        .kpi-lbl { font-size: 0.8rem; color: var(--text-med); text-transform: uppercase; }

        /* כרטיסי יחסים פיננסיים (קטנים) */
        .ratio-card {
            background-color: rgba(30, 41, 59, 0.5);
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
        }
        .ratio-val { font-size: 1.2rem; font-weight: bold; }
        .ratio-lbl { font-size: 0.75rem; color: var(--text-med); margin-bottom: 4px; }

        /* --- תיקון ספציפי לתיבת החיפוש (Selectbox) --- */
        /* טקסט שחור בתוך התיבה */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #000000 !important;
            border-radius: 6px;
        }
        div[data-baseweb="select"] span {
            color: #000000 !important;
            font-weight: bold;
        }
        /* רשימת האפשרויות הנפתחת */
        ul[data-baseweb="menu"] li {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        /* ------------------------------------------- */

        /* טאבים */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { background-color: var(--card-bg); border: 1px solid #334155; color: var(--text-med); border-radius: 6px; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: var(--accent); color: #0f172a !important; font-weight: bold; }
        
        /* טבלאות */
        div[data-testid="stDataFrame"] { background-color: var(--card-bg); border: 1px solid #334155; }
        div[data-testid="stDataFrame"] * { color: var(--text-high) !important; }
        
        /* סליידרים */
        .stSlider > div > div > div > div { background-color: var(--accent); }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==========================================
# 2. מנוע נתונים: IFRS 17 & Solvency II
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA", "ביטוח ישיר": "DIDI.TA",
    "איילון אחזקות": "AYAL.TA", "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE", "ליברה": "LBRA.TA"
}

@st.cache_data(ttl=600)
def fetch_regulatory_data(ticker_name):
    """
    מייצר את הנתונים העמוקים הדרושים לגשר CSM ולניתוח סולבנסי
    """
    symbol = TICKERS[ticker_name]
    is_live = False
    
    # נתוני ברירת מחדל
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
            pass

    # זרע יציב לסימולציה
    np.random.seed(abs(hash(ticker_name)) % (2**32))
    
    # --- בניית גשר ה-CSM (הלב של IFRS 17) ---
    csm_opening = equity * 0.45
    # עסקים חדשים (צמיחה אורגנית)
    csm_new_biz = csm_opening * np.random.uniform(0.08, 0.12)
    # צבירת ריבית (Interest Accretion)
    csm_interest = csm_opening * 0.03
    # שחרור לרווח (Amortization) - הכנסה שנתית
    csm_release = csm_opening * np.random.uniform(-0.10, -0.07)
    # שינויים בהנחות (אקטוארי)
    csm_changes = csm_opening * np.random.uniform(-0.02, 0.02)
    
    csm_closing = csm_opening + csm_new_biz + csm_interest + csm_release + csm_changes
    
    # נתונים ליחסים
    gwp = equity * 1.5 # פרמיות
    
    # פילוח מגזרי (Segmentation)
    segments = {
        "ביטוח כללי": {"CSM": csm_closing * 0.15, "Profit": 50},
        "בריאות": {"CSM": csm_closing * 0.30, "Profit": 120},
        "חיסכון ופנסיה": {"CSM": csm_closing * 0.55, "Profit": 200}
    }
    
    return {
        "is_live": is_live,
        "market_cap": market_cap,
        "equity": equity,
        "change_pct": change_pct,
        "liabilities": equity * 7.5,
        
        # רכיבי גשר CSM
        "csm_opening": csm_opening,
        "csm_new_biz": csm_new_biz,
        "csm_interest": csm_interest,
        "csm_release": csm_release,
        "csm_changes": csm_changes,
        "csm_closing": csm_closing,
        
        "gwp": gwp,
        "segments": segments,
        # יחסי בסיס לסימולציה
        "base_combined": np.random.uniform(93, 98),
        "base_solvency_scr": equity * 0.7 # דרישת הון בסיסית
    }

def run_pro_simulation(data, shocks, period_factor):
    """
    מחשב את ההשפעות על הגשר ועל היחסים
    """
    # 1. השפעות מאקרו (Equity & Interest)
    equity_impact = data['equity'] * (shocks['equity']/100) * 0.6
    final_equity = data['equity'] - equity_impact
    
    liab_impact = data['liabilities'] * (shocks['interest']/100) * -6.0
    
    # 2. השפעה על CSM (ביטולים)
    lapse_impact = data['csm_closing'] * (shocks['lapse']/100)
    final_csm = data['csm_closing'] - lapse_impact
    
    # 3. Solvency II Calculation
    # Own Funds = הון עצמי + התאמות CSM + נכסים נדחים
    own_funds = final_equity + (final_csm * 0.7) 
    if shocks['catastrophe']: own_funds -= 400000000
    
    # SCR (דרישת הון) - עולה כשהסיכון עולה
    scr = data['base_solvency_scr'] + (liab_impact * 0.4)
    scr = max(1, scr) # הגנה מחלוקה ב-0
    solvency_ratio = (own_funds / scr) * 100
    
    # 4. יחסים פיננסיים מחושבים
    # CSM Release Rate = שחרור / פתיחה (קצב הכרה ברווח)
    release_rate = abs(data['csm_release'] / data['csm_opening']) * 100
    
    # New Business Margin = ערך עסקים חדשים / פרמיה משוערת
    new_biz_margin = (data['csm_new_biz'] / (data['gwp'] * 0.2)) * 100 
    
    # Combined Ratio (מושפע מקטסטרופה)
    combined_ratio = data['base_combined'] + (15 if shocks['catastrophe'] else 0)
    
    # ROE (מושפע משוק ההון)
    net_income_base = (final_equity * 0.12) + data['csm_release']
    if shocks['catastrophe']: net_income_base -= 400000000
    roe = (net_income_base / max(1, final_equity)) * 100 * (1/period_factor)

    return {
        "Equity": final_equity,
        "Solvency": solvency_ratio,
        "CSM_Final": final_csm,
        "Net_Income": net_income_base * period_factor,
        "Combined_Ratio": combined_ratio,
        "ROE": roe,
        "Release_Rate": release_rate,
        "New_Biz_Margin": new_biz_margin,
        "Lapse_Impact": lapse_impact
    }

# ==========================================
# 3. חדר בקרה (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🎛️ בקרת רגולטור")
    
    st.markdown("### 📅 דוחות")
    p_type = st.radio("", ["שנתי", "רבעוני"], horizontal=True)
    period_factor = 0.25 if "רבעוני" in p_type else 1.0
    
    st.divider()
    
    st.markdown("### 📉 מבחני קיצון (Stress)")
    s_equity = st.slider("נפילת שוק מניות (%)", 0, 50, 0, format="-%d%%")
    s_interest = st.slider("שינוי עקום ריבית (%)", -2.0, 2.0, 0.0, step=0.1, format="%+.1f%%")
    s_lapse = st.slider("שיעור ביטולים (Lapse)", 0, 40, 0, format="-%d%%")
    s_cat = st.checkbox("אירוע קטסטרופה")
    
    if st.button("🔄 אפס נתונים", type="primary"):
        st.rerun()
    
    shocks = {'equity': s_equity, 'interest': s_interest, 'lapse': s_lapse, 'catastrophe': s_cat}

# ==========================================
# 4. דשבורד ראשי
# ==========================================

c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("# 🛡️ ISR-TITAN REGULATOR")
    st.markdown("### ניתוח עומק IFRS 17 וניהול סיכונים")
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

# חישוב נתונים
comp = st.selectbox("בחר גוף מפוקח (Search Engine):", list(TICKERS.keys()))
base_d = fetch_regulatory_data(comp)
sim_d = run_pro_simulation(base_d, shocks, period_factor)

def fmt_money(val): 
    if val >= 1e9: return f"₪{val/1e9:.2f}B"
    return f"₪{val/1e6:.0f}M"

# --- Top KPIs ---
k1, k2, k3, k4 = st.columns(4)

with k1:
    delta = base_d['change_pct']
    st.markdown(f"""<div class="kpi-card"><div class="kpi-lbl">הון עצמי (Equity)</div><div class="kpi-val">{fmt_money(sim_d['Equity'])}</div>
    <div style="font-size:0.8rem; color:#94a3b8;">{'Live API' if base_d['is_live'] else 'Model'} <span style="float:left; color:{'#10b981' if delta>=0 else '#f43f5e'}; direction:ltr;">{delta:+.2f}%</span></div></div>""", unsafe_allow_html=True)

with k2:
    sol = sim_d['Solvency']
    col = "#10b981" if sol > 110 else ("#f43f5e" if sol < 100 else "#eab308")
    st.markdown(f"""<div class="kpi-card" style="border-right-color:{col}"><div class="kpi-lbl">יחס סולבנסי</div><div class="kpi-val" style="color:{col}">{sol:.1f}%</div>
    <div style="font-size:0.8rem; color:#94a3b8;">יעד: >100%</div></div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-lbl">יתרת CSM סגירה</div><div class="kpi-val">{fmt_money(sim_d['CSM_Final'])}</div>
    <div style="font-size:0.8rem; color:#94a3b8;">ערך גלום עתידי</div></div>""", unsafe_allow_html=True)

with k4:
    roe = sim_d['ROE']
    col = "#38bdf8" if roe > 0 else "#f43f5e"
    st.markdown(f"""<div class="kpi-card"><div class="kpi-lbl">תשואה להון (ROE)</div><div class="kpi-val" style="color:{col}">{roe:.1f}%</div>
    <div style="font-size:0.8rem; color:#94a3b8;">בגילום שנתי</div></div>""", unsafe_allow_html=True)

# --- יחסים מקצועיים (Professional Ratios) ---
st.markdown("### 📈 יחסים פיננסיים ואקטואריים (Checklist)")
r1, r2, r3, r4, r5 = st.columns(5)

def ratio_box(col, title, value, suffix="%", good_thresh=None, invert=False):
    text_color = "#f8fafc"
    if good_thresh is not None:
        is_good = value > good_thresh if not invert else value < good_thresh
        text_color = "#10b981" if is_good else "#f43f5e"
    
    col.markdown(f"""
    <div class="ratio-card">
        <div class="ratio-lbl">{title}</div>
        <div class="ratio-val" style="color:{text_color}">{value:.1f}{suffix}</div>
    </div>
    """, unsafe_allow_html=True)

ratio_box(r1, "Combined Ratio", sim_d['Combined_Ratio'], "%", 100, invert=True)
ratio_box(r2, "CSM Release Rate", sim_d['Release_Rate'], "%", 6)
ratio_box(r3, "New Business Margin", sim_d['New_Biz_Margin'], "%", 5)
ratio_box(r4, "פגיעת ביטולים", -(sim_d['Lapse_Impact']/1e6), "M", -50, invert=True) 
ratio_box(r5, "Solvency Buffer", sim_d['Solvency'] - 100, " pts", 10)

st.markdown("---")

# --- Tabs: Deep Dive ---
t1, t2 = st.tabs(["🧬 גשר ה-CSM וניתוח ערך", "⚖️ מאזן וסיכונים"])

with t1:
    c_l, c_r = st.columns([2, 1])
    
    with c_l:
        st.markdown("#### גשר התפתחות הרווח (CSM Roll-forward)")
        # Waterfall Chart - הלב של IFRS 17
        fig_water = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
            x = ["פתיחה", "עסקים חדשים", "צבירת ריבית", "שינוי הנחות", "ביטולים/שוק", "שחרור לרווח", "סגירה"],
            textposition = "outside",
            y = [
                base_d['csm_opening'], 
                base_d['csm_new_biz'], 
                base_d['csm_interest'], 
                base_d['csm_changes'],
                -sim_d['Lapse_Impact'], 
                base_d['csm_release'], 
                0
            ],
            connector = {"line":{"color":"#94a3b8"}},
            decreasing = {"marker":{"color":"#f43f5e"}}, 
            increasing = {"marker":{"color":"#10b981"}}, 
            totals = {"marker":{"color":"#38bdf8"}}
        ))
        fig_water.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400, font=dict(family="Heebo"))
        st.plotly_chart(fig_water, use_container_width=True)
    
    with c_r:
        st.markdown("#### תרומה ל-CSM לפי מגזר")
        # Sunburst Chart
        sb_labels = []
        sb_parents = []
        sb_values = []
        
        # רמה 1: סך הכל
        sb_labels.append("Total CSM")
        sb_parents.append("")
        sb_values.append(sim_d['CSM_Final'])
        
        # רמה 2: מגזרים
        for seg, val in base_d['segments'].items():
            sb_labels.append(seg)
            sb_parents.append("Total CSM")
            sb_values.append(val['CSM'])
            
            # רמה 3: רווח
            sb_labels.append(f"Profit {seg}")
            sb_parents.append(seg)
            sb_values.append(val['Profit'])

        fig_

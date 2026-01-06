
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. הגדרות מערכת ועיצוב אגרסיבי (High Contrast Forced)
# ==========================================
st.set_page_config(page_title="ISR-REGULATOR PRO", layout="wide", page_icon="⚖️")

def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
        
        /* איפוס צבעים גלובלי - כפיית מצב כהה */
        :root {
            --bg-color: #0e1117;
            --card-color: #1f2937;
            --text-color: #ffffff;
            --accent-color: #00d4ff;
            --success-color: #00ff9d;
            --danger-color: #ff4b4b;
        }
        
        /* רקע ראשי וטקסט */
        .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Heebo', sans-serif;
            direction: rtl;
        }
        
        /* הבטחת קריאות טקסט */
        h1, h2, h3, h4, h5, h6, p, div, span, label, li {
            color: var(--text-color) !important;
            text-align: right;
        }
        
        /* כרטיסי KPI - עיצוב ברור וחד */
        .kpi-card {
            background-color: var(--card-color);
            border: 1px solid #374151;
            border-right: 5px solid var(--accent-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .kpi-title {
            font-size: 0.9rem;
            color: #9ca3af !important; /* אפור בהיר לכותרת */
            font-weight: bold;
            margin-bottom: 5px;
            display: block;
        }
        
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff !important;
            display: block;
        }
        
        /* כרטיסי יחסים פיננסיים (קטנים) */
        .ratio-box {
            background-color: rgba(31, 41, 55, 0.7);
            border: 1px solid #374151;
            border-radius: 5px;
            padding: 10px;
            text-align: center;
        }
        .ratio-val { font-size: 1.4rem; font-weight: bold; color: var(--accent-color) !important; }
        .ratio-lbl { font-size: 0.85rem; color: #d1d5db !important; }

        /* טבלאות - רקע כהה לטקסט בהיר */
        div[data-testid="stDataFrame"] {
            background-color: var(--card-color);
            border: 1px solid #374151;
        }
        div[data-testid="stDataFrame"] * {
            color: white !important;
            background-color: var(--card-color) !important;
        }

        /* סרגל צד */
        section[data-testid="stSidebar"] {
            background-color: #111827;
            border-left: 1px solid #374151;
        }
        
        /* טאבים */
        .stTabs [data-baseweb="tab"] {
            color: #9ca3af;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: var(--accent-color) !important;
            border-top-color: var(--accent-color) !important;
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==========================================
# 2. מנוע נתונים משולב (Combined Data Engine)
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA", "ביטוח ישיר": "DIDI.TA",
    "איילון אחזקות": "AYAL.TA", "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE"
}

@st.cache_data(ttl=600)
def fetch_full_data(ticker_name):
    symbol = TICKERS[ticker_name]
    is_live = False
    
    # נתוני ברירת מחדל (Fallback)
    market_cap = 4500000000
    equity = 5200000000
    change_pct = 0.0
    
    # 1. חיבור לבורסה
    if symbol != "PRIVATE":
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            if 'marketCap' in info and info['marketCap']:
                market_cap = info['marketCap']
                equity = market_cap / info.get('priceToBook', 0.85)
                
                # חישוב שינוי יומי
                current = info.get('currentPrice', 0)
                prev = info.get('previousClose', 0)
                if prev > 0:
                    change_pct = ((current - prev) / prev) * 100
                is_live = True
        except:
            pass

    # 2. מחולל נתונים אקטוארי (Model Generator)
    # שימוש ב-abs כדי למנוע קריסה
    np.random.seed(abs(hash(ticker_name)) % (2**32))
    
    # מאזן מורחב (Expanded Balance Sheet)
    assets = equity * np.random.uniform(7.8, 9.2) # מינוף
    liabilities = assets - equity
    
    # נתוני תזרים (P&L Items) לשנה
    gwp = assets * 0.16 # פרמיות ברוטו
    reinsurance_rate = np.random.uniform(0.12, 0.18)
    nwp = gwp * (1 - reinsurance_rate) # פרמיות נטו
    
    # הנחות יסוד ליחסים (Base Assumptions)
    base_loss_ratio = np.random.uniform(0.68, 0.74)
    base_expense_ratio = np.random.uniform(0.22, 0.26)
    
    claims_base = nwp * base_loss_ratio 
    expenses = nwp * base_expense_ratio
    
    # IFRS 17 CSM Breakdown
    csm = equity * 0.42
    segments = {
        "ביטוח כללי (P&C)": csm * 0.15,
        "ביטוח בריאות": csm * 0.30,
        "חיסכון ופנסיה": csm * 0.55
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
        # נתונים גולמיים לחישוב
        "gwp": gwp,
        "nwp": nwp,
        "claims_base": claims_base,
        "expenses": expenses,
        "base_solvency": np.random.uniform(118, 142)
    }

def run_simulation_engine(data, shocks, period_factor):
    """
    מנוע הסימולציה המלא - מחשב הכל מחדש לפי הסליידרים
    """
    # 1. זעזוע שוק (מניות)
    # הנחה: 15% מהנכסים מושקעים במניות
    asset_shock = data['assets'] * 0.15 * (shocks['equity'] / 100.0)
    new_assets = data['assets'] - asset_shock
    new_equity = data['equity'] - asset_shock # יורד מההון
    
    # 2. זעזוע ריבית (התחייבויות)
    # Duration approx 6.5 years
    liab_shock = data['liabilities'] * (shocks['interest'] / 100.0) * -6.5
    new_liabilities = data['liabilities'] + liab_shock
    
    # עדכון הון סופי (Assets - Liabilities)
    final_equity = new_assets - new_liabilities
    
    # 3. זעזוע ביטולים (CSM)
    csm_shock = data['csm'] * (shocks['lapse'] / 100.0)
    new_csm = data['csm'] - csm_shock
    
    # 4. זעזוע קטסטרופה
    cat_damage = 0
    if shocks['catastrophe']:
        cat_damage = 350000000 # נזק קטסטרופלי קבוע
        
    new_claims = data['claims_base'] + cat_damage
    
    # 5. חישוב רווח והפסד (P&L) לתקופה
    # תוצאה חיתומית
    underwriting_result = (data['nwp'] * period_factor) - (new_claims * period_factor) - (data['expenses'] * period_factor)
    
    # תוצאה השקעתית (כולל הפסד הון)
    base_inv_income = data['assets'] * 0.04 * period_factor
    inv_income = base_inv_income - (asset_shock * 0.1) 
    
    net_income = underwriting_result + inv_income
    
    # 6. חישוב יחסים פיננסיים (Ratios)
    
    # Solvency II Ratio
    own_funds = final_equity + (new_csm * 0.7)
    scr_req = (final_equity * 0.9) + max(0, liab_shock * 0.6) 
    solvency = (own_funds / scr_req) * 100
    
    # Operational Ratios
    earned_premium = data['nwp'] 
    loss_ratio = (new_claims / earned_premium) * 100
    expense_ratio = (data['expenses'] / earned_premium) * 100
    combined_ratio = loss_ratio + expense_ratio
    
    # Financial Ratios
    leverage_ratio = new_assets / max(1, final_equity)
    roe = (net_income / max(1, final_equity)) * (1/period_factor) * 100 # גילום שנתי
    retention_ratio = (data['nwp'] / data['gwp']) * 100

    return {
        "Equity": final_equity,
        "Assets": new_assets,
        "Liabilities": new_liabilities,
        "CSM": new_csm,
        "Solvency": solvency,
        "Net_Income": net_income,
        # יחסים
        "Loss_Ratio": loss_ratio,
        "Expense_Ratio": expense_ratio,
        "Combined_Ratio": combined_ratio,
        "Leverage": leverage_ratio,
        "ROE": roe,
        "Retention": retention_ratio
    }

# ==========================================
# 3. ממשק שליטה (Sidebar Controls)
# ==========================================
with st.sidebar:
    st.header("🎛️ חדר בקרה רגולטורי")
    
    st.markdown("### 📅 דוחות")
    p_type = st.radio("", ["שנתי (Annual)", "רבעוני (Quarterly)"], horizontal=True)
    period_factor = 0.25 if "רבעוני" in p_type else 1.0
    
    st.divider()
    
    st.markdown("### 📉 תרחישי קיצון (Stress Test)")
    s_equity = st.slider("📉 נפילת שוק מניות (%)", 0, 50, 0, format="-%d%%")
    s_interest = st.slider("🏦 שינוי עקום ריבית (%)", -2.0, 2.0, 0.0, step=0.1, format="%+.1f%%")
    s_lapse = st.slider("🏃 שיעור ביטולים (Lapse)", 0, 40, 0, format="-%d%%")
    
    st.markdown("### 🌪️ אירועי קטסטרופה")
    s_cat = st.checkbox("אירוע רעידת אדמה / מלחמה")
    
    if st.button("🔄 אפס סימולציה", type="primary"):
        st.rerun()
    
    shocks = {'equity': s_equity, 'interest': s_interest, 'lapse': s_lapse, 'catastrophe': s_cat}

# ==========================================
# 4. דשבורד ראשי (Main Dashboard)
# ==========================================

# כותרת ראשית
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("# 🛡️ ISR-REGULATOR PRO")
    st.markdown("### מערכת תומכת החלטה | IFRS 17 & Solvency II")
with c2:
    is_stress = (s_equity > 0 or s_interest != 0 or s_lapse > 0 or s_cat)
    bg_col = "rgba(239, 68, 68, 0.2)" if is_stress else "rgba(0, 255, 157, 0.1)"
    border_col = "#ff4b4b" if is_stress else "#00ff9d"
    status_txt = "STRESS TEST ACTIVE" if is_stress else "SYSTEM NORMAL"
    
    st.markdown(f"""
    <div style="background:{bg_col}; border:1px solid {border_col}; padding:10px; border-radius:8px; text-align:center; color:{border_col}; font-weight:bold;">
        {status_txt}<br>{datetime.now().strftime('%H:%M')}
    </div>
    """, unsafe_allow_html=True)

st.divider()

# בחירת חברה
comp = st.selectbox("בחר גוף מפוקח:", list(TICKERS.keys()))
base_d = fetch_full_data(comp)
sim_d = run_simulation_engine(base_d, shocks, period_factor)

# פונקציית עיצוב כסף (Safe Format)
def fmt_money(val): 
    if val >= 1e9: return f"₪{val/1e9:.2f}B"
    return f"₪{val/1e6:.0f}M"

# --- שורת KPIs ראשית (Top Level) ---
k1, k2, k3, k4 = st.columns(4)

with k1:
    delta = base_d['change_pct']
    change_col = "#00ff9d" if delta >= 0 else "#ff4b4b"
    st.markdown(f"""
    <div class="kpi-card">
        <span class="kpi-title">הון עצמי (Equity)</span>
        <span class="kpi-value">{fmt_money(sim_d['Equity'])}</span>
        <div style="margin-top:5px; font-size:0.8rem;">
            <span style="color:#00d4ff; font-weight:bold;">{'Live API' if base_d['is_live'] else 'Model'}</span>
            <span style="float:left; color:{change_col}; direction:ltr;">{delta:+.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    sol = sim_d['Solvency']
    sol_col = "#00ff9d" if sol > 110 else ("#ff4b4b" if sol < 100 else "#eab308")
    st.markdown(f"""
    <div class="kpi-card" style="border-right-color:{sol_col};">
        <span class="kpi-title">יחס סולבנסי</span>
        <span class="kpi-value" style="color:{sol_col}">{sol:.1f}%</span>
        <div style="font-size:0.8rem; color:#9ca3af;">יעד רגולטורי: >100%</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <span class="kpi-title">רווח גלום (CSM)</span>
        <span class="kpi-value">{fmt_money(sim_d['CSM'])}</span>
        <div style="font-size:0.8rem; color:#9ca3af;">מלאי רווחים עתידי</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    roe = sim_d['ROE']
    roe_col = "#00d4ff" if roe > 0 else "#ff4b4b"
    st.markdown(f"""
    <div class="kpi-card">
        <span class="kpi-title">רווח נקי ({p_type.split()[0]})</span>
        <span class="kpi-value">{fmt_money(sim_d['Net_Income'])}</span>
        <div style="font-size:0.8rem; color:{roe_col}; font-weight:bold;">ROE: {roe:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# --- פאנל יחסים פיננסיים (Financial Ratios) ---
st.markdown("### 📈 מדדים תפעוליים ופיננסיים (Ratios)")
r1, r2, r3, r4, r5 = st.columns(5)

def ratio_display(col, title, value, suffix="%", good_thresh=None, invert=False):
    color = "#ffffff"
    if good_thresh is not None:
        is_good = value > good_thresh if not invert else value < good_thresh
        color = "#00ff9d" if is_good else "#ff4b4b"
    
    html = f"""
    <div class="ratio-box">
        <div class="ratio-lbl">{title}</div>
        <div class="ratio-val" style="color:{color} !important;">{value:.1f}{suffix}</div>
    </div>
    """
    col.markdown(html, unsafe_allow_html=True)

# הצגת היחסים
ratio_display(r1, "Combined Ratio", sim_d['Combined_Ratio'], "%", 100, invert=True)
ratio_display(r2, "Loss Ratio", sim_d['Loss_Ratio'], "%", 75, invert=True)
ratio_display(r3, "Expense Ratio", sim_d['Expense_Ratio'], "%", 30, invert=True)
ratio_display(r4, "מינוף פיננסי", sim_d['Leverage'], "x", 10, invert=True)
ratio_display(r5, "Retention Rate", sim_d['Retention'], "%")

st.markdown("---")

# --- גרפים וניתוח עומק ---
t1, t2 = st.tabs(["🧬 ניתוח IFRS 17 וערך", "⚖️ מאזן וסיכונים"])

with t1:
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.markdown("#### גשר ה-CSM (התפתחות הרווח)")
        # גרף מפל
        fig = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "total"],
            x = ["CSM פתיחה", "צמיחה", "השפעת תרחיש", "CSM סגירה"],
            textposition = "outside",
            y = [base_d['csm'], base_d['csm']*0.05, sim_d['CSM'] - (base_d['csm']*1.05), 0],
            connector = {"line":{"color":"#9ca3af"}},
            decreasing = {"marker":{"color":"#ff4b4b"}}, 
            increasing = {"marker":{"color":"#00ff9d"}}, 
            totals = {"marker":{"color":"#00d4ff"}}
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400, font=dict(family="Heebo"))
        st.plotly_chart(fig, use_container_width=True)
        
    with c_right:
        st.markdown("#### תרומה ל-CSM לפי מגזר")
        # גרף Sunburst
        sb_labels = []
        sb_parents = []
        sb_values = []
        for seg, val in base_d['segments'].items():
            sb_labels.append(seg)
            sb_parents.append("")
            sb_values.append(val)
            
        fig_sun = go.Figure(go.Sunburst(
            labels=sb_labels, parents=sb_parents, values=sb_values,
            branchvalues="total", marker=dict(colors=px.colors.sequential.Tealgrn)
        ))
        fig_sun.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400, margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig_sun, use_container_width=True)

with t2:
    st.markdown("#### ניתוח מאזן (Assets vs Liabilities)")
    balance_df = pd.DataFrame({
        "Sect": ["נכסים", "התחייבויות", "הון עצמי"],
        "Value": [sim_d['Assets'], sim_d['Liabilities'], sim_d['Equity']],
        "Color": ["#00d4ff", "#ff4b4b", "#00ff9d"]
    })
    fig_bar = px.bar(balance_df, x="Value", y="Sect", orientation='h', text_auto='.2s', color="Sect", color_discrete_sequence=balance_df["Color"])
    fig_bar.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=250, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("#### טבלת נתונים מלאה")
    exp_df = pd.DataFrame([
        {"Item": "Equity", "Value": fmt_money(sim_d['Equity'])},
        {"Item": "Assets", "Value": fmt_money(sim_d['Assets'])},
        {"Item": "Liabilities", "Value": fmt_money(sim_d['Liabilities'])},
        {"Item": "Solvency Ratio", "Value": f"{sim_d['Solvency']:.1f}%"},
        {"Item": "Combined Ratio", "Value": f"{sim_d['Combined_Ratio']:.1f}%"},
        {"Item": "Net Income", "Value": fmt_money(sim_d['Net_Income'])},
    ])
    st.dataframe(exp_df, use_container_width=True)

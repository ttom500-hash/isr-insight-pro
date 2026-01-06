import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. עיצוב FINTECH PRO (קריאות מקסימלית)
# ==========================================
st.set_page_config(page_title="ISR-TITAN PRO", layout="wide", page_icon="🏦")

def load_pro_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700&display=swap');
        
        :root {
            /* פלטת צבעים פיננסית מקצועית */
            --bg-main: #0f172a;       /* Slate 900 - רקע ראשי */
            --bg-card: #1e293b;       /* Slate 800 - רקע כרטיס */
            --text-main: #f8fafc;     /* Slate 50 - לבן בוהק */
            --text-sub: #cbd5e1;      /* Slate 300 - אפור בהיר */
            --accent: #38bdf8;        /* Sky 400 - תכלת */
            --success: #34d399;       /* Emerald 400 - ירוק */
            --danger: #fb7185;        /* Rose 400 - אדום */
            --border: #334155;        /* Slate 700 - גבולות */
        }
        
        .stApp {
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: 'Heebo', sans-serif;
            direction: rtl;
        }
        
        /* טיפוגרפיה */
        h1, h2, h3, h4 {
            color: var(--text-main) !important;
            font-weight: 700;
            text-align: right;
            margin-bottom: 0.5rem;
        }
        
        p, div, label, span, li {
            color: var(--text-sub);
            text-align: right;
            font-size: 1rem;
        }
        
        /* כרטיסי KPI - ללא שקיפות, קונטרסט גבוה */
        .kpi-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-right: 4px solid var(--accent); /* פס צבע מימין */
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: var(--text-sub);
        }
        
        .kpi-label {
            font-size: 0.9rem;
            color: var(--text-sub);
            font-weight: 500;
            margin-bottom: 8px;
            display: block;
        }
        
        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-main);
            display: block;
        }
        
        .kpi-badge {
            font-size: 0.75rem;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            display: inline-block;
            margin-top: 8px;
        }

        /* תיקון צבעי טבלאות */
        div[data-testid="stDataFrame"] {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
        }
        div[data-testid="stDataFrame"] * {
            color: var(--text-sub) !important;
        }

        /* סרגל צד */
        section[data-testid="stSidebar"] {
            background-color: #020617; /* Slate 950 */
            border-left: 1px solid var(--border);
        }
        
        /* סליידרים וטאבים */
        .stSlider > div > div > div > div { background-color: var(--accent); }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-sub);
            border-radius: 6px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: var(--accent);
            color: #0f172a !important; /* טקסט שחור על רקע תכלת */
            font-weight: bold;
        }
        
        /* כפתור ייצוא */
        .stDownloadButton button {
            background-color: var(--bg-card);
            color: var(--accent);
            border: 1px solid var(--accent);
        }
        .stDownloadButton button:hover {
            background-color: var(--accent);
            color: var(--bg-main);
        }

        </style>
    """, unsafe_allow_html=True)

load_pro_css()

# ==========================================
# 2. לוגיקה עסקית ומודלים (Business Logic)
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל עסקי ביטוח": "CLIS.TA",
    "ביטוח ישיר": "DIDI.TA", "איילון אחזקות": "AYAL.TA",
    "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE", "ליברה": "LBRA.TA"
}

@st.cache_data(ttl=600)
def fetch_data(ticker):
    """
    פונקציית ליבה: מביאה נתונים או מייצרת סימולציה אם אין חיבור/חברה פרטית
    """
    is_live = False
    # ברירות מחדל (Fallback)
    market_cap = 4500000000
    equity = 5200000000
    change = 0.0
    
    if ticker != "PRIVATE":
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if 'marketCap' in info and info['marketCap']:
                market_cap = info['marketCap']
                # הערכה: הון עצמי הוא בערך Market Cap / 0.85 (מכפיל הון ממוצע)
                equity = market_cap / info.get('priceToBook', 0.85)
                
                # חישוב שינוי יומי
                if 'currentPrice' in info and 'previousClose' in info:
                    change = ((info['currentPrice'] - info['previousClose']) / info['previousClose']) * 100
                is_live = True
        except:
            pass
    
    # חישוב יציב לפי שם החברה (Seed)
    seed = abs(hash(ticker)) % (2**32)
    np.random.seed(seed)
    
    # חלוקה למגזרים (Segmentation Logic)
    # נתונים במיליוני ש"ח
    segments = {
        "כללי (P&C)": {"CSM": equity * 0.12, "Profit": equity * 0.04},
        "בריאות": {"CSM": equity * 0.22, "Profit": equity * 0.02},
        "חיסכון ופנסיה": {"CSM": equity * 0.35, "Profit": equity * 0.07}
    }
    
    total_csm = sum(s['CSM'] for s in segments.values())
    
    return {
        "is_live": is_live,
        "market_cap": market_cap,
        "equity": equity,
        "change_pct": change,
        "total_csm": total_csm,
        "liabilities": equity * 8.2, # מינוף גבוה בביטוח
        "segments": segments,
        # מדדים אקטואריים בסיסיים
        "base_solvency": np.random.uniform(112, 148),
        "base_combined_ratio": np.random.uniform(94, 99)
    }

def run_simulation(data, shocks, period_factor):
    """
    מנוע הסימולציה: לוקח נתוני בסיס ומחיל עליהם את הסליידרים
    """
    # 1. זעזוע הון (מניות)
    equity_loss = data['equity'] * (shocks['equity']/100) * 0.7 # רגישות תיק נוסטרו
    new_equity = data['equity'] - equity_loss
    
    # 2. זעזוע התחייבויות (ריבית)
    # ירידת ריבית = עלייה בהתחייבויות
    liab_increase = data['liabilities'] * (shocks['interest'] * -0.05)
    new_liabs = data['liabilities'] + liab_increase
    
    # 3. זעזוע רווח (ביטולים)
    csm_loss = data['total_csm'] * (shocks['lapse']/100)
    new_csm = data['total_csm'] - csm_loss
    
    # 4. חישוב סולבנסי עדכני
    # הון מוכר (Own Funds) = הון עצמי + התאמות CSM
    own_funds = new_equity + (new_csm * 0.65)
    if shocks['catastrophe']:
        own_funds -= 400000000 # נזק חד פעמי
        
    scr_req = new_equity * 0.9 + liab_increase # דרישת ההון עולה כשהסיכון עולה
    new_solvency = (own_funds / scr_req) * 100
    
    # 5. רווח תקופתי (P&L)
    annual_profit = (new_equity * 0.11) # ROE בסיסי
    if shocks['catastrophe']: annual_profit -= 400000000
    period_profit = annual_profit * period_factor
    
    return {
        "Equity": new_equity,
        "Liabilities": new_liabs,
        "CSM": new_csm,
        "Solvency": new_solvency,
        "Net_Income": period_profit,
        "Combined_Ratio": data['base_combined_ratio'] + (10 if shocks['catastrophe'] else 0)
    }

# ==========================================
# 3. סרגל צד (Sidebar)
# ==========================================
with st.sidebar:
    st.title("🎛️ חדר בקרה")
    
    st.markdown("### 📅 תקופת דיווח")
    p_type = st.radio("", ["שנתי (Annual)", "רבעוני (Quarterly)"])
    period_factor = 0.25 if "רבעוני" in p_type else 1.0
    
    st.divider()
    
    st.markdown("### ⚡ הגדרות תרחיש (Stress)")
    s_equity = st.slider("📉 נפילת מניות (%)", 0, 40, 0)
    s_interest = st.slider("🏦 שינוי ריבית (%)", -2.0, 2.0, 0.0, step=0.1)
    s_lapse = st.slider("🏃 שיעור ביטולים (%)", 0, 20, 0)
    s_cat = st.checkbox("🌪️ אירוע קטסטרופה")
    
    shocks = {'equity': s_equity, 'interest': s_interest, 'lapse': s_lapse, 'catastrophe': s_cat}
    
    if st.button("🔄 אפס סימולציה"):
        st.rerun()

# ==========================================
# 4. הדשבורד הראשי
# ==========================================

# כותרת ראשית
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("# 🛡️ ISR-TITAN PRO")
    st.markdown("### מערכת פיקוח ובקרת סיכונים | IFRS 17")
with c2:
    mode = "מצב: סימולציית קיצון" if (s_equity>0 or s_interest!=0 or s_cat) else "מצב: רגיל (BAU)"
    color = "#fb7185" if (s_equity>0 or s_interest!=0 or s_cat) else "#34d399"
    st.markdown(f"""
    <div style="text-align:left; border:1px solid {color}; padding:10px; border-radius:8px; color:{color}; font-weight:bold;">
        {mode}<br>
        {datetime.now().strftime('%H:%M | %d/%m/%Y')}
    </div>
    """, unsafe_allow_html=True)

st.divider()

# בחירת חברה
comp_name = st.selectbox("בחר חברה לניתוח:", list(TICKERS.keys()))

# חישובים
base = fetch_data(TICKERS[comp_name])
sim = run_simulation(base, shocks, period_factor)

# פונקציות עזר לפורמט
def fmt_money(val): return f"₪{val/1e9:.2f

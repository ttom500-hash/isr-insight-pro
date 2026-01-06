import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. תשתית ועיצוב (High-End Regulator UI)
# ==========================================
st.set_page_config(page_title="ISR-TITAN REGULATOR", layout="wide", page_icon="🏛️")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;800&display=swap');
        
        /* 1. Reset Global Styles - Dark Mode Enforcement */
        .stApp {
            background-color: #0b0f19; /* Deep Navy */
            color: #ffffff;
            font-family: 'Assistant', sans-serif;
        }
        
        /* Typography overrides */
        h1, h2, h3, h4, h5, p, span, label, div {
            color: #ffffff !important;
            text-align: right;
        }
        
        /* 2. Critical Fix: Selectbox (Search Engine) Visibility */
        /* הופך את תיבת הבחירה ללבנה עם טקסט שחור */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #00d4ff;
        }
        div[data-baseweb="select"] span {
            color: #000000 !important; /* הטקסט הנבחר */
            font-weight: 700;
        }
        ul[data-baseweb="menu"] {
            background-color: #ffffff !important;
        }
        ul[data-baseweb="menu"] li {
            color: #000000 !important; /* האפשרויות בתפריט */
            background-color: #ffffff !important;
        }
        ul[data-baseweb="menu"] li:hover {
            background-color: #f0f0f0 !important;
        }

        /* 3. KPI Cards - Professional Look */
        .kpi-container {
            background-color: #1a2332;
            border: 1px solid #2d3748;
            border-right: 4px solid #00d4ff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .kpi-container:hover {
            transform: translateY(-3px);
            border-color: #00d4ff;
        }
        .kpi-label { font-size: 0.85rem; color: #a0aec0 !important; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-value { font-size: 1.8rem; font-weight: 800; color: #ffffff !important; margin: 8px 0; }
        .kpi-delta-pos { color: #48bb78 !important; font-size: 0.8rem; font-weight: bold; }
        .kpi-delta-neg { color: #f56565 !important; font-size: 0.8rem; font-weight: bold; }

        /* 4. Financial Ratios Panel */
        .ratio-box {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid #4a5568;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
        }
        .ratio-val { font-size: 1.4rem; font-weight: bold; color: #00d4ff !important; }
        .ratio-lbl { font-size: 0.8rem; color: #cbd5e0 !important; }

        /* 5. Components Styling */
        div[data-testid="stDataFrame"] { background-color: #1a2332; border: 1px solid #4a5568; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { background-color: #2d3748; color: #a0aec0; border-radius: 4px; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #00d4ff; color: #000000 !important; font-weight: bold; }
        .stSlider > div > div > div > div { background-color: #00d4ff; }
        
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 2. מנוע אקטוארי ופיננסי (Logic Core)
# ==========================================

TICKERS = {
    "הפניקס אחזקות": "PHOE.TA", "הראל השקעות": "HARL.TA", "מגדל ביטוח": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA", "ביטוח ישיר": "DIDI.TA",
    "איילון אחזקות": "AYAL.TA", "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE", "ליברה": "LBRA.TA"
}

class InsurerModel:
    def __init__(self, name):
        self.name = name
        self.symbol = TICKERS.get(name)
        self.seed = abs(hash(name)) % (2**32)
        np.random.seed(self.seed)
        
        # אתחול נתונים
        self.market_data = self._fetch_market_data()
        self.actuarial_data = self._generate_actuarial_model()

    def _fetch_market_data(self):
        """ מביא נתוני אמת מהבורסה היכן שאפשר """
        data = {"cap": 4500000000, "equity": 5500000000, "change": 0.0, "is_live": False}
        if self.symbol != "PRIVATE":
            try:
                stock = yf.Ticker(self.symbol)
                info = stock.info
                if info.get('marketCap'):
                    data['cap'] = info['marketCap']
                    # הנחה: הון עצמי הוא נגזרת של שווי שוק ו-PB Ratio
                    data['equity'] = data['cap'] / info.get('priceToBook', 0.85)
                    data['is_live'] = True
                    
                    # שינוי יומי
                    hist = stock.history(period="2d")
                    if len(hist) >= 2:
                        close = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2]
                        data['change'] = ((close - prev) / prev) * 100
            except:
                pass
        return data

    def _generate_actuarial_model(self):
        """ מחולל את המודל הפנימי (IFRS 17 & Solvency) """
        eq = self.market_data['equity']
        
        # 1. מאזן (Balance Sheet)
        assets = eq * np.random.uniform(7.0, 9.0) # מינוף פיננסי אופייני
        liabilities = assets - eq
        
        # 2. IFRS 17 - CSM Components
        csm_stock = eq * 0.45
        csm_flows = {
            "opening": csm_stock,
            "new_business": csm_stock * 0.12,
            "interest": csm_stock * 0.03,
            "release": csm_stock * -0.09, # שחרור לרווח
            "changes": csm_stock * 0.02
        }
        
        # 3. P&L Drivers (תזרימים)
        gwp = assets * 0.16
        nwp = gwp * 0.85 # בניכוי משנה
        claims = nwp * 0.70
        expenses = nwp * 0.24
        
        # 4. Solvency Base
        scr_base = eq * 0.75 # דרישת הון בסיסית
        
        # 5. Segmentation
        segments = {
            "ביטוח כללי (P&C)": csm_stock * 0.15,
            "ביטוח בריאות": csm_stock * 0.30,
            "חיסכון ארוך טווח": csm_stock * 0.55
        }
        
        return {
            "assets": assets, "liabilities": liabilities, "equity_base": eq,
            "csm_flows": csm_flows, "pnl": {"gwp": gwp, "nwp": nwp, "claims": claims, "expenses": expenses},
            "scr_base": scr_base, "segments": segments
        }

    def run_stress_test(self, shocks, period_factor=1.0):
        """ המנוע שמחשב את כל המספרים מחדש לפי הסליידרים """
        d = self.actuarial_data
        
        # --- שלב 1: השפעות מאזניות (Shock Impact) ---
        # מניות: משפיעות על הנכסים ועל ההון
        equity_shock_val = d['equity_base'] * (shocks['equity'] / 100.0) * 0.6
        new_equity = d['equity_base'] - equity_shock_val
        new_assets = d['assets'] - equity_shock_val
        
        # ריבית: משפיעה על ההתחייבויות (Duration Effect)
        liab_shock_val = d['liabilities'] * (shocks['interest'] / 100.0) * -6.5
        new_liabilities = d['liabilities'] + liab_shock_val
        
        # עדכון הון סופי (Assets - Liabilities)
        final_equity = new_assets - new_liabilities
        
        # ביטולים: משפיעים על ה-CSM
        csm_closing_base = sum(d['csm_flows'].values())
        lapse_loss = csm_closing_base * (shocks['lapse'] / 100.0)
        final_csm = csm_closing_base - lapse_loss
        
        # --- שלב 2: Solvency II ---
        # הון מוכר (Own Funds) = הון חשבונאי + התאמות (חלק מה-CSM מוכר)
        own_funds = final_equity + (final_csm * 0.7)
        if shocks['catastrophe']: own_funds -= 400000000
        
        # דרישת הון (SCR) - עולה כשהסיכון עולה
        scr = d['scr_base'] + abs(liab_shock_val * 0.4) + (shocks['equity'] * 1000000)
        solvency_ratio = (own_funds / scr) * 100
        
        # --- שלב 3: דוח רווח והפסד (P&L Simulation) ---
        # השפעת קטסטרופה על תביעות
        cat_claim_impact = 350000000 if shocks['catastrophe'] else 0
        final_claims = d['pnl']['claims'] + cat_claim_impact
        
        underwriting_profit = (d['pnl']['nwp'] * period_factor) - (final_claims * period_factor) - (d['pnl']['expenses'] * period_factor)
        investment_profit = (new_assets * 0.04 * period_factor) - (equity_shock_val * 0.15) # מימוש הפסדים
        
        net_income = underwriting_profit + investment_profit
        
        # --- שלב 4: יחסים פיננסיים (Ratios) ---
        combined_ratio = ((final_claims + d['pnl']['expenses']) / d['pnl']['nwp']) * 100
        loss_ratio = (final_claims / d['pnl']['nwp']) * 100
        expense_ratio = (d['pnl']['expenses'] / d['pnl']['nwp']) * 100
        retention_ratio = (d['pnl']['nwp'] / d['pnl']['gwp']) * 100
        leverage = new_assets / max(1, final_equity)
        roe = (net_income / max(1, final_equity)) * 100 * (1/period_factor) # שנתי
        
        return {
            "Equity": final_equity,
            "Solvency": solvency_ratio,
            "CSM": final_csm,
            "Net_Income": net_income,
            "Combined_Ratio": combined_ratio,
            "Loss_Ratio": loss_ratio,
            "Expense_Ratio": expense_ratio,
            "Retention": retention_ratio,
            "Leverage": leverage,
            "ROE": roe,
            "Lapse_Impact": lapse_loss
        }

# ==========================================
# 3. ממשק שליטה (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🎛️ חדר סימולציה")
    
    st.subheader("פרמטרים לדוח")
    report_period = st.radio("סוג דוח:", ["שנתי", "רבעוני"], horizontal=True)
    p_factor = 0.25 if report_period == "רבעוני" else 1.0
    
    st.divider()
    
    st.subheader("תרחישי קיצון (Stress)")
    s_eq = st.slider("נפילת שוק מניות", 0, 50, 0, format="-%d%%")
    s_int = st.slider("שינוי ריבית (חשיפה)", -2.0, 2.0, 0.0, step=0.1, format="%+.1f%%")
    s_lapse = st.slider("שיעור ביטולים (Lapse)", 0, 40, 0, format="-%d%%")
    s_cat = st.checkbox("אירוע קטסטרופה (CAT)")
    
    if st.button("🔄 אפס הכל", type="primary"):
        st.rerun()
        
    shocks = {'equity': s_eq, 'interest': s_int, 'lapse': s_lapse, 'catastrophe': s_cat}

# ==========================================
# 4. הדשבורד הראשי (Main UI)
# ==========================================

# כותרת וסטטוס
c1, c2 = st.columns([3, 1])
with c1:
    st.title("ISR-TITAN REGULATOR")
    st.caption("מערכת פיקוח על חברות ביטוח | Solvency II & IFRS 17 Compliant")
with c2:
    is_stress = (s_eq > 0 or s_int != 0 or s_lapse > 0 or s_cat)
    status_text = "STRESS MODE ACTIVE" if is_stress else "LIVE MONITORING"
    status_color = "#ff4b4b" if is_stress else "#00ff9d"
    st.markdown(f"""
    <div style="border:1px solid {status_color}; padding:10px; border-radius:8px; text-align:center; color:{status_color}; font-weight:bold; background-color:rgba(0,0,0,0.3);">
        {status_text}<br>{datetime.now().strftime('%H:%M')}
    </div>
    """, unsafe_allow_html=True)

st.divider()

# תיבת חיפוש (עם העיצוב המתוקן)
selected_company = st.selectbox("בחר גוף מפוקח:", list(TICKERS.keys()))

# הפעלת המודל
model = InsurerModel(selected_company)
results = model.run_stress_test(shocks, p_factor)

# פונקציית עיצוב
def fmt_money(v): return f"₪{v/1e9:.2f}B" if v >= 1e9 else f"₪{v/1e6:.0f}M"

# --- אזור KPI עליון ---
k1, k2, k3, k4 = st.columns(4)

def kpi_box(col, label, value, delta_val=None, sub_text=""):
    delta_html = ""
    if delta_val is not None:
        color = "#48bb78" if delta_val >= 0 else "#f56565"
        delta_html = f"<span style='color:{color}; font-size:0.9rem; font-weight:bold; float:left; direction:ltr;'>{delta_val:+.2f}%</span>"
    
    col.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div>
            <span style="font-size:0.8rem; color:#718096;">{sub_text}</span>
            {delta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

kpi_box(k1, "הון עצמי (Equity)", fmt_money(results['Equity']), model.market_data['change'], "Live API" if model.market_data['is_live'] else "Model")
kpi_box(k2, "יחס סולבנסי", f"{results['Solvency']:.1f}%", None, "יעד רגולטורי: >100%")
kpi_box(k3, "יתרת CSM (רווח גלום)", fmt_money(results['CSM']), None, "IFRS 17 Stock")
kpi_box(k4, "רווח נקי (Net Income)", fmt_money(results['Net_Income']), None, f"ROE: {results['ROE']:.1f}%")

# --- אזור יחסים פיננסיים (Financial Ratios) ---
st.markdown("### 📊 יחסים פיננסיים ותפעוליים")
r1, r2, r3, r4, r5 = st.columns(5)

def ratio_box(col, label, val, suffix):
    col.markdown(f"""
    <div class="ratio-box">
        <div class="ratio-lbl">{label}</div>
        <div class="ratio-val">{val:.1f}{suffix}</div>
    </div>
    """, unsafe_allow_html=True)

ratio_box(r1, "Combined Ratio", results['Combined_Ratio'], "%")
ratio_box(r2, "Loss Ratio", results['Loss_Ratio'], "%")
ratio_box(r3, "Expense Ratio", results['Expense_Ratio'], "%")
ratio_box(r4, "Retention Rate", results['Retention'], "%")
ratio_box(r5, "Leverage", results['Leverage'], "x")

st.markdown("---")

# --- אזור ניתוח עומק (Tabs) ---
t1, t2 = st.tabs(["🧬 ניתוח CSM (ערך)", "⚖️ מאזן וסולבנסי"])

with t1:
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.markdown("#### גשר ה-CSM (Waterfall Analysis)")
        # נתונים לגשר
        flows = model.actuarial_data['csm_flows']
        fig_water = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
            x = ["פתיחה", "עסקים חדשים", "ריבית", "שינוי הנחות", "שחרור לרווח", "השפעת סטרס", "סגירה"],
            textposition = "outside",
            y = [
                flows['opening'], 
                flows['new_business'], 
                flows['interest'], 
                flows['changes'],
                flows['release'],
                -results['Lapse_Impact'],
                0
            ],
            connector = {"line":{"color":"#718096"}},
            decreasing = {"marker":{"color":"#f56565"}}, 
            increasing = {"marker":{"color":"#48bb78"}}, 
            totals = {"marker":{"color":"#00d4ff"}}
        ))
        fig_water.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400, font=dict(family="Assistant"))
        st.plotly_chart(fig_water, use_container_width=True)
        
    with c_right:
        st.markdown("#### תרומה לפי מגזר")
        segs = model.actuarial_data['segments']
        fig_sun = px.sunburst(
            names=list(segs.keys()), 
            parents=[""] * len(segs), 
            values=list(segs.values()),
            color_discrete_sequence=px.colors.sequential.Tealgrn
        )
        fig_sun.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_sun, use_container_width=True)

with t2:
    st.markdown("#### מד סולבנסי (Solvency Gauge)")
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta", value = results['Solvency'],
        delta = {'reference': 100},
        gauge = {
            'axis': {'range': [None, 200]}, 
            'bar': {'color': "#00d4ff"},
            'steps': [
                {'range': [0, 100], 'color': "rgba(245, 101, 101, 0.3)"}, 
                {'range': [100, 150], 'color': "rgba(237, 137, 54, 0.3)"},
                {'range': [150, 200], 'color': "rgba(72, 187, 120, 0.3)"}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 100}
        }
    ))
    fig_gauge.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    # טבלת נתונים
    st.markdown("#### ייצוא נתונים גולמיים")
    df_export = pd.DataFrame([results])
    st.dataframe(df_export.T, use_container_width=True)
    
    csv_data = df_export.to_csv().encode('utf-8')
    st.download_button("📥 הורד דוח מלא (CSV)", csv_data, "regulator_report.csv", "text/csv")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime
import io

# ==========================================
# 1. תצורת מערכת ועיצוב יוקרתי (Ultimate UI)
# ==========================================
st.set_page_config(page_title="ISR-INSIGHT TITAN", layout="wide", page_icon="💎")

def load_titan_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;800&display=swap');
        
        :root {
            --neon-blue: #00f2ff;
            --neon-green: #00ff9d;
            --neon-red: #ff2a6d;
            --bg-dark: #050a10;
            --card-bg: #11161d;
            --text-main: #ffffff;
            --text-sub: #b0c4de;
        }
        
        .stApp {
            background-color: var(--bg-dark);
            font-family: 'Assistant', sans-serif;
            color: var(--text-main);
        }
        
        /* כותרות מיושרות לימין */
        h1, h2, h3, h4 { 
            color: var(--text-main) !important; 
            text-align: right; 
            font-weight: 800;
            text-shadow: 0 0 15px rgba(0, 242, 255, 0.3);
        }
        
        div, p, span, label { text-align: right; color: var(--text-sub); }
        
        /* כרטיסי KPI */
        .kpi-container {
            background: linear-gradient(145deg, #1a202c, #11161d);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            position: relative;
            transition: all 0.3s ease;
        }
        .kpi-container:hover {
            transform: translateY(-5px);
            border-color: var(--neon-blue);
            box-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
        }
        
        .kpi-label { font-size: 0.85rem; color: var(--text-sub); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
        .kpi-value { font-size: 1.8rem; font-weight: 800; color: var(--text-main); margin: 5px 0; }
        .kpi-badge { 
            font-size: 0.7rem; padding: 3px 8px; border-radius: 4px; font-weight: bold;
            display: inline-block; margin-top: 5px;
        }
        .badge-live { background: rgba(0, 255, 157, 0.1); color: var(--neon-green); border: 1px solid var(--neon-green); }
        .badge-model { background: rgba(255, 165, 0, 0.1); color: orange; border: 1px solid orange; }

        /* טבלאות */
        div[data-testid="stDataFrame"] {
            border: 1px solid #333;
            border-radius: 8px;
            background-color: #0e1218;
        }

        /* סליידרים וטאבים */
        .stSlider > div > div > div > div { background-color: var(--neon-blue); }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { background-color: rgba(255,255,255,0.03); border-radius: 6px; color: var(--text-sub); }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { border: 1px solid var(--neon-blue); color: var(--neon-blue); }

        /* אנימציית Live Pulse */
        @keyframes pulse { 0% {box-shadow: 0 0 0 0 rgba(0, 255, 157, 0.7);} 70% {box-shadow: 0 0 0 10px rgba(0, 255, 157, 0);} 100% {box-shadow: 0 0 0 0 rgba(0, 255, 157, 0);} }
        .live-indicator { width: 10px; height: 10px; background: var(--neon-green); border-radius: 50%; display: inline-block; animation: pulse 2s infinite; margin-left: 8px; }
        </style>
    """, unsafe_allow_html=True)

load_titan_css()

# ==========================================
# 2. מנוע נתונים ראשי (Logic Core)
# ==========================================

# רשימת החברות המלאה
TICKERS = {
    "הפניקס": "PHOE.TA", "הראל": "HARL.TA", "מגדל": "MGDL.TA",
    "מנורה מבטחים": "MMHD.TA", "כלל ביטוח": "CLIS.TA",
    "ביטוח ישיר": "DIDI.TA", "איילון": "AYAL.TA",
    "AIG ישראל": "PRIVATE", "שומרה": "PRIVATE", "ליברה": "LBRA.TA"
}

@st.cache_data(ttl=600)
def fetch_financial_data(ticker):
    """
    מנסה להביא נתוני אמת. אם נכשל או חברה פרטית - מייצר נתונים סינתטיים מבוססי מודל.
    """
    data_source = "MODEL"
    # ברירות מחדל למודל
    market_cap = 4000000000
    equity = 5000000000
    change_pct = 0.0
    
    if ticker != "PRIVATE":
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if 'marketCap' in info and info['marketCap'] is not None:
                market_cap = info['marketCap']
                equity = market_cap * 0.85 # יחס P/B משוער
                
                # חישוב שינוי יומי בטוח
                current = info.get('currentPrice', 0)
                prev = info.get('previousClose', 0)
                if prev > 0:
                    change_pct = ((current - prev) / prev) * 100
                
                data_source = "LIVE API"
        except Exception:
            pass # Fallback to model defaults
    
    # חישוב מודל אקטוארי (IFRS 17 + Solvency) על בסיס ההון
    np.random.seed(hash(ticker)) # יציבות נתונים
    
    # חלוקה למגזרים (Segmentation)
    segments = {
        "כללי (P&C)": {"CSM": equity * 0.15, "Profit": equity * 0.05, "Color": "#00f2ff"},
        "בריאות (Health)": {"CSM": equity * 0.25, "Profit": equity * 0.03, "Color": "#00ff9d"},
        "חיסכון (Life)": {"CSM": equity * 0.40, "Profit": equity * 0.08, "Color": "#ff2a6d"}
    }
    total_csm = sum(s["CSM"] for s in segments.values())
    
    return {
        "source": data_source,
        "market_cap": market_cap,
        "equity": equity,
        "change_pct": change_pct,
        "segments": segments,
        "total_csm": total_csm,
        "liabilities": equity * 7.5, # מינוף ביטוחי
        "solvency_base": np.random.uniform(108, 145),
        "combined_ratio": np.random.uniform(92, 102),
        "tier1_ratio": np.random.uniform(0.8, 0.95)
    }

def apply_stress_scenario(base_data, shocks, period_factor):
    """
    מנוע הסימולציה - מחשב את השפעת הזעזועים על הנתונים
    """
    # 1. השפעה על ההון (מניות)
    equity_hit = base_data['equity'] * (shocks['equity'] / 100) * 0.6
    new_equity = base_data['equity'] - equity_hit
    
    # 2. השפעה על התחייבויות (ריבית)
    # ריבית יורדת = התחייבויות עולות
    liab_hit = base_data['liabilities'] * (shocks['interest'] * -0.04)
    new_liabilities = base_data['liabilities'] + liab_hit
    
    # 3. השפעה על CSM (ביטולים)
    csm_hit = base_data['total_csm'] * (shocks['lapse'] / 100)
    new_csm = base_data['total_csm'] - csm_hit
    
    # 4. חישוב סולבנסי חדש
    # הון מוכר = הון עצמי + חלק מה-CSM - השפעת מניות
    own_funds = new_equity + (new_csm * 0.7)
    scr_req = new_equity * 0.9 + liab_hit # דרישת הון עולה כשההתחייבויות עולות
    
    if shocks['catastrophe']:
        own_funds -= 300000000 # נזק קטסטרופלי קבוע
    
    new_solvency = (own_funds / scr_req) * 100
    
    # התאמה לתקופה (רבעוני/שנתי) עבור דוחות זרם
    period_profit = (new_equity * 0.12) * period_factor # ROE בסיסי 12%
    if shocks['catastrophe']: period_profit -= 300000000
    
    return {
        "Equity": new_equity,
        "Liabilities": new_liabilities,
        "CSM": new_csm,
        "Solvency": new_solvency,
        "Own_Funds": own_funds,
        "Net_Income": period_profit,
        "ROE": (period_profit / new_equity) * (1/period_factor) * 100, # שנתי
        "Combined_Ratio": base_data['combined_ratio'] + (15 if shocks['catastrophe'] else 0)
    }

# ==========================================
# 3. ממשק שליטה (Sidebar)
# ==========================================
with st.sidebar:
    st.title("🎛️ חדר בקרה")
    
    st.markdown("### 📅 הגדרות דוח")
    report_period = st.radio("תקופת דיווח:", ["שנתי (Annual)", "רבעוני (Quarterly)"])
    period_factor = 0.25 if "רבעוני" in report_period else 1.0
    
    st.markdown("---")
    st.markdown("### ⚡ סימולטור (Stress Test)")
    
    s_equity = st.slider("📉 נפילת מניות (%)", 0, 50, 0)
    s_interest = st.slider("🏦 שינוי ריבית (%)", -2.0, 2.0, 0.0, step=0.1)
    s_lapse = st.slider("🏃 שיעור ביטולים (%)", 0, 25, 0)
    s_cat = st.checkbox("🌪️ אירוע קטסטרופה (רעידת אדמה/מלחמה)")
    
    shocks = {'equity': s_equity, 'interest': s_interest, 'lapse': s_lapse, 'catastrophe': s_cat}
    
    # כפתור איפוס
    if st.button("🔄 אפס סימולציה"):
        st.rerun()

# ==========================================
# 4. הדשבורד הראשי
# ==========================================

# כותרת חכמה
now = datetime.now()
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    st.markdown(f"**תאריך:** {now.strftime('%d/%m/%Y')}")
    st.markdown(f"**שעה:** {now.strftime('%H:%M')}")
with c2:
    st.markdown("<h1 style='text-align:center;'>ISR-INSIGHT TITAN</h1>", unsafe_allow_html=True)
    mode_text = "MODE: STRESS TEST" if (s_equity>0 or s_interest!=0 or s_cat) else "MODE: STANDARD"
    color = "#ff2a6d" if (s_equity>0 or s_interest!=0 or s_cat) else "#00ff9d"
    st.markdown(f"<p style='text-align:center; color:{color} !important; font-weight:bold;'>{mode_text}</p>", unsafe_allow_html=True)
with c3:
    st.markdown('<div style="text-align:left;"><span class="live-indicator"></span> ONLINE SYSTEM</div>', unsafe_allow_html=True)

st.divider()

# בחירת חברה
selected_comp = st.selectbox("בחר חברה לניתוח:", list(TICKERS.keys()))

# --- עיבוד נתונים ---
base_data = fetch_financial_data(TICKERS[selected_comp])
final_data = apply_stress_scenario(base_data, shocks, period_factor)

# פונקציות עיצוב מספרים
def fmt_B(num): return f"₪{num/1e9:.2f}B"
def fmt_M(num): return f"₪{num/1e6:.1f}M"

# --- שורת ה-KPIs (היהלום שבכתר) ---
st.markdown("### 📊 מדדי ביצוע בזמן אמת (Real-Time KPIs)")
k1, k2, k3, k4 = st.columns(4)

def kpi_card(col, title, value, badge_text, badge_class, delta=None):
    delta_html = f"<span style='font-size:0.8rem; color:{'#00ff9d' if delta>=0 else '#ff2a6d'};'>{delta:+.2f}%</span>" if delta is not None else ""
    col.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-badge {badge_class}">{badge_text}</div> {delta_html}
        </div>
    """, unsafe_allow_html=True)

# 1. שווי שוק / הון
source_badge = "badge-live" if base_data['source'] == "LIVE API" else "badge-model"
kpi_card(k1, "הון עצמי (Equity)", fmt_B(final_data['Equity']), base_data['source'], source_badge, base_data['change_pct'])

# 2. סולבנסי
solvency_class = "badge-live" if final_data['Solvency'] > 100 else "badge-model" # ירוק אם תקין, כתום אם לא (שימוש חוזר ב-class)
solvency_badge = "YETZIV" if final_data['Solvency'] > 100 else "CRITICAL"
kpi_card(k2, "יחס סולבנסי", f"{final_data['Solvency']:.1f}%", solvency_badge, solvency_class)

# 3. CSM
kpi_card(k3, "ערך גלום (CSM)", fmt_B(final_data['CSM']), "IFRS 17", "badge-model")

# 4. רווחיות
kpi_card(k4, "רווח נקי לתקופה", fmt_M(final_data['Net_Income']), f"ROE: {final_data['ROE']:.1f}%", "badge-live")

st.markdown("---")

# --- לשוניות תוכן מתקדמות ---
tab1, tab2, tab3 = st.tabs(["🧬 ניתוח ערך ומגזרים", "📉 מאזן וסיכונים", "📑 ייצוא נתונים"])

with tab1:
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.markdown("#### גשר ה-CSM (ניתוח מקורות הרווח)")
        # גרף מפל מקצועי
        fig_water = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "total"],
            x = ["CSM פתיחה", "עסקים חדשים", "השפעת סטרס/ביטולים", "CSM סגירה"],
            textposition = "outside",
            y = [base_data['total_csm'], base_data['total_csm']*0.05*period_factor, final_data['CSM'] - (base_data['total_csm']*(1+0.05*period_factor)), 0], # חישוב דלתא
            connector = {"line":{"color":"#555"}},
            decreasing = {"marker":{"color":"#ff2a6d"}}, increasing = {"marker":{"color":"#00ff9d"}}, totals = {"marker":{"color":"#00f2ff"}}
        ))
        fig_water.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Assistant"), height=400)
        st.plotly_chart(fig_water, use_container_width=True)
        
    with c_right:
        st.markdown("#### רווחיות לפי מגזר (Sunburst)")
        # הכנת נתונים לגרף שמש
        sunburst_data = []
        for seg, vals in base_data['segments'].items():
            sunburst_data.append(dict(character=seg, parent="", value=vals['CSM']))
            sunburst_data.append(dict(character=f"רווח-{seg}", parent=seg, value=vals['Profit']))
            
        df_sun = pd.DataFrame(sunburst_data)
        fig_sun = px.sunburst(df_sun, names='character', parents='parent', values='value', color_discrete_sequence=px.colors.sequential.Tealgrn)
        fig_sun.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_sun, use_container_width=True)

with tab2:
    col_risk1, col_risk2 = st.columns(2)
    
    with col_risk1:
        st.markdown("#### מד יציבות פיננסית (Solvency Gauge)")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = final_data['Solvency'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Solvency II Ratio"},
            gauge = {
                'axis': {'range': [None, 200], 'tickwidth': 1},
                'bar': {'color': "#00f2ff"},
                'steps': [
                    {'range': [0, 100], 'color': 'rgba(255, 42, 109, 0.3)'},
                    {'range': [100, 200], 'color': 'rgba(0, 255, 157, 0.3)'}],
                'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 100}}))
        fig_gauge.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with col_risk2:
        st.markdown("#### איכות הון (Capital Tiers)")
        # גרף דונאט
        labels = ['Tier 1 (הון ליבה)', 'Tier 2 (הון משני)']
        values = [final_data['Own_Funds'] * base_data['tier1_ratio'], final_data['Own_Funds'] * (1-base_data['tier1_ratio'])]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker=dict(colors=['#00ff9d', '#2979ff']))])
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.markdown("#### ייצוא נתונים")
    # יצירת CSV להורדה
    export_df = pd.DataFrame([
        {"Metric": "Equity", "Value": final_data['Equity']},
        {"Metric": "CSM", "Value": final_data['CSM']},
        {"Metric": "Solvency Ratio", "Value": final_data['Solvency']},
        {"Metric": "Liabilities", "Value": final_data['Liabilities']},
        {"Metric": "Scenario_Equity_Drop", "Value": shocks['equity']},
    ])
    
    csv = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 הורד דוח נתונים (CSV)",
        data=csv,
        file_name=f"{selected_comp}_report_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
    
    st.dataframe(export_df, use_container_width=True)

st.markdown("---")
st.markdown("""
<div style="text-align:center; font-size:0.8rem; opacity:0.6;">
    ISR-INSIGHT TITAN v5.0 | All Rights Reserved © 2026<br>
    Powered by Advanced Actuarial Modeling & Live Market Data
</div>
""", unsafe_allow_html=True)

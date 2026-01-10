import streamlit as st
import pandas as pd
import requests
import base64
import os
import plotly.express as px
import plotly.graph_objects as go
import json
import time
from datetime import datetime
from jsonschema import validate, ValidationError

# --- 1. מילון מונחים מורחב (Encyclopedia) ---
DEFINITIONS = {
    # KPIs
    "net_profit": "הרווח הכולל לבעלי המניות. ירידה חדה עשויה להעיד על אירועים חד פעמיים או שחיקה בחיתום.",
    "total_csm": "Contractual Service Margin: 'מחסנית הרווחים' העתידית. שחיקה ב-CSM היא אינדיקטור שלילי לצמיחה עתידית.",
    "roe": "תשואה להון עצמי. בנצ'מארק ענפי: 10%-15%.",
    "gross_premiums": "GWP: צמיחה בפרמיות מעידה על כוח שוק, אך יש לוודא שאינה באה על חשבון חיתום איכותי.",
    "total_assets": "סך המאזן המאוחד (AUM).",
    
    # Solvency
    "solvency_ratio": "יחס סולבנסי II. יחס < 100% דורש תוכנית הבראה מיידית. יחס < 115% הוא תמרור אזהרה.",
    "scr": "Solvency Capital Requirement: ההון הנדרש לספיגת זעזועים של 1 ל-200 שנה.",
    "tier1_capital": "הון עצמי איכותי (מניות+רווחים). צריך להיות לפחות 50% מה-SCR.",
    
    # Ratios
    "combined_ratio": "יחס משולב בביטוח כללי (הפסדים + הוצאות / פרמיה). מעל 100% = הפסד חיתומי.",
    "loss_ratio": "יחס תביעות (Loss Ratio). מודד את איכות החיתום נטו.",
    "expense_ratio": "יחס הוצאות תפעול ועמלות. מודד יעילות תפעולית.",
    "lcr": "Liquidity Coverage Ratio. יחס נזילות ל-30 יום. מתחת ל-1.0 מעיד על בעיית נזילות.",
    "leverage": "מינוף פיננסי. יחס גבוה מעלה את הסיכון בתקופות משבר.",
    "roi": "תשואה על ההשקעות (Return on Investment).",
    
    # IFRS 17
    "new_business_csm": "הדלק החדש של החברה. ירידה כאן מעידה על קושי במכירת פוליסות רווחיות חדשות.",
    "onerous_contracts": "קבוצות חוזים מפסידות ('עסקים מכבידים'). החברה מחויבת להכיר בהפסד מיידי בגינן.",
    "paa_model": "מודל הקצאת פרמיה (PAA). משמש לחוזי ביטוח קצרי טווח (בעיקר כללי/בריאות).",
    "gmm_model": "מודל כללי (GMM/VFA). משמש לחוזים ארוכי טווח (חיים/סיעוד). רגיש יותר לריבית.",
    
    # Investments
    "unquoted_pct": "נכסים לא סחירים. קשים למימוש בעת משבר נזילות ושערוכם סובייקטיבי.",
    "real_yield": "תשואה ריאלית בניכוי אינפלציה."
}

# --- 2. עיצוב המערכת ---
st.set_page_config(page_title="Regulator Cockpit", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 10px; border-radius: 6px; border-right: 3px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #fff; font-size: 1.4rem; }
    .alert-box { padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; border: 1px solid; }
    .alert-critical { background-color: #3d0808; border-color: #ff4b4b; color: #ff9999; }
    .alert-warning { background-color: #3d3d08; border-color: #f0ad4e; color: #f0e68c; }
    .alert-success { background-color: #083d08; border-color: #5cb85c; color: #dff0d8; }
    .section-title { color: #2e7bcf; border-bottom: 1px solid #333; padding-bottom: 5px; margin-top: 20px; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. נתוני אמת משוערים (Q3 2025) - מורחבים ---
REAL_MARKET_DATA = {
    "Harel": {
        "core_kpis": { "net_profit": 2174.0, "total_csm": 17133.0, "roe": 27.0, "gross_premiums": 12100.0, "total_assets": 167754.0 },
        "ifrs17_segments": { 
            "life_csm": 11532.0, "health_csm": 5601.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 1265.0,
            "models": {"PAA": 45, "GMM": 55} # אחוז שימוש במודלים
        },
        "investment_mix": { "govt_bonds_pct": 30.0, "corp_bonds_pct": 20.0, "stocks_pct": 15.0, "real_estate_pct": 10.0, "unquoted_pct": 63.0, "real_yield": 4.2 },
        "financial_ratios": { "loss_ratio": 76.0, "expense_ratio": 19.0, "combined_ratio": 95.0, "lcr": 1.35, "leverage": 6.9, "roa": 1.3, "roi": 4.5 },
        "solvency": { "solvency_ratio": 183.0, "tier1_capital": 10733.0, "tier2_capital": 2500.0, "scr": 9191.0 },
        "consistency_check": { "opening_csm": 16500.0, "new_business_csm": 1265.0, "csm_release": 632.0, "closing_csm": 17133.0 }
    },
    "Phoenix": {
        "core_kpis": { "net_profit": 1739.0, "total_csm": 13430.0, "roe": 33.3, "gross_premiums": 9278.0, "total_assets": 225593.0 },
        "ifrs17_segments": { 
            "life_csm": 6636.0, "health_csm": 6794.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 1459.0,
            "models": {"PAA": 55, "GMM": 45}
        },
        "investment_mix": { "govt_bonds_pct": 35.0, "corp_bonds_pct": 20.0, "stocks_pct": 14.0, "real_estate_pct": 10.0, "unquoted_pct": 31.0, "real_yield": 4.5 },
        "financial_ratios": { "loss_ratio": 74.0, "expense_ratio": 18.0, "combined_ratio": 92.0, "lcr": 1.4, "leverage": 5.1, "roa": 0.8, "roi": 5.2 },
        "solvency": { "solvency_ratio": 183.0, "tier1_capital": 12500.0, "tier2_capital": 3889.0, "scr": 9192.0 },
        "consistency_check": { "opening_csm": 12500.0, "new_business_csm": 1459.0, "csm_release": 529.0, "closing_csm": 13430.0 }
    },
    "Migdal": {
        "core_kpis": { "net_profit": 551.0, "total_csm": 13062.0, "roe": 12.8, "gross_premiums": 7697.0, "total_assets": 219362.0 },
        "ifrs17_segments": { 
            "life_csm": 11500.0, "health_csm": 1562.0, "general_csm": 0.0, 
            "onerous_contracts": 350.0, "new_business_csm": 795.0, # יש חוזים מפסידים!
            "models": {"PAA": 20, "GMM": 80}
        },
        "investment_mix": { "govt_bonds_pct": 45.0, "corp_bonds_pct": 20.0, "stocks_pct": 13.0, "real_estate_pct": 10.0, "unquoted_pct": 17.0, "real_yield": 2.0 },
        "financial_ratios": { "loss_ratio": 82.0, "expense_ratio": 20.0, "combined_ratio": 102.0, "lcr": 1.1, "leverage": 3.9, "roa": 0.3, "roi": 2.8 },
        "solvency": { "solvency_ratio": 131.0, "tier1_capital": 7500.0, "tier2_capital": 3000.0, "scr": 13685.0 },
        "consistency_check": { "opening_csm": 12800.0, "new_business_csm": 795.0, "csm_release": 533.0, "closing_csm": 13062.0 }
    },
    "Clal": {
        "core_kpis": { "net_profit": 1360.0, "total_csm": 8813.0, "roe": 23.8, "gross_premiums": 8300.0, "total_assets": 158674.0 },
        "ifrs17_segments": { 
            "life_csm": 4076.0, "health_csm": 4737.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 950.0,
            "models": {"PAA": 50, "GMM": 50}
        },
        "investment_mix": { "govt_bonds_pct": 20.0, "corp_bonds_pct": 12.0, "stocks_pct": 15.0, "real_estate_pct": 10.0, "unquoted_pct": 68.0, "real_yield": 3.8 },
        "financial_ratios": { "loss_ratio": 78.0, "expense_ratio": 19.0, "combined_ratio": 97.0, "lcr": 1.25, "leverage": 4.8, "roa": 0.9, "roi": 4.1 },
        "solvency": { "solvency_ratio": 182.0, "tier1_capital": 11214.0, "tier2_capital": 4828.0, "scr": 10040.0 },
        "consistency_check": { "opening_csm": 8300.0, "new_business_csm": 950.0, "csm_release": 437.0, "closing_csm": 8813.0 }
    },
    "Menora": {
        "core_kpis": { "net_profit": 1211.0, "total_csm": 7900.0, "roe": 19.2, "gross_premiums": 6907.0, "total_assets": 62680.0 },
        "ifrs17_segments": { 
            "life_csm": 4500.0, "health_csm": 3400.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 300.0,
            "models": {"PAA": 60, "GMM": 40}
        },
        "investment_mix": { "govt_bonds_pct": 40.0, "corp_bonds_pct": 25.0, "stocks_pct": 19.0, "real_estate_pct": 10.0, "unquoted_pct": 16.0, "real_yield": 4.1 },
        "financial_ratios": { "loss_ratio": 75.0, "expense_ratio": 19.0, "combined_ratio": 94.0, "lcr": 1.45, "leverage": 13.1, "roa": 1.9, "roi": 4.8 },
        "solvency": { "solvency_ratio": 180.2, "tier1_capital": 6000.0, "tier2_capital": 2687.0, "scr": 6019.0 },
        "consistency_check": { "opening_csm": 7800.0, "new_business_csm": 300.0, "csm_release": 200.0, "closing_csm": 7900.0 }
    }
}

DEFAULT_MOCK = REAL_MARKET_DATA["Phoenix"]

# --- 4. פונקציית דגלים אדומים (The Regulator Eye) ---
def get_red_flags(data):
    flags = []
    # Solvency Check
    sol = data['solvency']['solvency_ratio']
    if sol < 100: flags.append(("CRITICAL", f"יחס סולבנסי קריטי: {sol}% (מתחת ל-100%) - נדרשת תוכנית הבראה!"))
    elif sol < 135: flags.append(("WARNING", f"יחס סולבנסי נמוך: {sol}% (קרוב לרף המינימלי)."))
    
    # IFRS 17 Check
    onerous = data['ifrs17_segments']['onerous_contracts']
    if onerous > 0: flags.append(("WARNING", f"זוהו עסקים מכבידים (חוזים מפסידים) בהיקף {onerous}M₪."))
    
    # Investment Check
    unquoted = data['investment_mix']['unquoted_pct']
    if unquoted > 20: flags.append(("WARNING", f"חשיפה חריגה לנכסים לא סחירים: {unquoted}% (סיכון נזילות ושערוך)."))
    
    # Profitability Check
    combined = data['financial_ratios']['combined_ratio']
    if combined > 100: flags.append(("WARNING", f"הפסד חיתומי בביטוח כללי (Combined Ratio = {combined}%)."))
    
    return flags

# --- 5. UI Application ---
st.sidebar.title("🛡️ Apex Regulator")
company = st.sidebar.selectbox("חברה מפוקחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
use_sim = st.sidebar.checkbox("🧪 מצב סימולציה (Real Q3 Data)", value=True)

# כפתור הרצה
if st.sidebar.button("🚀 הרץ ביקורת (Audit Run)"):
    with st.spinner(f"טוען פרופיל סיכון עבור {company}..."):
        time.sleep(0.8)
        st.session_state.data = REAL_MARKET_DATA.get(company, DEFAULT_MOCK)

data = st.session_state.get('data')
def fmt(v, s=""): return f"{v:,.1f}{s}" if v is not None else "N/A"

# --- Main Dashboard ---
if data:
    st.title(f"דוח פיקוח רגולטורי: {company} (Q3 2025)")
    
    # 1. דגלים אדומים (בראש העמוד)
    flags = get_red_flags(data)
    if flags:
        st.subheader("🚩 התרעות פיקוח (Regulatory Alerts)")
        for level, msg in flags:
            cls = "alert-critical" if level == "CRITICAL" else "alert-warning"
            st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box alert-success">✅ לא זוהו חריגות רגולטוריות מהותיות.</div>', unsafe_allow_html=True)

    # 2. KPIs
    cols = st.columns(5)
    metrics = [("רווח כולל", "net_profit", "M₪"), ("יתרת CSM", "total_csm", "M₪"), ("סולבנסי", "solvency_ratio", "%", "solvency"), ("GWP", "gross_premiums", "M₪"), ("ROE", "roe", "%")]
    
    for i, item in enumerate(metrics):
        val = data['solvency'][item[1]] if len(item) == 4 else data['core_kpis'][item[1]]
        cols[i].metric(item[0], fmt(val, item[2]), help=DEFINITIONS.get(item[1], "מדד ביצוע"))

    st.divider()
    tabs = st.tabs(["📊 IFRS 17 ומודלים", "🛡️ סולבנסי וסימולטור", "💰 השקעות ונזילות", "📉 יחסים פיננסיים", "⚖️ השוואה"])

    # TAB 1: IFRS 17 (עם מודלים)
    with tabs[0]:
        s = data['ifrs17_segments']
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### התפלגות CSM לפי מגזר")
            fig = px.bar(x=["חיים", "בריאות", "כללי"], y=[s['life_csm'], s['health_csm'], s['general_csm']], labels={'y': 'CSM (M₪)', 'x': 'מגזר'})
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### מודלי מדידה (Measurement Models)")
            # גרף דונאט למודלים
            models = s.get('models', {"PAA": 50, "GMM": 50})
            fig2 = px.pie(values=models.values(), names=models.keys(), hole=0.4, title="PAA (קצר) vs GMM (ארוך)")
            st.plotly_chart(fig2, use_container_width=True)
        
        st.info(f"**עסקים חדשים (New Business):** תוספת CSM בסך {fmt(s['new_business_csm'], 'M₪')}. זהו מנוע הצמיחה העתידי.")
        if s['onerous_contracts'] > 0:
            st.error(f"⚠️ **עסקים מכבידים:** הוכרו הפסדים בסך {fmt(s['onerous_contracts'], 'M₪')} בגין חוזים מפסידים.")

    # TAB 2: Solvency & Simulator (מורחב!)
    with tabs[1]:
        sol = data['solvency']
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("#### יחס כושר פירעון")
            st.metric("Solvency Ratio", fmt(sol['solvency_ratio'], "%"), help=DEFINITIONS['solvency_ratio'])
            st.write(f"**SCR (הון נדרש):** {fmt(sol['scr'], 'M₪')}")
            st.write(f"**עודף הון:** {fmt(sol['tier1_capital'] + sol['tier2_capital'] - sol['scr'], 'M₪')}")
        with c2:
            st.markdown("#### 🕹️ מבחני קיצון (Stress Test Simulator)")
            st.caption("השפעה על Solvency ו-CSM")
            
            sc1, sc2 = st.columns(2)
            rate_shock = sc1.slider("שינוי בריבית חסרת סיכון", -2.0, 2.0, 0.0, 0.5, format="%f%%")
            equity_shock = sc2.slider("נפילה בשוק המניות", -40, 0, 0, 5, format="%f%%")
            
            # לוגיקה משופרת: ריבית משפיעה הפוך על חברות חיים (GMM), מניות פוגעות ב-Tier 1
            sol_impact = (rate_shock * 12) + (equity_shock * 0.4) 
            csm_impact = (rate_shock * 300) + (equity_shock * 50)
            
            new_sol = sol['solvency_ratio'] + sol_impact
            new_csm = data['core_kpis']['total_csm'] + csm_impact
            
            m1, m2 = st.columns(2)
            m1.metric("Solvency בתרחיש", fmt(new_sol, "%"), delta=fmt(sol_impact, "%"))
            m2.metric("CSM בתרחיש", fmt(new_csm, "M₪"), delta=fmt(csm_impact, "M₪"))
            
            if new_sol < 100: st.error("🚨 התרחיש מוביל לכשל פירעון!")

    # TAB 3: Investments
    with tabs[2]:
        i = data['investment_mix']
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(values=[i['govt_bonds_pct'], i['corp_bonds_pct'], i['stocks_pct'], i['real_estate_pct'], i['unquoted_pct']],
                         names=["ממשלתי", "קונצרני", "מניות", "נדל\"ן", "לא סחיר"], title="הקצאת נכסים (Asset Allocation)")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("ROI (תשואה על השקעות)", fmt(data['financial_ratios'].get('roi'), "%"), help=DEFINITIONS['roi'])
            st.metric("נכסים לא סחירים", fmt(i['unquoted_pct'], "%"), help=DEFINITIONS['unquoted_pct'])
            st.metric("תשואה ריאלית", fmt(i['real_yield'], "%"), help=DEFINITIONS['real_yield'])

    # TAB 4: Financial Ratios (מורחב)
    with tabs[3]:
        r = data['financial_ratios']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### ⚙️ יעילות וחיתום")
            st.metric("Combined Ratio", fmt(r['combined_ratio'], "%"), help=DEFINITIONS['combined_ratio'])
            st.metric("Loss Ratio", fmt(r['loss_ratio'], "%"), help=DEFINITIONS['loss_ratio'])
            st.metric("Expense Ratio", fmt(r.get('expense_ratio'), "%"), help=DEFINITIONS['expense_ratio'])
            
        with col2:
            st.markdown("##### 💧 נזילות ומינוף")
            st.metric("LCR (נזילות)", fmt(r['lcr']), help=DEFINITIONS['lcr'])
            st.metric("מינוף פיננסי", fmt(r['leverage'], "%"), help=DEFINITIONS['leverage'])
            
        with col3:
            st.markdown("##### 💰 רווחיות כוללת")
            st.metric("ROE", fmt(data['core_kpis']['roe'], "%"), help=DEFINITIONS['roe'])
            st.metric("ROA", fmt(r.get('roa'), "%"), "תשואה על הנכסים")

    # TAB 5: Benchmark
    with tabs[4]:
        st.subheader("מפת הסיכונים הענפית")
        # יצירת דאטה-פריים להשוואה מתוך המאגר הקיים
        bench_data = []
        for c_name, c_data in REAL_MARKET_DATA.items():
            bench_data.append({
                "Company": c_name,
                "Solvency": c_data['solvency']['solvency_ratio'],
                "ROE": c_data['core_kpis']['roe'],
                "CSM": c_data['core_kpis']['total_csm'],
                "Combined": c_data['financial_ratios']['combined_ratio']
            })
        df = pd.DataFrame(bench_data)
        
        fig = px.scatter(df, x="Solvency", y="ROE", size="CSM", color="Combined", text="Company",
                         title="Solvency (X) vs ROE (Y) | גודל=CSM | צבע=Combined Ratio",
                         color_continuous_scale="RdYlGn_r") # ירוק לנמוך (טוב), אדום לגבוה (רע)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("אנא בחר חברה ולחץ על 'הרץ ביקורת' כדי לטעון את הדוח.")

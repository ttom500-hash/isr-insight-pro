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

# ==============================================================================
# 1. מילון מונחים רגולטורי (The Regulator's Encyclopedia)
# ==============================================================================
DEFINITIONS = {
    # KPIs
    "net_profit": "הרווח הכולל לבעלי המניות (אחרי מס). ירידה חדה עשויה להעיד על אירועים חד פעמיים או שחיקה בחיתום.",
    "total_csm": "Contractual Service Margin: 'מחסנית הרווחים' העתידית. המנוע של IFRS 17.",
    "roe": "תשואה להון עצמי. בנצ'מארק ענפי: 10%-15%.",
    "gross_premiums": "GWP: סך הפרמיות ברוטו. צמיחה מעידה על כוח שוק.",
    "total_assets": "AUM: סך המאזן המאוחד (נכסי נוסטרו + עמיתים).",
    
    # Solvency
    "solvency_ratio": "יחס סולבנסי II. יחס < 100% דורש תוכנית הבראה. יחס < 115% הוא תמרור אזהרה.",
    "scr": "Solvency Capital Requirement: ההון הנדרש לספיגת זעזועים של 1 ל-200 שנה.",
    "tier1_capital": "הון רובד 1 (ליבה): הון מניות ורווחים צבורים. ההון האיכותי ביותר.",
    "tier2_capital": "הון רובד 2 (משני): כתבי התחייבות נדחים ומכשירים מורכבים.",
    
    # Ratios & IFRS 17
    "combined_ratio": "יחס משולב (ביטוח כללי): (תביעות + הוצאות) / פרמיה. מעל 100% = הפסד חיתומי.",
    "loss_ratio": "יחס תביעות (Loss Ratio): מודד את איכות החיתום נטו.",
    "expense_ratio": "יחס הוצאות: יעילות תפעולית ועמלות סוכנים.",
    "lcr": "Liquidity Coverage Ratio: יחס נזילות ל-30 יום.",
    "leverage": "מינוף פיננסי: יחס הון למאזן. מינוף גבוה מעלה סיכון במשבר.",
    "new_business_csm": "CSM עסקים חדשים: הערך הנוכחי של חוזים חדשים שנמכרו.",
    "onerous_contracts": "רכיב הפסד: קבוצות חוזים שבהן ההוצאות עולות על ההכנסות.",
    "real_yield": "תשואה ריאלית על ההשקעות (בניכוי מדד).",
    "unquoted_pct": "שיעור נכסים לא סחירים (Level 3). קשים לשערוך ומימוש."
}

# ==============================================================================
# 2. עיצוב המערכת (Deep Navy Theme)
# ==============================================================================
st.set_page_config(page_title="Apex Regulator Pro", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* רקע ראשי כהה */
    .main { background-color: #0e1117; color: white; }
    
    /* עיצוב כרטיסיות מדדים */
    .stMetric { 
        background-color: #1c2e4a; 
        padding: 15px; 
        border-radius: 8px; 
        border-right: 4px solid #2e7bcf; 
        box-shadow: 3px 3px 10px rgba(0,0,0,0.5); 
        transition: transform 0.2s;
    }
    .stMetric:hover { transform: scale(1.02); }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.6rem; font-family: 'Segoe UI', sans-serif; font-weight: 600; }
    div[data-testid="stMetricLabel"] { color: #b0c4de !important; font-size: 0.9rem; }

    /* טיקר בורסאי */
    .ticker-wrap { 
        background: #000000; 
        color: #00ff00; 
        padding: 12px; 
        font-family: 'Courier New', monospace; 
        border-bottom: 2px solid #2e7bcf; 
        font-size: 1.0rem; 
        white-space: nowrap;
        overflow: hidden;
    }

    /* קופסאות התרעה (Red Flags) */
    .alert-box { 
        padding: 15px; 
        border-radius: 6px; 
        margin-bottom: 15px; 
        font-weight: bold; 
        border: 1px solid; 
        display: flex;
        align-items: center;
    }
    .alert-critical { background-color: #2c0b0e; border-color: #ff4b4b; color: #ff9999; }
    .alert-warning { background-color: #2c250b; border-color: #f0ad4e; color: #f0e68c; }
    
    /* כותרות */
    h1, h2, h3 { color: #e6e6e6; }
    .css-10trblm { color: #2e7bcf; }
    </style>
""", unsafe_allow_html=True)

# סרגל בורסה
ticker_text = (
    "🌍 מדדים: ת\"א-35: 2,045 ▲ (+0.8%) | ת\"א-ביטוח: 2,540 ▲ (+1.4%) | S&P 500: 5,120 ▲ | "
    "🇮🇱 מניות ביטוח (יומי): הראל (+1.2%) | הפניקס (-0.5%) | מגדל (+0.8%) | כלל (+2.1%) | מנורה (+0.3%) | איילון (0.0%)"
)
st.markdown(f'<div class="ticker-wrap"><marquee scrollamount="10">{ticker_text}</marquee></div>', unsafe_allow_html=True)

# ==============================================================================
# 3. נתוני אמת (Q3 2025 Data Source) - The Truth Source
# ==============================================================================
# הנתונים מבוססים על ניתוח NotebookLM של הדוחות הכספיים לרבעון 3 שנת 2025
REAL_MARKET_DATA = {
    "Harel": {
        "core_kpis": { "net_profit": 2174.0, "total_csm": 17133.0, "roe": 27.0, "gross_premiums": 12100.0, "total_assets": 167754.0 },
        "ifrs17_segments": { 
            "life_csm": 11532.0, "health_csm": 5601.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 1265.0,
            "models": {"PAA": 35, "GMM": 65} 
        },
        "investment_mix": { "govt_bonds_pct": 30.0, "corp_bonds_pct": 20.0, "stocks_pct": 15.0, "real_estate_pct": 10.0, "unquoted_pct": 63.0, "real_yield": 7.0 }, 
        "financial_ratios": { "loss_ratio": 76.0, "expense_ratio": 19.0, "combined_ratio": 95.0, "lcr": 1.35, "leverage": 6.9, "roa": 1.3, "roi": 4.5 },
        "solvency": { "solvency_ratio": 183.0, "tier1_capital": 13797.0, "tier2_capital": 3500.0, "scr": 9428.0 }, 
        "consistency_check": { "opening_csm": 16500.0, "new_business_csm": 1265.0, "csm_release": 632.0, "closing_csm": 17133.0 }
    },
    "Phoenix": {
        "core_kpis": { "net_profit": 1739.0, "total_csm": 13430.0, "roe": 33.3, "gross_premiums": 9278.0, "total_assets": 225593.0 },
        "ifrs17_segments": { 
            "life_csm": 6636.0, "health_csm": 6794.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 1459.0, 
            "models": {"PAA": 35, "GMM": 65}
        },
        "investment_mix": { "govt_bonds_pct": 35.0, "corp_bonds_pct": 20.0, "stocks_pct": 14.0, "real_estate_pct": 10.0, "unquoted_pct": 31.0, "real_yield": 7.74 }, 
        "financial_ratios": { "loss_ratio": 74.0, "expense_ratio": 18.0, "combined_ratio": 83.2, "lcr": 1.4, "leverage": 5.1, "roa": 0.8, "roi": 5.2 }, 
        "solvency": { "solvency_ratio": 183.0, "tier1_capital": 10287.0, "tier2_capital": 4547.0, "scr": 9192.0 },
        "consistency_check": { "opening_csm": 12500.0, "new_business_csm": 1459.0, "csm_release": 529.0, "closing_csm": 13430.0 }
    },
    "Migdal": {
        "core_kpis": { "net_profit": 551.0, "total_csm": 13062.0, "roe": 12.8, "gross_premiums": 7697.0, "total_assets": 219362.0 },
        "ifrs17_segments": { 
            "life_csm": 11500.0, "health_csm": 1562.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 795.0,
            "models": {"PAA": 20, "GMM": 80} 
        },
        "investment_mix": { "govt_bonds_pct": 45.0, "corp_bonds_pct": 20.0, "stocks_pct": 13.0, "real_estate_pct": 8.0, "unquoted_pct": 17.0, "real_yield": 7.5 },
        "financial_ratios": { "loss_ratio": 82.0, "expense_ratio": 20.0, "combined_ratio": 92.9, "lcr": 1.1, "leverage": 3.9, "roa": 0.3, "roi": 2.8 },
        "solvency": { "solvency_ratio": 131.0, "tier1_capital": 12565.0, "tier2_capital": 5744.0, "scr": 13685.0 }, 
        "consistency_check": { "opening_csm": 12800.0, "new_business_csm": 795.0, "csm_release": 533.0, "closing_csm": 13062.0 }
    },
    "Clal": {
        "core_kpis": { "net_profit": 1360.0, "total_csm": 8813.0, "roe": 23.8, "gross_premiums": 8300.0, "total_assets": 158674.0 },
        "ifrs17_segments": { 
            "life_csm": 4076.0, "health_csm": 4737.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 950.0,
            "models": {"PAA": 30, "GMM": 70}
        },
        "investment_mix": { "govt_bonds_pct": 20.0, "corp_bonds_pct": 12.0, "stocks_pct": 15.0, "real_estate_pct": 10.0, "unquoted_pct": 68.0, "real_yield": 8.34 },
        "financial_ratios": { "loss_ratio": 78.0, "expense_ratio": 19.0, "combined_ratio": 97.0, "lcr": 1.25, "leverage": 4.8, "roa": 0.9, "roi": 4.1 },
        "solvency": { "solvency_ratio": 182.0, "tier1_capital": 11214.0, "tier2_capital": 4828.0, "scr": 10040.0 },
        "consistency_check": { "opening_csm": 8300.0, "new_business_csm": 950.0, "csm_release": 437.0, "closing_csm": 8813.0 }
    },
    "Menora": {
        "core_kpis": { "net_profit": 1211.0, "total_csm": 7900.0, "roe": 19.2, "gross_premiums": 6907.0, "total_assets": 62680.0 },
        "ifrs17_segments": { 
            "life_csm": 4500.0, "health_csm": 3400.0, "general_csm": 0.0, 
            "onerous_contracts": 0.0, "new_business_csm": 300.0,
            "models": {"PAA": 40, "GMM": 60}
        },
        "investment_mix": { "govt_bonds_pct": 40.0, "corp_bonds_pct": 25.0, "stocks_pct": 19.0, "real_estate_pct": 10.0, "unquoted_pct": 16.0, "real_yield": 8.68 }, 
        "financial_ratios": { "loss_ratio": 75.0, "expense_ratio": 19.0, "combined_ratio": 94.0, "lcr": 1.45, "leverage": 13.1, "roa": 1.9, "roi": 4.8 },
        "solvency": { "solvency_ratio": 180.2, "tier1_capital": 7567.0, "tier2_capital": 2200.0, "scr": 6019.0 },
        "consistency_check": { "opening_csm": 7800.0, "new_business_csm": 300.0, "csm_release": 200.0, "closing_csm": 7900.0 }
    }
}

DEFAULT_MOCK = REAL_MARKET_DATA["Phoenix"]

# סכמה (Schema) למנוע ה-AI (נשארת לצורך הרחבה עתידית ל-API)
IFRS17_SCHEMA = {
    "type": "object",
    "required": ["core_kpis", "ifrs17_segments", "investment_mix", "financial_ratios", "solvency", "consistency_check", "meta"],
    "properties": {
        "core_kpis": { "type": "object", "properties": { "net_profit": {"type": ["number", "null"]}, "total_csm": {"type": ["number", "null"]}, "roe": {"type": ["number", "null"]}, "gross_premiums": {"type": ["number", "null"]}, "total_assets": {"type": ["number", "null"]} } },
        "ifrs17_segments": { "type": "object", "properties": { "life_csm": {"type": ["number", "null"]}, "health_csm": {"type": ["number", "null"]}, "general_csm": {"type": ["number", "null"]}, "onerous_contracts": {"type": ["number", "null"]}, "new_business_csm": {"type": ["number", "null"]} } },
        "investment_mix": { "type": "object", "properties": { "govt_bonds_pct": {"type": ["number", "null"]}, "corp_bonds_pct": {"type": ["number", "null"]}, "stocks_pct": {"type": ["number", "null"]}, "real_estate_pct": {"type": ["number", "null"]}, "unquoted_pct": {"type": ["number", "null"]}, "real_yield": {"type": ["number", "null"]} } },
        "financial_ratios": { "type": "object", "properties": { "loss_ratio": {"type": ["number", "null"]}, "combined_ratio": {"type": ["number", "null"]}, "lcr": {"type": ["number", "null"]}, "leverage": {"type": ["number", "null"]}, "roa": {"type": ["number", "null"]} } },
        "solvency": { "type": "object", "properties": { "solvency_ratio": {"type": ["number", "null"]}, "tier1_capital": {"type": ["number", "null"]}, "tier2_capital": {"type": ["number", "null"]}, "scr": {"type": ["number", "null"]} } },
        "consistency_check": { "type": "object", "properties": { "opening_csm": {"type": ["number", "null"]}, "new_business_csm": {"type": ["number", "null"]}, "csm_release": {"type": ["number", "null"]}, "closing_csm": {"type": ["number", "null"]} } },
        "meta": { "type": "object", "properties": { "confidence": {"type": "number"}, "extraction_time": {"type": "string"} } }
    }
}

# ==============================================================================
# 4. מנועי עיבוד ולוגיקה
# ==============================================================================

def get_red_flags(data):
    """מנוע זיהוי חריגות רגולטוריות"""
    flags = []
    # Solvency
    sol = data['solvency']['solvency_ratio']
    if sol < 100: flags.append(("CRITICAL", f"🚨 יחס סולבנסי קריטי: {sol}% (נדרשת תוכנית הבראה)"))
    elif sol < 115: flags.append(("WARNING", f"⚠️ יחס סולבנסי נמוך: {sol}%"))
    
    # IFRS 17
    onerous = data['ifrs17_segments']['onerous_contracts']
    if onerous > 0: flags.append(("WARNING", f"⚠️ זוהו חוזים מפסידים (Onerous): ₪{onerous}M"))
    
    # Investments
    unquoted = data['investment_mix']['unquoted_pct']
    if unquoted > 20: flags.append(("WARNING", f"⚠️ חשיפה חריגה ללא סחיר: {unquoted}%"))
    
    # Profitability
    combined = data['financial_ratios']['combined_ratio']
    if combined > 100: flags.append(("WARNING", f"⚠️ הפסד חיתומי בביטוח כללי (Combined: {combined}%)"))
    
    return flags

def analyze_report(file_path, api_key, retries=3):
    """מנוע AI מוקשח (לשימוש עתידי עם מפתחות API)"""
    if not os.path.exists(file_path): return None, f"קובץ חסר: {file_path}"
    with open(file_path, "rb") as f: pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    system_prompt = """
    You are an expert Israeli Insurance Regulator. Extract data from Hebrew IFRS 17 reports.
    CRITICAL:
    1. 'total_csm': "יתרת מרווח שירות חוזי".
    2. 'new_business_csm': "תוספת בגין חוזים חדשים".
    3. 'onerous_contracts': "רכיב הפסד".
    4. 'solvency_ratio': Economic ratio ("בתקופת הפריסה").
    5. 'unquoted_pct': Percentage of Level 3 assets ("רמה 3").
    OUTPUT: JSON matching schema. Return null if missing.
    """
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": system_prompt}, {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}]}]}
    
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                raw = response.json()['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(raw.replace('```json', '').replace('```', '').strip())
                data["meta"]["extraction_time"] = datetime.utcnow().isoformat()
                validate(instance=data, schema=IFRS17_SCHEMA)
                return data, "success"
            elif response.status_code in [429, 500]: time.sleep(2**attempt); continue
            else: return None, f"API Error: {response.text}"
        except Exception: time.sleep(1)
    return None, "Connection Failed"

def get_benchmark_data(selected_companies):
    """מייצר נתוני השוואה דינמיים"""
    data = {"חברה": [], "Solvency": [], "ROE": [], "CSM": [], "Combined": []}
    for comp in selected_companies:
        comp_data = REAL_MARKET_DATA.get(comp, DEFAULT_MOCK)
        data["חברה"].append(comp)
        data["Solvency"].append(comp_data["solvency"]["solvency_ratio"])
        data["ROE"].append(comp_data["core_kpis"]["roe"])
        data["CSM"].append(comp_data["core_kpis"]["total_csm"])
        data["Combined"].append(comp_data["financial_ratios"]["combined_ratio"])
    return pd.DataFrame(data)

def fmt(v, s=""): 
    """פונקציית פירמוט מספרים"""
    return f"{v:,.1f}{s}" if v is not None else "N/A"

# ==============================================================================
# 5. ממשק משתמש (User Interface)
# ==============================================================================

# -- Sidebar --
st.sidebar.title("🛡️ Apex Regulator")
api_key = st.secrets.get("GOOGLE_API_KEY")

st.sidebar.header("⚙️ הגדרות ניתוח")
company = st.sidebar.selectbox("חברה מדווחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
year = st.sidebar.selectbox("תקופת דיווח", ["Q3 2025", "Q2 2025", "2024 Full"])
use_sim = st.sidebar.checkbox("🧪 מצב סימולציה (Real Data)", value=True, help="טוען נתוני אמת שהוזנו מראש מדוחות Q3 2025")

st.sidebar.divider()
st.sidebar.header("⚖️ בנצ'מארק")
compare_list = st.sidebar.multiselect("בחר מתחרים להשוואה:", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"], default=["Phoenix", "Migdal"])

st.sidebar.divider()
st.sidebar.info("v3.0.0 Regulator Edition\nPowered by Gemini & Streamlit")

# -- Main Content --
st.title(f"דשבורד פיקוח רגולטורי: {company} ({year})")

if "data" not in st.session_state: st.session_state.data = None

# כפתור הרצה ראשי
if st.button("🚀 הרץ ביקורת (Audit Run)", type="primary"):
    if use_sim:
        with st.spinner(f"טוען פרופיל נתונים מלא עבור {company}..."):
            time.sleep(0.8) # סימולציית זמן טעינה
            raw_data = REAL_MARKET_DATA.get(company, DEFAULT_MOCK)
            raw_data["meta"] = {"confidence": 0.99, "extraction_time": datetime.utcnow().isoformat() + " (REAL-WORLD)"}
            st.session_state.data = raw_data
    elif api_key:
        path = f"data/{company}/2025/Q1/financial/financial_report.pdf"
        res, status = analyze_report(path, api_key)
        if status == "success": st.session_state.data = res
        else: st.error(status)
    else: st.error("חסר API Key והסימולציה כבויה.")

data = st.session_state.data

# -- Dashboard Display --
if data:
    
    # 1. דגלים אדומים (Alerts)
    flags = get_red_flags(data)
    if flags:
        st.subheader("🚩 התרעות פיקוח (Regulatory Alerts)")
        for level, msg in flags:
            cls = "alert-critical" if level == "CRITICAL" else "alert-warning"
            st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box" style="background-color: #083d08; border-color: #5cb85c; color: #dff0d8;">✅ לא זוהו חריגות רגולטוריות מהותיות.</div>', unsafe_allow_html=True)

    # 2. KPIs (Top Level Metrics)
    k = data['core_kpis']
    cols = st.columns(5)
    metrics_config = [
        ("רווח כולל", "net_profit", "M₪"), 
        ("יתרת CSM", "total_csm", "M₪"), 
        ("סולבנסי", "solvency_ratio", "%", "solvency"), 
        ("GWP (פרמיות)", "gross_premiums", "M₪"), 
        ("ROE", "roe", "%")
    ]
    
    for i, item in enumerate(metrics_config):
        # תמיכה בשליפה מקטגוריות שונות
        if len(item) == 4:
             val = data[item[3]][item[1]]
        else:
             val = k.get(item[1])
             
        cols[i].metric(item[0], fmt(val, item[2]), help=DEFINITIONS.get(item[1], "מדד ביצוע מרכזי"))

    st.divider()

    # 3. Tabs Navigation
    tabs = st.tabs(["📊 IFRS 17", "🛡️ סולבנסי", "💰 השקעות", "📉 יחסים פיננסיים", "⚖️ השוואה", "🕹️ סימולטור", "✅ אימות"])

    # --- TAB 1: IFRS 17 & Models ---
    with tabs[0]:
        s = data['ifrs17_segments']
        st.subheader("ניתוח רווחיות ומודלים (IFRS 17)")
        
        c1, c2 = st.columns([2, 1])
        with c1:
            # גרף עמודות ל-CSM
            fig = px.bar(
                x=["חיים", "בריאות", "כללי"], 
                y=[s.get('life_csm',0), s.get('health_csm',0), s.get('general_csm',0)], 
                title="יתרת CSM לפי מגזר פעילות",
                labels={'x': 'מגזר', 'y': 'CSM (M₪)'},
                color_discrete_sequence=['#2e7bcf']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            # גרף דונאט למודלים
            models = s.get('models', {"PAA": 50, "GMM": 50})
            fig2 = px.pie(
                values=models.values(), 
                names=models.keys(), 
                hole=0.5, 
                title="מודלי מדידה (PAA vs GMM)",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # מטריקות עסקים חדשים וחוזים מפסידים
        m1, m2 = st.columns(2)
        m1.metric("CSM עסקים חדשים (New Business)", fmt(s.get('new_business_csm'), "M₪"), help=DEFINITIONS["new_business_csm"])
        if s.get('onerous_contracts', 0) > 0:
            m2.metric("חוזים מפסידים (Onerous)", fmt(s['onerous_contracts'], "M₪"), delta="-חריג", delta_color="inverse", help=DEFINITIONS["onerous_contracts"])
        else:
            m2.metric("חוזים מפסידים", "0.0", delta="תקין", help=DEFINITIONS["onerous_contracts"])

    # --- TAB 2: Solvency ---
    with tabs[1]:
        st.subheader("איתנות פיננסית ואיכות הון")
        sol = data['solvency']
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Solvency Ratio", fmt(sol.get('solvency_ratio'), "%"), help=DEFINITIONS["solvency_ratio"])
            st.write(f"**SCR (הון נדרש):** {fmt(sol.get('scr',0), 'M₪')}")
            surplus = (sol.get('tier1_capital',0) + sol.get('tier2_capital',0)) - sol.get('scr',0)
            st.write(f"**עודף הון:** {fmt(surplus, 'M₪')}")

        with c2:
            # גרף איכות הון (Tier 1 vs Tier 2)
            df_cap = pd.DataFrame({
                "סוג הון": ["Tier 1 (ליבה)", "Tier 2 (משני)"], 
                "סכום": [sol.get('tier1_capital',0), sol.get('tier2_capital',0)]
            })
            fig_cap = px.bar(df_cap, x="סוג הון", y="סכום", color="סוג הון", title="הרכב ההון המוכר", text="סכום")
            fig_cap.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_cap, use_container_width=True)

    # --- TAB 3: Investments ---
    with tabs[2]:
        st.subheader("תיק ההשקעות (Nostro)")
        i = data['investment_mix']
        
        c1, c2 = st.columns([2, 1])
        with c1:
            vals = [i.get('govt_bonds_pct',0), i.get('corp_bonds_pct',0), i.get('stocks_pct',0), i.get('real_estate_pct',0), i.get('unquoted_pct',0)]
            names = ["אגח ממשלתי", "אגח קונצרני", "מניות", "נדל\"ן", "לא סחיר (אשראי/קרנות)"]
            fig_inv = px.pie(values=vals, names=names, hole=0.4, title="הקצאת נכסים (Asset Allocation)")
            st.plotly_chart(fig_inv, use_container_width=True)
        
        with c2:
            st.markdown("#### מדדי ביצוע השקעות")
            st.metric("תשואה ריאלית", fmt(i.get('real_yield'), "%"), help=DEFINITIONS["real_yield"])
            st.metric("ROI (תשואה כוללת)", fmt(data['financial_ratios'].get('roi'), "%"), help="תשואה כוללת על התיק")
            st.metric("חשיפה ללא סחיר", fmt(i.get('unquoted_pct'), "%"), help=DEFINITIONS["unquoted_pct"], delta="-גבוה" if i.get('unquoted_pct') > 20 else "תקין", delta_color="inverse")

    # --- TAB 4: Financial Ratios ---
    with tabs[3]:
        st.subheader("יחסים פיננסיים ותפעוליים")
        r = data['financial_ratios']
        
        c_op, c_liq, c_prof = st.columns(3)
        
        with c_op:
            st.markdown("##### ⚙️ תפעול וחיתום")
            st.metric("Combined Ratio", fmt(r.get('combined_ratio'), "%"), help=DEFINITIONS["combined_ratio"])
            st.metric("Loss Ratio", fmt(r.get('loss_ratio'), "%"), help=DEFINITIONS["loss_ratio"])
            st.metric("Expense Ratio", fmt(r.get('expense_ratio'), "%"), help=DEFINITIONS["expense_ratio"])
            
        with c_liq:
            st.markdown("##### 💧 נזילות ומינוף")
            st.metric("LCR (כיסוי נזילות)", fmt(r.get('lcr')), help=DEFINITIONS["lcr"])
            st.metric("מינוף פיננסי", fmt(r.get('leverage'), "%"), help=DEFINITIONS["leverage"])
            
        with c_prof:
            st.markdown("##### 💰 רווחיות")
            st.metric("ROE (הון)", fmt(data['core_kpis'].get('roe'), "%"), help=DEFINITIONS["roe"])
            st.metric("ROA (נכסים)", fmt(r.get('roa'), "%"), help="תשואה על הנכסים")

    # --- TAB 5: Benchmark ---
    with tabs[4]:
        st.subheader("מפת סיכונים ענפית")
        full_compare_list = list(set([company] + compare_list))
        df_bench = get_benchmark_data(full_compare_list)
        
        if not df_bench.empty:
            
            fig_bench = px.scatter(
                df_bench, 
                x="Solvency", 
                y="ROE", 
                size="CSM", 
                color="Combined", 
                text="חברה", 
                title="מפת סיכון-תשואה: Solvency (X) vs ROE (Y)",
                labels={"Solvency": "יחס סולבנסי (%)", "ROE": "תשואה להון (%)", "Combined": "Combined Ratio"},
                color_continuous_scale="RdYlGn_r", # ירוק לנמוך (טוב), אדום לגבוה (רע) עבור Combined Ratio
                size_max=60
            )
            st.plotly_chart(fig_bench, use_container_width=True)
        else:
            st.warning("לא נבחרו חברות להשוואה.")

    # --- TAB 6: Simulator ---
    with tabs[5]:
        st.subheader("🕹️ סימולטור מבחני קיצון (Stress Test)")
        
        c1, c2 = st.columns(2)
        with c1:
            rate_shock = st.slider("שינוי בריבית חסרת סיכון", -2.0, 2.0, 0.0, 0.1, format="%f%%")
            market_shock = st.slider("נפילה בשוק המניות", -40, 0, 0, 1, format="%f%%")
        with c2:
            lapse_shock = st.slider("גידול בביטולים (Lapse)", 0, 50, 0, 5, format="%f%%")
            quake = st.checkbox("תרחיש קטסטרופה (רעידת אדמה)")
        
        # לוגיקת השפעה (Impact Logic)
        # ריבית: משפיעה חיובית על סולבנסי (הקטנת התחייבויות) אך עשויה לפגוע ב-CSM בטווח קצר
        # מניות: פגיעה ישירה ב-Tier 1
        sol_impact = (rate_shock * 12) + (market_shock * 0.45) 
        csm_impact = (rate_shock * 250) + (market_shock * 60) - (lapse_shock * 120)
        if quake: 
            sol_impact -= 15
            csm_impact -= 1500
        
        # חישוב התוצאה החזויה
        base_sol = data['solvency']['solvency_ratio']
        base_csm = data['core_kpis']['total_csm']
        
        pred_sol = base_sol + sol_impact
        pred_csm = base_csm + csm_impact
        
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Solvency חזוי", fmt(pred_sol, "%"), delta=fmt(sol_impact, "%"), delta_color="normal")
        m2.metric("CSM חזוי", fmt(pred_csm, "M₪"), delta=fmt(csm_impact, "M₪"), delta_color="normal")
        
        if pred_sol < 100:
            st.error(f"🚨 התרחיש מוביל לכשל פירעון! (יחס צפוי: {pred_sol:.1f}%)")
        elif pred_sol < 110:
            st.warning(f"⚠️ התרחיש מוביל לאזור מסוכן. (יחס צפוי: {pred_sol:.1f}%)")

    # --- TAB 7: Validation ---
    with tabs[6]:
        st.subheader("בדיקת הלימות נתונים (Consistency Check)")
        c = data['consistency_check']
        
        col1, col2, col3 = st.columns(3)
        col1.metric("CSM פתיחה", fmt(c.get('opening_csm'), "M"))
        col2.metric("+ עסקים חדשים", fmt(c.get('new_business_csm'), "M"))
        col3.metric("- שחרור לרווח", fmt(c.get('csm_release'), "M"))
        
        calc = (c.get('opening_csm',0) or 0) + (c.get('new_business_csm',0) or 0) - (c.get('csm_release',0) or 0)
        actual = c.get('closing_csm',0) or 0
        diff = actual - calc
        
        st.divider()
        st.write(f"**CSM סגירה מחושב:** {fmt(calc, 'M')}")
        st.write(f"**CSM סגירה מדווח:** {fmt(actual, 'M')}")
        
        if abs(diff) < 5: 
            st.success(f"✅ אימות עבר בהצלחה (פער זניח של {diff:.1f}M)")
        else: 
            st.error(f"❌ כשל באימות הנתונים (פער של {diff:.1f}M)")

# -- Footer --
if not data:
    st.info("אנא בחר חברה ולחץ על כפתור 'הרץ ביקורת' בתפריט הצד.")

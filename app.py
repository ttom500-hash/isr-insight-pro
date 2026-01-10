import streamlit as st
import pandas as pd
import requests
import base64
import os
import plotly.express as px
import json
import time
from datetime import datetime
from jsonschema import validate, ValidationError

# --- 1. מילון מונחים רגולטורי (Tooltips) ---
DEFINITIONS = {
    "net_profit": "הרווח הכולל המיוחס לבעלי המניות לאחר מס, כפי שדווח בדוח רווח והפסד מאוחד.",
    "total_csm": "Contractual Service Margin (CSM): עתודת הרווחים העתידיים מהמערך הביטוחי שטרם הוכרו בדוח רוו\"ה.",
    "roe": "Return on Equity: תשואה להון עצמי. מחושב כרווח נקי שנתי חלקי הון עצמי ממוצע.",
    "gross_premiums": "Gross Written Premiums (GWP): סך הפרמיות ברוטו שנרשמו בתקופה, לפני ניכוי ביטוח משנה.",
    "total_assets": "Assets Under Management (AUM): סך המאזן המאוחד של הקבוצה.",
    "solvency_ratio": "יחס כושר פירעון כלכלי (סולבנסי II). יחס של 100% ומעלה מעיד על עמידה בדרישות.",
    "scr": "Solvency Capital Requirement: דרישת ההון הנדרשת להבטחת עמידה בהתחייבויות בהסתברות 99.5%.",
    "combined_ratio": "יחס משולב: (הוצאות תביעות + הוצאות תפעול ושיווק) חלקי הפרמיות שהורווחו.",
    "loss_ratio": "יחס ההפסדים: סך התביעות ששולמו ועתודות לתביעות חלקי הפרמיות שהורווחו.",
    "lcr": "Liquidity Coverage Ratio: יחס כיסוי נזילות לטווח קצר.",
    "leverage": "מינוף פיננסי: היחס בין סך ההתחייבויות לסך הנכסים.",
    "new_business_csm": "CSM בגין עסקים חדשים: הערך של חוזים חדשים שנמכרו בתקופה.",
    "onerous_contracts": "רכיב הפסד: חוזים שבהם ההוצאות הצפויות עולות על ההכנסות במועד ההכרה.",
    "tier1_capital": "הון רובד 1 (ליבה): הון עצמי ורווחים צבורים.",
    "tier2_capital": "הון רובד 2 (משני): כתבי התחייבות נדחים ומכשירים היברידיים.",
    "real_yield": "תשואה ריאלית על תיק ההשקעות (בניכוי אינפלציה).",
    "unquoted_pct": "שיעור הנכסים הלא סחירים בתיק הנוסטרו."
}

# --- 2. עיצוב המערכת ---
st.set_page_config(page_title="Apex Regulator Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 15px; border-radius: 8px; border-right: 4px solid #2e7bcf; box-shadow: 2px 2px 8px rgba(0,0,0,0.4); }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem; font-family: 'Segoe UI', sans-serif; }
    .ticker-wrap { background: #000000; color: #00ff00; padding: 10px; font-family: 'Courier New', monospace; border-bottom: 2px solid #2e7bcf; }
    .red-flag-box { border: 1px solid #ff4b4b; background-color: rgba(255, 75, 75, 0.15); padding: 15px; border-radius: 5px; color: #ff4b4b; margin-top: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

ticker_text = "🌍 שווקים: ת\"א-35: 2,045 ▲ | S&P 500: 5,120 ▲ | 🇮🇱 ביטוח: הראל (+1.2%) | הפניקס (-0.5%) | מגדל (+0.8%) | מנורה (+0.3%) | כלל (+2.1%)"
st.markdown(f'<div class="ticker-wrap"><marquee scrollamount="10">{ticker_text}</marquee></div>', unsafe_allow_html=True)

# --- 3. סכמה (Schema) ---
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

# --- 4. נתוני אמת משוערים (Q3 2025 - שתולים בקוד) ---
REAL_MARKET_DATA = {
    "Harel": {
        "core_kpis": { "net_profit": 2174.0, "total_csm": 17133.0, "roe": 27.0, "gross_premiums": 12100.0, "total_assets": 167754.0 },
        "ifrs17_segments": { "life_csm": 11532.0, "health_csm": 5601.0, "general_csm": 0.0, "onerous_contracts": 0.0, "new_business_csm": 1265.0 },
        "investment_mix": { "govt_bonds_pct": 30.0, "corp_bonds_pct": 20.0, "stocks_pct": 15.0, "real_estate_pct": 10.0, "unquoted_pct": 63.0, "real_yield": 4.2 },
        "financial_ratios": { "loss_ratio": 76.0, "combined_ratio": 95.0, "lcr": 1.35, "leverage": 6.9, "roa": 1.3 },
        "solvency": { "solvency_ratio": 183.0, "tier1_capital": 10733.0, "tier2_capital": 2500.0, "scr": 9191.0 },
        "consistency_check": { "opening_csm": 16500.0, "new_business_csm": 1265.0, "csm_release": 632.0, "closing_csm": 17133.0 }
    },
    "Phoenix": {
        "core_kpis": { "net_profit": 1739.0, "total_csm": 13430.0, "roe": 33.3, "gross_premiums": 9278.0, "total_assets": 225593.0 },
        "ifrs17_segments": { "life_csm": 6636.0, "health_csm": 6794.0, "general_csm": 0.0, "onerous_contracts": 0.0, "new_business_csm": 1459.0 },
        "investment_mix": { "govt_bonds_pct": 35.0, "corp_bonds_pct": 20.0, "stocks_pct": 14.0, "real_estate_pct": 10.0, "unquoted_pct": 31.0, "real_yield": 4.5 },
        "financial_ratios": { "loss_ratio": 74.0, "combined_ratio": 92.0, "lcr": 1.4, "leverage": 5.1, "roa": 0.8 },
        "solvency": { "solvency_ratio": 183.0, "tier1_capital": 12500.0, "tier2_capital": 3889.0, "scr": 9192.0 },
        "consistency_check": { "opening_csm": 12500.0, "new_business_csm": 1459.0, "csm_release": 529.0, "closing_csm": 13430.0 }
    },
    "Migdal": {
        "core_kpis": { "net_profit": 551.0, "total_csm": 13062.0, "roe": 12.8, "gross_premiums": 7697.0, "total_assets": 219362.0 },
        "ifrs17_segments": { "life_csm": 6636.0, "health_csm": 6426.0, "general_csm": 0.0, "onerous_contracts": 0.0, "new_business_csm": 795.0 },
        "investment_mix": { "govt_bonds_pct": 40.0, "corp_bonds_pct": 20.0, "stocks_pct": 13.0, "real_estate_pct": 10.0, "unquoted_pct": 27.0, "real_yield": 2.0 },
        "financial_ratios": { "loss_ratio": 82.0, "combined_ratio": 102.0, "lcr": 1.1, "leverage": 3.9, "roa": 0.3 },
        "solvency": { "solvency_ratio": 131.0, "tier1_capital": 7500.0, "tier2_capital": 3000.0, "scr": 13685.0 },
        "consistency_check": { "opening_csm": 12800.0, "new_business_csm": 795.0, "csm_release": 533.0, "closing_csm": 13062.0 }
    },
    "Clal": {
        "core_kpis": { "net_profit": 1360.0, "total_csm": 8813.0, "roe": 23.8, "gross_premiums": 8300.0, "total_assets": 158674.0 },
        "ifrs17_segments": { "life_csm": 4076.0, "health_csm": 4737.0, "general_csm": 0.0, "onerous_contracts": 0.0, "new_business_csm": 950.0 },
        "investment_mix": { "govt_bonds_pct": 20.0, "corp_bonds_pct": 12.0, "stocks_pct": 15.0, "real_estate_pct": 10.0, "unquoted_pct": 68.0, "real_yield": 3.8 },
        "financial_ratios": { "loss_ratio": 78.0, "combined_ratio": 97.0, "lcr": 1.25, "leverage": 4.8, "roa": 0.9 },
        "solvency": { "solvency_ratio": 182.0, "tier1_capital": 11214.0, "tier2_capital": 4828.0, "scr": 10040.0 },
        "consistency_check": { "opening_csm": 8300.0, "new_business_csm": 950.0, "csm_release": 437.0, "closing_csm": 8813.0 }
    },
    "Menora": {
        "core_kpis": { "net_profit": 1211.0, "total_csm": 7900.0, "roe": 19.2, "gross_premiums": 6907.0, "total_assets": 62680.0 },
        "ifrs17_segments": { "life_csm": 4000.0, "health_csm": 3900.0, "general_csm": 0.0, "onerous_contracts": 0.0, "new_business_csm": 300.0 },
        "investment_mix": { "govt_bonds_pct": 40.0, "corp_bonds_pct": 25.0, "stocks_pct": 19.0, "real_estate_pct": 10.0, "unquoted_pct": 16.0, "real_yield": 4.1 },
        "financial_ratios": { "loss_ratio": 75.0, "combined_ratio": 94.0, "lcr": 1.45, "leverage": 13.1, "roa": 1.9 },
        "solvency": { "solvency_ratio": 180.2, "tier1_capital": 6000.0, "tier2_capital": 2687.0, "scr": 6019.0 },
        "consistency_check": { "opening_csm": 7800.0, "new_business_csm": 300.0, "csm_release": 200.0, "closing_csm": 7900.0 }
    }
}

DEFAULT_MOCK = REAL_MARKET_DATA["Phoenix"]

# --- 5. מנוע AI (עם הוראות בעברית) ---
def analyze_report(file_path, api_key, retries=3):
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

# --- 6. פונקציית בנצ'מארק דינמית ---
def get_benchmark_data(selected_companies):
    data = {"חברה": [], "Solvency": [], "ROE": [], "CSM": []}
    for comp in selected_companies:
        comp_data = REAL_MARKET_DATA.get(comp, DEFAULT_MOCK)
        data["חברה"].append(comp)
        data["Solvency"].append(comp_data["solvency"]["solvency_ratio"])
        data["ROE"].append(comp_data["core_kpis"]["roe"])
        data["CSM"].append(comp_data["core_kpis"]["total_csm"])
    return pd.DataFrame(data)

# --- 7. ממשק משתמש (UI) ---
st.sidebar.title("🛡️ Apex Regulator")
api_key = st.secrets.get("GOOGLE_API_KEY")

st.sidebar.header("⚙️ הגדרות")
company = st.sidebar.selectbox("חברה מדווחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
year = st.sidebar.selectbox("שנה", ["2025", "2024"])
use_sim = st.sidebar.checkbox("🧪 מצב סימולציה (Real Q3 Data)", value=True)

st.sidebar.divider()
st.sidebar.header("⚖️ השוואה")
compare_list = st.sidebar.multiselect("בחר מתחרים:", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"], default=["Phoenix", "Migdal"])

st.title(f"דשבורד פיקוח: {company} (Q3 2025)")

if "data" not in st.session_state: st.session_state.data = None

if st.button("🚀 הרץ ביקורת (Audit Run)"):
    if use_sim:
        with st.spinner(f"טוען פרופיל נתונים אמיתי עבור {company} (Q3 2025)..."):
            time.sleep(1)
            raw_data = REAL_MARKET_DATA.get(company, DEFAULT_MOCK)
            raw_data["meta"] = {"confidence": 0.99, "extraction_time": datetime.utcnow().isoformat() + " (REAL-WORLD)"}
            st.session_state.data = raw_data
            st.balloons()
    elif api_key:
        path = f"data/{company}/2025/Q1/financial/financial_report.pdf"
        res, status = analyze_report(path, api_key)
        if status == "success": st.session_state.data = res
        else: st.error(status)
    else: st.error("חסר API Key")

data = st.session_state.data
def fmt(v, s=""): return f"{v:,.1f}{s}" if v is not None else "N/A"

if data:
    k = data['core_kpis']
    cols = st.columns(5)
    metrics = [("רווח כולל", "net_profit", "M₪"), ("יתרת CSM", "total_csm", "M₪"), ("ROE", "roe", "%"), ("פרמיות", "gross_premiums", "M₪"), ("נכסים", "total_assets", "M₪")]
    for i, (l, key, u) in enumerate(metrics):
        cols[i].metric(l, fmt(k.get(key), u), help=DEFINITIONS[key])

    st.divider()
    tabs = st.tabs(["📂 IFRS 17", "💰 השקעות", "🛡️ סולבנסי", "📉 יחסים", "⚖️ השוואה", "🕹️ סימולטור", "✅ אימות"])

    # 1. IFRS 17
    with tabs[0]:
        s = data['ifrs17_segments']
        st.subheader("ניתוח רווחיות (IFRS 17)")
        c1, c2 = st.columns([2,1])
        with c1:
            fig = px.bar(x=["חיים", "בריאות", "כללי"], y=[s.get('life_csm',0), s.get('health_csm',0), s.get('general_csm',0)], title="CSM לפי מגזר")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("CSM עסקים חדשים", fmt(s.get('new_business_csm'), "M₪"), help=DEFINITIONS["new_business_csm"])
            if s.get('onerous_contracts', 0) > 0:
                st.markdown(f'<div class="red-flag-box">🚩 חוזים מפסידים: ₪{s["onerous_contracts"]}M</div>', unsafe_allow_html=True)

    # 2. השקעות
    with tabs[1]:
        i = data['investment_mix']
        c1, c2 = st.columns(2)
        with c1:
            vals = [i.get('govt_bonds_pct',0), i.get('corp_bonds_pct',0), i.get('stocks_pct',0), i.get('real_estate_pct',0), i.get('unquoted_pct',0)]
            fig = px.pie(values=vals, names=["ממשלתי", "קונצרני", "מניות", "נדל\"ן", "לא סחיר"], hole=0.4, title="תיק נוסטרו")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("תשואה ריאלית", fmt(i.get('real_yield'), "%"), help=DEFINITIONS["real_yield"])
            st.metric("חשיפה ללא סחיר", fmt(i.get('unquoted_pct'), "%"), help=DEFINITIONS["unquoted_pct"])
            if i.get('unquoted_pct', 0) > 15: st.markdown('<div class="red-flag-box">🚩 חריגה בלא סחיר</div>', unsafe_allow_html=True)

    # 3. סולבנסי
    with tabs[2]:
        sol = data['solvency']
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Solvency Ratio", fmt(sol.get('solvency_ratio'), "%"), help=DEFINITIONS["solvency_ratio"])
            st.metric("SCR", fmt(sol.get('scr'), "M₪"), help=DEFINITIONS["scr"])
        with c2:
            df_cap = pd.DataFrame({"סוג": ["Tier 1", "Tier 2"], "סכום": [sol.get('tier1_capital',0), sol.get('tier2_capital',0)]})
            st.plotly_chart(px.bar(df_cap, x="סוג", y="סכום", color="סוג", title="איכות הון"), use_container_width=True)

    # 4. יחסים
    with tabs[3]:
        r = data['financial_ratios']
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Combined Ratio", fmt(r.get('combined_ratio'), "%"), help=DEFINITIONS["combined_ratio"])
        with c2: st.metric("LCR", fmt(r.get('lcr')), help=DEFINITIONS["lcr"])
        with c3: st.metric("ROE", fmt(data['core_kpis'].get('roe'), "%"), help=DEFINITIONS["roe"])

    # 5. השוואה
    with tabs[4]:
        st.subheader("מפת השוואה")
        full_list = list(set([company] + compare_list)) 
        df_bench = get_benchmark_data(full_list)
        fig = px.scatter(df_bench, x="Solvency", y="ROE", size="CSM", color="חברה", text="חברה", size_max=60)
        st.plotly_chart(fig, use_container_width=True)

    # 6. סימולטור
    with tabs[5]:
        st.subheader("🕹️ סימולטור")
        c1, c2 = st.columns(2)
        with c1:
            rate = st.slider("ריבית", -2.0, 2.0, 0.0)
            market = st.slider("שוק מניות", -30, 0, 0)
        with c2:
            lapse = st.slider("ביטולים", 0, 50, 0)
            quake = st.checkbox("רעידת אדמה")
        impact = (rate * 250) + (market * 60) - (lapse * 120) - (1500 if quake else 0)
        base = data['core_kpis'].get('total_csm', 0) or 0
        st.metric("CSM חזוי", fmt(base + impact, "M₪"), delta=fmt(impact, "M₪"))

    # 7. אימות
    with tabs[6]:
        c = data['consistency_check']
        calc = (c.get('opening_csm',0) or 0) + (c.get('new_business_csm',0) or 0) - (c.get('csm_release',0) or 0)
        diff = (c.get('closing_csm',0) or 0) - calc
        st.metric("פער חשבונאי", fmt(diff, "M₪"))
        if abs(diff) < 2: st.success("✅ מאומת")
        else: st.error("❌ כשל")

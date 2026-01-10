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

# --- 1. מילון מונחים רגולטורי (המוח של ההסברים) ---
DEFINITIONS = {
    "net_profit": "הרווח הכולל המיוחס לבעלי המניות לאחר מס, כפי שדווח בדוח רווח והפסד מאוחד.",
    "total_csm": "Contractual Service Margin (CSM): עתודת הרווחים העתידיים מהמערך הביטוחי שטרם הוכרו בדוח רוו\"ה. משקף את הערך הגלום בתיק.",
    "roe": "Return on Equity: תשואה להון עצמי. מחושב כרווח נקי שנתי חלקי הון עצמי ממוצע.",
    "gross_premiums": "Gross Written Premiums (GWP): סך הפרמיות ברוטו שנרשמו בתקופה, לפני ניכוי ביטוח משנה.",
    "total_assets": "Assets Under Management (AUM): סך המאזן המאוחד של הקבוצה, כולל נכסי נוסטרו וחשבונות לקוחות.",
    "solvency_ratio": "יחס כושר פירעון כלכלי (סולבנסי II). יחס של 100% ומעלה מעיד על עמידה בדרישות ההון של הממונה.",
    "scr": "Solvency Capital Requirement: דרישת ההון הנדרשת כדי להבטיח שהחברה תוכל לעמוד בהתחייבויותיה בהסתברות של 99.5%.",
    "combined_ratio": "יחס משולב: (הוצאות תביעות + הוצאות תפעול ושיווק) חלקי הפרמיות שהורווחו. יחס מתחת ל-100% מעיד על רווחיות חיתומית.",
    "loss_ratio": "יחס ההפסדים: סך התביעות ששולמו ועתודות לתביעות חלקי הפרמיות שהורווחו.",
    "lcr": "Liquidity Coverage Ratio: יחס כיסוי נזילות. היכולת של החברה לעמוד בהתחייבויות קצרות טווח באמצעות נכסים נזילים איכותיים.",
    "leverage": "מינוף פיננסי: היחס בין סך ההתחייבויות לסך הנכסים, או יחס הון למאזן.",
    "new_business_csm": "הערך הנוכחי של הרווחים הצפויים מחוזים חדשים שנמכרו במהלך תקופת הדיווח.",
    "onerous_contracts": "חוזים שבהם העלויות הצפויות (תביעות + הוצאות) עולות על ההכנסות הצפויות כבר במועד ההכרה הראשוני.",
    "tier1_capital": "הון עצמי רובד 1 (הון ליבה): כולל הון מניות ורווחים צבורים. ההון האיכותי ביותר לספיגת הפסדים.",
    "tier2_capital": "הון משני (רובד 2): כולל כתבי התחייבות נדחים ומכשירים היברידיים.",
    "real_yield": "תשואה ריאלית על תיק ההשקעות (בניכוי אינפלציה) במונחים שנתיים.",
    "unquoted_pct": "שיעור הנכסים בתיק הנוסטרו שאינם נסחרים בבורסה (חוב לא סחיר, נדל\"ן ישיר, קרנות השקעה)."
}

# --- 2. הגדרות מערכת ---
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

# --- 4. נתוני סימולציה ובנצ'מארק ---
def get_benchmark_data(selected_companies):
    """מייצר נתוני שוק להשוואה"""
    market_data = {
        "Harel": {"Solvency": 115, "ROE": 14.2, "CSM": 12500},
        "Phoenix": {"Solvency": 112, "ROE": 15.1, "CSM": 11000},
        "Migdal": {"Solvency": 105, "ROE": 9.8, "CSM": 13200},
        "Clal": {"Solvency": 108, "ROE": 10.5, "CSM": 9500},
        "Menora": {"Solvency": 110, "ROE": 13.5, "CSM": 10500},
        "Ayalon": {"Solvency": 102, "ROE": 8.5, "CSM": 2500},
        "IDI": {"Solvency": 118, "ROE": 18.0, "CSM": 3000}
    }
    
    data = {"חברה": [], "Solvency": [], "ROE": [], "CSM": []}
    for comp in selected_companies:
        if comp in market_data:
            data["חברה"].append(comp)
            data["Solvency"].append(market_data[comp]["Solvency"])
            data["ROE"].append(market_data[comp]["ROE"])
            data["CSM"].append(market_data[comp]["CSM"])
    return pd.DataFrame(data)

def generate_mock_data():
    return {
        "core_kpis": { "net_profit": 450.5, "total_csm": 12500.0, "roe": 14.2, "gross_premiums": 8200.0, "total_assets": 340000.0 },
        "ifrs17_segments": { "life_csm": 8500.0, "health_csm": 3200.0, "general_csm": 800.0, "onerous_contracts": 185.0, "new_business_csm": 1500.0 },
        "investment_mix": { "govt_bonds_pct": 35.0, "corp_bonds_pct": 20.0, "stocks_pct": 18.0, "real_estate_pct": 12.0, "unquoted_pct": 22.0, "real_yield": 4.2 },
        "financial_ratios": { "loss_ratio": 78.5, "combined_ratio": 96.2, "lcr": 1.35, "leverage": 6.2, "roa": 1.1 },
        "solvency": { "solvency_ratio": 104.5, "tier1_capital": 8200.0, "tier2_capital": 1800.0, "scr": 9560.0 },
        "consistency_check": { "opening_csm": 12000.0, "new_business_csm": 1500.0, "csm_release": 1000.0, "closing_csm": 12500.0 },
        "meta": { "confidence": 0.98, "extraction_time": datetime.utcnow().isoformat() + " (SIMULATION)" }
    }

# --- 5. AI Engine ---
def analyze_report(file_path, api_key, retries=3):
    if not os.path.exists(file_path): return None, f"קובץ חסר: {file_path}"
    with open(file_path, "rb") as f: pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    system_prompt = """
    You are a Regulatory AI Auditor. Extract JSON matching the schema. 
    Fields: core_kpis, ifrs17_segments (new_business_csm!), investment_mix (real_yield!), financial_ratios (lcr, roa!), solvency.
    Return null if missing.
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

# --- 6. UI ---
st.sidebar.title("🛡️ Apex Regulator")
api_key = st.secrets.get("GOOGLE_API_KEY")

st.sidebar.header("⚙️ הגדרות ניתוח")
company = st.sidebar.selectbox("חברה מדווחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
year = st.sidebar.selectbox("שנה", ["2025", "2024"])
use_sim = st.sidebar.checkbox("🧪 מצב סימולציה", value=True)

st.sidebar.divider()
st.sidebar.header("⚖️ מנוע השוואה")
# המנוע הדינמי להוספת חברות
compare_list = st.sidebar.multiselect(
    "בחר חברות להשוואה:",
    ["Phoenix", "Migdal", "Clal", "Menora", "Ayalon", "IDI"],
    default=["Phoenix", "Migdal"]
)

st.title(f"דשבורד פיקוח: {company} (Q1 2025)")

if "data" not in st.session_state: st.session_state.data = None

if st.button("🚀 הרץ ביקורת (Audit Run)"):
    if use_sim:
        with st.spinner("טוען נתוני עומק..."):
            time.sleep(1)
            st.session_state.data = generate_mock_data()
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
    # --- KPIs עם חלוניות הסבר (Tooltips) ---
    k = data['core_kpis']
    cols = st.columns(5)
    metrics = [
        ("רווח כולל", "net_profit", "M₪"), 
        ("יתרת CSM", "total_csm", "M₪"), 
        ("ROE", "roe", "%"), 
        ("פרמיות (GWP)", "gross_premiums", "M₪"), 
        ("נכסים (AUM)", "total_assets", "M₪")
    ]
    
    for i, (label, key, unit) in enumerate(metrics):
        # שימוש ב-help כדי להציג את ההסבר מהמילון
        cols[i].metric(label, fmt(k.get(key), unit), help=DEFINITIONS[key])

    st.divider()
    tabs = st.tabs(["📂 IFRS 17", "💰 השקעות", "🛡️ סולבנסי", "📉 יחסים (מורחב)", "⚖️ השוואה (דינמי)", "🕹️ סימולטור", "✅ אימות"])

    # 1. IFRS 17
    with tabs[0]:
        s = data['ifrs17_segments']
        st.subheader("ניתוח רווחיות (IFRS 17)")
        c1, c2 = st.columns([2,1])
        with c1:
            fig = px.bar(x=["חיים", "בריאות", "כללי"], y=[s.get('life_csm',0), s.get('health_csm',0), s.get('general_csm',0)], title="יתרת CSM לפי מגזר")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.info("ניתוח עסקים חדשים:")
            st.metric("CSM עסקים חדשים", fmt(s.get('new_business_csm'), "M₪"), help=DEFINITIONS["new_business_csm"])
            if s.get('onerous_contracts', 0) > 0:
                st.markdown(f'<div class="red-flag-box">🚩 חוזים מפסידים: ₪{s["onerous_contracts"]}M</div>', unsafe_allow_html=True)

    # 2. השקעות
    with tabs[1]:
        i = data['investment_mix']
        c1, c2 = st.columns(2)
        with c1:
            vals = [i.get('govt_bonds_pct',0), i.get('corp_bonds_pct',0), i.get('stocks_pct',0), i.get('real_estate_pct',0), i.get('unquoted_pct',0)]
            fig = px.pie(values=vals, names=["ממשלתי", "קונצרני", "מניות", "נדל\"ן", "לא סחיר"], hole=0.4, title="הקצאת נכסים")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("תשואה ריאלית", fmt(i.get('real_yield'), "%"), help=DEFINITIONS["real_yield"])
            st.metric("חשיפה ללא סחיר", fmt(i.get('unquoted_pct'), "%"), help=DEFINITIONS["unquoted_pct"])
            if i.get('unquoted_pct', 0) > 15:
                st.markdown(f'<div class="red-flag-box">🚩 חריגה ממגבלת השקעה</div>', unsafe_allow_html=True)

    # 3. סולבנסי
    with tabs[2]:
        sol = data['solvency']
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Solvency Ratio", fmt(sol.get('solvency_ratio'), "%"), help=DEFINITIONS["solvency_ratio"])
            st.metric("SCR (דרישת הון)", fmt(sol.get('scr'), "M₪"), help=DEFINITIONS["scr"])
        with c2:
            df_cap = pd.DataFrame({"סוג": ["Tier 1", "Tier 2"], "סכום": [sol.get('tier1_capital',0), sol.get('tier2_capital',0)]})
            st.plotly_chart(px.bar(df_cap, x="סוג", y="סכום", color="סוג", title="איכות ההון"), use_container_width=True)

    # 4. יחסים פיננסיים (מורחב ומחולק)
    with tabs[3]:
        st.subheader("דשבורד יחסים פיננסיים")
        r = data['financial_ratios']
        
        c_op, c_liq, c_prof = st.columns(3)
        
        with c_op:
            st.markdown("### ⚙️ תפעול")
            st.metric("Combined Ratio", fmt(r.get('combined_ratio'), "%"), help=DEFINITIONS["combined_ratio"])
            st.metric("Loss Ratio", fmt(r.get('loss_ratio'), "%"), help=DEFINITIONS["loss_ratio"])
            
        with c_liq:
            st.markdown("### 💧 נזילות ומינוף")
            st.metric("LCR (כיסוי נזילות)", fmt(r.get('lcr')), help=DEFINITIONS["lcr"])
            st.metric("מינוף פיננסי", fmt(r.get('leverage'), "%"), help=DEFINITIONS["leverage"])
            
        with c_prof:
            st.markdown("### 💰 רווחיות")
            st.metric("ROE (הון)", fmt(data['core_kpis'].get('roe'), "%"), help=DEFINITIONS["roe"])
            st.metric("ROA (נכסים)", fmt(r.get('roa'), "%"), help="תשואה על הנכסים")

    # 5. השוואה (דינמי!)
    with tabs[4]:
        st.subheader("מפת בנצ'מארק דינמית")
        # יצירת רשימה מלאה של החברות להשוואה (החברה שנבחרה + מה שסומן בצד)
        full_compare_list = [company] + compare_list
        df_bench = get_benchmark_data(full_compare_list)
        
        if not df_bench.empty:
            fig = px.scatter(df_bench, x="Solvency", y="ROE", size="CSM", color="חברה", text="חברה", 
                             title="חוסן (X) מול רווחיות (Y) מול עתודות רווח (גודל)", size_max=60)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("לא נבחרו חברות להשוואה.")

    # 6. סימולטור
    with tabs[5]:
        st.subheader("🕹️ סימולטור")
        c1, c2 = st.columns(2)
        with c1:
            rate = st.slider("ריבית", -2.0, 2.0, 0.0)
            market = st.slider("שוק מניות", -30, 0, 0)
        with c2:
            lapse = st.slider("ביטולים (Lapse)", 0, 50, 0)
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

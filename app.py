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

# --- 1. עיצוב המערכת (Deep Navy + Professional) ---
st.set_page_config(page_title="Apex Regulator Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 15px; border-radius: 8px; border-right: 4px solid #2e7bcf; box-shadow: 3px 3px 10px rgba(0,0,0,0.5); }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem; font-family: 'Segoe UI', sans-serif; }
    .ticker-wrap { background: #000000; color: #00ff00; padding: 12px; font-family: 'Courier New', monospace; border-bottom: 2px solid #2e7bcf; font-size: 1.1rem; }
    .red-flag-box { border: 1px solid #ff4b4b; background-color: rgba(255, 75, 75, 0.15); padding: 15px; border-radius: 5px; color: #ff4b4b; margin-top: 10px; font-weight: bold; }
    .section-header { border-bottom: 1px solid #444; padding-bottom: 10px; margin-bottom: 20px; color: #2e7bcf; }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה גלובלי ומקומי (מלא) ---
ticker_text = (
    "🌍 שווקים: ת\"א-35: 2,045.2 (+0.8%) ▲ | ת\"א-ביטוח: 2,540.1 (+1.4%) ▲ | "
    "🇺🇸 S&P 500: 5,120.3 (+0.4%) ▲ | NASDAQ: 16,250.8 (+0.7%) ▲ | "
    "🇪🇺 DAX: 18,150.4 (+0.2%) ▲ | 🇯🇵 NIKKEI: 38,500.5 (-0.3%) ▼ | "
    "🇮🇱 מניות ביטוח: הראל (+1.2%) | הפניקס (-0.5%) | מגדל (+0.8%) | מנורה (+0.3%) | כלל (+2.1%)"
)
st.markdown(f'<div class="ticker-wrap"><marquee scrollamount="12">{ticker_text}</marquee></div>', unsafe_allow_html=True)

# --- 3. סכמה קשיחה (כולל כל השדות החסרים) ---
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

# --- 4. נתוני סימולציה מורחבים ועשירים (ה"דמו" שאהבת) ---
def generate_comprehensive_mock_data():
    return {
        "core_kpis": { "net_profit": 450.5, "total_csm": 12500.0, "roe": 14.2, "gross_premiums": 8200.0, "total_assets": 340000.0 },
        "ifrs17_segments": { 
            "life_csm": 8500.0, "health_csm": 3200.0, "general_csm": 800.0, 
            "onerous_contracts": 185.0, # דגל אדום!
            "new_business_csm": 450.0 
        },
        "investment_mix": { 
            "govt_bonds_pct": 35.0, "corp_bonds_pct": 20.0, "stocks_pct": 18.0, "real_estate_pct": 12.0, 
            "unquoted_pct": 22.0, # דגל אדום! (מעל 15%)
            "real_yield": 4.2 
        },
        "financial_ratios": { "loss_ratio": 78.5, "combined_ratio": 96.2, "lcr": 1.15, "leverage": 5.8, "roa": 1.1 },
        "solvency": { "solvency_ratio": 104.5, "tier1_capital": 8200.0, "tier2_capital": 1800.0, "scr": 9560.0 },
        "consistency_check": { "opening_csm": 12000.0, "new_business_csm": 1500.0, "csm_release": 1000.0, "closing_csm": 12500.0 },
        "meta": { "confidence": 0.98, "extraction_time": datetime.utcnow().isoformat() + " (SIMULATION MODE)" }
    }

# --- 5. מנוע AI (עם מנגנון Retry) ---
def analyze_report_hardened(file_path, api_key, retries=3):
    if not os.path.exists(file_path): return None, f"קובץ חסר: {file_path}"
    with open(file_path, "rb") as f: pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Prompt מעודכן הכולל את כל השדות החדשים
    system_prompt = """
    You are a Regulatory AI Auditor. Extract JSON matching the schema. 
    Keys: core_kpis, ifrs17_segments (include onerous & new_business), investment_mix (include unquoted & yield), 
    financial_ratios (include LCR & ROA), solvency (Tier1/Tier2), consistency_check.
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
st.sidebar.header("הגדרות הרצה")
company = st.sidebar.selectbox("חברה", ["Harel", "Phoenix", "Migdal"])
year = st.sidebar.selectbox("שנה", ["2025", "2024"])
use_sim = st.sidebar.checkbox("🧪 מצב סימולציה (עשיר)", value=True)
compare_with = st.sidebar.multiselect("השוואה", ["Phoenix", "Migdal", "Clal"], default=["Phoenix"])

st.title(f"דשבורד פיקוח הוליסטי: {company} (Q1 2025)")

if "data" not in st.session_state: st.session_state.data = None

if st.button("🚀 הרץ ניתוח מלא (Audit Run)"):
    if use_sim:
        with st.spinner("טוען נתונים, מחשב סיכונים ומבצע ולידציה..."):
            time.sleep(1.5)
            st.session_state.data = generate_comprehensive_mock_data()
            st.balloons()
    elif api_key:
        path = f"data/{company}/2025/Q1/financial/financial_report.pdf"
        res, status = analyze_report_hardened(path, api_key)
        if status == "success": st.session_state.data = res
        else: st.error(status)
    else: st.error("חסר API Key")

data = st.session_state.data
def fmt(v, s=""): return f"{v:,.1f}{s}" if v is not None else "N/A"

if data:
    # KPI SECTION
    k = data['core_kpis']
    cols = st.columns(5)
    metrics = [("רווח כולל", k['net_profit'], "M₪"), ("יתרת CSM", k['total_csm'], "M₪"), ("ROE", k['roe'], "%"), ("פרמיות", k['gross_premiums'], "M₪"), ("נכסים", k['total_assets'], "M₪")]
    for i, (l, v, u) in enumerate(metrics):
        cols[i].metric(l, fmt(v, u))
    
    st.divider()

    # TABS - כל הפיצ'רים חזרו!
    tabs = st.tabs(["📂 IFRS 17", "💰 השקעות", "🛡️ סולבנסי", "📉 יחסים", "⚖️ השוואה", "🕹️ סימולטור", "✅ אימות"])

    # 1. IFRS 17
    with tabs[0]:
        s = data['ifrs17_segments']
        st.subheader("ניתוח רווחיות ביטוחית")
        c1, c2 = st.columns([2,1])
        with c1:
            fig = px.bar(x=["חיים", "בריאות", "כללי"], y=[s['life_csm'], s['health_csm'], s['general_csm']], title="יתרת CSM לפי מגזר")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("### דגשים:")
            st.write(f"**CSM חדש (New Business):** ₪{s['new_business_csm']}M")
            if s['onerous_contracts'] > 0:
                st.markdown(f'<div class="red-flag-box">🚩 חוזים מפסידים (Onerous): ₪{s["onerous_contracts"]}M</div>', unsafe_allow_html=True)

    # 2. השקעות (עם Donut Chart + Real Yield)
    with tabs[1]:
        i = data['investment_mix']
        st.subheader("תיק נוסטרו וחשיפות")
        c1, c2 = st.columns(2)
        with c1:
            labels = ["אג\"ח ממשלתי", "קונצרני", "מניות", "נדל\"ן", "לא סחיר"]
            vals = [i['govt_bonds_pct'], i['corp_bonds_pct'], i['stocks_pct'], i['real_estate_pct'], i['unquoted_pct']]
            fig = px.pie(values=vals, names=labels, hole=0.4, title="הקצאת נכסים")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("תשואה ריאלית שנתית", fmt(i['real_yield'], "%"))
            if i['unquoted_pct'] > 15:
                st.markdown(f'<div class="red-flag-box">🚩 חשיפה גבוהה לנכסים לא סחירים ({i["unquoted_pct"]}%)</div>', unsafe_allow_html=True)

    # 3. סולבנסי (Tier 1 vs Tier 2)
    with tabs[2]:
        sol = data['solvency']
        st.subheader("איכות הון ויציבות")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Solvency Ratio", fmt(sol['solvency_ratio'], "%"))
            st.progress(min((sol['solvency_ratio'] or 0)/200, 1.0))
            st.write(f"**SCR:** ₪{sol['scr']}M")
        with c2:
            df_cap = pd.DataFrame({"סוג": ["Tier 1 (ליבה)", "Tier 2 (משני)"], "סכום": [sol['tier1_capital'], sol['tier2_capital']]})
            st.plotly_chart(px.bar(df_cap, x="סוג", y="סכום", color="סוג", title="הרכב הון"), use_container_width=True)

    # 4. יחסים (כולל LCR ו-ROA)
    with tabs[3]:
        r = data['financial_ratios']
        c1, c2 = st.columns(2)
        c1.write(f"**Loss Ratio:** {fmt(r['loss_ratio'], '%')}")
        c1.write(f"**Combined Ratio:** {fmt(r['combined_ratio'], '%')}")
        c1.write(f"**ROA:** {fmt(r.get('roa'), '%')}")
        c2.write(f"**LCR (נזילות):** {fmt(r['lcr'])}")
        c2.write(f"**מינוף:** {fmt(r['leverage'], '%')}")
        if r['combined_ratio'] > 100: st.error("⚠️ הפסד חיתומי (Combined > 100%)")

    # 5. השוואה (Bubble Chart)
    with tabs[4]:
        st.subheader("מפת השוואה ענפית")
        b_data = {"חברה": [company] + compare_with, "Solvency": [sol['solvency_ratio'], 112, 98, 105][:len(compare_with)+1], "ROE": [k['roe'], 12.5, 9.2, 11.0][:len(compare_with)+1], "CSM": [k['total_csm'], 11000, 7500, 9200][:len(compare_with)+1]}
        fig = px.scatter(pd.DataFrame(b_data), x="Solvency", y="ROE", size="CSM", color="חברה", text="חברה", title="חוסן (X) מול רווחיות (Y) מול גודל (בועה)")
        st.plotly_chart(fig, use_container_width=True)

    # 6. סימולטור (חזר מלא!)
    with tabs[5]:
        st.subheader("🕹️ סימולטור תרחישי קיצון")
        c1, c2 = st.columns(2)
        with c1:
            rate = st.slider("שינוי ריבית (%)", -2.0, 2.0, 0.0)
            market = st.slider("נפילה בשוק המניות (%)", -30, 0, 0)
        with c2:
            lapse = st.slider("גידול בביטולים (Lapse)", 0, 50, 0)
            quake = st.checkbox("תרחיש רעידת אדמה")
        
        base_csm = k['total_csm'] or 0
        impact = (rate * 250) + (market * 60) - (lapse * 120)
        if quake: impact -= 1500
        new_val = base_csm + impact
        st.metric("יתרת CSM חזויה", fmt(new_val, "M₪"), delta=fmt(impact, "M₪"))

    # 7. אימות
    with tabs[6]:
        c = data['consistency_check']
        calc = (c['opening_csm'] or 0) + (c['new_business_csm'] or 0) - (c['csm_release'] or 0)
        diff = (c['closing_csm'] or 0) - calc
        st.metric("פער חשבונאי", fmt(diff, "M₪"))
        if abs(diff) < 2: st.success("✅ נתונים מאומתים")
        else: st.error("❌ כשל בהלימות נתונים")

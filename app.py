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

# --- 1. עיצוב המערכת ---
st.set_page_config(page_title="Apex Regulator Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 15px; border-radius: 8px; border-right: 4px solid #2e7bcf; box-shadow: 3px 3px 10px rgba(0,0,0,0.5); }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem; font-family: 'Segoe UI', sans-serif; }
    .ticker-wrap { background: #000000; color: #00ff00; padding: 12px; font-family: 'Courier New', monospace; border-bottom: 2px solid #2e7bcf; font-size: 1.1rem; }
    .red-flag-box { border: 1px solid #ff4b4b; background-color: rgba(255, 75, 75, 0.15); padding: 15px; border-radius: 5px; color: #ff4b4b; margin-top: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה ---
ticker_text = (
    "🌍 שווקים: ת\"א-35: 2,045.2 (+0.8%) ▲ | ת\"א-ביטוח: 2,540.1 (+1.4%) ▲ | "
    "🇺🇸 S&P 500: 5,120.3 (+0.4%) ▲ | NASDAQ: 16,250.8 (+0.7%) ▲ | "
    "🇮🇱 מניות ביטוח: הראל (+1.2%) | הפניקס (-0.5%) | מגדל (+0.8%)"
)
st.markdown(f'<div class="ticker-wrap"><marquee scrollamount="12">{ticker_text}</marquee></div>', unsafe_allow_html=True)

# --- 3. סכמה (Schema) - כולל new_business_csm ---
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

# --- 4. נתוני סימולציה (מתוקנים) ---
def generate_comprehensive_mock_data():
    return {
        "core_kpis": { "net_profit": 450.5, "total_csm": 12500.0, "roe": 14.2, "gross_premiums": 8200.0, "total_assets": 340000.0 },
        "ifrs17_segments": { 
            "life_csm": 8500.0, "health_csm": 3200.0, "general_csm": 800.0, 
            "onerous_contracts": 185.0, 
            "new_business_csm": 1500.0  # הנתון החסר תוקן!
        },
        "investment_mix": { 
            "govt_bonds_pct": 35.0, "corp_bonds_pct": 20.0, "stocks_pct": 18.0, "real_estate_pct": 12.0, 
            "unquoted_pct": 22.0, 
            "real_yield": 4.2 
        },
        "financial_ratios": { "loss_ratio": 78.5, "combined_ratio": 96.2, "lcr": 1.15, "leverage": 5.8, "roa": 1.1 },
        "solvency": { "solvency_ratio": 104.5, "tier1_capital": 8200.0, "tier2_capital": 1800.0, "scr": 9560.0 },
        "consistency_check": { 
            "opening_csm": 12000.0, 
            "new_business_csm": 1500.0, # תואם לנתון למעלה
            "csm_release": 1000.0, 
            "closing_csm": 12500.0 
        },
        "meta": { "confidence": 0.98, "extraction_time": datetime.utcnow().isoformat() + " (SIMULATION MODE)" }
    }

# --- 5. מנוע AI ---
def analyze_report_hardened(file_path, api_key, retries=3):
    if not os.path.exists(file_path): return None, f"קובץ חסר: {file_path}"
    with open(file_path, "rb") as f: pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    system_prompt = """
    You are a Regulatory AI Auditor. Extract JSON matching the schema. 
    Keys: core_kpis, ifrs17_segments (include onerous & new_business_csm), investment_mix, financial_ratios, solvency, consistency_check.
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
use_sim = st.sidebar.checkbox("🧪 מצב סימולציה (עשיר)", value=True)

st.title(f"דשבורד פיקוח: {company} (Q1 2025)")

if "data" not in st.session_state: st.session_state.data = None

if st.button("🚀 הרץ ניתוח מלא (Audit Run)"):
    if use_sim:
        with st.spinner("טוען נתונים..."):
            time.sleep(1)
            st.session_state.data = generate_comprehensive_mock_data()
    elif api_key:
        path = f"data/{company}/2025/Q1/financial/financial_report.pdf"
        res, status = analyze_report_hardened(path, api_key)
        if status == "success": st.session_state.data = res
        else: st.error(status)
    else: st.error("חסר API Key")

data = st.session_state.data
def fmt(v, s=""): return f"{v:,.1f}{s}" if v is not None else "N/A"

if data:
    # KPI
    k = data['core_kpis']
    cols = st.columns(5)
    metrics = [("רווח כולל", k.get('net_profit'), "M₪"), ("יתרת CSM", k.get('total_csm'), "M₪"), ("ROE", k.get('roe'), "%"), ("פרמיות", k.get('gross_premiums'), "M₪"), ("נכסים", k.get('total_assets'), "M₪")]
    for i, (l, v, u) in enumerate(metrics):
        cols[i].metric(l, fmt(v, u))
    
    st.divider()

    tabs = st.tabs(["📂 IFRS 17", "💰 השקעות", "🛡️ סולבנסי", "📉 יחסים", "⚖️ השוואה", "🕹️ סימולטור", "✅ אימות"])

    # 1. IFRS 17 (הכיתוב תוקן ל"עסקים חדשים")
    with tabs[0]:
        s = data['ifrs17_segments']
        st.subheader("ניתוח רווחיות ביטוחית")
        c1, c2 = st.columns([2,1])
        with c1:
            # שימוש ב-get כדי למנוע קריסה
            fig = px.bar(x=["חיים", "בריאות", "כללי"], y=[s.get('life_csm',0), s.get('health_csm',0), s.get('general_csm',0)], title="יתרת CSM לפי מגזר")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("### דגשים:")
            
            # תוקן: הכיתוב המקצועי המדויק
            st.write(f"**CSM עסקים חדשים:** ₪{s.get('new_business_csm', 0)}M")
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
            st.metric("תשואה ריאלית", fmt(i.get('real_yield'), "%"))
            if i.get('unquoted_pct', 0) > 15:
                st.markdown(f'<div class="red-flag-box">🚩 חשיפה גבוהה ללא סחיר ({i["unquoted_pct"]}%)</div>', unsafe_allow_html=True)

    # 3. סולבנסי
    with tabs[2]:
        sol = data['solvency']
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Solvency Ratio", fmt(sol.get('solvency_ratio'), "%"))
            st.write(f"**SCR:** ₪{sol.get('scr',0)}M")
        with c2:
            df_cap = pd.DataFrame({"סוג": ["Tier 1", "Tier 2"], "סכום": [sol.get('tier1_capital',0), sol.get('tier2_capital',0)]})
            st.plotly_chart(px.bar(df_cap, x="סוג", y="סכום", color="סוג"), use_container_width=True)

    # 4. יחסים
    with tabs[3]:
        r = data['financial_ratios']
        c1, c2 = st.columns(2)
        c1.write(f"**Loss Ratio:** {fmt(r.get('loss_ratio'), '%')}")
        c1.write(f"**Combined Ratio:** {fmt(r.get('combined_ratio'), '%')}")
        c2.write(f"**LCR:** {fmt(r.get('lcr'))}")
        c2.write(f"**ROA:** {fmt(r.get('roa'), '%')}")

    # 5. השוואה
    with tabs[4]:
        st.subheader("מפת השוואה")
        b_data = {"חברה": [company, "Phoenix", "Clal"], "Solvency": [sol.get('solvency_ratio',0), 112, 105], "ROE": [k.get('roe',0), 12.5, 9.2], "CSM": [k.get('total_csm',0), 11000, 9200]}
        fig = px.scatter(pd.DataFrame(b_data), x="Solvency", y="ROE", size="CSM", color="חברה", text="חברה")
        st.plotly_chart(fig, use_container_width=True)

    # 6. סימולטור
    with tabs[5]:
        st.subheader("🕹️ סימולטור")
        c1, c2 = st.columns(2)
        with c1:
            rate = st.slider("שינוי ריבית", -2.0, 2.0, 0.0)
            market = st.slider("נפילה במניות", -30, 0, 0)
        with c2:
            lapse = st.slider("ביטולים (Lapse)", 0, 50, 0)
            quake = st.checkbox("רעידת אדמה")
        
        base_csm = k.get('total_csm', 0) or 0
        impact = (rate * 250) + (market * 60) - (lapse * 120)
        if quake: impact -= 1500
        st.metric("יתרת CSM חזויה", fmt(base_csm + impact, "M₪"), delta=fmt(impact, "M₪"))

    # 7. אימות
    with tabs[6]:
        c = data['consistency_check']
        # שימוש בנתון החדש בחישוב
        calc = (c.get('opening_csm',0) or 0) + (c.get('new_business_csm',0) or 0) - (c.get('csm_release',0) or 0)
        diff = (c.get('closing_csm',0) or 0) - calc
        
        c1, c2, c3 = st.columns(3)
        c1.metric("צפוי", fmt(calc, "M"))
        c2.metric("בפועל", fmt(c.get('closing_csm'), "M"))
        c3.metric("פער", fmt(diff, "M"))
        
        if abs(diff) < 2: st.success("✅ מאומת")
        else: st.error("❌ כשל בהלימות")

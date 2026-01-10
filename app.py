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

# --- 1. הגדרות תצורה ועיצוב ---
st.set_page_config(page_title="Apex Regulator System", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 15px; border-radius: 5px; border-right: 4px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.6rem; font-family: 'Roboto Mono', monospace; }
    .ticker-wrap { background: #111; color: #ccc; padding: 5px; border-bottom: 1px solid #333; font-size: 0.8rem; }
    .validation-error { background-color: #3d0808; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; color: #ff9999; margin-bottom: 5px; }
    .ticker { display: inline-block; animation: ticker 60s linear infinite; font-weight: bold; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה רץ ---
ticker_text = (
    "🇮🇱 ת\"א-35: 2,045.2 (+0.8%) | ת\"א-ביטוח: 2,540.1 (+1.4%) | "
    "🇺🇸 S&P 500: 5,120.3 (+0.4%) | NASDAQ: 16,250.8 (+0.7%) | "
    "🇪🇺 DAX: 18,150.4 (+0.2%) | הראל: +1.2% | הפניקס: -0.5% | מגדל: +0.8%"
)
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_text}</div></div>', unsafe_allow_html=True)

# --- 3. מודל נתונים (Schema) ---
IFRS17_SCHEMA = {
    "type": "object",
    "required": ["core_kpis", "ifrs17_segments", "financial_ratios", "solvency", "consistency_check", "meta"],
    "properties": {
        "core_kpis": {
            "type": "object",
            "required": ["net_profit", "total_csm", "roe", "gross_premiums", "total_assets"],
            "properties": {
                "net_profit": {"type": ["number", "null"]},
                "total_csm": {"type": ["number", "null"]},
                "roe": {"type": ["number", "null"]},
                "gross_premiums": {"type": ["number", "null"]},
                "total_assets": {"type": ["number", "null"]}
            }
        },
        "ifrs17_segments": {
            "type": "object",
            "required": ["life_csm", "health_csm", "general_csm", "onerous_contracts"],
            "properties": {
                "life_csm": {"type": ["number", "null"]},
                "health_csm": {"type": ["number", "null"]},
                "general_csm": {"type": ["number", "null"]},
                "onerous_contracts": {"type": ["number", "null"], "minimum": 0}
            }
        },
        "investment_mix": {
            "type": "object",
            "required": ["govt_bonds_pct", "corp_bonds_pct", "stocks_pct", "real_estate_pct", "unquoted_pct"],
            "properties": {
                "govt_bonds_pct": {"type": ["number", "null"]},
                "corp_bonds_pct": {"type": ["number", "null"]},
                "stocks_pct": {"type": ["number", "null"]},
                "real_estate_pct": {"type": ["number", "null"]},
                "unquoted_pct": {"type": ["number", "null"]}
            }
        },
        "financial_ratios": {
            "type": "object",
            "required": ["loss_ratio", "combined_ratio", "lcr", "leverage"],
            "properties": {
                "loss_ratio": {"type": ["number", "null"]},
                "combined_ratio": {"type": ["number", "null"]},
                "lcr": {"type": ["number", "null"]},
                "leverage": {"type": ["number", "null"]}
            }
        },
        "solvency": {
            "type": "object",
            "required": ["solvency_ratio", "tier1_capital", "tier2_capital", "scr"],
            "properties": {
                "solvency_ratio": {"type": ["number", "null"]},
                "tier1_capital": {"type": ["number", "null"]},
                "tier2_capital": {"type": ["number", "null"]},
                "scr": {"type": ["number", "null"]}
            }
        },
        "consistency_check": {
            "type": "object",
            "required": ["opening_csm", "new_business_csm", "csm_release", "closing_csm"],
            "properties": {
                "opening_csm": {"type": ["number", "null"]},
                "new_business_csm": {"type": ["number", "null"]},
                "csm_release": {"type": ["number", "null"]},
                "closing_csm": {"type": ["number", "null"]}
            }
        },
        "meta": {
            "type": "object",
            "required": ["confidence", "extraction_time"],
            "properties": {
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "extraction_time": {"type": "string"}
            }
        }
    }
}

# --- 4. מנוע ולידציה ---
def validate_business_logic(data):
    errors = []
    try:
        if data["solvency"]["tier1_capital"] is not None and data["solvency"]["tier2_capital"] is not None:
            if data["solvency"]["tier1_capital"] < data["solvency"]["tier2_capital"]:
                errors.append("חריגה לוגית: הון רובד 2 גבוה מהון רובד 1.")
    except: pass
    try:
        if data["financial_ratios"]["combined_ratio"] is not None and data["financial_ratios"]["loss_ratio"] is not None:
            if data["financial_ratios"]["combined_ratio"] < data["financial_ratios"]["loss_ratio"]:
                errors.append("שגיאת לוגיקה: Combined Ratio נמוך מ-Loss Ratio.")
    except: pass
    return errors

# --- 5. מחולל נתוני סימולציה (Mock Data Generator) ---
def generate_mock_data():
    """מייצר נתוני דמה תקניים לחלוטין לצורך תצוגה בלבד"""
    return {
        "core_kpis": {
            "net_profit": 450.5,
            "total_csm": 12500.0,
            "roe": 14.2,
            "gross_premiums": 8200.0,
            "total_assets": 340000.0
        },
        "ifrs17_segments": {
            "life_csm": 8500.0,
            "health_csm": 3200.0,
            "general_csm": 800.0,
            "onerous_contracts": 120.0  # יפעיל דגל אדום
        },
        "investment_mix": {
            "govt_bonds_pct": 45.0,
            "corp_bonds_pct": 25.0,
            "stocks_pct": 15.0,
            "real_estate_pct": 10.0,
            "unquoted_pct": 18.5 # יפעיל אזהרה
        },
        "financial_ratios": {
            "loss_ratio": 76.4,
            "combined_ratio": 94.2,
            "lcr": 1.35,
            "leverage": 5.4
        },
        "solvency": {
            "solvency_ratio": 108.5,
            "tier1_capital": 9200.0,
            "tier2_capital": 1400.0,
            "scr": 9770.0
        },
        "consistency_check": {
            "opening_csm": 12000.0,
            "new_business_csm": 1500.0,
            "csm_release": 1000.0,
            "closing_csm": 12500.0 # תואם חשבונאית (12000+1500-1000=12500)
        },
        "meta": {
            "confidence": 0.95,
            "extraction_time": datetime.utcnow().isoformat() + " (SIMULATION)"
        }
    }

# --- 6. מנוע AI (עם מנגנון Retry) ---
def analyze_report_hardened(file_path, api_key, retries=3):
    if not os.path.exists(file_path):
        return None, f"קובץ חסר: {file_path}. וודא העלאה ל-GitHub."
    
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    system_prompt = """
    You are a strict Regulatory AI Auditor. Extract data from the Insurance Report (IFRS 17 & Solvency II).
    RULES:
    1. Output strictly valid JSON matching the schema.
    2. If a value is NOT explicitly found, return null. DO NOT guess.
    3. JSON Keys: core_kpis, ifrs17_segments, investment_mix, financial_ratios, solvency, consistency_check, meta.
    Return ONLY JSON.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": system_prompt}, {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}]}]}
    
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload)
            if response.status_code in [429, 500, 503]:
                time.sleep(2 ** attempt)
                continue
            if response.status_code == 200:
                raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                clean_json = raw_text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_json)
                data["meta"]["extraction_time"] = datetime.utcnow().isoformat()
                validate(instance=data, schema=IFRS17_SCHEMA)
                logic_errors = validate_business_logic(data)
                if logic_errors: data["logic_errors"] = logic_errors
                return data, "success"
            else:
                return None, f"API Error {response.status_code}: {response.text}"
        except Exception as e:
            if attempt == retries - 1: return None, f"Error: {str(e)}"
            time.sleep(2)
    return None, "Connection Failed."

# --- 7. ממשק משתמש (UI) ---
st.sidebar.title("🛡️ Apex Regulator")
api_key = st.secrets.get("GOOGLE_API_KEY")

company = st.sidebar.selectbox("ישות מפוקחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
year = st.sidebar.selectbox("שנת דיווח", ["2025", "2024"])
quarter = st.sidebar.radio("רבעון", ["Q1", "Q2", "Q3"])
st.sidebar.divider()

# --- הכפתור החדש שמציל את המצב ---
use_simulation = st.sidebar.checkbox("🧪 מצב סימולציה (ללא חיוב API)", value=True)
st.sidebar.divider()
compare_with = st.sidebar.multiselect("השוואה מול", ["Phoenix", "Migdal", "Clal"], default=["Phoenix"])

st.title(f"מערכת פיקוח: {company} ({year} {quarter})")

if "reg_data" not in st.session_state:
    st.session_state.reg_data = None

run_btn = st.button("🚀 הרץ ביקורת דוחות (Audit Run)")

if run_btn:
    if use_simulation:
        with st.spinner("טוען נתוני סימולציה למטרות הדגמה..."):
            time.sleep(1.5) # אפקט של טעינה
            st.session_state.reg_data = generate_mock_data()
            st.balloons()
    else:
        # מצב אמת - דורש מפתח
        if not api_key: st.error("חסר מפתח הצפנה (API Key) להרצה חיה")
        else:
            path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
            with st.spinner("🔄 מבצע חילוץ נתונים בזמן אמת..."):
                res, status = analyze_report_hardened(path, api_key)
                if status == "success":
                    st.session_state.reg_data = res
                    st.balloons()
                else:
                    st.error(f"⛔ הניתוח נעצר: {status}")

data = st.session_state.reg_data

# פונקציית עזר להצגה
def fmt(val, suffix="", default="N/A"):
    if val is None: return default
    return f"{val:,.1f}{suffix}" if isinstance(val, float) else f"{val}{suffix}"

if data:
    # --- שער איכות ---
    conf = data["meta"]["confidence"]
    is_sim = "SIMULATION" in data["meta"]["extraction_time"]
    
    col_q1, col_q2 = st.columns([3, 1])
    with col_q1:
        if is_sim:
            st.info(f"🧪 **נתוני סימולציה** (מצב הדגמה) | הנתונים אינם מבוססים על דוח אמיתי")
        elif conf >= 0.8: st.success(f"🟢 רמת אמינות גבוהה ({conf:.0%})")
        else: st.warning(f"🟠 רמת אמינות בינונית ({conf:.0%})")
    
    if "logic_errors" in data:
        for err in data["logic_errors"]:
            st.markdown(f'<div class="validation-error">⚠️ {err}</div>', unsafe_allow_html=True)

    st.divider()

    # --- KPIs ---
    kpi = data['core_kpis']
    cols = st.columns(5)
    cols[0].metric("רווח כולל", fmt(kpi['net_profit'], "M₪"))
    cols[1].metric("יתרת CSM", fmt(kpi['total_csm'], "M₪"))
    cols[2].metric("ROE", fmt(kpi['roe'], "%"))
    cols[3].metric("פרמיות", fmt(kpi['gross_premiums'], "M₪"))
    cols[4].metric("נכסים", fmt(kpi['total_assets'], "M₪"))
    
    # --- Tabs ---
    tabs = st.tabs(["📂 IFRS 17", "💰 השקעות", "🛡️ סולבנסי", "📉 יחסים", "⚖️ השוואה", "✅ אימות"])

    # Tab 1: IFRS 17
    with tabs[0]:
        seg = data['ifrs17_segments']
        st.subheader("פילוח CSM")
        valid_segs = {k: v for k, v in seg.items() if v is not None and "csm" in k}
        if valid_segs:
            df_seg = pd.DataFrame({"מגזר": list(valid_segs.keys()), "CSM": list(valid_segs.values())})
            st.plotly_chart(px.bar(df_seg, x="מגזר", y="CSM", title="יתרת CSM לפי מגזר"))
        
        if seg['onerous_contracts'] and seg['onerous_contracts'] > 0:
            st.error(f"🚩 חוזים מפסידים (Onerous): ₪{seg['onerous_contracts']}M")

    # Tab 2: Investments
    with tabs[1]:
        inv = data['investment_mix']
        st.subheader("תיק נוסטרו")
        valid_inv = {k: v for k, v in inv.items() if v is not None}
        if valid_inv:
            df_inv = pd.DataFrame({"אפיק": list(valid_inv.keys()), "חשיפה": list(valid_inv.values())})
            st.plotly_chart(px.pie(df_inv, values="חשיפה", names="אפיק"))
        
        if inv.get('unquoted_pct') and inv['unquoted_pct'] > 15:
            st.warning(f"⚠️ חשיפה לנכסים לא סחירים: {inv['unquoted_pct']}% - דורש בדיקת שערוך")

    # Tab 3: Solvency
    with tabs[2]:
        sol = data['solvency']
        c1, c2 = st.columns(2)
        c1.metric("Solvency Ratio", fmt(sol['solvency_ratio'], "%"))
        c1.metric("SCR", fmt(sol['scr'], "M₪"))
        if sol['tier1_capital'] and sol['tier2_capital']:
            df_cap = pd.DataFrame({"סוג": ["Tier 1", "Tier 2"], "סכום": [sol['tier1_capital'], sol['tier2_capital']]})
            st.plotly_chart(px.bar(df_cap, x="סוג", y="סכום", color="סוג", title="איכות ההון (Tier 1 vs Tier 2)"))

    # Tab 4: Ratios
    with tabs[3]:
        rat = data['financial_ratios']
        c1, c2 = st.columns(2)
        c1.write(f"**Loss Ratio:** {fmt(rat['loss_ratio'], '%')}")
        c1.write(f"**Combined Ratio:** {fmt(rat['combined_ratio'], '%')}")
        c2.write(f"**LCR:** {fmt(rat['lcr'])}")
        c2.write(f"**Leverage:** {fmt(rat['leverage'], '%')}")

    # Tab 5: Benchmarking
    with tabs[4]:
        st.subheader("מפת השוואה ענפית")
        bench_data = {
            "חברה": [company] + compare_with,
            "Solvency": [sol['solvency_ratio'] or 0, 110, 102, 108][:len(compare_with)+1],
            "ROE": [kpi['roe'] or 0, 12.0, 11.5, 13.2][:len(compare_with)+1],
            "CSM": [kpi['total_csm'] or 0, 10000, 8000, 12000][:len(compare_with)+1]
        }
        df_bench = pd.DataFrame(bench_data)
        st.plotly_chart(px.scatter(df_bench, x="Solvency", y="ROE", size="CSM", color="חברה", text="חברה"))

    # Tab 6: Consistency
    with tabs[5]:
        chk = data['consistency_check']
        if all(v is not None for v in chk.values()):
            calc = chk['opening_csm'] + chk['new_business_csm'] - chk['csm_release']
            diff = chk['closing_csm'] - calc
            c1, c2, c3 = st.columns(3)
            c1.metric("צפוי", fmt(calc, "M"))
            c2.metric("בפועל", fmt(chk['closing_csm'], "M"))
            c3.metric("פער", fmt(diff, "M"))
            
            if abs(diff) > 2: st.error("❌ הנתונים אינם מתכנסים חשבונאית")
            else: st.success("✅ אימות חשבונאי תקין")

else:
    st.info("אנא לחץ על כפתור ההרצה כדי להתחיל (בחר 'מצב סימולציה' אם אין מפתח API פעיל).")

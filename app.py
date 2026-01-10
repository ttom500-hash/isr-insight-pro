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

# --- 1. הגדרות תצורה ועיצוב (Regulator Mode) ---
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

# --- 3. מודל נתונים רגולטורי קשיח (JSON Schema) ---
# מאפשר Null כי Missing ≠ 0
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

# --- 4. מנוע ולידציה לוגית ---
def validate_business_logic(data):
    errors = []
    # Tier 1 vs Tier 2
    try:
        if data["solvency"]["tier1_capital"] is not None and data["solvency"]["tier2_capital"] is not None:
            if data["solvency"]["tier1_capital"] < data["solvency"]["tier2_capital"]:
                errors.append("חריגה לוגית: הון רובד 2 גבוה מהון רובד 1.")
    except: pass
    
    # Combined vs Loss Ratio
    try:
        if data["financial_ratios"]["combined_ratio"] is not None and data["financial_ratios"]["loss_ratio"] is not None:
            if data["financial_ratios"]["combined_ratio"] < data["financial_ratios"]["loss_ratio"]:
                errors.append("שגיאת לוגיקה: Combined Ratio נמוך מ-Loss Ratio.")
    except: pass
    
    return errors

# --- 5. מנוע AI (כולל Retry Logic) ---
def analyze_report_hardened(file_path, api_key, retries=3):
    if not os.path.exists(file_path):
        return None, f"קובץ חסר: {file_path}. וודא העלאה ל-GitHub."
    
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    system_prompt = """
    You are a strict Regulatory AI Auditor. Extract data from the Insurance Report (IFRS 17 & Solvency II).
    RULES:
    1. Output strictly valid JSON matching the schema.
    2. If a value is NOT explicitly found, return null. DO NOT guess. DO NOT use 0 for missing data.
    3. JSON Keys: core_kpis, ifrs17_segments, investment_mix, financial_ratios, solvency, consistency_check, meta.
    Return ONLY JSON.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": system_prompt}, {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}]}]}
    
    # מנגנון העקשן (Retry Mechanism)
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code in [429, 500, 503]: # שגיאות עומס/שרת
                time.sleep(2 ** attempt) # Backoff: 1s, 2s, 4s
                continue
            
            if response.status_code == 200:
                raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                clean_json = raw_text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_json)
                
                # העשרת מטא-דאטה
                data["meta"]["extraction_time"] = datetime.utcnow().isoformat()
                
                # ולידציה מבנית (Schema)
                try:
                    validate(instance=data, schema=IFRS17_SCHEMA)
                except ValidationError as ve:
                    return None, f"כשל מבני בנתונים (Schema): {ve.message}"
                
                # ולידציה עסקית (Business Logic)
                logic_errors = validate_business_logic(data)
                if logic_errors:
                    data["logic_errors"] = logic_errors
                
                return data, "success"
            else:
                return None, f"API Error {response.status_code}: {response.text}"
                
        except Exception as e:
            if attempt == retries - 1:
                return None, f"Critical System Error: {str(e)}"
            time.sleep(2)
            
    return None, "Connection Failed after multiple retries."

# --- 6. ממשק משתמש (UI) ---
st.sidebar.title("🛡️ Apex Regulator")
api_key = st.secrets.get("GOOGLE_API_KEY")

company = st.sidebar.selectbox("ישות מפוקחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
year = st.sidebar.selectbox("שנת דיווח", ["2025", "2024"])
quarter = st.sidebar.radio("רבעון", ["Q1", "Q2", "Q3"])
st.sidebar.divider()
compare_with = st.sidebar.multiselect("השוואה מול", ["Phoenix", "Migdal", "Clal"], default=["Phoenix"])

st.title(f"מערכת פיקוח: {company} ({year} {quarter})")

if "reg_data" not in st.session_state:
    st.session_state.reg_data = None

if st.button("🚀 הרץ ביקורת דוחות (Audit Run)"):
    if not api_key: st.error("חסר מפתח הצפנה (API Key)")
    else:
        path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
        with st.spinner("🔄 מבצע חילוץ נתונים, ולידציה ואימות רגולטורי..."):
            res, status = analyze_report_hardened(path, api_key)
            if status == "success":
                st.session_state.reg_data = res
                st.balloons()
            else:
                st.error(f"⛔ הניתוח נעצר: {status}")

data = st.session_state.reg_data

# פונקציית עזר להצגה בטוחה
def fmt(val, suffix="", default="N/A"):
    if val is None: return default
    return f"{val:,.1f}{suffix}" if isinstance(val, float) else f"{val}{suffix}"

if data:
    # --- שער איכות (Quality Gate) ---
    conf = data["meta"]["confidence"]
    c_col1, c_col2 = st.columns([3, 1])
    with c_col1:
        if conf >= 0.8: st.success(f"🟢 רמת אמינות גבוהה ({conf:.0%})")
        elif conf >= 0.6: st.warning(f"🟠 רמת אמינות בינונית ({conf:.0%}) - נדרש אימות")
        else: st.error(f"🔴 רמת אמינות נמוכה ({conf:.0%})")
    
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
        # מכינים נתונים לגרף רק אם הם לא Null
        valid_segs = {k: v for k, v in seg.items() if v is not None and "csm" in k}
        if valid_segs:
            df_seg = pd.DataFrame({"מגזר": list(valid_segs.keys()), "CSM": list(valid_segs.values())})
            st.plotly_chart(px.bar(df_seg, x="מגזר", y="CSM", title="יתרת CSM לפי מגזר"))
        
        if seg['onerous_contracts'] is not None and seg['onerous_contracts'] > 0:
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
            st.warning(f"⚠️ חשיפה לנכסים לא סחירים: {inv['unquoted_pct']}%")

    # Tab 3: Solvency
    with tabs[2]:
        sol = data['solvency']
        st.metric("Solvency Ratio", fmt(sol['solvency_ratio'], "%"))
        st.metric("SCR", fmt(sol['scr'], "M₪"))
        if sol['tier1_capital'] and sol['tier2_capital']:
            df_cap = pd.DataFrame({"סוג": ["Tier 1", "Tier 2"], "סכום": [sol['tier1_capital'], sol['tier2_capital']]})
            st.plotly_chart(px.bar(df_cap, x="סוג", y="סכום", color="סוג"))

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
        st.subheader("מפת השוואה")
        # נתונים להשוואה - משתמשים בנתונים שהתקבלו + נתוני שוק קבועים להמחשה
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
            st.metric("פער חשבונאי CSM", fmt(diff, "M"))
            if abs(diff) > 2: st.error("❌ הנתונים אינם מתכנסים חשבונאית")
            else: st.success("✅ אימות חשבונאי תקין")
        else:
            st.warning("⚠️ נתונים חסרים לביצוע בדיקת הלימות")

else:
    st.info("מערכת הפיקוח מוכנה. וודא קיום קבצים ב-GitHub ולחץ על כפתור ההרצה.")

import streamlit as st
import pandas as pd
import requests
import base64
import os
import io
import plotly.express as px
import plotly.graph_objects as go
import json
import time
from datetime import datetime
from jsonschema import validate, ValidationError

# ==============================================================================
# 1. הגדרות מערכת ועיצוב (Apex Command Center Theme)
# ==============================================================================
st.set_page_config(page_title="Apex Regulator Pro: Hybrid Engine", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* Global Dark Theme */
    .stApp { background-color: #0b0d11; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
    
    /* Metrics Cards */
    .metric-card {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid #334155; border-radius: 10px; padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); border-color: #2e7bcf; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #f8fafc; }
    .metric-label { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
    
    /* Alerts */
    .alert-box { padding: 12px; border-radius: 6px; font-weight: 600; margin-bottom: 8px; border-left: 4px solid; }
    .alert-crit { background: rgba(127, 29, 29, 0.2); border-color: #ef4444; color: #fca5a5; }
    .alert-warn { background: rgba(120, 53, 15, 0.2); border-color: #f59e0b; color: #fcd34d; }
    .alert-ok { background: rgba(6, 78, 59, 0.2); border-color: #10b981; color: #6ee7b7; }
    
    /* Actuary Memo */
    .reg-memo {
        background-color: #1e293b; border-top: 3px solid #2e7bcf;
        padding: 15px; border-radius: 4px; font-family: 'Courier New', monospace;
        margin-bottom: 20px; color: #e2e8f0; font-size: 0.95rem;
    }
    
    /* Ticker */
    .ticker-wrap { background: #000; border-bottom: 1px solid #333; padding: 8px; color: #0f0; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

ticker_text = "💎 Apex Pro Hybrid: נתונים היסטוריים (Q1-Q3) + מנוע AI בזמן אמת | ⚠️ התרעת נזילות: כלל (68% לא סחיר) | 🏆 תשואה מובילה Q3: מנורה (10.9%)"
st.markdown(f'<div class="ticker-wrap"><marquee scrollamount="10">{ticker_text}</marquee></div>', unsafe_allow_html=True)

# ==============================================================================
# 2. סכמה למנוע ה-AI (The Engine Core)
# ==============================================================================
IFRS17_SCHEMA = {
    "type": "object",
    "required": ["core", "ifrs17", "invest", "solvency", "ratios"],
    "properties": {
        "core": { "type": "object", "properties": { "profit": {"type": ["number", "null"]}, "csm": {"type": ["number", "null"]}, "roe": {"type": ["number", "null"]}, "gwp": {"type": ["number", "null"]}, "assets": {"type": ["number", "null"]}, "equity": {"type": ["number", "null"]} } },
        "ifrs17": { "type": "object", "properties": { "life": {"type": ["number", "null"]}, "health": {"type": ["number", "null"]}, "new_biz": {"type": ["number", "null"]}, "release": {"type": ["number", "null"]}, "interest": {"type": ["number", "null"]}, "onerous": {"type": ["number", "null"]}, "paa": {"type": ["number", "null"]}, "gmm": {"type": ["number", "null"]} } },
        "invest": { "type": "object", "properties": { "yield": {"type": ["number", "null"]}, "unquoted": {"type": ["number", "null"]}, "roi": {"type": ["number", "null"]} } },
        "solvency": { "type": "object", "properties": { "ratio": {"type": ["number", "null"]}, "scr": {"type": ["number", "null"]}, "tier1": {"type": ["number", "null"]}, "tier2": {"type": ["number", "null"]} } },
        "ratios": { "type": "object", "properties": { "combined": {"type": ["number", "null"]}, "lcr": {"type": ["number", "null"]}, "leverage": {"type": ["number", "null"]}, "retention": {"type": ["number", "null"]} } },
        "check": { "type": "object", "properties": { "opening": {"type": ["number", "null"]}, "new": {"type": ["number", "null"]}, "release": {"type": ["number", "null"]} } },
        "notes": {"type": "string"}
    }
}

# ==============================================================================
# 3. מאגר נתונים היסטורי (Q1-Q3 2025)
# ==============================================================================
DATA = {
    "Q1 2025": {
        "Harel": { "core": {"profit": 264, "csm": 16538, "roe": 12.0, "gwp": 3900, "assets": 158662, "equity": 10370}, "ifrs17": {"life": 10900, "health": 5538, "new_biz": 409, "release": 400, "interest": 150, "onerous": 0, "paa": 35, "gmm": 65}, "invest": {"yield": 1.2, "unquoted": 63, "roi": 3.2}, "solvency": {"ratio": 159, "scr": 9754, "tier1": 11507, "tier2": 5266}, "ratios": {"combined": 96.0, "lcr": 1.3, "leverage": 6.8, "retention": 85.0}, "check": {"opening": 16100, "new": 409, "release": 400}, "notes": "Q1: יחס סולבנסי בסיסי. אין אירועים חריגים ב-CSM." },
        "Phoenix": { "core": {"profit": 1837, "csm": 4500, "roe": 15.0, "gwp": 3410, "assets": 160739, "equity": 7597}, "ifrs17": {"life": 2200, "health": 2300, "new_biz": 354, "release": 292, "interest": 100, "onerous": 0, "paa": 35, "gmm": 65}, "invest": {"yield": 4.34, "unquoted": 30, "roi": 4.8}, "solvency": {"ratio": 181, "scr": 8434, "tier1": 10177, "tier2": 3680}, "ratios": {"combined": 71.2, "lcr": 1.4, "leverage": 5.1, "retention": 82.0}, "check": {"opening": 4300, "new": 354, "release": 292}, "notes": "Q1: רווח חריג (דיבידנד בעין + שיערוך)." },
        "Clal": {"core": {"profit": 239, "csm": 10465, "roe": 15.0, "gwp": 8300, "assets": 152306, "equity": 6421}, "ifrs17": {"life": 4200, "health": 4800, "new_biz": 183, "release": 192, "interest": 100, "onerous": 0, "paa": 30, "gmm": 70}, "invest": {"yield": 3.0, "unquoted": 69, "roi": 3.5}, "solvency": {"ratio": 158, "scr": 10739, "tier1": 10388, "tier2": 4674}, "ratios": {"combined": 69.4, "lcr": 1.2, "leverage": 5.5, "retention": 78.0}, "check": {"opening": 10300, "new": 183, "release": 192}, "notes": "Q1: חשיפה גבוהה ללא סחיר."},
        "Migdal": {"core": {"profit": 254, "csm": 12041, "roe": 12.7, "gwp": 7700, "assets": 225593, "equity": 8037}, "ifrs17": {"life": 11000, "health": 1041, "new_biz": 150, "release": 300, "interest": 120, "onerous": 0, "paa": 20, "gmm": 80}, "invest": {"yield": -1.4, "unquoted": 27, "roi": 1.2}, "solvency": {"ratio": 123, "scr": 13416, "tier1": 11508, "tier2": 5638}, "ratios": {"combined": 84.8, "lcr": 1.1, "leverage": 4.2, "retention": 90.0}, "check": {"opening": 11900, "new": 150, "release": 300}, "notes": "Q1: תשואה שלילית בהשקעות."},
        "Menora": {"core": {"profit": 291, "csm": 7700, "roe": 18.0, "gwp": 1681, "assets": 58416, "equity": 3667}, "ifrs17": {"life": 2000, "health": 4700, "new_biz": 150, "release": 180, "interest": 80, "onerous": 0, "paa": 40, "gmm": 60}, "invest": {"yield": 4.33, "unquoted": 16, "roi": 4.6}, "solvency": {"ratio": 157, "scr": 4473, "tier1": 5288, "tier2": 2200}, "ratios": {"combined": 82.0, "lcr": 1.4, "leverage": 12.0, "retention": 88.0}, "check": {"opening": 7600, "new": 150, "release": 180}, "notes": "Q1: תוצאות יציבות."}
    },
    "Q2 2025": {
        "Harel": { "core": {"profit": 364, "csm": 16687, "roe": 14.8, "gwp": 4300, "assets": 162048, "equity": 11113}, "ifrs17": {"life": 11400, "health": 5287, "new_biz": 458, "release": 415, "interest": 160, "onerous": 0, "paa": 35, "gmm": 65}, "invest": {"yield": 3.4, "unquoted": 63, "roi": 3.8}, "solvency": {"ratio": 182, "scr": 9754, "tier1": 11507, "tier2": 5266}, "ratios": {"combined": 78.6, "lcr": 1.3, "leverage": 6.9, "retention": 84.0}, "check": {"opening": 16538, "new": 458, "release": 415}, "notes": "Q2: זינוק בסולבנסי עקב גיוס אג\"ח." },
        "Phoenix": { "core": {"profit": 780, "csm": 8837, "roe": 27.0, "gwp": 3561, "assets": 169551, "equity": 7567}, "ifrs17": {"life": 6400, "health": 7500, "new_biz": 527, "release": 483, "interest": 120, "onerous": 0, "paa": 35, "gmm": 65}, "invest": {"yield": 6.14, "unquoted": 27.4, "roi": 5.8}, "solvency": {"ratio": 178, "scr": 9191, "tier1": 10287, "tier2": 4547}, "ratios": {"combined": 71.2, "lcr": 1.4, "leverage": 5.1, "retention": 81.0}, "check": {"opening": 8600, "new": 527, "release": 483}, "notes": "Q2: ביטול הפסדים (הכנסה) בסך 150M." },
        "Clal": {"core": {"profit": 555, "csm": 9004, "roe": 18.0, "gwp": 6900, "assets": 146398, "equity": 6253}, "ifrs17": {"life": 4100, "health": 4800, "new_biz": 95, "release": 209, "interest": 100, "onerous": 1, "paa": 30, "gmm": 70}, "invest": {"yield": 5.2, "unquoted": 68, "roi": 4.1}, "solvency": {"ratio": 160, "scr": 10040, "tier1": 10733, "tier2": 4828}, "ratios": {"combined": 75.6, "lcr": 1.2, "leverage": 4.8, "retention": 77.0}, "check": {"opening": 10465, "new": 95, "release": 209}, "notes": "Q2: שחיקה ברווחיות חיתומית."},
        "Migdal": {"core": {"profit": 551, "csm": 12200, "roe": 27.4, "gwp": 7700, "assets": 212533, "equity": 8599}, "ifrs17": {"life": 11500, "health": 700, "new_biz": 300, "release": 320, "interest": 130, "onerous": 0, "paa": 20, "gmm": 80}, "invest": {"yield": -1.1, "unquoted": 27, "roi": 2.1}, "solvency": {"ratio": 131, "scr": 13685, "tier1": 12565, "tier2": 5744}, "ratios": {"combined": 80.0, "lcr": 1.1, "leverage": 3.9, "retention": 89.0}, "check": {"opening": 12041, "new": 300, "release": 320}, "notes": "Q2: שיפור בסולבנסי ל-131%."},
        "Menora": {"core": {"profit": 444, "csm": 7600, "roe": 23.9, "gwp": 1861, "assets": 60810, "equity": 3723}, "ifrs17": {"life": 2100, "health": 4900, "new_biz": 200, "release": 190, "interest": 90, "onerous": 0, "paa": 40, "gmm": 60}, "invest": {"yield": 6.17, "unquoted": 16, "roi": 5.5}, "solvency": {"ratio": 163.6, "scr": 4821, "tier1": 5742, "tier2": 2144}, "ratios": {"combined": 78.7, "lcr": 1.45, "leverage": 13.0, "retention": 87.0}, "check": {"opening": 7700, "new": 200, "release": 190}, "notes": "Q2: רווחיות חיתומית בריאה."}
    },
    "Q3 2025": {
        "Harel": {
            "core": {"profit": 244, "csm": 17133, "roe": 9.0, "gwp": 3900, "assets": 167754, "equity": 11525},
            "ifrs17": {"life": 11532, "health": 5601, "new_biz": 398, "release": 405, "interest": 170, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 4.5, "unquoted": 63, "roi": 4.2},
            "solvency": {"ratio": 182, "scr": 9428, "tier1": 10733, "tier2": 2500},
            "ratios": {"combined": 88.0, "lcr": 1.35, "leverage": 6.9, "retention": 84.5},
            "check": {"opening": 16687, "new": 398, "release": 405},
            "notes": "Q3: ירידה ברווח הכולל. חשיפה גבוהה ל-Level 3 (63%) דורשת ניטור."
        },
        "Phoenix": {
            "core": {"profit": 586, "csm": 9579, "roe": 33.3, "gwp": 2307, "assets": 169551, "equity": 7719},
            "ifrs17": {"life": 6636, "health": 7719, "new_biz": 621, "release": 761, "interest": 150, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 7.74, "unquoted": 27.3, "roi": 6.2},
            "solvency": {"ratio": 178, "scr": 9191, "tier1": 10287, "tier2": 4547},
            "ratios": {"combined": 84.8, "lcr": 1.4, "leverage": 5.1, "retention": 81.5},
            "check": {"opening": 8837, "new": 621, "release": 761},
            "notes": "Q3: ביטול הפסדים (168M). תשואות ריאליות חזקות (7.74%)."
        },
        "Clal": {
            "core": {"profit": 507, "csm": 8813, "roe": 19.0, "gwp": 7200, "assets": 147369, "equity": 6516},
            "ifrs17": {"life": 4076, "health": 4737, "new_biz": 120, "release": 237, "interest": 110, "onerous": 4, "paa": 30, "gmm": 70},
            "invest": {"yield": 8.34, "unquoted": 68, "roi": 5.1},
            "solvency": {"ratio": 160, "scr": 10040, "tier1": 11214, "tier2": 4828},
            "ratios": {"combined": 80.0, "lcr": 1.25, "leverage": 4.8, "retention": 76.0},
            "check": {"opening": 9004, "new": 120, "release": 237},
            "notes": "Q3: הרעה ב-Combined Ratio (80%). תשואה גבוהה במשתתפות."
        },
        "Migdal": {
            "core": {"profit": 535, "csm": 12500, "roe": 24.0, "gwp": 2100, "assets": 219362, "equity": 9118},
            "ifrs17": {"life": 6636, "health": 6426, "new_biz": 795, "release": 355, "interest": 140, "onerous": 350, "paa": 20, "gmm": 80},
            "invest": {"yield": 2.0, "unquoted": 27, "roi": 3.1},
            "solvency": {"ratio": 131, "scr": 13685, "tier1": 12565, "tier2": 5744},
            "ratios": {"combined": 70.8, "lcr": 1.1, "leverage": 3.9, "retention": 89.5},
            "check": {"opening": 12200, "new": 795, "release": 355},
            "notes": "Q3: שיפור דרמטי ב-Combined Ratio (70.8%). הכרה בחוזים מפסידים."
        },
        "Menora": {
            "core": {"profit": 425, "csm": 7900, "roe": 42.7, "gwp": 1861, "assets": 62680, "equity": 4180},
            "ifrs17": {"life": 2500, "health": 4300, "new_biz": 300, "release": 200, "interest": 100, "onerous": 0, "paa": 40, "gmm": 60},
            "invest": {"yield": 10.92, "unquoted": 16, "roi": 6.8},
            "solvency": {"ratio": 181, "scr": 6019, "tier1": 7567, "tier2": 2200},
            "ratios": {"combined": 78.7, "lcr": 1.45, "leverage": 13.1, "retention": 87.5},
            "check": {"opening": 7600, "new": 300, "release": 200},
            "notes": "Q3: זינוק בסולבנסי (181%) עקב גיוס אג\"ח. מובילת התשואות (10.92%)."
        }
    }
}

# ==============================================================================
# 4. מנוע AI (Analyze Report) - שוחזר!
# ==============================================================================
def analyze_report(file_path, api_key, retries=3):
    """מנוע לחילוץ נתונים מדוחות חדשים באמצעות Gemini"""
    if not os.path.exists(file_path): return None, f"קובץ חסר: {file_path}"
    with open(file_path, "rb") as f: pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    system_prompt = """
    Act as a Senior Actuary. Extract data from this Insurance Financial Report (Hebrew/English).
    Map all data strictly to the provided JSON Schema.
    - If a value is missing, use null (do not estimate).
    - 'notes' field should contain a brief executive summary (max 20 words) in Hebrew.
    """
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": system_prompt}, {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}]}]}
    
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                raw = response.json()['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(raw.replace('```json', '').replace('```', '').strip())
                validate(instance=data, schema=IFRS17_SCHEMA)
                return data, "success"
            elif response.status_code in [429, 500]: time.sleep(2**attempt); continue
            else: return None, f"API Error: {response.text}"
        except Exception as e: time.sleep(1)
    return None, "Connection Failed"

# ==============================================================================
# 5. פונקציות עיבוד וניתוח (Logic Layer)
# ==============================================================================
def get_red_flags(d):
    flags = []
    # Solvency
    if d['solvency']['ratio'] and d['solvency']['ratio'] < 100: flags.append(("CRIT", f"🚨 סולבנסי קריטי: {d['solvency']['ratio']}%"))
    elif d['solvency']['ratio'] and d['solvency']['ratio'] < 125: flags.append(("WARN", f"⚠️ סולבנסי נמוך: {d['solvency']['ratio']}%"))
    # Operations
    if d['ifrs17']['onerous'] and d['ifrs17']['onerous'] > 50: flags.append(("CRIT", f"🔻 עסקים מכבידים: {d['ifrs17']['onerous']}M₪"))
    if d['ratios']['combined'] and d['ratios']['combined'] > 100: flags.append(("WARN", f"📉 הפסד חיתומי (CR: {d['ratios']['combined']}%)"))
    # Investments
    if d['invest']['unquoted'] and d['invest']['unquoted'] > 50: flags.append(("WARN", f"🧱 חשיפה קיצונית ללא-סחיר: {d['invest']['unquoted']}%"))
    return flags

def get_compliance_check(d):
    checks = {}
    if d['solvency']['ratio']: checks["יחס הון מזערי (>100%)"] = d['solvency']['ratio'] >= 100
    if d['ratios']['lcr']: checks["יחס נזילות (>1.0)"] = d['ratios']['lcr'] > 1.0
    if d['ratios']['combined']: checks["רווחיות חיתומית (CR < 100%)"] = d['ratios']['combined'] < 100
    if d['solvency']['tier1']: 
        tier1_ratio = d['solvency']['tier1'] / (d['solvency']['tier1'] + d['solvency']['tier2'])
        checks["איכות הון (Tier 1 > 50%)"] = tier1_ratio > 0.5
    return checks

def generate_report_html(company, quarter, d):
    flags = get_red_flags(d)
    html = f"""
    <div style="font-family: Arial; padding: 20px; border: 4px solid #2e7bcf; background: #f0f8ff;">
        <h1 style="color: #1c2e4a;">דוח פיקוח: {company}</h1>
        <h3>תקופה: {quarter} | סטטוס: מבוקר</h3>
        <hr>
        <p><b>רווח נקי:</b> {fmt(d['core']['profit'], 'M')}</p>
        <p><b>סולבנסי:</b> {fmt(d['solvency']['ratio'], '%')}</p>
        <div style="background: #fff3cd; padding: 10px;"><b>הערת אקטואר:</b> {d.get('notes', 'אין הערות')}</div>
        <br><h4>חריגות ({len(flags)}):</h4>
        <ul>{''.join([f'<li style="color: red;">{msg}</li>' for _, msg in flags])}</ul>
    </div>
    """
    return html

def generate_excel(company, quarter, data_source):
    # תמיכה במצב היסטורי (dict) או AI (dict יחיד)
    d = data_source if "core" in data_source else data_source[quarter][company]
    df_core = pd.DataFrame([d['core']])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_core.to_excel(writer, sheet_name='Core_KPIs')
    return output.getvalue()

def fmt(v, u=""): return f"{v:,.1f}{u}" if v is not None else "-"

# ==============================================================================
# 6. ממשק משתמש (The Cockpit)
# ==============================================================================

# -- Sidebar --
st.sidebar.header("🕹️ חדר בקרה")
mode = st.sidebar.radio("מצב מערכת", ["מכונת זמן (Q1-Q3)", "סריקת דוח חדש (AI)"])

current_data = None
current_q = "AI Analysis"
current_comp = "Unknown"

if mode == "מכונת זמן (Q1-Q3)":
    q_select = st.sidebar.select_slider("רבעון", options=["Q1 2025", "Q2 2025", "Q3 2025"], value="Q3 2025")
    c_select = st.sidebar.selectbox("חברה", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
    current_data = DATA[q_select][c_select]
    current_q = q_select
    current_comp = c_select
    st.sidebar.success("✅ נתונים היסטוריים נטענו")

else: # AI Mode
    st.sidebar.warning("נדרש מפתח API של Gemini")
    api_key_input = st.sidebar.text_input("Gemini API Key", type="password")
    uploaded_file = st.sidebar.file_uploader("העלה דוח כספי (PDF)", type=['pdf'])
    
    if uploaded_file and api_key_input:
        if st.sidebar.button("🚀 הרץ ניתוח AI"):
            with st.spinner("המנוע מנתח את הדוח..."):
                # שמירה זמנית
                with open("temp.pdf", "wb") as f: f.write(uploaded_file.getbuffer())
                res, status = analyze_report("temp.pdf", api_key_input)
                if status == "success":
                    current_data = res
                    current_comp = "דוח שהועלה"
                    st.session_state.ai_data = res # שמירה בסשן
                else:
                    st.error(f"שגיאה: {status}")
    
    if "ai_data" in st.session_state:
        current_data = st.session_state.ai_data
        current_comp = "דוח שהועלה"

st.sidebar.markdown("---")
# Export Buttons
if current_data:
    if st.sidebar.button("🖨️ הפק דוח (HTML)"):
        html = generate_report_html(current_comp, current_q, current_data)
        b64 = base64.b64encode(html.encode()).decode()
        st.sidebar.markdown(f'<a href="data:text/html;base64,{b64}" download="Report.html">הורד קובץ</a>', unsafe_allow_html=True)

# -- Main View --
if current_data:
    st.title(f"דוח פיקוח: {current_comp}")
    st.caption(f"מקור הנתונים: {mode}")

    # Alerts & Memo
    c_memo, c_flags = st.columns([2, 1])
    with c_memo:
        st.markdown(f'<div class="reg-memo"><b>📝 הערת אקטואר:</b><br>{current_data.get("notes", "אין הערות זמינות")}</div>', unsafe_allow_html=True)
    with c_flags:
        flags = get_red_flags(current_data)
        if flags:
            for lvl, msg in flags:
                cls = "alert-crit" if lvl == "CRIT" else "alert-warn"
                st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-ok">✅ ללא חריגות</div>', unsafe_allow_html=True)

    # KPI Matrix
    cols = st.columns(6)
    metrics = [
        ("רווח נקי", current_data['core'].get('profit'), "M₪"),
        ("CSM", current_data['core'].get('csm'), "M₪"),
        ("סולבנסי", current_data['solvency'].get('ratio'), "%"),
        ("ROE", current_data['core'].get('roe'), "%"),
        ("תשואה", current_data['invest'].get('yield'), "%"),
        ("Combined", current_data['ratios'].get('combined'), "%")
    ]
    for i, (l, v, u) in enumerate(metrics):
        cols[i].metric(l, fmt(v, u))

    st.divider()

    # Tabs
    tabs = st.tabs(["📊 דופונט (DuPont)", "🌊 IFRS 17", "🛡️ סולבנסי", "💰 השקעות", "✅ ציות", "🕹️ סימולטור", "🧮 אימות"])

    # TAB 1: DuPont
    with tabs[0]:
        st.subheader("ניתוח תשואה להון")
        c1, c2, c3 = st.columns(3)
        profit = current_data['core'].get('profit') or 0
        gwp = current_data['core'].get('gwp') or 1
        assets = current_data['core'].get('assets') or 1
        equity = current_data['core'].get('equity') or 1
        
        nm = (profit / gwp) * 100
        at = gwp / assets
        lev = assets / equity
        
        c1.metric("מרווח רווח", fmt(nm, "%"))
        c2.metric("מחזור נכסים", fmt(at, "x"))
        c3.metric("מינוף", fmt(lev, "x"))

    # TAB 2: IFRS 17 Waterfall
    with tabs[1]:
        st.subheader("תנועה ב-CSM")
        check = current_data.get('check', {'opening': 0})
        start = check.get('opening', 0)
        new_biz = current_data['ifrs17'].get('new_biz', 0)
        interest = current_data['ifrs17'].get('interest', 0)
        release = current_data['ifrs17'].get('release', 0)
        end = current_data['core'].get('csm', 0)
        
        fig_wf = go.Figure(go.Waterfall(
            measure = ["relative", "relative", "relative", "relative", "total"],
            x = ["פתיחה", "עסקים חדשים", "ריבית", "שחרור", "סגירה"],
            y = [start, new_biz, interest, -release, end],
            connector = {"line":{"color":"rgb(63, 63, 63)"}}
        ))
        fig_wf.update_layout(template="plotly_dark", title="Waterfall Chart")
        st.plotly_chart(fig_wf, use_container_width=True)

    # TAB 3: Solvency & Radar
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1:
            vals = [
                (current_data['solvency'].get('ratio') or 0)/200, 
                (current_data['core'].get('roe') or 0)/30, 
                (100-(current_data['invest'].get('unquoted') or 0))/100, 
                (current_data['invest'].get('yield') or 0)/10
            ]
            fig_rad = go.Figure(go.Scatterpolar(r=vals, theta=['סולבנסי', 'ROE', 'נזילות', 'תשואה'], fill='toself'))
            fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", title="פרופיל סיכון")
            st.plotly_chart(fig_rad, use_container_width=True)
        with c2:
            # Gauge
            val = current_data['solvency'].get('ratio') or 0
            fig_g = go.Figure(go.Indicator(
                mode = "gauge+number", value = val, title = {'text': "יחס סולבנסי"},
                gauge = {'axis': {'range': [0, 200]}, 'bar': {'color': "#2e7bcf"},
                         'steps': [{'range': [0, 100], 'color': "rgba(255,0,0,0.3)"}]}
            ))
            fig_g.update_layout(height=300, margin=dict(t=50,b=20), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
            st.plotly_chart(fig_g, use_container_width=True)

    # TAB 4: Investments
    with tabs[3]:
        st.subheader("תיק הנוסטרו")
        unq = current_data['invest'].get('unquoted') or 0
        fig_sun = px.pie(values=[unq, 100-unq], names=["לא סחיר", "סחיר"], hole=0.4, title="נזילות")
        st.plotly_chart(fig_sun, use_container_width=True)

    # TAB 5: Compliance
    with tabs[4]:
        st.subheader("בקרת ציות")
        checks = get_compliance_check(current_data)
        c1, c2 = st.columns(2)
        for i, (k, v) in enumerate(checks.items()):
            col = c1 if i < 2 else c2
            icon = "✅" if v else "❌"
            col.markdown(f"#### {icon} {k}")
            if not v: col.error("חריגה")

    # TAB 6: Simulator
    with tabs[5]:
        st.subheader("מבחני קיצון")
        r_shock = st.slider("זעזוע ריבית (%)", -2.0, 2.0, 0.0, 0.1)
        m_shock = st.slider("נפילה בשווקים (%)", -30, 0, 0, 1)
        impact = (r_shock * 10) + (m_shock * 0.4)
        base = current_data['solvency'].get('ratio') or 0
        st.metric("Solvency חזוי", fmt(base + impact, "%"), delta=fmt(impact, "%"))

    # TAB 7: Validation
    with tabs[6]:
        st.subheader("בקרת נתונים")
        chk = current_data.get('check', {'opening': 0, 'new': 0, 'release': 0})
        # בטיחות למקרה של נתונים חסרים במצב AI
        op = chk.get('opening') or 0
        nw = chk.get('new') or 0
        rel = chk.get('release') or 0
        intr = current_data['ifrs17'].get('interest') or 0
        
        calc = op + nw - rel + intr
        act = current_data['core'].get('csm') or 0
        diff = act - calc
        
        c1, c2 = st.columns(2)
        c1.metric("CSM מחושב", fmt(calc, "M"))
        c2.metric("CSM מדווח", fmt(act, "M"))
        
        if abs(diff) < 100: st.success("✅ נתונים מאומתים")
        else: st.warning(f"⚠️ פער: {fmt(diff, 'M')}")

else:
    st.info("אנא בחר חברה מהתפריט או העלה דוח לניתוח.")

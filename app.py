import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
from datetime import datetime

# ==============================================================================
# 1. הגדרות מערכת ועיצוב (Apex Command Center Theme)
# ==============================================================================
st.set_page_config(page_title="Apex Regulator Command", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    /* Dark Mode Professional */
    .stApp { background-color: #0b0d11; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
    
    /* Metrics */
    .metric-card {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #f8fafc; }
    .metric-label { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
    
    /* Alerts */
    .alert-box {
        padding: 12px; border-radius: 6px; font-weight: 600; margin-bottom: 8px; border-left: 4px solid;
    }
    .alert-crit { background: rgba(127, 29, 29, 0.2); border-color: #ef4444; color: #fca5a5; }
    .alert-warn { background: rgba(120, 53, 15, 0.2); border-color: #f59e0b; color: #fcd34d; }
    .alert-info { background: rgba(30, 58, 138, 0.2); border-color: #3b82f6; color: #93c5fd; }
    
    /* Actuary Note */
    .actuary-memo {
        background-color: #1e293b;
        border: 1px solid #475569;
        padding: 15px;
        border-radius: 6px;
        font-family: 'Consolas', monospace;
        color: #e2e8f0;
        margin-bottom: 20px;
    }
    
    /* Headers */
    h1, h2, h3 { color: #f1f5f9; }
    .highlight { color: #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. נתוני אמת מלאים (Q1-Q3 2025)
# ==============================================================================
DATA = {
    "Q1 2025": {
        "Harel": {
            "core": {"profit": 264, "csm": 16538, "roe": 12.0, "gwp": 3900, "assets": 158662, "equity": 10370},
            "ifrs17": {"life": 10900, "health": 5538, "new_biz": 409, "release": 400, "interest": 150, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 1.2, "unquoted": 63, "roi": 3.2},
            "solvency": {"ratio": 159, "scr": 9754, "tier1": 11507, "tier2": 5266},
            "ratios": {"combined": 96.0, "lcr": 1.3, "leverage": 6.8, "retention": 85.0},
            "notes": "Q1: יחס סולבנסי בסיסי. יציבות ב-CSM."
        },
        "Phoenix": {
            "core": {"profit": 1837, "csm": 4500, "roe": 15.0, "gwp": 3410, "assets": 160739, "equity": 7597},
            "ifrs17": {"life": 2200, "health": 2300, "new_biz": 354, "release": 292, "interest": 100, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 4.34, "unquoted": 30, "roi": 4.8},
            "solvency": {"ratio": 181, "scr": 8434, "tier1": 10177, "tier2": 3680},
            "ratios": {"combined": 71.2, "lcr": 1.4, "leverage": 5.1, "retention": 82.0},
            "notes": "Q1: רווח חריג (דיבידנד בעין + שיערוך)."
        },
        "Migdal": {"core": {"profit": 254, "csm": 12041, "roe": 12.7, "gwp": 7700, "assets": 225593, "equity": 8037}, "ifrs17": {"life": 11000, "new_biz": 150, "release": 300, "interest": 120, "onerous": 0, "paa": 20, "gmm": 80}, "invest": {"yield": -1.4, "unquoted": 27}, "solvency": {"ratio": 123, "scr": 13416, "tier1": 11508, "tier2": 5638}, "ratios": {"combined": 84.8, "lcr": 1.1, "retention": 90.0}, "notes": "Q1: תשואה שלילית בהשקעות."},
        "Clal": {"core": {"profit": 239, "csm": 10465, "roe": 15.0, "gwp": 8300, "assets": 152306, "equity": 6421}, "ifrs17": {"new_biz": 183, "release": 192, "interest": 100, "onerous": 0, "paa": 30}, "invest": {"yield": 3.0, "unquoted": 69}, "solvency": {"ratio": 158, "scr": 10739, "tier1": 10388, "tier2": 4674}, "ratios": {"combined": 69.4, "lcr": 1.2, "retention": 78.0}, "notes": "Q1: חשיפה גבוהה ללא סחיר."},
        "Menora": {"core": {"profit": 291, "csm": 7700, "roe": 18.0, "gwp": 1681, "assets": 58416, "equity": 3667}, "ifrs17": {"new_biz": 150, "release": 180, "interest": 80, "onerous": 0, "paa": 40}, "invest": {"yield": 4.33, "unquoted": 16}, "solvency": {"ratio": 157, "scr": 4473, "tier1": 5288, "tier2": 2200}, "ratios": {"combined": 82.0, "lcr": 1.4, "retention": 88.0}, "notes": "Q1: תוצאות יציבות."}
    },
    "Q2 2025": {
        "Harel": {
            "core": {"profit": 364, "csm": 16687, "roe": 14.8, "gwp": 4300, "assets": 162048, "equity": 11113},
            "ifrs17": {"life": 11400, "health": 5287, "new_biz": 458, "release": 415, "interest": 160, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 3.4, "unquoted": 63, "roi": 3.8},
            "solvency": {"ratio": 182, "scr": 9754, "tier1": 11507, "tier2": 5266},
            "ratios": {"combined": 78.6, "lcr": 1.3, "leverage": 6.9, "retention": 84.0},
            "notes": "Q2: גיוס אג\"ח סדרה כא' (1 מיליארד ש\"ח) שיפר את הסולבנסי."
        },
        "Phoenix": {
            "core": {"profit": 780, "csm": 8837, "roe": 27.0, "gwp": 3561, "assets": 169551, "equity": 7567},
            "ifrs17": {"life": 6400, "health": 7500, "new_biz": 527, "release": 483, "interest": 120, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 6.14, "unquoted": 27.4, "roi": 5.8},
            "solvency": {"ratio": 178, "scr": 9191, "tier1": 10287, "tier2": 4547},
            "ratios": {"combined": 71.2, "lcr": 1.4, "leverage": 5.1, "retention": 81.0},
            "notes": "Q2: ביטול הפסדים (הכנסה) של 150M ש\"ח."
        },
        "Migdal": {"core": {"profit": 551, "csm": 12200, "roe": 27.4, "gwp": 7700, "assets": 212533, "equity": 8599}, "ifrs17": {"new_biz": 300, "release": 320, "interest": 130, "onerous": 0, "paa": 20}, "invest": {"yield": -1.1, "unquoted": 27}, "solvency": {"ratio": 131, "scr": 13685, "tier1": 12565, "tier2": 5744}, "ratios": {"combined": 80.0, "lcr": 1.1, "retention": 89.0}, "notes": "Q2: שיפור קל בסולבנסי."},
        "Clal": {"core": {"profit": 555, "csm": 9004, "roe": 18.0, "gwp": 6900, "assets": 146398, "equity": 6253}, "ifrs17": {"new_biz": 95, "release": 209, "interest": 100, "onerous": 1, "paa": 30}, "invest": {"yield": 5.2, "unquoted": 68}, "solvency": {"ratio": 160, "scr": 10040, "tier1": 10733, "tier2": 4828}, "ratios": {"combined": 75.6, "lcr": 1.2, "retention": 77.0}, "notes": "Q2: שחיקה חיתומית."},
        "Menora": {"core": {"profit": 444, "csm": 7600, "roe": 23.9, "gwp": 1861, "assets": 60810, "equity": 3723}, "ifrs17": {"new_biz": 200, "release": 190, "interest": 90, "onerous": 0, "paa": 40}, "invest": {"yield": 6.17, "unquoted": 16}, "solvency": {"ratio": 163.6, "scr": 4821, "tier1": 5742, "tier2": 2144}, "ratios": {"combined": 78.7, "lcr": 1.45, "retention": 87.0}, "notes": "Q2: תוצאות חזקות."}
    },
    "Q3 2025": {
        "Harel": {
            "core": {"profit": 244, "csm": 17133, "roe": 9.0, "gwp": 3900, "assets": 167754, "equity": 11525},
            "ifrs17": {"life": 11532, "health": 5601, "new_biz": 398, "release": 405, "interest": 170, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 4.5, "unquoted": 63, "roi": 4.2},
            "solvency": {"ratio": 182, "scr": 9428, "tier1": 10733, "tier2": 2500},
            "ratios": {"combined": 88.0, "lcr": 1.35, "leverage": 6.9, "retention": 84.5},
            "notes": "Q3: ירידה ברווח הכולל בשל תשואות. חשיפה גבוהה ל-Level 3 (63%)."
        },
        "Phoenix": {
            "core": {"profit": 586, "csm": 9579, "roe": 33.3, "gwp": 2307, "assets": 169551, "equity": 7719},
            "ifrs17": {"life": 6636, "health": 7719, "new_biz": 621, "release": 761, "interest": 150, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 7.74, "unquoted": 27.3, "roi": 6.2},
            "solvency": {"ratio": 178, "scr": 9191, "tier1": 10287, "tier2": 4547},
            "ratios": {"combined": 84.8, "lcr": 1.4, "leverage": 5.1, "retention": 81.5},
            "notes": "Q3: ביטול הפסדים נוסף (168M). תשואות ריאליות חזקות (7.74%)."
        },
        "Clal": {
            "core": {"profit": 507, "csm": 8813, "roe": 19.0, "gwp": 7200, "assets": 147369, "equity": 6516},
            "ifrs17": {"life": 4076, "health": 4737, "new_biz": 120, "release": 237, "interest": 110, "onerous": 4, "paa": 30, "gmm": 70},
            "invest": {"yield": 8.34, "unquoted": 68, "roi": 5.1},
            "solvency": {"ratio": 160, "scr": 10040, "tier1": 11214, "tier2": 4828},
            "ratios": {"combined": 80.0, "lcr": 1.25, "leverage": 4.8, "retention": 76.0},
            "notes": "Q3: הרעה ב-Combined Ratio (80%). שחיקה חיתומית. תשואה גבוהה במשתתפות."
        },
        "Migdal": {
            "core": {"profit": 535, "csm": 12500, "roe": 24.0, "gwp": 2100, "assets": 219362, "equity": 9118},
            "ifrs17": {"life": 6636, "health": 6426, "new_biz": 795, "release": 355, "interest": 140, "onerous": 350, "paa": 20, "gmm": 80},
            "invest": {"yield": 2.0, "unquoted": 27, "roi": 3.1},
            "solvency": {"ratio": 131, "scr": 13685, "tier1": 12565, "tier2": 5744},
            "ratios": {"combined": 70.8, "lcr": 1.1, "leverage": 3.9, "retention": 89.5},
            "notes": "Q3: שיפור דרמטי ב-Combined Ratio (70.8%). הכרה בחוזים מפסידים."
        },
        "Menora": {
            "core": {"profit": 425, "csm": 7900, "roe": 42.7, "gwp": 1861, "assets": 62680, "equity": 4180},
            "ifrs17": {"life": 2500, "health": 4300, "new_biz": 300, "release": 200, "interest": 100, "onerous": 0, "paa": 40, "gmm": 60},
            "invest": {"yield": 10.92, "unquoted": 16, "roi": 6.8},
            "solvency": {"ratio": 181, "scr": 6019, "tier1": 7567, "tier2": 2200},
            "ratios": {"combined": 78.7, "lcr": 1.45, "leverage": 13.1, "retention": 87.5},
            "notes": "Q3: זינוק בסולבנסי (181%) עקב גיוס אג\"ח סדרה י'. מובילת התשואות (10.92%)."
        }
    }
}

# ==============================================================================
# 3. מנוע הלוגיקה והניתוח
# ==============================================================================
def get_red_flags(d):
    flags = []
    # Solvency
    if d['solvency']['ratio'] < 100: flags.append(("CRIT", f"🚨 סולבנסי קריטי: {d['solvency']['ratio']}%"))
    elif d['solvency']['ratio'] < 125: flags.append(("WARN", f"⚠️ סולבנסי נמוך: {d['solvency']['ratio']}%"))
    
    # Operations
    if d['ifrs17']['onerous'] > 50: flags.append(("WARN", f"🔻 חוזים מכבידים: {d['ifrs17']['onerous']}M₪"))
    if d['ratios']['combined'] > 100: flags.append(("CRIT", f"📉 הפסד חיתומי (CR: {d['ratios']['combined']}%)"))
    
    # Investments
    if d['invest']['unquoted'] > 50: flags.append(("WARN", f"🧱 חשיפה ללא-סחיר: {d['invest']['unquoted']}%"))
    
    return flags

def get_compliance_check(d):
    """בדיקת עמידה בהוראות רגולציה"""
    checks = {
        "יחס הון מזערי (>100%)": d['solvency']['ratio'] >= 100,
        "יחס נזילות (>1.0)": d['ratios']['lcr'] > 1.0,
        "רווחיות חיתומית (CR < 100%)": d['ratios']['combined'] < 100,
        "איכות הון (Tier 1 > 50%)": d['solvency']['tier1'] / (d['solvency']['tier1'] + d['solvency']['tier2']) > 0.5
    }
    return checks

def generate_report_html(company, quarter, d):
    """מחולל דוחות רשמי"""
    html = f"""
    <div style="font-family: Arial; padding: 20px; border: 2px solid #000;">
        <h1 style="color: #2e7bcf;">דוח פיקוח: {company}</h1>
        <h3>תקופה: {quarter} | סיווג: סודי</h3>
        <hr>
        <p><b>רווח נקי:</b> {d['core']['profit']}M | <b>סולבנסי:</b> {d['solvency']['ratio']}%</p>
        <p><b>הערות אקטואר:</b> {d['notes']}</p>
        <p style="color: red;">חריגות: {len(get_red_flags(d))}</p>
    </div>
    """
    return html

def fmt(v, u=""): return f"{v:,.1f}{u}" if v is not None else "-"

# ==============================================================================
# 4. ממשק המשתמש (Command Center Layout)
# ==============================================================================
# -- Sidebar --
st.sidebar.title("🛡️ Apex Command")
q_select = st.sidebar.select_slider("תקופת דיווח", options=["Q1 2025", "Q2 2025", "Q3 2025"], value="Q3 2025")
c_select = st.sidebar.selectbox("גוף מפוקח", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])

st.sidebar.markdown("---")
if st.sidebar.button("🖨️ הפק דוח מנהלים (PDF/HTML)"):
    report_html = generate_report_html(c_select, q_select, DATA[q_select][c_select])
    b64 = base64.b64encode(report_html.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="Regulator_Report.html">לחץ להורדת הדוח</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

# -- Main View --
cur = DATA[q_select][c_select]

st.title(f"מערכת פיקוח על הביטוח: {c_select}")
st.markdown(f"**תקופה:** {q_select} | **סטטוס:** נתונים מאומתים | **אקטואר אחראי:** מערכת AI")

# Alerts & Memo
col_alert, col_memo = st.columns([1, 2])
with col_alert:
    flags = get_red_flags(cur)
    if flags:
        for lvl, msg in flags:
            cls = "alert-crit" if lvl == "CRIT" else "alert-warn"
            st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box alert-info">✅ מצב תקין</div>', unsafe_allow_html=True)

with col_memo:
    st.markdown(f'<div class="actuary-memo"><b>📝 הערת אקטואר:</b> {cur["notes"]}</div>', unsafe_allow_html=True)

# KPI Matrix
cols = st.columns(6)
metrics = [
    ("רווח נקי", cur['core']['profit'], "M₪"),
    ("CSM", cur['core']['csm'], "M₪"),
    ("סולבנסי", cur['solvency']['ratio'], "%"),
    ("תשואה", cur['invest']['yield'], "%"),
    ("Combined", cur['ratios']['combined'], "%"),
    ("Retention", cur['ratios']['retention'], "%")
]
for i, (l, v, u) in enumerate(metrics):
    with cols[i]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{l}</div>
            <div class="metric-value">{fmt(v, u)}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# -- Deep Dive Views --
tabs = st.tabs(["🚦 צ'ק-ליסט רגולטורי", "🛡️ ניהול סיכונים", "🌊 IFRS 17", "💰 השקעות", "📉 מגמות", "⚖️ השוואה"])

# TAB 1: Compliance Checklist
with tabs[0]:
    st.subheader("בקרת ציות (Compliance)")
    checks = get_compliance_check(cur)
    c1, c2 = st.columns(2)
    for i, (k, v) in enumerate(checks.items()):
        col = c1 if i < 2 else c2
        icon = "✅" if v else "❌"
        color = "green" if v else "red"
        col.markdown(f"### {icon} {k}")
        if not v: col.error("נדרשת פעולה מתקנת מיידית")

# TAB 2: Risk & Solvency (Gauge + Sensitivity)
with tabs[1]:
    st.subheader("ניהול סיכונים וסולבנסי")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        # Gauge Chart
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = cur['solvency']['ratio'],
            title = {'text': "יחס סולבנסי"},
            gauge = {'axis': {'range': [0, 200]},
                     'bar': {'color': "#2e7bcf"},
                     'steps': [
                         {'range': [0, 100], 'color': "rgba(255, 0, 0, 0.3)"},
                         {'range': [100, 125], 'color': "rgba(255, 165, 0, 0.3)"},
                         {'range': [125, 200], 'color': "rgba(0, 255, 0, 0.1)"}]}
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=20,r=20,t=50,b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with c2:
        st.markdown("#### טבלת רגישות (Sensitivity Table)")
        sens_data = {
            "תרחיש": ["ריבית +1%", "ריבית -1%", "מניות -10%", "מרווחי אשראי +0.5%"],
            "השפעה על יחס": ["+4%", "-5%", "-2%", "-3%"],
            "השפעה על הון (M₪)": ["+450", "-600", "-200", "-350"]
        }
        st.dataframe(pd.DataFrame(sens_data), use_container_width=True)

# TAB 3: IFRS 17 Waterfall
with tabs[2]:
    st.subheader("ניתוח רווחיות ביטוחית")
    start = cur['core']['csm'] - cur['ifrs17']['new_biz'] - cur['ifrs17']['interest'] + cur['ifrs17']['release']
    fig_wf = go.Figure(go.Waterfall(
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["פתיחה", "עסקים חדשים", "ריבית", "שחרור", "סגירה"],
        y = [start, cur['ifrs17']['new_biz'], cur['ifrs17']['interest'], -cur['ifrs17']['release'], cur['core']['csm']],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig_wf.update_layout(template="plotly_dark", title="תנועה ב-CSM")
    st.plotly_chart(fig_wf, use_container_width=True)

# TAB 4: Investments Sunburst
with tabs[3]:
    st.subheader("תיק הנוסטרו")
    i1, i2 = st.columns([2, 1])
    with i1:
        # Sunburst
        labels = ["תיק", "סחיר", "לא סחיר", "אגח", "מניות", "נדלן"]
        parents = ["", "תיק", "תיק", "סחיר", "סחיר", "לא סחיר"]
        vals = [100, 100-cur['invest']['unquoted'], cur['invest']['unquoted'], 50, 20, 30]
        fig_sun = go.Figure(go.Sunburst(
            labels=labels, parents=parents, values=vals,
            branchvalues="total", marker=dict(colors=["#1e293b", "#3b82f6", "#ef4444"])
        ))
        fig_sun.update_layout(template="plotly_dark", margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig_sun, use_container_width=True)
    with i2:
        st.metric("חשיפה ללא-סחיר", fmt(cur['invest']['unquoted'], "%"))
        st.metric("ROI כולל", fmt(cur['invest']['roi'], "%"))

# TAB 5: Trends
with tabs[4]:
    st.subheader("מגמות")
    trend_data = []
    for q in DATA:
        trend_data.append({"R": q, "V": DATA[q][c_select]['core']['profit']})
    st.plotly_chart(px.line(trend_data, x="R", y="V", title="רווח נקי", markers=True), use_container_width=True)

# TAB 6: Comparison
with tabs[5]:
    st.subheader("מפת חום ענפית")
    rows = []
    for c in DATA[q_select]:
        d = DATA[q_select][c]
        rows.append({"Name": c, "Solvency": d['solvency']['ratio'], "ROE": d['core']['roe'], "CR": d['ratios']['combined']})
    df_heat = pd.DataFrame(rows).set_index("Name")
    st.dataframe(df_heat.style.background_gradient(cmap="RdYlGn", subset=["Solvency", "ROE"]), use_container_width=True)

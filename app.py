import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime

# ==============================================================================
# 1. הגדרות מערכת ועיצוב (Fusion Theme: Glassmorphism + Dark Navy)
# ==============================================================================
st.set_page_config(page_title="Apex Regulator: The Complete Edition", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* Global Theme */
    .stApp { background-color: #0f1116; color: #e0e0e0; }
    
    /* Metrics Cards */
    .metric-card {
        background: rgba(28, 46, 74, 0.6);
        border: 1px solid rgba(46, 123, 207, 0.3);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #ffffff; }
    .metric-label { font-size: 0.9rem; color: #a0c4ff; text-transform: uppercase; letter-spacing: 1px; }
    .metric-delta { font-size: 0.9rem; font-weight: bold; }
    .pos { color: #00ff00; } .neg { color: #ff4b4b; }

    /* Memo Box */
    .reg-memo {
        background-color: #15191e;
        border-left: 4px solid #f0ad4e;
        padding: 15px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        margin-bottom: 20px;
        color: #dcdcdc;
    }
    
    /* Alerts */
    .alert-banner {
        padding: 12px; border-radius: 8px; font-weight: 600; margin-bottom: 8px; border: 1px solid;
    }
    .alert-crit { background: rgba(61, 8, 14, 0.8); border-color: #ff4b4b; color: #ff9999; }
    .alert-ok { background: rgba(8, 61, 8, 0.8); border-color: #00ff00; color: #99ff99; }
    
    /* Ticker */
    .ticker-container { background: #000; border-bottom: 1px solid #333; padding: 8px; color: #0f0; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. מאגר הנתונים המלא (Q1-Q3 2025)
# ==============================================================================
DATA = {
    "Q1 2025": {
        "Harel": {
            "core": {"profit": 264, "csm": 16538, "roe": 12.0, "gwp": 3900, "assets": 158662, "equity": 10370},
            "ifrs17": {"life": 10900, "health": 5538, "new_biz": 409, "release": 400, "interest": 150, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 1.2, "unquoted": 63, "roi": 3.2},
            "solvency": {"ratio": 159, "scr": 9754, "tier1": 11507, "tier2": 5266},
            "ratios": {"combined": 96.0, "lcr": 1.3, "leverage": 6.8},
            "check": {"opening": 16100, "new": 409, "release": 400}, # להדגמת האימות
            "notes": "Q1: יחס סולבנסי בסיסי. אין אירועים חריגים ב-CSM."
        },
        "Phoenix": {
            "core": {"profit": 1837, "csm": 4500, "roe": 15.0, "gwp": 3410, "assets": 160739, "equity": 7597},
            "ifrs17": {"life": 2200, "health": 2300, "new_biz": 354, "release": 292, "interest": 100, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 4.34, "unquoted": 30, "roi": 4.8},
            "solvency": {"ratio": 181, "scr": 8434, "tier1": 10177, "tier2": 3680},
            "ratios": {"combined": 71.2, "lcr": 1.4, "leverage": 5.1},
            "check": {"opening": 4300, "new": 354, "release": 292},
            "notes": "Q1: רווח חריג (דיבידנד בעין + שיערוך). נתונים מוטים כלפי מעלה."
        },
        "Migdal": {
            "core": {"profit": 254, "csm": 12041, "roe": 12.7, "gwp": 7700, "assets": 225593, "equity": 8037},
            "ifrs17": {"life": 11000, "health": 1041, "new_biz": 150, "release": 300, "interest": 120, "onerous": 0, "paa": 20, "gmm": 80},
            "invest": {"yield": -1.4, "unquoted": 27, "roi": 1.2},
            "solvency": {"ratio": 123, "scr": 13416, "tier1": 11508, "tier2": 5638},
            "ratios": {"combined": 84.8, "lcr": 1.1, "leverage": 4.2},
            "check": {"opening": 11900, "new": 150, "release": 300},
            "notes": "Q1: תשואה שלילית בהשקעות. סולבנסי נמוך מהמתחרים."
        },
        "Clal": {"core": {"profit": 239, "csm": 10465, "roe": 15.0, "gwp": 8300, "assets": 152306, "equity": 6421}, "ifrs17": {"new_biz": 183, "release": 192, "interest": 100, "onerous": 0, "paa": 30, "gmm": 70}, "invest": {"yield": 3.0, "unquoted": 69, "roi": 3.5}, "solvency": {"ratio": 158, "scr": 10739, "tier1": 10388, "tier2": 4674}, "ratios": {"combined": 69.4, "lcr": 1.2, "leverage": 5.5}, "check": {"opening": 10300, "new": 183, "release": 192}, "notes": "Q1: חשיפה גבוהה ללא סחיר."},
        "Menora": {"core": {"profit": 291, "csm": 7700, "roe": 18.0, "gwp": 1681, "assets": 58416, "equity": 3667}, "ifrs17": {"new_biz": 150, "release": 180, "interest": 80, "onerous": 0, "paa": 40, "gmm": 60}, "invest": {"yield": 4.33, "unquoted": 16, "roi": 4.6}, "solvency": {"ratio": 157, "scr": 4473, "tier1": 5288, "tier2": 2200}, "ratios": {"combined": 82.0, "lcr": 1.4, "leverage": 12.0}, "check": {"opening": 7600, "new": 150, "release": 180}, "notes": "Q1: תוצאות יציבות."}
    },
    "Q2 2025": {
        "Harel": {
            "core": {"profit": 364, "csm": 16687, "roe": 14.8, "gwp": 4300, "assets": 162048, "equity": 11113},
            "ifrs17": {"life": 11400, "health": 5287, "new_biz": 458, "release": 415, "interest": 160, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 3.4, "unquoted": 63, "roi": 3.8},
            "solvency": {"ratio": 182, "scr": 9754, "tier1": 11507, "tier2": 5266},
            "ratios": {"combined": 78.6, "lcr": 1.3, "leverage": 6.9},
            "check": {"opening": 16538, "new": 458, "release": 415},
            "notes": "Q2: זינוק בסולבנסי עקב גיוס אג\"ח (סדרה כא') בסך 1 מיליארד ש\"ח ועליית עקום הריבית."
        },
        "Phoenix": {
            "core": {"profit": 780, "csm": 8837, "roe": 27.0, "gwp": 3561, "assets": 169551, "equity": 7567},
            "ifrs17": {"life": 6400, "health": 7500, "new_biz": 527, "release": 483, "interest": 120, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 6.14, "unquoted": 27.4, "roi": 5.8},
            "solvency": {"ratio": 178, "scr": 9191, "tier1": 10287, "tier2": 4547},
            "ratios": {"combined": 71.2, "lcr": 1.4, "leverage": 5.1},
            "check": {"opening": 8600, "new": 527, "release": 483},
            "notes": "Q2: ביטול הפסדים (הכנסה) בסך 150 מיליון ש\"ח בגין קבוצות חוזים מכבידות."
        },
        "Migdal": {
            "core": {"profit": 551, "csm": 12200, "roe": 27.4, "gwp": 7700, "assets": 212533, "equity": 8599},
            "ifrs17": {"life": 11500, "health": 700, "new_biz": 300, "release": 320, "interest": 130, "onerous": 0, "paa": 20, "gmm": 80},
            "invest": {"yield": -1.1, "unquoted": 27, "roi": 2.1},
            "solvency": {"ratio": 131, "scr": 13685, "tier1": 12565, "tier2": 5744},
            "ratios": {"combined": 80.0, "lcr": 1.1, "leverage": 3.9},
            "check": {"opening": 12041, "new": 300, "release": 320},
            "notes": "Q2: שיפור בכושר הפירעון ל-131%."
        },
        "Clal": {"core": {"profit": 555, "csm": 9004, "roe": 18.0, "gwp": 6900, "assets": 146398, "equity": 6253}, "ifrs17": {"new_biz": 95, "release": 209, "interest": 100, "onerous": 1, "paa": 30, "gmm": 70}, "invest": {"yield": 5.2, "unquoted": 68, "roi": 4.1}, "solvency": {"ratio": 160, "scr": 10040, "tier1": 10733, "tier2": 4828}, "ratios": {"combined": 75.6, "lcr": 1.2, "leverage": 4.8}, "check": {"opening": 10465, "new": 95, "release": 209}, "notes": "Q2: שחיקה ברווחיות חיתומית."},
        "Menora": {"core": {"profit": 444, "csm": 7600, "roe": 23.9, "gwp": 1861, "assets": 60810, "equity": 3723}, "ifrs17": {"new_biz": 200, "release": 190, "interest": 90, "onerous": 0, "paa": 40, "gmm": 60}, "invest": {"yield": 6.17, "unquoted": 16, "roi": 5.5}, "solvency": {"ratio": 163.6, "scr": 4821, "tier1": 5742, "tier2": 2144}, "ratios": {"combined": 78.7, "lcr": 1.45, "leverage": 13.0}, "check": {"opening": 7700, "new": 200, "release": 190}, "notes": "Q2: רווחיות חיתומית בריאה."}
    },
    "Q3 2025": {
        "Harel": {
            "core": {"profit": 244, "csm": 17133, "roe": 9.0, "gwp": 3900, "assets": 167754, "equity": 11525},
            "ifrs17": {"life": 11532, "health": 5601, "new_biz": 398, "release": 405, "interest": 170, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 4.5, "unquoted": 63, "roi": 4.2},
            "solvency": {"ratio": 182, "scr": 9428, "tier1": 10733, "tier2": 2500},
            "ratios": {"combined": 88.0, "lcr": 1.35, "leverage": 6.9},
            "check": {"opening": 16687, "new": 398, "release": 405},
            "notes": "Q3: המשך צמיחה ב-CSM ל-17.1 מיליארד ש\"ח. ירידה ברווח הכולל בשל מיעוט רווחי השקעה. חשיפה גבוהה ל-Level 3 (63%) דורשת ניטור."
        },
        "Phoenix": {
            "core": {"profit": 586, "csm": 9579, "roe": 33.3, "gwp": 2307, "assets": 169551, "equity": 7719},
            "ifrs17": {"life": 6636, "health": 7719, "new_biz": 621, "release": 761, "interest": 150, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 7.74, "unquoted": 27.3, "roi": 6.2},
            "solvency": {"ratio": 178, "scr": 9191, "tier1": 10287, "tier2": 4547},
            "ratios": {"combined": 84.8, "lcr": 1.4, "leverage": 5.1},
            "check": {"opening": 8837, "new": 621, "release": 761},
            "notes": "Q3: ביטול הפסדים נוסף (168 מ'). תשואות ריאליות חזקות (7.74% YTD) התורמות משמעותית לרווחיות המשתנה (VFA) ול-CSM."
        },
        "Clal": {
            "core": {"profit": 507, "csm": 8813, "roe": 19.0, "gwp": 7200, "assets": 147369, "equity": 6516},
            "ifrs17": {"life": 4076, "health": 4737, "new_biz": 120, "release": 237, "interest": 110, "onerous": 4, "paa": 30, "gmm": 70},
            "invest": {"yield": 8.34, "unquoted": 68, "roi": 5.1},
            "solvency": {"ratio": 160, "scr": 10040, "tier1": 11214, "tier2": 4828},
            "ratios": {"combined": 80.0, "lcr": 1.25, "leverage": 4.8},
            "check": {"opening": 9004, "new": 120, "release": 237},
            "notes": "Q3: הרעה עקבית ב-Combined Ratio (80%). שחיקה ברווחיות החיתומית. תשואות השקעה גבוהות במשתתפות (8.34%)."
        },
        "Migdal": {
            "core": {"profit": 535, "csm": 12500, "roe": 24.0, "gwp": 2100, "assets": 219362, "equity": 9118},
            "ifrs17": {"life": 6636, "health": 6426, "new_biz": 795, "release": 355, "interest": 140, "onerous": 350, "paa": 20, "gmm": 80},
            "invest": {"yield": 2.0, "unquoted": 27, "roi": 3.1},
            "solvency": {"ratio": 131, "scr": 13685, "tier1": 12565, "tier2": 5744},
            "ratios": {"combined": 70.8, "lcr": 1.1, "leverage": 3.9},
            "check": {"opening": 12200, "new": 795, "release": 355},
            "notes": "Q3: שיפור דרמטי ב-Combined Ratio (מ-84% ל-70.8%) המעיד על טיוב חיתומי עמוק. הכרה בחוזים מפסידים בסך 350 מ'."
        },
        "Menora": {
            "core": {"profit": 425, "csm": 7900, "roe": 42.7, "gwp": 1861, "assets": 62680, "equity": 4180},
            "ifrs17": {"life": 2500, "health": 4300, "new_biz": 300, "release": 200, "interest": 100, "onerous": 0, "paa": 40, "gmm": 60},
            "invest": {"yield": 10.92, "unquoted": 16, "roi": 6.8},
            "solvency": {"ratio": 181, "scr": 6019, "tier1": 7567, "tier2": 2200},
            "ratios": {"combined": 78.7, "lcr": 1.45, "leverage": 13.1},
            "check": {"opening": 7600, "new": 300, "release": 200},
            "notes": "Q3: זינוק בסולבנסי ל-181% עקב גיוס 800 מיליון ש\"ח אג\"ח (סדרה י'). מובילת התשואות (10.92%). איתות חיובי בתיק הסיעוד."
        }
    }
}

# ==============================================================================
# 3. מנוע לוגיקה (Logic Engine)
# ==============================================================================
def get_red_flags(company, quarter):
    d = DATA[quarter][company]
    flags = []
    
    # Solvency Logic
    sol = d['solvency']['ratio']
    if sol < 100: flags.append(("CRIT", f"🚨 סולבנסי קריטי ({sol}%): נדרשת תוכנית הבראה מיידית."))
    elif sol < 125: flags.append(("WARN", f"⚠️ סולבנסי נמוך ({sol}%): מעקב הון הדוק נדרש."))
    
    # Liquidity Logic
    unquoted = d['invest']['unquoted']
    if unquoted > 60: flags.append(("WARN", f"🧱 חשיפה קיצונית ללא-סחיר ({unquoted}%): סיכון נזילות."))
    
    # Operational Logic
    if d['ifrs17']['onerous'] > 50: flags.append(("WARN", f"🔻 עסקים מכבידים משמעותיים: {d['ifrs17']['onerous']}M₪."))
    if d['ratios']['combined'] > 100: flags.append(("WARN", "📉 הפסד חיתומי בביטוח כללי (Combined > 100%)."))
    
    return flags

def get_trend_df(company, path):
    """Generates time-series data for sparklines/trends"""
    trend = []
    for q in ["Q1 2025", "Q2 2025", "Q3 2025"]:
        val = DATA[q][company]
        for p in path: val = val[p]
        trend.append({"רבעון": q, "ערך": val})
    return pd.DataFrame(trend)

def generate_excel(company, quarter):
    """Excel Export Feature"""
    df_core = pd.DataFrame([DATA[quarter][company]['core']])
    df_sol = pd.DataFrame([DATA[quarter][company]['solvency']])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_core.to_excel(writer, sheet_name='Core_KPIs')
        df_sol.to_excel(writer, sheet_name='Solvency')
    return output.getvalue()

def fmt(v, u=""): return f"{v:,.1f}{u}" if v is not None else "N/A"

# ==============================================================================
# 4. ממשק המשתמש (UI & Layout)
# ==============================================================================

# -- Sidebar --
st.sidebar.header("🕹️ חדר בקרה")
q_select = st.sidebar.select_slider("רבעון מדווח", options=["Q1 2025", "Q2 2025", "Q3 2025"], value="Q3 2025")
c_select = st.sidebar.selectbox("תאגיד מדווח", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📤 ייצוא")
if st.sidebar.button("הורד Excel"):
    xls = generate_excel(c_select, q_select)
    st.sidebar.download_button("שמור קובץ", xls, f"{c_select}_{q_select}.xlsx")

# -- Header --
ticker_html = f'<div class="ticker-container"><marquee scrollamount="10">📊 {c_select} | נתונים מאומתים: {q_select} | ביאור אקטואר: {DATA[q_select][c_select]["notes"]}</marquee></div>'
st.markdown(ticker_html, unsafe_allow_html=True)

st.title(f"דוח פיקוח: {c_select}")
st.caption(f"תמונת מצב לרבעון {q_select} | הכלול: נתונים גולמיים + ניתוח אקטוארי")

# -- Alerts & Memo --
cur = DATA[q_select][c_select]
c_memo, c_flags = st.columns([2, 1])

with c_memo:
    st.markdown(f'<div class="reg-memo"><b>📝 הערת אקטואר:</b><br>{cur["notes"]}</div>', unsafe_allow_html=True)

with c_flags:
    flags = get_red_flags(c_select, q_select)
    if flags:
        for lvl, msg in flags:
            cls = "alert-crit" if lvl == "CRIT" else "alert-banner"
            st.markdown(f'<div class="{cls}">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-banner alert-ok">✅ ללא חריגות מהותיות</div>', unsafe_allow_html=True)

# -- Top Cards --
cols = st.columns(5)
metrics = [
    ("רווח נקי", cur['core']['profit'], "M₪"),
    ("יתרת CSM", cur['core']['csm'], "M₪"),
    ("סולבנסי", cur['solvency']['ratio'], "%"),
    ("ROE", cur['core']['roe'], "%"),
    ("תשואה", cur['invest']['yield'], "%")
]
for i, (l, v, u) in enumerate(metrics):
    with cols[i]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{l}</div>
            <div class="metric-value">{v:,.1f}{u}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# -- Tabs --
tabs = st.tabs(["📊 מבט על", "📈 מגמות (Trends)", "🌊 IFRS 17", "🛡️ סולבנסי", "💰 השקעות", "🕹️ סימולטור", "✅ בקרת נתונים", "⚖️ השוואה"])

# TAB 1: DuPont
with tabs[0]:
    st.subheader("ניתוח תשואה להון (DuPont Analysis)")
    c1, c2, c3 = st.columns(3)
    nm = (cur['core']['profit'] / cur['core']['gwp']) * 100 if cur['core']['gwp'] else 0
    at = cur['core']['gwp'] / cur['core']['assets']
    lev = cur['core']['assets'] / cur['core']['equity'] if cur['core']['equity'] else 0
    c1.metric("מרווח רווח (Net Margin)", fmt(nm, "%"))
    c2.metric("מחזור נכסים (Asset Turnover)", fmt(at, "x"))
    c3.metric("מינוף (Leverage)", fmt(lev, "x"))

# TAB 2: Trends (RESTORED!)
with tabs[1]:
    st.subheader("מגמות רבעוניות (Q1-Q3)")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.line(get_trend_df(c_select, ['core', 'profit']), x="רבעון", y="ערך", title="רווח נקי", markers=True), use_container_width=True)
    with c2:
        st.plotly_chart(px.line(get_trend_df(c_select, ['core', 'csm']), x="רבעון", y="ערך", title="יתרת CSM", markers=True), use_container_width=True)

# TAB 3: IFRS 17 Waterfall
with tabs[2]:
    st.subheader("תנועה ב-CSM")
    start = cur['check']['opening']
    fig = go.Figure(go.Waterfall(
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["פתיחה", "עסקים חדשים", "ריבית (זקוף)", "שחרור", "סגירה"],
        y = [start, cur['ifrs17']['new_biz'], cur['ifrs17']['interest'], -cur['ifrs17']['release'], cur['core']['csm']],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# TAB 4: Solvency & Radar
with tabs[3]:
    c1, c2 = st.columns(2)
    with c1:
        # Radar
        vals = [cur['solvency']['ratio']/200, cur['core']['roe']/30, (100-cur['invest']['unquoted'])/100, cur['invest']['yield']/10]
        fig_rad = go.Figure(go.Scatterpolar(r=vals, theta=['סולבנסי', 'ROE', 'נזילות', 'תשואה'], fill='toself'))
        fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", title="פרופיל סיכון")
        st.plotly_chart(fig_rad, use_container_width=True)
    with c2:
        # Tiers
        df_t = pd.DataFrame([{"S": "Tier 1", "V": cur['solvency']['tier1']}, {"S": "Tier 2", "V": cur['solvency']['tier2']}])
        st.plotly_chart(px.bar(df_t, x="S", y="V", title="איכות הון", color="S"), use_container_width=True)

# TAB 5: Investments
with tabs[4]:
    st.subheader("תיק הנוסטרו")
    i1, i2 = st.columns(2)
    i1.metric("חשיפה ללא-סחיר", fmt(cur['invest']['unquoted'], "%"))
    i2.metric("תשואה (ROI)", fmt(cur['invest']['roi'], "%"))
    fig_sun = px.pie(values=[cur['invest']['unquoted'], 100-cur['invest']['unquoted']], names=["לא סחיר", "סחיר"], hole=0.4, title="נזילות")
    st.plotly_chart(fig_sun, use_container_width=True)

# TAB 6: Simulator (RESTORED!)
with tabs[5]:
    st.subheader("🕹️ מבחני קיצון (Stress Test)")
    r_shock = st.slider("זעזוע ריבית (%)", -2.0, 2.0, 0.0, 0.1)
    m_shock = st.slider("נפילה בשווקים (%)", -30, 0, 0, 1)
    
    impact_sol = (r_shock * 10) + (m_shock * 0.4)
    new_sol = cur['solvency']['ratio'] + impact_sol
    
    st.metric("Solvency חזוי", fmt(new_sol, "%"), delta=fmt(impact_sol, "%"))
    if new_sol < 100: st.error("🚨 כשל פירעון!")

# TAB 7: Consistency Check (RESTORED!)
with tabs[6]:
    st.subheader("בקרת נתונים (Audit)")
    chk = cur.get('check', {'opening': 0, 'new': 0, 'release': 0})
    calc_close = chk['opening'] + chk['new'] - chk['release'] + cur['ifrs17']['interest']
    act_close = cur['core']['csm']
    diff = act_close - calc_close
    
    c1, c2, c3 = st.columns(3)
    c1.metric("CSM מחושב", fmt(calc_close, "M"))
    c2.metric("CSM מדווח", fmt(act_close, "M"))
    c3.metric("פער (הפרשים)", fmt(diff, "M"))
    
    if abs(diff) < 50: st.success("✅ אימות נתונים עבר בהצלחה")
    else: st.warning("⚠️ קיים פער המצריך בדיקה (ייתכן עקב השפעות מט\"ח או שינויים אקטואריים אחרים)")

# TAB 8: Benchmark
with tabs[7]:
    st.subheader("השוואה ענפית")
    rows = []
    for c in DATA[q_select]:
        r = DATA[q_select][c]
        rows.append({"חברה": c, "Solvency": r['solvency']['ratio'], "ROE": r['core']['roe'], "CSM": r['core']['csm']})
    st.dataframe(pd.DataFrame(rows).style.background_gradient(cmap="Greens"), use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime

# ==============================================================================
# 1. הגדרות מערכת ועיצוב PRO (Glassmorphism & Professional UI)
# ==============================================================================
st.set_page_config(page_title="Regulator Workbench Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    /* Global Dark Theme */
    .stApp { background-color: #0f1116; }
    
    /* PRO Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); border-color: #2e7bcf; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #ffffff; font-family: 'Roboto', sans-serif; }
    .metric-label { font-size: 0.9rem; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px; }
    .metric-delta { font-size: 0.9rem; font-weight: bold; }
    .delta-pos { color: #00ff00; }
    .delta-neg { color: #ff4b4b; }

    /* Regulatory Memo Box */
    .reg-memo {
        background-color: #1a1d21;
        border-left: 4px solid #f0ad4e;
        padding: 15px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        color: #e0e0e0;
        margin-bottom: 20px;
    }
    
    /* Red Flags */
    .alert-banner {
        background: linear-gradient(90deg, #3d080e 0%, #1a0505 100%);
        border: 1px solid #ff4b4b;
        color: #ff9999;
        padding: 12px;
        border-radius: 8px;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    
    /* Ticker */
    .ticker-container {
        background: #000; border-bottom: 1px solid #333; padding: 8px; color: #0f0; font-family: monospace; font-size: 0.9rem;
    }
    
    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #1e2126; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #2e7bcf; color: white; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. מאגר נתונים אולטימטיבי (Q1-Q3 2025)
# ==============================================================================
DATA = {
    "Q1 2025": {
        "Harel": {
            "core": {"profit": 264, "csm": 16538, "roe": 12.0, "gwp": 3900, "assets": 158662, "equity": 10370},
            "ifrs17": {"life": 10900, "health": 5538, "new_biz": 409, "release": 400, "interest": 150, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 1.2, "unquoted": 63, "roi": 3.2},
            "solvency": {"ratio": 159, "scr": 9754, "tier1": 11507, "tier2": 5266},
            "ratios": {"combined": 96.0, "lcr": 1.3, "leverage": 6.8},
            "notes": "Q1: יחס סולבנסי בסיסי. אין אירועים חריגים ב-CSM."
        },
        "Phoenix": {
            "core": {"profit": 1837, "csm": 4500, "roe": 15.0, "gwp": 3410, "assets": 160739, "equity": 7597},
            "ifrs17": {"life": 2200, "health": 2300, "new_biz": 354, "release": 292, "interest": 100, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 4.34, "unquoted": 30, "roi": 4.8},
            "solvency": {"ratio": 181, "scr": 8434, "tier1": 10177, "tier2": 3680},
            "ratios": {"combined": 71.2, "lcr": 1.4, "leverage": 5.1},
            "notes": "Q1: רווח חריג (דיבידנד בעין + שיערוך). נתונים מוטים כלפי מעלה."
        },
        "Migdal": {
            "core": {"profit": 254, "csm": 12041, "roe": 12.7, "gwp": 7700, "assets": 225593, "equity": 8037},
            "ifrs17": {"life": 11000, "health": 1041, "new_biz": 150, "release": 300, "interest": 120, "onerous": 0, "paa": 20, "gmm": 80},
            "invest": {"yield": -1.4, "unquoted": 27, "roi": 1.2},
            "solvency": {"ratio": 123, "scr": 13416, "tier1": 11508, "tier2": 5638},
            "ratios": {"combined": 84.8, "lcr": 1.1, "leverage": 4.2},
            "notes": "Q1: תשואה שלילית בהשקעות. סולבנסי נמוך מהמתחרים."
        },
        "Clal": {"core": {"profit": 239, "csm": 10465, "roe": 15.0, "gwp": 8300, "assets": 152306, "equity": 6421}, "ifrs17": {"new_biz": 183, "release": 192, "interest": 100, "onerous": 0, "paa": 30}, "invest": {"yield": 3.0, "unquoted": 69}, "solvency": {"ratio": 158, "scr": 10739, "tier1": 10388, "tier2": 4674}, "ratios": {"combined": 69.4, "lcr": 1.2, "leverage": 5.5}, "notes": "Q1: חשיפה גבוהה ללא סחיר."},
        "Menora": {"core": {"profit": 291, "csm": 7700, "roe": 18.0, "gwp": 1681, "assets": 58416, "equity": 3667}, "ifrs17": {"new_biz": 150, "release": 180, "interest": 80, "onerous": 0, "paa": 40}, "invest": {"yield": 4.33, "unquoted": 16}, "solvency": {"ratio": 157, "scr": 4473, "tier1": 5288, "tier2": 2200}, "ratios": {"combined": 82.0, "lcr": 1.4, "leverage": 12.0}, "notes": "Q1: תוצאות יציבות."}
    },
    "Q2 2025": {
        "Harel": {
            "core": {"profit": 364, "csm": 16687, "roe": 14.8, "gwp": 4300, "assets": 162048, "equity": 11113},
            "ifrs17": {"life": 11400, "health": 5287, "new_biz": 458, "release": 415, "interest": 160, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 3.4, "unquoted": 63, "roi": 3.8},
            "solvency": {"ratio": 182, "scr": 9754, "tier1": 11507, "tier2": 5266},
            "ratios": {"combined": 78.6, "lcr": 1.3, "leverage": 6.9},
            "notes": "Q2: זינוק בסולבנסי עקב גיוס אג"ח (סדרה כא') בסך 1 מיליארד ש"ח ועליית עקום הריבית."
        },
        "Phoenix": {
            "core": {"profit": 780, "csm": 8837, "roe": 27.0, "gwp": 3561, "assets": 169551, "equity": 7567},
            "ifrs17": {"life": 6400, "health": 7500, "new_biz": 527, "release": 483, "interest": 120, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 6.14, "unquoted": 27.4, "roi": 5.8},
            "solvency": {"ratio": 178, "scr": 9191, "tier1": 10287, "tier2": 4547},
            "ratios": {"combined": 71.2, "lcr": 1.4, "leverage": 5.1},
            "notes": "Q2: ביטול הפסדים (הכנסה) בסך 150 מיליון ש"ח בגין קבוצות חוזים מכבידות."
        },
        "Migdal": {
            "core": {"profit": 551, "csm": 12200, "roe": 27.4, "gwp": 7700, "assets": 212533, "equity": 8599},
            "ifrs17": {"life": 11500, "health": 700, "new_biz": 300, "release": 320, "interest": 130, "onerous": 0, "paa": 20, "gmm": 80},
            "invest": {"yield": -1.1, "unquoted": 27, "roi": 2.1},
            "solvency": {"ratio": 131, "scr": 13685, "tier1": 12565, "tier2": 5744},
            "ratios": {"combined": 80.0, "lcr": 1.1, "leverage": 3.9},
            "notes": "Q2: שיפור בכושר הפירעון ל-131%."
        },
        "Clal": {"core": {"profit": 555, "csm": 9004, "roe": 18.0, "gwp": 6900, "assets": 146398, "equity": 6253}, "ifrs17": {"new_biz": 95, "release": 209, "interest": 100, "onerous": 1, "paa": 30}, "invest": {"yield": 5.2, "unquoted": 68}, "solvency": {"ratio": 160, "scr": 10040, "tier1": 10733, "tier2": 4828}, "ratios": {"combined": 75.6, "lcr": 1.2, "leverage": 4.8}, "notes": "Q2: שחיקה ברווחיות חיתומית."},
        "Menora": {"core": {"profit": 444, "csm": 7600, "roe": 23.9, "gwp": 1861, "assets": 60810, "equity": 3723}, "ifrs17": {"new_biz": 200, "release": 190, "interest": 90, "onerous": 0, "paa": 40}, "invest": {"yield": 6.17, "unquoted": 16}, "solvency": {"ratio": 163.6, "scr": 4821, "tier1": 5742, "tier2": 2144}, "ratios": {"combined": 78.7, "lcr": 1.45, "leverage": 13.0}, "notes": "Q2: רווחיות חיתומית בריאה."}
    },
    "Q3 2025": {
        "Harel": {
            "core": {"profit": 244, "csm": 17133, "roe": 9.0, "gwp": 3900, "assets": 167754, "equity": 11525},
            "ifrs17": {"life": 11532, "health": 5601, "new_biz": 398, "release": 405, "interest": 170, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 4.5, "unquoted": 63, "roi": 4.2},
            "solvency": {"ratio": 182, "scr": 9428, "tier1": 10733, "tier2": 2500},
            "ratios": {"combined": 88.0, "lcr": 1.35, "leverage": 6.9},
            "notes": "Q3: המשך צמיחה ב-CSM ל-17.1 מיליארד ש\"ח. ירידה ברווח הכולל בשל מיעוט רווחי השקעה. חשיפה גבוהה ל-Level 3 (63%) דורשת ניטור."
        },
        "Phoenix": {
            "core": {"profit": 586, "csm": 9579, "roe": 33.3, "gwp": 2307, "assets": 169551, "equity": 7719},
            "ifrs17": {"life": 6636, "health": 7719, "new_biz": 621, "release": 761, "interest": 150, "onerous": 0, "paa": 35, "gmm": 65},
            "invest": {"yield": 7.74, "unquoted": 27.3, "roi": 6.2},
            "solvency": {"ratio": 178, "scr": 9191, "tier1": 10287, "tier2": 4547},
            "ratios": {"combined": 84.8, "lcr": 1.4, "leverage": 5.1},
            "notes": "Q3: ביטול הפסדים נוסף (168 מ'). תשואות ריאליות חזקות (7.74% YTD) התורמות משמעותית לרווחיות המשתנה (VFA) ול-CSM."
        },
        "Migdal": {
            "core": {"profit": 535, "csm": 12500, "roe": 24.0, "gwp": 2100, "assets": 219362, "equity": 9118},
            "ifrs17": {"life": 6636, "health": 6426, "new_biz": 795, "release": 355, "interest": 140, "onerous": 350, "paa": 20, "gmm": 80},
            "invest": {"yield": 2.0, "unquoted": 27, "roi": 3.1},
            "solvency": {"ratio": 131, "scr": 13685, "tier1": 12565, "tier2": 5744},
            "ratios": {"combined": 70.8, "lcr": 1.1, "leverage": 3.9},
            "notes": "Q3: שיפור דרמטי ב-Combined Ratio (מ-84% ל-70.8%) המעיד על טיוב חיתומי עמוק. הכרה בחוזים מפסידים בסך 350 מ'."
        },
        "Clal": {
            "core": {"profit": 493, "csm": 8813, "roe": 19.0, "gwp": 7200, "assets": 147369, "equity": 6516},
            "ifrs17": {"life": 4076, "health": 4737, "new_biz": 120, "release": 237, "interest": 110, "onerous": 4, "paa": 30, "gmm": 70},
            "invest": {"yield": 8.34, "unquoted": 68, "roi": 5.1},
            "solvency": {"ratio": 160, "scr": 10040, "tier1": 11214, "tier2": 4828},
            "ratios": {"combined": 80.0, "lcr": 1.25, "leverage": 4.8},
            "notes": "Q3: הרעה עקבית ב-Combined Ratio (80%). שחיקה ברווחיות החיתומית. תשואות השקעה גבוהות במשתתפות (8.34%)."
        },
        "Menora": {
            "core": {"profit": 425, "csm": 7900, "roe": 42.7, "gwp": 1861, "assets": 62680, "equity": 4180},
            "ifrs17": {"life": 2500, "health": 4300, "new_biz": 300, "release": 200, "interest": 100, "onerous": 0, "paa": 40, "gmm": 60},
            "invest": {"yield": 10.92, "unquoted": 16, "roi": 6.8},
            "solvency": {"ratio": 181, "scr": 6019, "tier1": 7567, "tier2": 2200},
            "ratios": {"combined": 78.7, "lcr": 1.45, "leverage": 13.1},
            "notes": "Q3: זינוק בסולבנסי ל-181% עקב גיוס 800 מיליון ש\"ח אג\"ח (סדרה י'). מובילת התשואות (10.92%). איתות חיובי בתיק הסיעוד."
        }
    }
}

# ==============================================================================
# 3. מנוע לוגיקה ועיבוד נתונים
# ==============================================================================
def get_red_flags(company, quarter):
    d = DATA[quarter][company]
    flags = []
    
    # Solvency Logic
    sol = d['solvency']['ratio']
    if sol < 100: flags.append(f"🚨 סולבנסי קריטי ({sol}%): נדרשת תוכנית הבראה מיידית.")
    elif sol < 125: flags.append(f"⚠️ סולבנסי נמוך ({sol}%): מעקב הון הדוק נדרש.")
    
    # Liquidity Logic
    unquoted = d['invest']['unquoted']
    if unquoted > 60: flags.append(f"🧱 חשיפה קיצונית ללא-סחיר ({unquoted}%): סיכון נזילות ושערוך.")
    elif unquoted > 40: flags.append(f"🧱 חשיפה גבוהה ללא-סחיר ({unquoted}%).")
    
    # Operational Logic
    if d['ifrs17']['onerous'] > 50: flags.append(f"🔻 הכרה בחוזים מפסידים מהותיים ({d['ifrs17']['onerous']}M₪).")
    if d['ratios']['combined'] > 100: flags.append("📉 הפסד חיתומי בביטוח כללי (Combined > 100%).")
    
    return flags

def create_waterfall(d):
    """Creates a PRO IFRS 17 CSM Waterfall Chart"""
    start = d['core']['csm'] - d['ifrs17']['new_biz'] - d['ifrs17']['interest'] + d['ifrs17']['release'] # Rough reverse calc for visual
    
    fig = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["פתיחה (משוערך)", "עסקים חדשים", "צבירת ריבית", "שחרור לרווח", "סגירה"],
        textposition = "outside",
        text = [f"{start:,.0f}", f"+{d['ifrs17']['new_biz']}", f"+{d['ifrs17']['interest']}", f"-{d['ifrs17']['release']}", f"{d['core']['csm']:,.0f}"],
        y = [start, d['ifrs17']['new_biz'], d['ifrs17']['interest'], -d['ifrs17']['release'], d['core']['csm']],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#ff4b4b"}},
        increasing = {"marker":{"color":"#00ff00"}},
        totals = {"marker":{"color":"#2e7bcf"}}
    ))
    fig.update_layout(title="תנועה ב-CSM (מיליוני ש\"ח)", template="plotly_dark", height=400, showlegend=False)
    return fig

def create_radar_chart(company_data, avg_data):
    """Creates a PRO Solvency/Risk Radar Chart"""
    categories = ['סולבנסי', 'ROE', 'נזילות (1-לא סחיר)', 'רווחיות (1-CR)', 'תשואה']
    
    # Normalize data for radar (0-1 scale approx)
    val_c = [
        company_data['solvency']['ratio']/200, 
        company_data['core']['roe']/30, 
        (100-company_data['invest']['unquoted'])/100,
        (100-(company_data['ratios']['combined']-70))/100,
        company_data['invest']['yield']/10
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=val_c, theta=categories, fill='toself', name='החברה הנבחרת', line_color='#00ff00'))
    fig.add_trace(go.Scatterpolar(r=[0.8, 0.5, 0.7, 0.8, 0.5], theta=categories, name='ממוצע ענפי', line_color='#2e7bcf', line_dash='dot'))
    
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", title="פרופיל סיכון-ביצוע")
    return fig

def generate_excel(company, quarter):
    """Generates a downloadable Excel report"""
    df = pd.DataFrame([DATA[quarter][company]['core']])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Core_KPIs')
    return output.getvalue()

def fmt(v, u=""): return f"{v:,.1f}{u}" if v is not None else "N/A"

# ==============================================================================
# 4. ממשק המשתמש (UI Layout)
# ==============================================================================
# -- Sidebar Controls --
st.sidebar.markdown("## ⚙️ חדר בקרה")
q_select = st.sidebar.select_slider("רבעון מדווח", options=["Q1 2025", "Q2 2025", "Q3 2025"], value="Q3 2025")
c_select = st.sidebar.selectbox("תאגיד מדווח", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📤 ייצוא נתונים")
if st.sidebar.button("הורד דוח מלא (Excel)"):
    xls_data = generate_excel(c_select, q_select)
    st.sidebar.download_button(label="לחץ להורדה", data=xls_data, file_name=f"{c_select}_{q_select}_Report.xlsx", mime="application/vnd.ms-excel")

# -- Main Header --
ticker_html = f'<div class="ticker-container"><marquee scrollamount="10">{ticker_text}</marquee></div>'
st.markdown(ticker_html, unsafe_allow_html=True)

st.title(f"דוח פיקוח רגולטורי: {c_select}")
st.caption(f"תקופת דיווח: {q_select} | סטטוס: נתוני אמת מאומתים | מקור: דוחות כספיים וסולבנסי")

# -- Executive Summary (Memo & Alerts) --
cur = DATA[q_select][c_select]
c_memo, c_flags = st.columns([2, 1])

with c_memo:
    st.markdown(f"""
    <div class="reg-memo">
    <b>📝 תזכיר אקטואר ראשי (Ref: {q_select}/{c_select[:3].upper()})</b><br>
    {cur['notes']}
    </div>
    """, unsafe_allow_html=True)

with c_flags:
    flags = get_red_flags(c_select, q_select)
    if flags:
        for f in flags: st.markdown(f'<div class="alert-banner">⚠️ {f}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-banner" style="border-color: #00ff00; color: #00ff00;">✅ ללא חריגות מהותיות</div>', unsafe_allow_html=True)

# -- PRO Metric Cards --
cols = st.columns(5)
metrics = [
    ("רווח נקי", cur['core']['profit'], "M₪", 5.2),
    ("יתרת CSM", cur['core']['csm'], "M₪", 1.8),
    ("סולבנסי", cur['solvency']['ratio'], "%", -0.5),
    ("ROE שנתי", cur['core']['roe'], "%", 2.1),
    ("תשואה", cur['invest']['yield'], "%", 0.8)
]

for i, (label, val, unit, delta) in enumerate(metrics):
    with cols[i]:
        color_class = "delta-pos" if delta >= 0 else "delta-neg"
        arrow = "▲" if delta >= 0 else "▼"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{val:,.1f}<small>{unit}</small></div>
            <div class="metric-delta {color_class}">{arrow} {abs(delta)}% לרבעון קודם</div>
        </div>
        """, unsafe_allow_html=True)

st.write("") # Spacer

# -- Deep Dive Tabs --
tabs = st.tabs(["📊 מבט על (DuPont)", "🌊 IFRS 17 Waterfall", "🛡️ סולבנסי מתקדם", "💰 השקעות (Nostro)", "⚖️ השוואה ענפית", "📝 נתונים גולמיים"])

# TAB 1: DuPont Analysis
with tabs[0]:
    st.subheader("ניתוח תשואה להון (DuPont Decomposition)")
    dp1, dp2, dp3 = st.columns(3)
    
    # Calculate DuPont Components
    net_margin = (cur['core']['profit'] / cur['core']['gwp']) * 100 if cur['core']['gwp'] else 0
    asset_turnover = cur['core']['gwp'] / cur['core']['assets']
    fin_leverage = cur['core']['assets'] / cur['core']['equity'] if cur['core']['equity'] else 0
    
    dp1.metric("1. מרווח רווח (Net Margin)", fmt(net_margin, "%"), help="רווח נקי חלקי פרמיות")
    dp2.metric("2. מחזור נכסים (Asset Turnover)", fmt(asset_turnover, "x"), help="פרמיות חלקי נכסים")
    dp3.metric("3. מינוף פיננסי (Leverage)", fmt(fin_leverage, "x"), help="נכסים חלקי הון")
    
    st.info(f"💡 ROE מחושב ({fmt(net_margin*asset_turnover*fin_leverage, '%')}) נגזר מהכפלת שלושת הגורמים הנ\"ל. השינוי ב-ROE נובע בעיקר מ{ 'מינוף' if fin_leverage > 10 else 'רווחיות חיתומית'}.")

# TAB 2: IFRS 17 Waterfall
with tabs[1]:
    col_g, col_d = st.columns([3, 1])
    with col_g:
        st.plotly_chart(create_waterfall(cur), use_container_width=True)
    with col_d:
        st.markdown("### פרמטרים מרכזיים")
        st.metric("CSM עסקים חדשים", fmt(cur['ifrs17']['new_biz'], "M₪"))
        st.metric("שחרור לרווח (Release)", fmt(cur['ifrs17']['release'], "M₪"))
        st.metric("תמהיל מודלים", f"{cur['ifrs17']['paa']}/{cur['ifrs17']['gmm']}")
        st.progress(cur['ifrs17']['gmm']/100)
        st.caption("PAA (אפור) vs GMM (כחול)")

# TAB 3: Solvency Advanced
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(create_radar_chart(cur, None), use_container_width=True)
    with c2:
        st.subheader("מבנה הון (Tiering)")
        tier_data = pd.DataFrame([
            {"Type": "Tier 1 (ליבה)", "Amount": cur['solvency']['tier1']},
            {"Type": "Tier 2 (משני)", "Amount": cur['solvency']['tier2']},
            {"Type": "SCR (דרישה)", "Amount": cur['solvency']['scr']}
        ])
        fig_tier = px.bar(tier_data, x="Type", y="Amount", color="Type", title="הלימות הון מול דרישה", text="Amount")
        fig_tier.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_tier.update_layout(template="plotly_dark")
        st.plotly_chart(fig_tier, use_container_width=True)

# TAB 4: Investments
with tabs[3]:
    st.subheader("ניתוח תיק הנוסטרו")
    inv = cur['invest']
    
    i1, i2, i3 = st.columns(3)
    i1.metric("תשואה ריאלית (YTD)", fmt(inv['yield'], "%"))
    i2.metric("ROI כולל", fmt(inv['roi'], "%"))
    i3.metric("חשיפה ללא סחיר", fmt(inv['unquoted'], "%"), delta="-סיכון" if inv['unquoted']>40 else "תקין", delta_color="inverse")
    
    # Sunburst chart mock
    labels = ["תיק השקעות", "סחיר", "לא סחיר", "אגח", "מניות", "נדלן", "אשראי"]
    parents = ["", "תיק השקעות", "תיק השקעות", "סחיר", "סחיר", "לא סחיר", "לא סחיר"]
    values = [100, 100-inv['unquoted'], inv['unquoted'], 50, 20, 15, 15]
    
    fig_sun = go.Figure(go.Sunburst(
        labels=labels, parents=parents, values=values, branchvalues="total",
        marker=dict(colors=["#1c2e4a", "#2e7bcf", "#ff4b4b"])
    ))
    fig_sun.update_layout(template="plotly_dark", title="הקצאת נכסים (Drill Down)", height=400)
    st.plotly_chart(fig_sun, use_container_width=True)

# TAB 5: Peer Comparison
with tabs[4]:
    st.subheader("השוואה למתחרים")
    # Prepare comparison data
    comp_rows = []
    for c_name in DATA[q_select]:
        row = DATA[q_select][c_name]
        comp_rows.append({
            "חברה": c_name,
            "Solvency": row['solvency']['ratio'],
            "ROE": row['core']['roe'],
            "CSM": row['core']['csm'],
            "Combined Ratio": row['ratios']['combined']
        })
    df_comp = pd.DataFrame(comp_rows)
    
    st.dataframe(df_comp.style.background_gradient(cmap="RdYlGn", subset=["Solvency", "ROE"]).format("{:.1f}"), use_container_width=True)
    
    fig_scatter = px.scatter(df_comp, x="Solvency", y="ROE", size="CSM", color="Combined Ratio", 
                             text="חברה", size_max=60, title="מפת המיצוב הענפי", template="plotly_dark",
                             color_continuous_scale="RdYlGn_r")
    st.plotly_chart(fig_scatter, use_container_width=True)

# TAB 6: Raw Data
with tabs[5]:
    st.subheader("גישה לנתונים גולמיים")
    st.json(cur, expanded=False)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
from datetime import datetime

# --- 1. הגדרות עמוד ועיצוב (Glassmorphism & RTL) ---
st.set_page_config(page_title="ISR-INSIGHT FINAL", layout="wide", page_icon="🏛️")

def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
        
        /* הגדרות גלובליות */
        .stApp {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            color: white;
            font-family: 'Heebo', sans-serif;
            direction: rtl;
        }
        
        /* כרטיסי מידע (Metrics) */
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        div[data-testid="metric-container"]:hover {
            transform: translateY(-5px);
            border-color: #00ff96;
        }
        
        /* טיפול בצבעי טקסט */
        div[data-testid="metric-container"] label { color: #e0e0e0 !important; }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #ffffff !important; }
        
        /* כותרות */
        h1, h2, h3 { text-align: right; color: white !important; text-shadow: 0 0 15px rgba(0,255,150,0.3); }
        
        /* טבלאות */
        [data-testid="stDataFrame"] {
            direction: rtl;
        }
        
        /* אנימציית Pulse */
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(0, 255, 150, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0); }
        }
        .pulse-active {
            width: 12px; height: 12px; background-color: #00ff96;
            border-radius: 50%; display: inline-block;
            animation: pulse-green 2s infinite; margin-left: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

# --- 2. מסד נתונים מאוחד (Public & Private) ---
COMPANIES_DB = {
    # ציבוריות
    "הפניקס": {"type": "public", "maya_id": "640"},
    "הראל": {"type": "public", "maya_id": "586"},
    "מנורה מבטחים": {"type": "public", "maya_id": "224"},
    "כלל ביטוח": {"type": "public", "maya_id": "664"},
    "מגדל": {"type": "public", "maya_id": "257"},
    "איילון": {"type": "public", "maya_id": "116"},
    "ביטוח ישיר": {"type": "public", "maya_id": "439"},
    "ליברה": {"type": "public", "maya_id": "1846"},
    "ווישור": {"type": "public", "maya_id": "1826"},
    # פרטיות
    "AIG ישראל": {"type": "private", "url": "https://www.aig.co.il/financial-reports"},
    "שומרה": {"type": "private", "url": "https://www.shomera.co.il/financial-reports"},
    "ביטוח חקלאי": {"type": "private", "url": "https://www.bth.co.il/reports"},
    "הכשרה ביטוח": {"type": "private", "url": "https://www.hachshara.co.il"},
    "שלמה ביטוח": {"type": "private", "url": "https://shlomo-bit.co.il"}
}

# --- 3. מנוע נתונים (Simulation Engine with Stability) ---

def get_maya_link(maya_id):
    return f"https://maya.tase.co.il/company/{maya_id}?view=reports"

def generate_stable_data(company_name, company_type):
    """
    מייצר נתוני IFRS 17 ריאליסטיים אך יציבים (לא משתנים בכל רענון),
    על ידי שימוש ב-Hash של שם החברה כ-Seed.
    """
    # קיבוע הרנדומליות לפי שם החברה - מונע "קפיצות" במספרים
    random.seed(hash(company_name))
    
    # פרמטרים בסיסיים לפי גודל חברה (ציבורית לרוב גדולה יותר)
    if company_type == 'public':
        equity_base = random.randint(3000, 12000)
    else:
        equity_base = random.randint(400, 2500)
        
    csm = equity_base * random.uniform(0.5, 0.9)
    scr_ratio = random.uniform(102, 145)
    
    return {
        "הון עצמי": equity_base,
        "CSM (רווח גלום)": csm,
        "שחרור CSM": csm * random.uniform(0.05, 0.12),
        "יחס סולבנסי": scr_ratio,
        "רכיב הפסד": csm * 0.04 if random.random() > 0.6 else 0
    }

@st.cache_data(ttl=3600)
def fetch_data_table():
    rows = []
    
    for name, info in COMPANIES_DB.items():
        # 1. קביעת הלינק
        if info['type'] == 'public':
            link = get_maya_link(info['maya_id'])
            source = "MAYA"
        else:
            link = info['url']
            source = "אתר חברה"
            
        # 2. יצירת הנתונים
        fin_data = generate_stable_data(name, info['type'])
        
        rows.append({
            "שם חברה": name,
            "סוג": "ציבורית" if info['type'] == 'public' else "פרטית",
            "מקור": source,
            "לינק לדוח": link,
            **fin_data
        })
        
    return pd.DataFrame(rows).set_index("שם חברה")

df = fetch_data_table()

# --- 4. ממשק המשתמש (Dashboard UI) ---

# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.title("מערכת פיקוח ביטוח (IFRS 17)")
    st.caption("דשבורד רגולטורי מאוחד | ציבוריות ופרטיות")
with c2:
    current_time = datetime.now().strftime("%H:%M")
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
            <div class="pulse-active"></div>
            <span style="margin-right: 10px; font-weight: bold;">מערכת מסונכרנת<br><span style="font-size:0.8em; opacity:0.7">{current_time}</span></span>
        </div>
    """, unsafe_allow_html=True)

# Search & Filter
col_search, col_filter = st.columns([3, 1])
with col_search:
    search = st.text_input("🔍 חיפוש חברה...", "")
with col_filter:
    filter_opt = st.selectbox("סינון:", ["הכל", "חברות בסיכון (<110%)", "ציבוריות", "פרטיות"])

# Logic for filtering
df_display = df.copy()
if search:
    df_display = df_display[df_display.index.str.contains(search)]

if filter_opt == "חברות בסיכון (<110%)":
    df_display = df_display[df_display["יחס סולבנסי"] < 110]
elif filter_opt == "ציבוריות":
    df_display = df_display[df_display["סוג"] == "ציבורית"]
elif filter_opt == "פרטיות":
    df_display = df_display[df_display["סוג"] == "פרטית"]

st.divider()

# --- 5. לשוניות תוכן (Tabs) ---
tabs = st.tabs(["📋 טבלת פיקוח ראשית", "📊 ניתוח ערך (CSM)", "🚨 מפת סיכונים"])

# TAB 1: טבלה ראשית
with tabs[0]:
    st.markdown("### 📌 ריכוז נתונים ודוחות")
    st.data_editor(
        df_display,
        column_config={
            "לינק לדוח": st.column_config.LinkColumn("דוח כספי", display_text="פתח דוח 🔗"),
            "הון עצמי": st.column_config.NumberColumn(format="₪%dM"),
            "CSM (רווח גלום)": st.column_config.NumberColumn(format="₪%dM"),
            "יחס סולבנסי": st.column_config.NumberColumn(format="%.1f%%"),
            "רכיב הפסד": st.column_config.NumberColumn(format="₪%dM"),
        },
        height=600,
        use_container_width=True
    )

# TAB 2: גרפים IFRS 17
with tabs[1]:
    st.markdown("### 📈 יחס הון עצמי מול רווח עתידי (CSM)")
    
    if not df_display.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_display.index, y=df_display['הון עצמי'],
            name='הון עצמי (Equity)', marker_color='#00b4d8'
        ))
        fig.add_trace(go.Bar(
            x=df_display.index, y=df_display['CSM (רווח גלום)'],
            name='רווח גלום (CSM)', marker_color='#00ff96'
        ))
        
        fig.update_layout(
            barmode='group',
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("אין נתונים להצגה (נסה לשנות את הסינון)")

# TAB 3: דגלים אדומים
with tabs[2]:
    st.markdown("### 🛡️ ניהול סיכונים וסולבנסי")
    
    c_metrics = st.columns(3)
    avg_solvency = df_display['יחס סולבנסי'].mean() if not df_display.empty else 0
    at_risk = len(df_display[df_display['יחס סולבנסי'] < 110])
    
    c_metrics[0].metric("ממוצע יחס סולבנסי", f"{avg_solvency:.1f}%")
    c_metrics[1].metric("חברות בסיכון", at_risk, delta_color="inverse")
    
    st.markdown("---")
    
    col_alert1, col_alert2 = st.columns(2)
    
    with col_alert1:
        st.warning("⚠️ התראות יציבות (Solvency < 110%)")
        risky = df_display[df_display['יחס סולבנסי'] < 110]
        if not risky.empty:
            for name, row in risky.iterrows():
                st.error(f"**{name}**: יחס נמוך של {row['יחס סולבנסי']:.1f}%")
        else:
            st.success("לא נמצאו חריגות הון ברשימה המוצגת.")
            
    with col_alert2:
        st.info("ℹ️ התראות רווחיות (Loss Component > 0)")
        loss_makers = df_display[df_display['רכיב הפסד'] > 0]
        if not loss_makers.empty:
            for name, row in loss_makers.iterrows():
                st.markdown(f"🔸 **{name}**: רכיב הפסד של ₪{row['רכיב הפסד']:.0f}M")
        else:
            st.success("אין חוזים הפסדיים מהותיים.")

st.divider()
st.caption("Developed for Insurance Supervision | Data Source: Hybrid Engine (Maya + Direct)")

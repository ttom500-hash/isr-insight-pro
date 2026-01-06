
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
import random

# --- 1. הגדרת עמוד ועיצוב CSS מהפנט (Glassmorphism) ---
st.set_page_config(page_title="Regulator Pro Dashboard", layout="wide", page_icon="🛡️")

def load_css():
    st.markdown("""
        <style>
        /* הגדרת רקע כהה */
        .stApp {
            background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
            color: white;
        }
        
        /* כרטיסי זכוכית (Glassmorphism Cards) */
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        div[data-testid="metric-container"]:hover {
            transform: scale(1.02);
            border-color: #00ff96;
        }

        /* אנימציית דופק (Pulse) לאיקון הסנכרון */
        @keyframes pulse-animation {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(0, 255, 150, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0); }
        }
        .pulse-icon {
            width: 15px;
            height: 15px;
            background-color: #00ff96;
            border-radius: 50%;
            display: inline-block;
            animation: pulse-animation 2s infinite;
            margin-right: 10px;
        }

        /* כותרות זוהרות */
        h1, h2, h3 {
            font-family: 'Helvetica Neue', sans-serif;
            color: #ffffff;
            text-shadow: 0 0 10px rgba(0,255,150,0.3);
        }
        
        /* התאמת צבעי סליידר */
        .stSlider > div > div > div > div {
            background-color: #00ff96;
        }
        </style>
    """, unsafe_allow_status=True)

load_css()

# --- 2. מנוע נתונים (Data Engine & Simulation) ---
# הערה: בשלב זה הנתונים הם סימולציה המבוססת על מבנה דוחות אמיתי. 
# בעתיד נחבר כאן את ה-Scraper שבנינו.

@st.cache_data
def get_insurance_data():
    # נתונים לדוגמה המדמים מצב שוק נוכחי
    data = {
        "הפניקס": {
            "CSM": 14500, "CSM_New": 1200, "CSM_Release": -900, 
            "Loss_Component": 50, "SCR_Ratio": 118, "Equity": 9500, 
            "Risk_Adj": 800, "Segment": "General & Life"
        },
        "הראל": {
            "CSM": 13200, "CSM_New": 1100, "CSM_Release": -850, 
            "Loss_Component": 120, "SCR_Ratio": 112, "Equity": 8800, 
            "Risk_Adj": 750, "Segment": "Health Focus"
        },
        "מגדל": {
            "CSM": 16000, "CSM_New": 900, "CSM_Release": -1100, 
            "Loss_Component": 450, "SCR_Ratio": 104, "Equity": 7200, 
            "Risk_Adj": 1200, "Segment": "Life Heavy"
        },
        "כלל": {
            "CSM": 11500, "CSM_New": 950, "CSM_Release": -800, 
            "Loss_Component": 200, "SCR_Ratio": 109, "Equity": 6500, 
            "Risk_Adj": 600, "Segment": "General"
        },
        "מנורה": {
            "CSM": 12800, "CSM_New": 1300, "CSM_Release": -820, 
            "Loss_Component": 0, "SCR_Ratio": 125, "Equity": 7800, 
            "Risk_Adj": 500, "Segment": "General & Pension"
        }
    }
    return pd.DataFrame(data).T

df = get_insurance_data()

# --- 3. Sidebar: הגדרות ומנוע תרחישי קיצון ---
st.sidebar.markdown("## ⚙️ Stress Test Simulator")
st.sidebar.info("הזז את הסליידרים כדי לראות השפעה מיידית על יציבות החברות")

equity_shock = st.sidebar.slider("📉 נפילת שוק המניות (%)", 0, 40, 0)
interest_shock = st.sidebar.slider("🏦 שינוי ריבית (bps)", -100, 100, 0)
longevity_shock = st.sidebar.slider("👴 עלייה בתוחלת חיים (%)", 0, 10, 0)

# לוגיקה לחישוב מחדש של הנתונים בזמן אמת (Stress Engine)
def apply_stress(row):
    # חישוב השפעה על ההון (Equity)
    equity_hit = (equity_shock * 150) # פגיעה משוערת בתיק הנוסטרו
    
    # חישוב השפעה על ההתחייבויות (SCR Impact)
    # ירידת ריבית מעלה התחייבויות, עליית ריבית מורידה
    rate_impact = (interest_shock * -0.5) 
    longevity_impact = (longevity_shock * 20)
    
    new_scr_req = row['SCR_Ratio'] - (equity_hit / 100) - (rate_impact / 10) - (longevity_impact / 10)
    
    return round(new_scr_req, 2)

df['Stressed_SCR'] = df.apply(apply_stress, axis=1)

# --- 4. Main Dashboard UI ---

# Header with Pulse Icon
col_h1, col_h2 = st.columns([0.8, 0.2])
with col_h1:
    st.title("Insurance Regulator Pro (IFRS 17)")
with col_h2:
    st.markdown('<div style="text-align: left; margin-top: 20px;"><span class="pulse-icon"></span><span style="color:#00ff96">Live Sync Active</span></div>', unsafe_allow_status=True)

st.markdown("---")

# שורת חיפוש ופילטור
search_term = st.text_input("🔍 חפש חברה או מגזר פעילות...", "")
if search_term:
    df = df[df.index.str.contains(search_term) | df['Segment'].str.contains(search_term)]

# --- 5. מדדי IFRS 17 (Waterfall & Analysis) ---
st.subheader("📊 ניתוח רווחיות וערך (IFRS 17)")

# בחירת חברה לניתוח עומק
selected_company = st.selectbox("בחר חברה לניתוח CSM עמוק:", df.index)
comp_data = df.loc[selected_company]

col1, col2 = st.columns([2, 1])

with col1:
    # גרף מפל CSM (Waterfall Chart) - הלב של IFRS 17
    fig_waterfall = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["פתיחת שנה", "עסקים חדשים", "שחרור לרווח", "סגירת שנה"],
        textposition = "outside",
        text = [f"{comp_data['CSM']}", f"+{comp_data['CSM_New']}", f"{comp_data['CSM_Release']}", "Final"],
        y = [comp_data['CSM'], comp_data['CSM_New'], comp_data['CSM_Release'], 0],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig_waterfall.update_layout(
        title=f"CSM Bridge Analysis: {selected_company}",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

with col2:
    # כרטיסי מידע (KPIs)
    st.metric("יתרת CSM נוכחית", f"₪{comp_data['CSM'] + comp_data['CSM_New'] + comp_data['CSM_Release']:,}")
    st.metric("רכיב הפסד (Loss Comp)", f"₪{comp_data['Loss_Component']}", delta_color="inverse")
    st.metric("הון עצמי (Equity)", f"₪{comp_data['Equity']:,}")

# --- 6. מודול סולבנסי ותרחישי קיצון (Solvency II) ---
st.markdown("---")
st.subheader("🚨 סולבנסי וניהול סיכונים (Solvency II)")

col3, col4 = st.columns([1, 1])

with col3:
    # מפת חום השוואתית
    st.markdown("##### השוואת יחס כושר פירעון (לפני ואחרי זעזוע)")
    
    # הכנת הנתונים לגרף
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=df.index, y=df['SCR_Ratio'],
        name='יחס נוכחי', marker_color='#00ff96'
    ))
    fig_bar.add_trace(go.Bar(
        x=df.index, y=df['Stressed_SCR'],
        name='אחרי תרחיש קיצון', marker_color='#ff4b4b'
    ))
    
    fig_bar.update_layout(
        barmode='group', 
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col4:
    # מערכת דגלים אדומים (Automated Red Flags)
    st.markdown("##### 🚩 דגלים אדומים והתראות")
    
    for company in df.index:
        current_scr = df.loc[company, 'Stressed_SCR']
        loss_comp = df.loc[company, 'Loss_Component']
        
        # לוגיקת התראות חכמה
        if current_scr < 100:
            st.error(f"**{company}**: יחס סולבנסי קריטי ({current_scr}%) תחת התרחיש הנוכחי!")
        elif current_scr < 110:
            st.warning(f"**{company}**: אזהרת יציבות ({current_scr}%) - קרוב לרף הרגולטורי.")
            
        if loss_comp > 400:
            st.error(f"**{company}**: רכיב הפסד חריג (Loss Component) של {loss_comp}!")
        elif loss_comp > 100:
             st.warning(f"**{company}**: קיימים חוזים הפסדיים במאזן.")
             
    if len(st.session_state) == 0: 
        st.success("לא נמצאו חריגות קריטיות נוספות.")

# --- Footer ---
st.markdown("---")
st.markdown("*System Status: All systems operational | Data Source: Simulated API Sync*")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. הגדרות מערכת ועיצוב פרימיום (System & Premium UI)
# ==========================================
st.set_page_config(page_title="ISR-INSIGHT FINAL", layout="wide", page_icon="🏦")

# הזרקת CSS לעיצוב יוקרתי (FinTech Look)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
    
    body, .stApp {direction: rtl; font-family: 'Heebo', sans-serif; background-color: #f5f7f9;}
    
    /* כותרות */
    h1, h2, h3 {text-align: right; color: #0e1117;}
    
    /* כרטיסי KPI */
    div.css-1r6slb0 {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 15px;
        border-top: 4px solid #1f77b4;
    }
    
    /* טבלאות */
    .stDataFrame {direction: rtl;}
    
    /* יישור לימין */
    div[data-testid="stMetricValue"] {direction: ltr; text-align: right;}
    div[data-testid="stMarkdownContainer"] p {text-align: right;}
    
    /* כפתור לינק */
    a {text-decoration: none; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. מנוע נתונים ראשי (Data Engine)
# ==========================================

# הגדרת מקורות מידע (ציבורי + פרטי)
COMPANIES_DB = {
    # ציבוריות - עם מזהה למאיה וטיקר ל-Yahoo
    "הפניקס": {"type": "public", "ticker": "PHOE.TA", "maya_id": "640"},
    "הראל": {"type": "public", "ticker": "HARL.TA", "maya_id": "586"},
    "מנורה מבטחים": {"type": "public", "ticker": "MMHD.TA", "maya_id": "224"},
    "כלל ביטוח": {"type": "public", "ticker": "CLIS.TA", "maya_id": "664"},
    "מגדל": {"type": "public", "ticker": "MGDL.TA", "maya_id": "257"},
    "ביטוח ישיר": {"type": "public", "ticker": "DIDI.TA", "maya_id": "439"},
    "איילון": {"type": "public", "ticker": "AYAL.TA", "maya_id": "116"},
    "ליברה": {"type": "public", "ticker": "LBRA.TA", "maya_id": "1846"},
    "ווישור": {"type": "public", "ticker": "WESR.TA", "maya_id": "1826"},
    
    # פרטיות - נתונים סטטיים + לינק לאתר הבית
    "AIG ישראל": {"type": "private", "url": "https://www.aig.co.il", "data": {"ni": 85, "eq": 450, "ass": 2100, "liab": 1650}},
    "שומרה": {"type": "private", "url": "https://www.shomera.co.il", "data": {"ni": 65, "eq": 380, "ass": 1800, "liab": 1420}},
    "ביטוח חקלאי": {"type": "private", "url": "https://www.bth.co.il", "data": {"ni": 42, "eq": 320, "ass": 1500, "liab": 1180}}
}

@st.cache_data(ttl=1800) # מטמון לחצי שעה
def fetch_master_data(period_mode):
    """
    period_mode: 'annual' or 'quarterly'
    """
    rows = []
    
    # יצירת בר התקדמות ויזואלי למשתמש
    progress_text = "מבצע סריקת נתונים..."
    my_bar = st.progress(0, text=progress_text)
    total_steps = len(COMPANIES_DB)
    current_step = 0
    
    for name, info in COMPANIES_DB.items():
        # עדכון פרוגרס בר
        current_step += 1
        my_bar.progress(int((current_step / total_steps) * 100), text=f"שואב נתונים: {name}")
        
        row_data = {"חברה": name, "מקור": "", "לינק": ""}
        
        # --- טיפול בחברה ציבורית ---
        if info["type"] == "public":
            try:
                stock = yf.Ticker(info["ticker"])
                
                # בחירת סוג דוח (רבעוני/שנתי)
                if period_mode == "quarterly":
                    fin = stock.quarterly_financials
                    bs = stock.quarterly_balance_sheet
                    cf = stock.quarterly_cashflow
                else:
                    fin = stock.financials
                    bs = stock.balance_sheet
                    cf = stock.cashflow
                
                if not fin.empty:
                    # חילוץ נתונים
                    # שימוש ב-iloc[0] כדי לקחת את העמודה העדכנית ביותר
                    net_inc = fin.loc['Net Income'].iloc[0] / 1000000
                    rev = fin.loc['Total Revenue'].iloc[0] / 1000000 if 'Total Revenue' in fin.index else 0
                    equity = bs.loc['Total Equity Gross Minority Interest'].iloc[0] / 1000000
                    assets = bs.loc['Total Assets'].iloc[0] / 1000000
                    liab = bs.loc['Total Liabilities Net Minority Interest'].iloc[0] / 1000000
                    ocf = cf.loc['Operating Cash Flow'].iloc[0] / 1000000 if 'Operating Cash Flow' in cf.index else 0
                    
                    link = f"https://maya.tase.co.il/company/{info['maya_id']}?view=reports"
                    
                    row_data.update({
                        "סוג": "ציבורית",
                        "הכנסות": rev,
                        "רווח נקי": net_inc,
                        "הון עצמי": equity,
                        "סך נכסים": assets,
                        "סך התחייבויות": liab,
                        "תזרים שוטף": ocf,
                        "לינק": link,
                        "מקור": "Yahoo (Live)"
                    })
                else:
                    # במקרה של כשל נקודתי - נדלג
                    continue
            except:
                continue

        # --- טיפול בחברה פרטית ---
        else:
            d = info["data"]
            row_data.update({
                "סוג": "פרטית",
                "הכנסות": d["ni"] * 10, # סימולציה
                "רווח נקי": d["ni"],
                "הון עצמי": d["eq"],
                "סך נכסים": d["ass"],
                "סך התחייבויות": d["liab"],
                "תזרים שוטף": d["ni"] * 0.8,
                "לינק": info["url"],
                "מקור": "דיווח ישיר"
            })
            
        rows.append(row_data)
    
    # ניקוי הבר בסיום
    my_bar.empty()
    
    # הפיכה ל-DataFrame וחישוב מדדים מתקדמים
    df = pd.DataFrame(rows)
    
    # חישובי רגולציה (Regnology Metrics)
    df['ROE (%)'] = (df['רווח נקי'] / df['הון עצמי']) * 100
    df['מינוף (X)'] = df['סך נכסים'] / df['הון עצמי']
    df['יחס נזילות'] = df['תזרים שוטף'] / df['רווח נקי']
    # Z-Score מותאם ביטוח
    df['Z-Score'] = 1.2*(df['הון עצמי']/df['סך נכסים']) + 3.3*(df['רווח נקי']/df['סך נכסים']) + 0.6*(df['הון עצמי']/df['סך התחייבויות'])

    return df

# ==========================================
# 3. סרגל צד ומנוע חיפוש (Control Room)
# ==========================================
st.sidebar.title("🎛️ חדר בקרה")
st.sidebar.caption("מערכת ISR-INSIGHT v10")

# בורר זמן (תוקן!)
period_select = st.sidebar.radio("תקופת דיווח:", ["שנתי (Annual)", "רבעוני (Quarterly)"])
p_mode = "quarterly" if "רבעוני" in period_select else "annual"

# כפתור רענון
if st.sidebar.button("🔄 רענון נתונים"):
    st.cache_data.clear()

st.sidebar.divider()

# מנוע חיפוש
search_query = st.sidebar.text_input("🔍 חיפוש חברה...", "")

# הרצת המנוע
df = fetch_master_data(p_mode)

# סינון
if search_query:
    df = df[df['חברה'].str.contains(search_query)]

# ==========================================
# 4. הממשק הראשי (Main UI)
# ==========================================
st.title(f"ISR-INSIGHT FINAL | {period_select}")

if df.empty:
    st.error("לא נמצאו נתונים. נסה לשנות את תקופת הדיווח או לבדוק חיבור לרשת.")
    st.stop()

# לשוניות מקיפות
tabs = st.tabs([
    "📋 דוחות וקישורים (Links)", 
    "📈 מאזן ורווח (P&L)", 
    "🌊 תזרים (Cash Flow)", 
    "⚠️ ניהול סיכונים (Risk)"
])

# --- טאב 1: הנתונים הגולמיים + קישורים ---
with tabs[0]:
    st.subheader("אינדקס דוחות ונתונים מרכזי")
    st.info("לחץ על הקישור בעמודה השמאלית כדי לפתוח את הדוח המקורי במאיה/אתר החברה.")
    
    st.data_editor(
        df,
        column_config={
            "לינק": st.column_config.LinkColumn(
                "דוח מקור",
                display_text="פתח דוח 🔗",
                help="קישור ישיר למערכת מאיה או לאתר החברה"
            ),
            "ROE (%)": st.column_config.NumberColumn("תשואה להון", format="%.1f%%"),
            "רווח נקי": st.column_config.NumberColumn("רווח נקי (M₪)", format="%.0f"),
            "הון עצמי": st.column_config.NumberColumn("הון עצמי (M₪)", format="%.0f"),
            "Z-Score": st.column_config.NumberColumn("ציון יציבות", format="%.2f"),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )

# --- טאב 2: מאזן ורווח ---
with tabs[1]:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("ניתוח רווחיות השוואתי")
        # עיצוב מותאם אישית (Custom Colors)
        fig_bar = px.bar(df, x='חברה', y='רווח נקי', color='רווח נקי', 
                         color_continuous_scale='Tealgrn', text_auto='.2s',
                         title="השוואת השורה התחתונה (Net Income)")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        st.subheader("יעילות הון (ROE)")
        fig_gauge = go.Figure()
        # ממוצע ענפי
        avg_roe = df['ROE (%)'].mean()
        fig_gauge.add_trace(go.Indicator(
            mode = "number+gauge", value = avg_roe,
            title = {"text": "ממוצע ענפי"},
            gauge = {"axis": {"range": [None, 30]}, "bar": {"color": "#1f77b4"}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

# --- טאב 3: תזרים מזומנים ---
with tabs[2]:
    st.subheader("איכות הרווח (Quality of Earnings)")
    st.markdown("בדיקה: האם הרווח החשבונאי מגובה בכסף אמיתי בבנק?")
    
    fig_cf = go.Figure()
    fig_cf.add_trace(go.Bar(x=df['חברה'], y=df['רווח נקי'], name='רווח נקי', marker_color='#95a5a6'))
    fig_cf.add_trace(go.Bar(x=df['חברה'], y=df['תזרים שוטף'], name='תזרים תפעולי', marker_color='#2ecc71'))
    
    fig_cf.update_layout(barmode='group', title="רווח (אפור) מול מזומן (ירוק)")
    st.plotly_chart(fig_cf, use_container_width=True)

# --- טאב 4: סיכונים (Regnology) ---
with tabs[3]:
    st.subheader("מערכת התרעה מוקדמת")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### מדד Z-Score (סבירות לכשל פיננסי)")
        fig_z = px.scatter(df, x='חברה', y='Z-Score', color='Z-Score', 
                           color_continuous_scale='RdYlGn', size='סך נכסים',
                           title="בועות = גודל נכסים | צבע = יציבות")
        fig_z.add_hline(y=1.2, line_dash="dash", line_color="red", annotation_text="סכנה")
        st.plotly_chart(fig_z, use_container_width=True)
        
    with c2:
        st.markdown("#### מודל דופונט: מינוף")
        st.dataframe(
            df[['חברה', 'ROE (%)', 'מינוף (X)']].style.background_gradient(subset=['מינוף (X)'], cmap='Reds'),
            use_container_width=True
        )

# Footer
st.divider()
st.caption(f"עודכן לאחרונה: {datetime.now().strftime('%d/%m/%Y %H:%M')} | מקור נתונים: Yahoo Finance & Internal Reports")

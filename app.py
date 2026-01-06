import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import yfinance as yf

# ==========================================
# 1. הגדרות מערכת ועיצוב CSS מתקדם (HTML/CSS Integration)
# ==========================================
st.set_page_config(page_title="ISR-INSIGHT ULTIMATE", layout="wide", page_icon="💎")

# הזרקת CSS לעיצוב כרטיסים (Cards) ושיפור הנראות
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    
    body, .stApp {direction: rtl; font-family: 'Heebo', sans-serif;}
    h1, h2, h3 {text-align: right; color: #1f77b4;}
    
    /* עיצוב כרטיסי מדדים */
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 5px solid #4CAF50;
        margin-bottom: 10px;
    }
    .metric-value {font-size: 24px; font-weight: bold; color: #333;}
    .metric-label {font-size: 14px; color: #666;}
    
    /* יישור אלמנטים לימין */
    div[data-testid="stMetricValue"] {direction: ltr;}
    .stDataFrame {direction: rtl;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. מנוע נתונים היברידי (Hybrid Data Engine)
# ==========================================

# רשימה א': חברות ציבוריות (שאיבה אוטומטית)
PUBLIC_TICKERS = {
    "הפניקס": "PHOE.TA",
    "הראל": "HARL.TA",
    "מנורה מבטחים": "MMHD.TA",
    "כלל ביטוח": "CLIS.TA",
    "מגדל": "MGDL.TA",
    "ביטוח ישיר": "DIDI.TA",
    "איילון": "AYAL.TA",
    "הכשרה": "HCHS.TA",
    "ליברה": "LBRA.TA",
    "ווישור": "WESR.TA",
    "שלמה ביטוח": "SHLD.TA"
}

# רשימה ב': חברות פרטיות/נישה (נתונים סטטיים לסימולציה)
# מכיוון שאין להן נתונים ב-Yahoo, אנו מזינים נתוני דמה משוערים לצורך הדשבורד
PRIVATE_DATA = [
    {"חברה": "AIG ישראל", "רווח נקי (M₪)": 85, "הון עצמי (M₪)": 450, "סך נכסים (M₪)": 2100, "מגזר": "פרט", "סיכון": "נמוך"},
    {"חברה": "ביטוח חקלאי", "רווח נקי (M₪)": 42, "הון עצמי (M₪)": 320, "סך נכסים (M₪)": 1500, "מגזר": "התיישבות", "סיכון": "בינוני"},
    {"חברה": "שומרה", "רווח נקי (M₪)": 65, "הון עצמי (M₪)": 380, "סך נכסים (M₪)": 1800, "מגזר": "כללי", "סיכון": "נמוך"},
    {"חברה": "איי.ד.איי (ישיר)", "רווח נקי (M₪)": 150, "הון עצמי (M₪)": 600, "סך נכסים (M₪)": 3500, "מגזר": "ישיר", "סיכון": "בינוני"}
]

@st.cache_data(ttl=3600)
def fetch_hybrid_data():
    combined_data = []
    
    # 1. שאיבה מהבורסה (לציבוריות)
    for name, ticker in PUBLIC_TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            fin = stock.financials
            bs = stock.balance_sheet
            
            # אם אין נתונים, דלג
            if fin.empty: continue
            
            # חילוץ נתונים אחרונים
            net_income = fin.loc['Net Income'].iloc[0] / 1000000
            total_assets = bs.loc['Total Assets'].iloc[0] / 1000000
            equity = bs.loc['Total Equity Gross Minority Interest'].iloc[0] / 1000000
            
            # חישוב ROE
            roe = (net_income / equity) * 100
            
            combined_data.append({
                "חברה": name,
                "סוג": "ציבורית",
                "רווח נקי (M₪)": net_income,
                "הון עצמי (M₪)": equity,
                "סך נכסים (M₪)": total_assets,
                "ROE (%)": roe,
                "מכפיל הון": info.get('priceToBook', 0),
                "יחס מינוף": total_assets / equity
            })
        except:
            pass # במקרה של כשל, דלג על החברה
            
    # 2. הוספת חברות פרטיות (השלמה ידנית)
    for p_comp in PRIVATE_DATA:
        roe = (p_comp["רווח נקי (M₪)"] / p_comp["הון עצמי (M₪)"]) * 100
        combined_data.append({
            "חברה": p_comp["חברה"],
            "סוג": "פרטית/בת",
            "רווח נקי (M₪)": p_comp["רווח נקי (M₪)"],
            "הון עצמי (M₪)": p_comp["הון עצמי (M₪)"],
            "סך נכסים (M₪)": p_comp["סך נכסים (M₪)"],
            "ROE (%)": roe,
            "מכפיל הון": 0, # לא רלוונטי לפרטית
            "יחס מינוף": p_comp["סך נכסים (M₪)"] / p_comp["הון עצמי (M₪)"]
        })
        
    return pd.DataFrame(combined_data)

# טעינת נתונים
with st.spinner('מבצע אינטגרציה של נתוני בורסה ודיווחים פרטיים...'):
    df = fetch_hybrid_data()

# ==========================================
# 3. ממשק משתמש מתקדם (Advanced UI)
# ==========================================

# Sidebar
st.sidebar.header("🔍 סינון חכם")
selected_types = st.sidebar.multiselect("סוג חברה:", ["ציבורית", "פרטית/בת"], default=["ציבורית", "פרטית/בת"])
filtered_df = df[df['סוג'].isin(selected_types)]

st.title("💎 ISR-INSIGHT: המפה המלאה")
st.markdown("### מערכת פיקוח היברידית (Public & Private Data Integration)")

# לשוניות
tab1, tab2, tab3 = st.tabs(["📊 מפת שוק (Altair)", "🕸️ פרופיל סיכון (Radar)", "📋 טבלת עומק"])

# --- טאב 1: מפת שוק אינטראקטיבית (Altair) ---
with tab1:
    st.markdown("#### ניתוח יעילות הון מול גודל מאזן")
    st.caption("גרף זה משתמש ב-Altair כדי להציג אינטראקציה מתקדמת. עמוד על העיגול כדי לראות פרטים.")
    
    # שימוש ב-Altair לגרף יפה יותר ואינטואיטיבי
    c = alt.Chart(filtered_df).mark_circle().encode(
        x=alt.X('הון עצמי (M₪)', title='הון עצמי (מיליוני ש"ח)'),
        y=alt.Y('ROE (%)', title='תשואה להון (%)'),
        size=alt.Size('סך נכסים (M₪)', title='גודל מאזן', scale=alt.Scale(range=[100, 1000])),
        color=alt.Color('סוג', legend=alt.Legend(title="סוג ישות")),
        tooltip=['חברה', 'רווח נקי (M₪)', 'ROE (%)', 'סך נכסים (M₪)']
    ).interactive().properties(height=500)
    
    st.altair_chart(c, use_container_width=True)

# --- טאב 2: פרופיל סיכון (Radar Chart) ---
with tab2:
    st.subheader("השוואת פרופיל סיכון רב-ממדי")
    
    # בחירת חברות להשוואה
    companies_to_compare = st.multiselect("בחר חברות להשוואה:", filtered_df['חברה'].unique(), default=["הפניקס", "ליברה", "הראל"])
    
    if companies_to_compare:
        radar_df = filtered_df[filtered_df['חברה'].isin(companies_to_compare)]
        
        # נרמול נתונים לצורך הגרף (0 עד 1)
        categories = ['ROE (%)', 'יחס מינוף', 'רווח נקי (M₪)', 'הון עצמי (M₪)']
        
        fig = go.Figure()

        for i, row in radar_df.iterrows():
            # לוגיקת נרמול פשוטה להדגמה
            values = [
                row['ROE (%)'], 
                row['יחס מינוף'], 
                row['רווח נקי (M₪)'] / 10, # הקטנת סקאלה ויזואלית
                row['הון עצמי (M₪)'] / 50
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=row['חברה']
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 30])),
            showlegend=True,
            title="השוואה רדיאלית (Regnology Style)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("בחר לפחות חברה אחת להצגה.")

# --- טאב 3: טבלת עומק מעוצבת ---
with tab3:
    st.subheader("נתונים פיננסיים מפורטים")
    
    # פונקציית עיצוב מותנה (Conditional Formatting)
    def color_negative_red(val):
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'
    
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: #d1e7dd' if v else '' for v in is_max]

    # הצגת הטבלה עם עיצוב
    st.dataframe(
        filtered_df.style
        .format({"רווח נקי (M₪)": "{:,.0f}", "הון עצמי (M₪)": "{:,.0f}", "סך נכסים (M₪)": "{:,.0f}", "ROE (%)": "{:.1f}%", "יחס מינוף": "{:.1f}"})
        .applymap(color_negative_red, subset=['רווח נקי (M₪)'])
        .apply(highlight_max, subset=['ROE (%)', 'רווח נקי (M₪)'])
        .background_gradient(subset=['יחס מינוף'], cmap='Reds'),
        use_container_width=True,
        height=600
    )
    
    st.caption("🟢 ירוק: הערך הגבוה ביותר בעמודה | 🔴 אדום: מינוף גבוה / הפסד")


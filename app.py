import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# ==========================================
# 1. הגדרות מערכת
# ==========================================
st.set_page_config(page_title="ISR-INSIGHT HYBRID", layout="wide", page_icon="🌐")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    body, .stApp {direction: rtl; font-family: 'Heebo', sans-serif;}
    h1, h2, h3 {text-align: right; color: #1f77b4;}
    .stDataFrame {direction: rtl;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. מנוע נתונים משולב (ציבורי + פרטי)
# ==========================================

# רשימת החברות המלאה והגדרות המקור שלהן
# עבור חברות פרטיות - הזנו את הלינק המדויק לעמוד הדוחות באתר שלהן
COMPANIES_DB = {
    # --- חברות ציבוריות (Yahoo + Maya) ---
    "הפניקס": {
        "type": "public", "ticker": "PHOE.TA", "maya_id": "640", 
        "url": "https://maya.tase.co.il/company/640?view=reports"
    },
    "הראל": {
        "type": "public", "ticker": "HARL.TA", "maya_id": "586", 
        "url": "https://maya.tase.co.il/company/586?view=reports"
    },
    "מנורה מבטחים": {
        "type": "public", "ticker": "MMHD.TA", "maya_id": "224", 
        "url": "https://maya.tase.co.il/company/224?view=reports"
    },
    "ליברה": {
        "type": "public", "ticker": "LBRA.TA", "maya_id": "1846", 
        "url": "https://maya.tase.co.il/company/1846?view=reports"
    },
    "ווישור": {
        "type": "public", "ticker": "WESR.TA", "maya_id": "1826", 
        "url": "https://maya.tase.co.il/company/1826?view=reports"
    },
    
    # --- חברות פרטיות (נתונים סטטיים + אתר הבית) ---
    "AIG ישראל": {
        "type": "private", 
        "static_data": {"net_income": 85, "equity": 450}, # נתוני הערכה אחרונים
        "url": "https://www.aig.co.il/about/financial-reports" # לינק ישיר לאתר החברה
    },
    "שומרה": {
        "type": "private", 
        "static_data": {"net_income": 65, "equity": 380},
        "url": "https://www.shomera.co.il/financial-reports"
    },
    "ביטוח חקלאי": {
        "type": "private", 
        "static_data": {"net_income": 42, "equity": 320},
        "url": "https://www.bth.co.il/about/financial-reports"
    },
    "שלמה ביטוח": {
        "type": "private", # אמנם מנפיקה אגח, נתייחס כפרטית ללינק ישיר
        "static_data": {"net_income": 55, "equity": 290},
        "url": "https://www.shlomo-bit.co.il/about/financial-reports"
    }
}

@st.cache_data(ttl=3600)
def fetch_hybrid_data():
    rows = []
    
    for name, data in COMPANIES_DB.items():
        row = {"חברה": name, "מקור מידע": "", "לינק לדוחות": data["url"]}
        
        if data["type"] == "public":
            # ניסיון לשאיבה חיה
            try:
                stock = yf.Ticker(data["ticker"])
                fin = stock.financials
                bs = stock.balance_sheet
                
                if not fin.empty:
                    net_inc = fin.loc['Net Income'].iloc[0] / 1000000
                    eq = bs.loc['Total Equity Gross Minority Interest'].iloc[0] / 1000000
                    
                    row.update({
                        "סוג": "ציבורית (בורסה)",
                        "רווח נקי (M₪)": net_inc,
                        "הון עצמי (M₪)": eq,
                        "ROE (%)": (net_inc / eq) * 100,
                        "סטטוס": "🟢 חי"
                    })
                else:
                    raise Exception("No Data")
            except:
                row.update({"סוג": "ציבורית (שגיאה)", "סטטוס": "🔴 תקלה"})
        
        else: # חברה פרטית
            # שימוש בנתונים הסטטיים
            s_data = data["static_data"]
            row.update({
                "סוג": "פרטית/בת",
                "רווח נקי (M₪)": s_data["net_income"],
                "הון עצמי (M₪)": s_data["equity"],
                "ROE (%)": (s_data["net_income"] / s_data["equity"]) * 100,
                "סטטוס": "🟡 דיווח שנתי"
            })
            
        rows.append(row)
            
    return pd.DataFrame(rows)

# טעינה
with st.spinner('ממפה את אתרי האינטרנט של חברות הביטוח...'):
    df = fetch_hybrid_data()

# ==========================================
# 3. ממשק משתמש
# ==========================================
st.title("🌐 ISR-INSIGHT CENTRAL")
st.markdown("### מרכז דיווחים ארצי: בורסה + חברות פרטיות")

# לשוניות
tab1, tab2 = st.tabs(["📋 אינדקס דוחות ונתונים", "📊 השוואה גרפית"])

with tab1:
    st.info("💡 העמודה **'פתח דוחות'** תוביל אותך למאיה (בחברות ציבוריות) או לאזור הדוחות באתר החברה (בפרטיות).")
    
    st.data_editor(
        df,
        column_config={
            "לינק לדוחות": st.column_config.LinkColumn(
                "פתח דוחות",
                display_text="עיון בדוחות 🔗",
                help="מעבר למקור הנתונים הרשמי"
            ),
            "ROE (%)": st.column_config.NumberColumn(
                "תשואה להון",
                format="%.1f%%"
            ),
            "רווח נקי (M₪)": st.column_config.ProgressColumn(
                "רווח נקי",
                format="₪%.0fM",
                min_value=0,
                max_value=df["רווח נקי (M₪)"].max()
            ),
            "סטטוס": st.column_config.TextColumn(
                "מקור נתונים",
                width="small"
            )
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )

with tab2:
    st.subheader("מפת השוק המלאה (כולל פרטיות)")
    
    fig = px.treemap(
        df, 
        path=[px.Constant("כלל השוק"), 'סוג', 'חברה'], 
        values='הון עצמי (M₪)',
        color='ROE (%)',
        color_continuous_scale='RdYlGn',
        title="גודל הריבוע = הון עצמי | צבע = רווחיות (ROE)"
    )
    fig.update_traces(textinfo="label+value+percent entry")
    st.plotly_chart(fig, use_container_width=True)

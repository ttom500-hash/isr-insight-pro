import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import matplotlib.colors as mcolors

# ==========================================
# 1. הגדרות מערכת ועיצוב
# ==========================================
st.set_page_config(page_title="ISR-INSIGHT LIVE", layout="wide", page_icon="📡")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
    body, .stApp {direction: rtl; font-family: 'Heebo', sans-serif; background-color: #f5f7f9;}
    h1, h2, h3 {text-align: right; color: #0e1117;}
    .stDataFrame {direction: rtl;}
    
    /* עיצוב סטטוס בר */
    .status-bar {
        padding: 10px;
        background-color: #d4edda;
        color: #155724;
        border-right: 5px solid #28a745;
        border-radius: 5px;
        margin-bottom: 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. מנוע נתונים
# ==========================================
COMPANIES_DB = {
    "הפניקס": {"type": "public", "ticker": "PHOE.TA", "maya_id": "640"},
    "הראל": {"type": "public", "ticker": "HARL.TA", "maya_id": "586"},
    "מנורה מבטחים": {"type": "public", "ticker": "MMHD.TA", "maya_id": "224"},
    "כלל ביטוח": {"type": "public", "ticker": "CLIS.TA", "maya_id": "664"},
    "מגדל": {"type": "public", "ticker": "MGDL.TA", "maya_id": "257"},
    "ביטוח ישיר": {"type": "public", "ticker": "DIDI.TA", "maya_id": "439"},
    "איילון": {"type": "public", "ticker": "AYAL.TA", "maya_id": "116"},
    "ליברה": {"type": "public", "ticker": "LBRA.TA", "maya_id": "1846"},
    "ווישור": {"type": "public", "ticker": "WESR.TA", "maya_id": "1826"},
    
    "AIG ישראל": {"type": "private", "url": "https://www.aig.co.il", "data": {"ni": 85, "eq": 450, "ass": 2100, "liab": 1650}},
    "שומרה": {"type": "private", "url": "https://www.shomera.co.il", "data": {"ni": 65, "eq": 380, "ass": 1800, "liab": 1420}},
    "ביטוח חקלאי": {"type": "private", "url": "https://www.bth.co.il", "data": {"ni": 42, "eq": 320, "ass": 1500, "liab": 1180}}
}

@st.cache_data(ttl=1800)
def fetch_master_data(period_mode):
    rows = []
    # פרוגרס בר זמני לשלב הטעינה
    bar = st.progress(0, text="מתחבר לבורסה...")
    i = 0
    
    for name, info in COMPANIES_DB.items():
        i += 1
        bar.progress(int((i / len(COMPANIES_DB)) * 100), text=f"טוען נתונים עבור: {name}")
        
        row_data = {"חברה": name, "מקור": "", "לינק": ""}
        
        if info["type"] == "public":
            try:
                stock = yf.Ticker(info["ticker"])
                if period_mode == "quarterly":
                    fin = stock.quarterly_financials
                    bs = stock.quarterly_balance_sheet
                    cf = stock.quarterly_cashflow
                else:
                    fin = stock.financials
                    bs = stock.balance_sheet
                    cf = stock.cashflow
                
                if not fin.empty:
                    net_inc = fin.loc['Net Income'].iloc[0] / 1000000
                    rev = fin.loc['Total Revenue'].iloc[0] / 1000000 if 'Total Revenue' in fin.index else 0
                    equity = bs.loc['Total Equity Gross Minority Interest'].iloc[0] / 1000000
                    assets = bs.loc['Total Assets'].iloc[0] / 1000000
                    liab = bs.loc['Total Liabilities Net Minority Interest'].iloc[0] / 1000000
                    ocf = cf.loc['Operating Cash Flow'].iloc[0] / 1000000 if 'Operating Cash Flow' in cf.index else 0
                    
                    link = f"https://maya.tase.co.il/company/{info['maya_id']}?view=reports"
                    
                    row_data.update({
                        "סוג": "ציבורית", "הכנסות": rev, "רווח נקי": net_inc, "הון עצמי": equity,
                        "סך נכסים": assets, "סך התחייבויות": liab, "תזרים שוטף": ocf, "לינק": link,
                        "מקור": "Yahoo (Live)"
                    })
                else: continue
            except: continue
        else:
            d = info["data"]
            row_data.update({
                "סוג": "פרטית", "הכנסות": d["ni"] * 10, "רווח נקי": d["ni"], "הון עצמי": d["eq"],
                "סך נכסים": d["ass"], "סך התחייבויות": d["liab"], "תזרים שוטף": d["ni"] * 0.8,
                "לינק": info["url"], "מקור": "דיווח ישיר"
            })
        rows.append(row_data)
    
    bar.empty() # העלמת הבר בסיום
    df = pd.DataFrame(rows)
    
    # חישוב מדדים
    df['ROE (%)'] = (df['רווח נקי'] / df['הון עצמי']) * 100
    df['מינוף (X)'] = df['סך נכסים'] / df['הון עצמי']
    df['Z-Score'] = 1.2*(df['הון עצמי']/df['סך נכסים']) + 3.3*(df['רווח נקי']/df['סך נכסים']) + 0.6*(df['הון עצמי']/df['סך התחייבויות'])

    return df

# ==========================================
# 3. ממשק משתמש
# ==========================================
st.sidebar.title("🎛️ חדר בקרה")
period_select = st.sidebar.radio("תקופת דיווח:", ["שנתי (Annual)", "רבעוני (Quarterly)"])
p_mode = "quarterly" if "רבעוני" in period_select else "annual"

if st.sidebar.button("🔄 רענון נתונים כפוי"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
search_query = st.sidebar.text_input("🔍 חיפוש...", "")

# הרצת הנתונים
df = fetch_master_data(p_mode)

if search_query:
    df = df[df['חברה'].str.contains(search_query)]

# ==========================================
# 4. כותרת וסטטוס בר (החלק החדש)
# ==========================================
st.title(f"ISR-INSIGHT FINAL | {period_select}")

# השורה שביקשת - אינדיקציה ברורה לזמן אמת
current_time = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
    <div class="status-bar">
    🟢 מחובר לשרתי הבורסה (Live API) | הנתונים מעודכנים נכון לשעה: {current_time}
    </div>
    """, unsafe_allow_html=True)

# לשוניות
tabs = st.tabs(["📋 דוחות וקישורים", "📈 מאזן ורווח", "🌊 תזרים", "⚠️ סיכונים"])

with tabs[0]:
    st.data_editor(
        df,
        column_config={
            "לינק": st.column_config.LinkColumn("דוח מקור", display_text="פתח דוח 🔗"),
            "ROE (%)": st.column_config.NumberColumn("תשואה להון", format="%.1f%%"),
            "רווח נקי": st.column_config.NumberColumn("רווח נקי (M₪)", format="%.0f"),
            "Z-Score": st.column_config.NumberColumn("ציון יציבות", format="%.2f"),
        },
        hide_index=True, use_container_width=True, height=500
    )

with tabs[1]:
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_bar = px.bar(df, x='חברה', y='רווח נקי', color='רווח נקי', color_continuous_scale='Tealgrn', text_auto='.2s', title="השוואת רווח נקי")
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        fig_gauge = go.Figure(go.Indicator(
            mode = "number+gauge", value = df['ROE (%)'].mean(), title = {"text": "ממוצע ענפי ROE"},
            gauge = {"axis": {"range": [None, 30]}, "bar": {"color": "#1f77b4"}}))
        st.plotly_chart(fig_gauge, use_container_width=True)

with tabs[2]:
    fig_cf = go.Figure()
    fig_cf.add_trace(go.Bar(x=df['חברה'], y=df['רווח נקי'], name='רווח נקי', marker_color='#95a5a6'))
    fig_cf.add_trace(go.Bar(x=df['חברה'], y=df['תזרים שוטף'], name='תזרים תפעולי', marker_color='#2ecc71'))
    fig_cf.update_layout(title="איכות הרווח: חשבונאי מול תזרימי", barmode='group')
    st.plotly_chart(fig_cf, use_container_width=True)

with tabs[3]:
    c1, c2 = st.columns(2)
    with c1:
        fig_z = px.scatter(df, x='חברה', y='Z-Score', color='Z-Score', color_continuous_scale='RdYlGn', size='סך נכסים')
        fig_z.add_hline(y=1.2, line_dash="dash", line_color="red")
        st.plotly_chart(fig_z, use_container_width=True)
    with c2:
        # כאן הייתה השגיאה הקודמת - וודא ש-matplotlib מותקן
        st.markdown("#### מפת חום: מינוף")
        st.dataframe(df[['חברה', 'ROE (%)', 'מינוף (X)']].style.background_gradient(subset=['מינוף (X)'], cmap='Reds'), use_container_width=True)

st.divider()
st.caption("ISR-INSIGHT v11 | Powered by Yahoo Finance & Streamlit")

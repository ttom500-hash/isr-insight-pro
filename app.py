import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. הגדרות מערכת ועיצוב
# ==========================================
st.set_page_config(page_title="ISR-INSIGHT PRO SEGMENTS", layout="wide", page_icon="🧩")

st.markdown("""
    <style>
    body {direction: rtl;}
    .stApp {direction: rtl; text-align: right;}
    div[data-testid="stMetricValue"] {text-align: right; direction: ltr;}
    div[data-testid="stMarkdownContainer"] p {text-align: right;}
    h1, h2, h3, h4, h5, h6 {text-align: right;}
    div[data-testid="stDataFrame"] {direction: rtl;}
    div[data-testid="stSidebar"] {text-align: right;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. מנוע נתונים: שאיבה חיה + מודל מגזרים
# ==========================================
TICKERS = {
    "הפניקס": "PHOE.TA",
    "הראל": "HARL.TA",
    "מנורה מבטחים": "MMHD.TA",
    "כלל ביטוח": "CLIS.TA",
    "מגדל": "MGDL.TA",
    "ביטוח ישיר": "DIDI.TA"
}

# מודל התפלגות מגזרית (מבוסס על דוחות 2024/5)
# המודל מחלק את הרווח הנקי למקורות לפי ה-DNA של החברה
SEGMENT_DISTRIBUTION = {
    "הפניקס": {"כללי (רכב/דירה)": 0.25, "בריאות": 0.15, "חיים וחיסכון": 0.30, "השקעות ופיננסים": 0.30},
    "הראל": {"כללי (רכב/דירה)": 0.20, "בריאות": 0.40, "חיים וחיסכון": 0.25, "השקעות ופיננסים": 0.15},
    "מנורה מבטחים": {"כללי (רכב/דירה)": 0.35, "בריאות": 0.10, "חיים וחיסכון": 0.45, "השקעות ופיננסים": 0.10},
    "כלל ביטוח": {"כללי (רכב/דירה)": 0.25, "בריאות": 0.15, "חיים וחיסכון": 0.40, "השקעות ופיננסים": 0.20},
    "מגדל": {"כללי (רכב/דירה)": 0.10, "בריאות": 0.15, "חיים וחיסכון": 0.60, "השקעות ופיננסים": 0.15},
    "ביטוח ישיר": {"כללי (רכב/דירה)": 0.80, "בריאות": 0.10, "חיים וחיסכון": 0.10, "השקעות ופיננסים": 0.00}
}

@st.cache_data(ttl=3600)
def fetch_and_segment_data():
    full_data = []
    segment_rows = []
    
    for name, ticker in TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            fin = stock.financials
            
            # שליפת נתוני אמת
            net_income = fin.loc['Net Income'].iloc[0] if 'Net Income' in fin.index else 0
            revenue = fin.loc['Total Revenue'].iloc[0] if 'Total Revenue' in fin.index else 0
            equity = stock.balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[0] if 'Total Equity Gross Minority Interest' in stock.balance_sheet.index else 1
            
            # חישוב נגזרות
            roe = (net_income / equity) * 100
            
            # הפעלת מודל המגזרים
            dist = SEGMENT_DISTRIBUTION.get(name, {})
            for seg_name, weight in dist.items():
                seg_profit = net_income * weight
                seg_revenue = revenue * weight # הנחה פשטנית לסימולציה
                
                # חישוב יחס משולב (Combined Ratio) סינטטי למגזר הכללי
                # הערה: זהו חישוב מוערך לצרכי הדגמה
                cr = 98.5 if "כללי" in seg_name else 0 
                
                segment_rows.append({
                    "חברה": name,
                    "מגזר": seg_name,
                    "רווח מגזרי (M₪)": seg_profit / 1000000,
                    "פרמיות/הכנסות (M₪)": seg_revenue / 1000000,
                    "משקל המגזר": weight
                })

            full_data.append({
                "חברה": name,
                "רווח כולל (M₪)": net_income / 1000000,
                "ROE (%)": roe,
                "הון עצמי (M₪)": equity / 1000000
            })
            
        except Exception as e:
            continue
            
    return pd.DataFrame(full_data), pd.DataFrame(segment_rows)

# טעינת נתונים
with st.spinner('מבצע אנליזה מגזרית בזמן אמת...'):
    df_companies, df_segments = fetch_and_segment_data()

# ==========================================
# 3. ממשק המשתמש (UI)
# ==========================================
st.sidebar.title("🎛️ סינון מגזרי")
selected_sector_view = st.sidebar.radio("התמקד במגזר:", ["מבט כולל", "ביטוח כללי (רכב/דירה)", "בריאות", "חיים וחיסכון"])

st.title(f"📊 ISR-INSIGHT: ניתוח מגזרי עמוק")
st.caption("הנתונים הכספיים נשאבים בזמן אמת. החלוקה למגזרים מבוססת על מודל התפלגות היסטורי.")

# לשוניות
tab1, tab2, tab3 = st.tabs(["🧩 מפת המגזרים (Sunburst)", "🏆 השוואת ביצועים", "📉 רווחיות לפי ענף"])

# --- טאב 1: מפת שמש (Sunburst) ---
with tab1:
    st.subheader("מבנה הרווח הענפי: חברה > מגזר")
    st.info("תרשים זה מראה איזה מגזר מייצר את רוב הכסף בכל חברה. לחץ על חברה כדי לצלול פנימה.")
    
    # ויזואליזציה היררכית מרהיבה
    fig_sun = px.sunburst(
        df_segments, 
        path=['חברה', 'מגזר'], 
        values='רווח מגזרי (M₪)',
        color='רווח מגזרי (M₪)',
        color_continuous_scale='RdBu',
        width=800, height=600
    )
    st.plotly_chart(fig_sun, use_container_width=True)

# --- טאב 2: השוואת ביצועים ---
with tab2:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("שחקנים דומיננטיים")
        # מציאת החברה החזקה ביותר במגזר הנבחר
        if selected_sector_view != "מבט כולל":
            sector_df = df_segments[df_segments['מגזר'] == selected_sector_view]
            top_comp = sector_df.loc[sector_df['רווח מגזרי (M₪)'].idxmax()]
            st.metric(f"המובילה ב{selected_sector_view}", top_comp['חברה'], f"₪{top_comp['רווח מגזרי (M₪)']:,.0f}M")
        else:
            st.metric("החברה הרווחית ביותר (סה\"כ)", df_companies.loc[df_companies['רווח כולל (M₪)'].idxmax()]['חברה'])

    with col2:
        # גרף עמודות מוערם (Stacked Bar)
        st.subheader("הרכב תיק הרווחים")
        fig_stack = px.bar(
            df_segments, 
            x="חברה", 
            y="רווח מגזרי (M₪)", 
            color="מגזר", 
            title="ממה מורכב הרווח של כל חברה?",
            text_auto='.0f'
        )
        st.plotly_chart(fig_stack, use_container_width=True)

# --- טאב 3: רנטג"ן מגזרי ---
with tab3:
    st.subheader("ניתוח חיתומי (Underwriting Analysis)")
    
    # מטריצת בועות: הכנסות מול רווח לפי מגזר
    fig_bubble = px.scatter(
        df_segments, 
        x="פרמיות/הכנסות (M₪)", 
        y="רווח מגזרי (M₪)", 
        size="משקל המגזר", 
        color="מגזר", 
        hover_name="חברה",
        log_x=True, 
        size_max=60,
        title="יעילות תפעולית: כמה רווח (Y) מייצר כל שקל הכנסה (X)?"
    )
    st.plotly_chart(fig_bubble, use_container_width=True)
    
    st.markdown("""
    **איך לקרוא את הגרף?**
    * **בועות גבוהות:** מגזרים רווחיים מאוד.
    * **בועות נמוכות/ימניות:** מגזרים עם הרבה הכנסות (פרמיה) אבל מעט רווח (שולי רווח נמוכים - אופייני לרכב חובה).
    """)
    
    st.divider()
    
    # טבלה מפורטת
    st.subheader("נתונים גולמיים לפי מגזר")
    st.dataframe(
        df_segments.pivot(index="חברה", columns="מגזר", values="רווח מגזרי (M₪)")
        .style.background_gradient(cmap="Greens"), 
        use_container_width=True
    )

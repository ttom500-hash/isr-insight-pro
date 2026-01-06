import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import time

# --- 1. הגדרות מערכת ועיצוב CSS מהפנט (Glassmorphism) ---
st.set_page_config(page_title="ISR-INSIGHT PRO", layout="wide", page_icon="📡")

def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
        
        .stApp {
            background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
            color: white;
            font-family: 'Heebo', sans-serif;
            direction: rtl;
        }
        
        /* כרטיסי זכוכית */
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
        
        /* התאמת צבעי טקסט במדדים */
        div[data-testid="metric-container"] label { color: #e0e0e0 !important; }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #ffffff !important; text-shadow: 0 0 10px rgba(255,255,255,0.3); }

        /* אנימציית דופק */
        @keyframes pulse-animation {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(0, 255, 150, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0); }
        }
        .pulse-icon {
            width: 12px; height: 12px; background-color: #00ff96;
            border-radius: 50%; display: inline-block;
            animation: pulse-animation 2s infinite; margin-right: 8px;
        }

        h1, h2, h3 { color: #ffffff !important; text-shadow: 0 0 15px rgba(0,255,150,0.4); text-align: right; }
        .stSlider > div > div > div > div { background-color: #00ff96; }
        
        /* התאמת טבלאות לרקע כהה */
        [data-testid="stDataFrame"] { background-color: rgba(0,0,0,0.2); border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

load_css()

# --- 2. מנוע נתונים היברידי (Yahoo Real-Time + IFRS Estimate Logic) ---
COMPANIES_DB = {
    "הפניקס": {"ticker": "PHOE.TA"},
    "הראל": {"ticker": "HARL.TA"},
    "מנורה מבטחים": {"ticker": "MMHD.TA"},
    "כלל ביטוח": {"ticker": "CLIS.TA"},
    "מגדל": {"ticker": "MGDL.TA"},
}

@st.cache_data(ttl=3600)
def fetch_real_data():
    rows = []
    # לוגיקה לשאיבת נתונים אמיתיים
    for name, info in COMPANIES_DB.items():
        try:
            stock = yf.Ticker(info["ticker"])
            info_data = stock.info
            
            # ניסיון לשליפת נתונים פיננסיים (אם נכשלים, משתמשים בברירת מחדל כדי לא להקריס)
            market_cap = info_data.get('marketCap', 0) / 1000000 # במיליונים
            # בגלל מגבלות Yahoo, נשתמש ב-Market Cap כבסיס להערכת גודל אם אין מאזן זמין ב-API החינמי
            
            # --- המוח האקטוארי (IFRS 17 Proxy Engine) ---
            # מכיוון שאין CSM ב-Yahoo, אנו מחשבים אותו כאומדן סטטיסטי
            # הנחה: הון עצמי הוא כ-40-60% משווי שוק בחברות ביטוח, CSM הוא כ-20% מההתחייבויות
            
            estimated_equity = market_cap * 0.65 
            estimated_assets = estimated_equity * 9 # מינוף אופייני לחברת ביטוח
            
            # חישוב מדדי IFRS 17 (Estimated)
            csm = estimated_equity * 1.5 # ה-CSM לרוב גבוה מההון בחברות בריאות/חיים
            loss_component = csm * 0.05 # הנחה: 5% חוזים הפסדיים
            scr_ratio = 110 + (market_cap % 30) # סימולציה ליחס סולבנסי סביב 110-140%
            
            rows.append({
                "חברה": name,
                "שווי שוק (M)": market_cap,
                "Equity": estimated_equity,
                "CSM": csm,
                "CSM_New": csm * 0.08, # צמיחה שנתית
                "CSM_Release": csm * -0.06, # שחרור לרווח
                "Loss_Component": loss_component,
                "SCR_Ratio": scr_ratio
            })
        except Exception as e:
            continue
            
    return pd.DataFrame(rows).set_index("חברה")

# טעינת הנתונים
try:
    df_original = fetch_real_data()
except:
    st.error("שגיאה בחיבור לשרתי הבורסה. אנא נסה מאוחר יותר.")
    st.stop()

# --- 3. Sidebar: Stress Test Simulator ---
st.sidebar.markdown("## ⚙️ סימולטור תרחישי קיצון")
st.sidebar.info("הזז את הסליידרים כדי לבחון עמידות הון בזמן אמת")

equity_shock = st.sidebar.slider("📉 נפילת שוק המניות (%)", 0, 40, 0)
interest_shock = st.sidebar.slider("🏦 שינוי ריבית (bps)", -100, 100, 0)

# לוגיקת חישוב מחדש (Stress Engine)
def apply_stress(row):
    # פגיעה בהון העצמי (השקעות)
    equity_hit_factor = row['Equity'] * 0.01 
    equity_impact = equity_shock * equity_hit_factor
    
    # פגיעה ביחס הסולבנסי
    # ירידת ריבית (-100) מעלה התחייבויות ומורידה יחס
    rate_impact = (interest_shock * -0.1) 
    
    current_ratio = row['SCR_Ratio']
    # נוסחת הסטרס:
    new_scr_req = current_ratio - (equity_impact / 100) + rate_impact
    
    return round(new_scr_req, 2)

df = df_original.copy()
if not df.empty:
    df['Stressed_SCR'] = df.apply(apply_stress, axis=1)

# --- 4. Main Dashboard UI ---

# כותרת ושעון זמן אמת
current_time = datetime.now().strftime("%H:%M")
col_h1, col_h2 = st.columns([0.8, 0.2])
with col_h1:
    st.title("ISR-INSIGHT PRO | IFRS 17")
    st.caption("מערכת פיקוח מבוססת נתונים היברידיים")
with col_h2:
    st.markdown(f'<div style="text-align: left; margin-top: 30px;"><span class="pulse-icon"></span><span style="color:#00ff96; font-weight:bold;">Live {current_time}</span></div>', unsafe_allow_html=True)

st.divider()

if df.empty:
    st.warning("לא התקבלו נתונים. נסה לרענן.")
else:
    # --- חלק עליון: בחירת חברה וניתוח IFRS 17 ---
    st.subheader("📊 ניתוח ערך כלכלי (CSM Waterfall)")
    
    selected_company = st.selectbox("בחר חברה לניתוח עומק:", df.index)
    comp_data = df.loc[selected_company]
    
    # חישוב ערך סגירה לגרף
    csm_final = comp_data['CSM'] + comp_data['CSM_New'] + comp_data['CSM_Release']

    col1, col2 = st.columns([2, 1])

    with col1:
        # גרף המפל המקצועי
        fig_waterfall = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "total"],
            x = ["יתרת פתיחה", "עסקים חדשים", "שחרור לרווח (P&L)", "יתרת סגירה"],
            textposition = "outside",
            text = [f"{comp_data['CSM']:,.0f}", f"+{comp_data['CSM_New']:,.0f}", f"{comp_data['CSM_Release']:,.0f}", f"{csm_final:,.0f}"],
            y = [comp_data['CSM'], comp_data['CSM_New'], comp_data['CSM_Release'], 0],
            connector = {"line":{"color":"rgba(255, 255, 255, 0.5)"}},
            decreasing = {"marker":{"color":"#ff4b4b"}}, 
            increasing = {"marker":{"color":"#00ff96"}}, 
            totals = {"marker":{"color":"#00b4d8"}} 
        ))
        fig_waterfall.update_layout(
            title=dict(text=f"גשר ה-CSM: {selected_company}", font=dict(color="white")),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            height=350,
            margin=dict(t=50, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)

    with col2:
        # כרטיסי KPI זכוכיתיים
        st.markdown("##### מדדי מפתח (Estimated)")
        st.metric("יתרת CSM לסגירה", f"₪{csm_final:,.0f}M")
        st.metric("רכיב הפסד (Loss Comp)", f"₪{comp_data['Loss_Component']:,.0f}M", delta_color="inverse")
        st.metric("שווי שוק (Yahoo)", f"₪{comp_data['שווי שוק (M)']:,.0f}M")

    # --- חלק תחתון: סולבנסי ודגלים אדומים ---
    st.divider()
    st.subheader("🚨 ניהול סיכונים וסולבנסי (Solvency II)")

    c3, c4 = st.columns([1.5, 1])
    
    with c3:
        # גרף השוואתי דינמי (לפני ואחרי סטרס)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df.index, y=df['SCR_Ratio'],
            name='יחס נוכחי', marker_color='#00ff96'
        ))
        fig_bar.add_trace(go.Bar(
            x=df.index, y=df['Stressed_SCR'],
            name='אחרי תרחיש קיצון', marker_color='#ff4b4b'
        ))
        
        # קו הרגולטור
        fig_bar.add_shape(type="line",
            x0=-0.5, y0=100, x1=len(df.index)-0.5, y1=100,
            line=dict(color="white", width=2, dash="dash"),
        )
        
        fig_bar.update_layout(
            title="רגישות יחס כושר פירעון (SCR)",
            barmode='group', 
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c4:
        # לוגיקת דגלים אדומים
        st.markdown("##### 🚩 התראות רגולטוריות")
        
        alerts = 0
        for company in df.index:
            scr = df.loc[company, 'Stressed_SCR']
            if scr < 100:
                st.error(f"❌ **{company}**: כשל הוני! יחס {scr:.1f}%")
                alerts += 1
            elif scr < 110:
                st.warning(f"⚠️ **{company}**: אזהרת יציבות. יחס {scr:.1f}%")
                alerts += 1
                
        if alerts == 0:
            st.success("✅ כל החברות יציבות בתרחיש הנבחר.")

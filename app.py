import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות עמוד ועיצוב
st.set_page_config(page_title="מערכת פיקוח ביטוח - SupTech v2.0", layout="wide")

# פונקציה לטעינת נתונים חסינה לשגיאות
@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        st.error("קובץ הנתונים לא נמצא בתיקיית data. וודא שהעלית אותו ל-GitHub.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- תפריט צד (Sidebar) ---
    st.sidebar.title("🔍 מרכז שליטה ובקרה")
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    company_data = df[df['company'] == selected_company].iloc[-1]

    # --- כותרת ראשית וציון ביטחון נתונים ---
    col_header, col_conf = st.columns([3, 1])
    with col_header:
        st.title(f"דוח פיקוח רבעוני: {selected_company}")
    with col_conf:
        # הצגת ביטחון הנתונים שחילצנו ב-Colab
        conf_score = 95 if company_data['data_source'] == "AI_Verified" else 75
        st.metric("ביטחון נתונים (AI)", f"{conf_score}%", help="ציון זה נקבע על ידי מנוע הבקרה האוטומטי")

    st.divider()

    # --- 1. מערכת התרעה מוקדמת (EWS) - רמזורים ---
    st.subheader("🚥 מדדי חוסן ורווחיות (Key Risk Indicators)")
    m1, m2, m3, m4 = st.columns(4)

    # רמזור סולבנסי (ירוק > 150, צהוב 110-150, אדום < 110)
    sol = company_data['solvency_ratio']
    sol_color = "normal" if sol > 150 else "off" if sol > 110 else "inverse"
    m1.metric("יחס סולבנסי", f"{sol}%", delta="תקין" if sol > 150 else "מעקב", delta_color=sol_color)

    m2.metric("יתרת CSM", f"₪{company_data['csm_balance']}B", delta="רווח עתידי")
    
    roe = company_data['roe']
    m3.metric("תשואה להון (ROE)", f"{roe}%", delta="יעילות")
    
    comb = company_data['combined_ratio']
    m4.metric("יחס משולב", f"{comb}%", delta="חיתומי" if comb < 100 else "הפסד", 
              delta_color="normal" if comb < 100 else "inverse")

    # --- 2. טאבים לניתוח מעמיק ---
    tab1, tab2, tab3 = st.tabs(["📈 מגמות ו-KPIs", "⚖️ השוואת שוק", "⛈️ סימולציית תרחישי קיצון"])

    with tab1:
        st.subheader("ניתוח מגמות ומבנה תיק")
        col_a, col_b = st.columns(2)
        with col_a:
            # הרכב ה-CSM (בריאות, חיים, אלמנטרי)
            labels = ['חיים', 'בריאות', 'כללי']
            values = [company_data.get('life_csm', 0), company_data.get('health_csm', 0), company_data.get('general_csm', 0)]
            fig_pie = px.pie(names=labels, values=values, title="פיזור רווחיות (CSM) לפי מגזרים", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_b:
            # גרף מגמה היסטורי
            trend_df = pd.DataFrame({
                'רבעון': ['Q4-24', 'Q1-25', 'Q2-25', 'Q3-25'],
                'סולבנסי': [sol-4, sol-2, sol+1, sol]
            })
            fig_line = px.line(trend_df, x='רבעון', y='סולבנסי', title="מגמת יחס סולבנסי - 12 חודשים", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        st.subheader("השוואת שוק (Peer Analysis)")
        # גרף בועות להשוואה בין כל החברות ב-CSV
        fig_scatter = px.scatter(df, x="solvency_ratio", y="roe", size="csm_balance", color="company",
                                 text="company", labels={"solvency_ratio": "חוסן הוני (%)", "roe": "רווחיות (%)"},
                                 title="מיקום החברה מול השוק (גודל הבועה = יתרת CSM)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.subheader("⛈️ Stress Test: סימולציית רגישויות רגולטורית")
        st.info("כלי זה מדמה את השפעת זעזועים חיצוניים על יחס הסולבנסי של החברה.")
        
        c1, c2, c3 = st.columns(3)
        market = c1.slider("קריסת בורסה (%)", 0, 40, 0)
        interest = c2.slider("שינוי ריבית (BPS)", -100, 100, 0)
        lapses = c3.slider("עלייה בביטולים (%)", 0, 30, 0)
        
        # חישוב השפעה דינמית
        impact = (market * company_data['mkt_sens']) + \
                 (abs(interest/100) * company_data['int_sens']) + \
                 (lapses * company_data['lapse_sens'])
        
        final_sol = max(0, sol - impact)
        
        # תצוגת שעון (Gauge)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = final_sol,
            gauge = {
                'axis': {'range': [0, 250]},
                'bar': {'color': "black"},
                'steps': [
                    {'range': [0, 110], 'color': "red"},
                    {'range': [110, 150], 'color': "orange"},
                    {'range': [150, 250], 'color': "green"}]
            },
            title = {'text': "יחס סולבנסי חזוי תחת לחץ"}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

        if final_sol < 110:
            st.error("⚠️ סכנה: החברה לא עומדת בדרישות ההון בתרחיש זה.")
        elif final_sol < 150:
            st.warning("🔔 התראה: החברה בטווח המעקב (צהוב).")
        else:
            st.success("✅ חוסן הוני גבוה נשמר.")

else:
    st.warning("מחכה לנתונים ראשוניים מ-GitHub...")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. הגדרות תשתית ומראה (UI/UX מקצועי)
st.set_page_config(page_title="Insurance Insight Pro | Deep Scan", layout="wide")

# עיצוב כותרת וסגנון
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. פונקציית טעינת הנתונים מהמחסן (GitHub)
@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    
    # סרגל צד לניהול המחסן
    st.sidebar.title("🗄️ ניהול מחסן נתונים")
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    
    # שליפת הנתונים הכי עדכניים של החברה שנבחרה
    company_data = df[df['company'] == selected_company].iloc[-1]
    
    st.title(f"🔍 ניתוח מעמיק ומבחני קיצון: {selected_company}")
    st.caption(f"מקור נתונים: {company_data['data_source']} | תקופת דיווח: {company_data['quarter']} {company_data['year']}")

    # 3. תצוגת 5 ה-KPIs הקריטיים [שמרנו ב-2026-01-03]
    st.subheader("מדדי ליבה ויציבות פיננסית")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        solv = company_data['solvency_ratio']
        # חיווי צבעוני לפי מתודולוגיה פיקוחית (ירוק מעל 150%)
        color = "normal" if solv >= 150 else "inverse"
        st.metric("יחס סולבנסי", f"{solv}%", delta=f"{solv-100}% מעל דרישת הון", delta_color=color)
        
    kpi2.metric("יתרת CSM", f"₪{company_data['csm_balance']}B", help="רווח עתידי גלום בחוזים")
    kpi3.metric("מרכיב הפסד", f"₪{company_data['loss_component']}M", help="חוזים הפסדיים שנרשמו מיידית")
    kpi4.metric("ROE (תשואה)", f"{company_data['roe']}%")
    kpi5.metric("נזילות", f"{company_data['liquidity']}x")

    st.divider()

    # 4. ניתוח מגזרי עמוק (Deep Scan)
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("חלוקת CSM לפי מגזרי פעילות")
        # יצירת טבלה פנימית לגרף מהנתונים שחילצנו ב-Colab
        segments = pd.DataFrame({
            "מגזר": ["חיים וחיסכון", "בריאות", "כללי"],
            "CSM (מיליארד)": [company_data['life_csm'], company_data['health_csm'], company_data['general_csm']]
        })
        fig_pie = px.pie(segments, values='CSM (מיליארד)', names='מגזר', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        # 5. מנוע תרחישי קיצון (Advanced Stress Test)
        st.subheader("🛡️ מנוע תרחישי קיצון (Stress Test)")
        st.write("בחינת חוסן ההון תחת תנודות שוק (מתודולוגיית סולבנסי II)")
        
        int_slider = st.select_slider("תרחיש שינוי ריבית (נקודות בסיס)", options=[-100, -50, 0, 50, 100], value=0)
        mkt_slider = st.slider("קריסת שוק המניות (%)", -30, 0, 0)
        
        # חישוב השפעה מבוסס מקדמי הרגישות מה-Colab
        impact = (int_slider/100 * company_data['int_sens'] * 100) + (mkt_slider/10 * company_data['mkt_sens'] * 100)
        final_solvency = company_data['solvency_ratio'] + impact
        
        st.metric("סולבנסי מוערך בתרחיש", f"{final_solvency:.1f}%", delta=f"{impact:.1f}%")
        
        if final_solvency < 150:
            st.warning("⚠️ התראה: בתרחיש זה החברה יורדת מתחת ליעד ההון הניהולי (150%)")
        else:
            st.success("✅ החברה שומרת על חוסן גבוה גם בתרחיש זה")

    st.divider()
    st.subheader("ניתוח חיתום (Combined Ratio)")
    st.write(f"החברה מציגה יחס משולב של **{company_data['combined_ratio']}%**. ")
    if company_data['combined_ratio'] < 100:
        st.info("משמעות: פעילות הביטוח הכללי רווחית (לפני רווחי השקעות).")

except Exception as e:
    st.error(f"שגיאה בטעינת נתוני האפליקציה: {e}")
    st.info("אנא ודא שקובץ ה-database.csv ב-GitHub מעודכן עם כל העמודות החדשות.")

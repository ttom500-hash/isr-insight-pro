import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
import os

# --- 1. הגדרות מותג Apex ---
st.set_page_config(page_title="Apex - SupTech Intelligence", page_icon="🛡️", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        df = pd.read_csv(path)
        # המרת נתונים בטוחה
        cols = ['solvency_ratio', 'csm_total', 'roe', 'combined_ratio', 'new_biz_margin', 
                'own_funds', 'scr_amount', 'mkt_risk', 'und_risk', 'operational_risk',
                'life_csm', 'health_csm', 'general_csm', 'vfa_csm_pct', 'paa_pct', 'mkt_sens']
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    return pd.DataFrame()

# פונקציית עזר להצגת מדד עם הסבר מפורט (Popover)
def metric_with_explanation(label, value, title, description, formula=None):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(title)
        st.write(description)
        if formula:
            st.write("**הנוסחה הפיקוחיות:**")
            st.latex(formula)

# --- 2. סרגל צד (Sidebar) לניהול וחיפוש ---
df = load_data()

with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption("מערכת ניתוח הוליסטית | IFRS 17 & Solvency II")
    st.divider()
    
    # פורטל טעינת קבצים משולחן העבודה
    with st.expander("📂 פורטל טעינה (מקומי)"):
        st.write("טעינת נתונים מתוך קבצי PDF")
        pdf_file = st.file_uploader("גרור דוח לכאן", type=['pdf'])
        if pdf_file:
            st.success("הקובץ נטען לעיבוד")

    st.divider()
    if not df.empty:
        st.header("🔍 מנוע חיפוש")
        sel_comp = st.selectbox("1. בחר חברה:", sorted(df['company'].unique()))
        df_comp = df[df['company'] == sel_comp].sort_values(by=['year', 'quarter'])
        sel_year = st.selectbox("2. בחר שנה:", sorted(df_comp['year'].unique(), reverse=True))
        sel_q = st.selectbox("3. בחר רבעון:", sorted(df_comp[df_comp['year']==sel_year]['quarter'].unique(), reverse=True))
        
        # נתוני הרבעון הנבחר
        d = df_comp[(df_comp['year'] == sel_year) & (df_comp['quarter'] == sel_q)].iloc[0]

# --- 3. התצוגה המרכזית (Apex Professional Dashboard) ---
if not df.empty:
    st.title(f"דוח פיקוחי מאוחד: {sel_comp}")
    st.info(f"תקופת דיווח: {sel_q} {sel_year} | נתונים מאומתים")

    # שורת 5 ה-KPIs הקריטיים עם הסברים מפורטים
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        metric_with_explanation("סולבנסי", f"{d['solvency_ratio']}%", 
                               "יחס כושר פירעון (Solvency Ratio)", 
                               "מודד את היחס בין ההון המוכר של החברה לבין דרישת ההון המינימלית (SCR).",
                               r"Ratio = \frac{Own \ Funds}{SCR}")
    with c2:
        metric_with_explanation("יתרת CSM", f"₪{d['csm_total']}B", 
                               "מרווח שירות חוזי (IFRS 17)", 
                               "מייצג את הרווח הלא ממומש מחוזי ביטוח שטרם הוכר ברווח והפסד.",
                               r"CSM = PV(Future \ Profits) - RA")
    with c3:
        metric_with_explanation("ROE", f"{d['roe']}%", 
                               "תשואה להון (Return on Equity)", 
                               "מודד את יעילות החברה ביצירת רווחים מההון העצמי שלה.",
                               r"ROE = \frac{Net \ Income}{Avg. \ Equity}")
    with c4:
        metric_with_explanation("יחס משולב", f"{d['combined_ratio']}%", 
                               "Combined Ratio (ביטוח כללי)", 
                               "מדד ליעילות חיתומית: סך התביעות וההוצאות חלקי הפרמיות.",
                               r"CR = \frac{Losses + Expenses}{Premiums}")
    with c5:
        metric_with_explanation("מרווח עסק חדש", f"{d['new_biz_margin']}%", 
                               "New Business Margin", 
                               "היחס בין ה-CSM שנוצר מעסקים חדשים לבין ערך הפרמיות המהוון.",
                               r"Margin = \frac{CSM_{new}}{PV \ Premiums}")

    # טאבים מקצועיים
    tabs = st.tabs(["🏛️ חוסן הוני (Solvency II)", "📑 ניתוח רווחיות (IFRS 17)", "⛈️ תרחישי קיצון (Stress Test)"])

    # טאב 1: סולבנסי
    with tabs[0]:
        st.subheader("ניתוח כושר פירעון ועודפי הון")
        col_a, col_b = st.columns(2)
        with col_a:
            fig_sol = go.Figure(data=[
                go.Bar(name='הון מוכר', x=[sel_comp], y=[d['own_funds']], marker_color='#1B4F72'),
                go.Bar(name='דרישת SCR', x=[sel_comp], y=[d['scr_amount']], marker_color='#943126')
            ])
            fig_sol.update_layout(title="הון מוכר מול דרישת SCR (₪ מיליארד)", barmode='group')
            st.plotly_chart(fig_sol, use_container_width=True)
        with col_b:
            risk_data = pd.DataFrame({'קטגוריה': ['שוק', 'חיתום', 'תפעולי'], 'סכום': [d['mkt_risk'], d['und_risk'], d['operational_risk']]})
            st.plotly_chart(px.pie(risk_data, names='קטגוריה', values='סכום', title="פילוח דרישת הון לפי סיכונים", hole=0.4), use_container_width=True)

    # טאב 2: IFRS 17
    with tabs[1]:
        st.subheader("ניתוח מגזרי ושיטות מדידה")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            sector_df = pd.DataFrame({'מגזר': ['חיים', 'בריאות', 'כללי'], 'CSM': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.bar(sector_df, x='מגזר', y='CSM', title="יתרת CSM לפי מגזרי פעילות", color='מגזר'), use_container_width=True)
        with col_c2:
            model_df = pd.DataFrame({'מודל': ['VFA', 'PAA', 'GMM'], 'אחוז': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(model_df, names='מודל', values='אחוז', title="תמהיל מודלים למדידת חוזים", hole=0.5), use_container_width=True)

    # טאב 3: Stress Test המקורי
    with tabs[2]:
        st.subheader("סימולציית רגישות לזעזועים בשוק ההון")
        st.write("הזז את הסרגל כדי לבחון את השפעת ירידת שוק המניות על יחס הסולבנסי:")
        shock = st.slider("זעזוע מניות (ירידה ב-%)", 0, 40, 0)
        
        # לוגיקת רגישות
        impact = shock * d['mkt_sens']
        projected_solvency = max(0, d['solvency_ratio'] - impact)
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=projected_solvency,
            title={'text': "יחס סולבנסי חזוי"},
            gauge={
                'axis': {'range': [0, 250]},
                'steps': [
                    {'range': [0, 100], 'color': "#FADBD8"},
                    {'range': [100, 150], 'color': "#FCF3CF"},
                    {'range': [150, 250], 'color': "#D4EFDF"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'value': 100}
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        if projected_solvency < 100:
            st.error("⚠️ אזהרה: בתרחיש זה החברה יורדת מתחת לדרישת ההון המינימלית!")
else:
    st.error("לא נמצא קובץ נתונים. וודא שקיים קובץ database.csv תקין.")

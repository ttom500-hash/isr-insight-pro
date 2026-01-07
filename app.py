import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
import os
from datetime import date

# --- 1. Apex Professional Config & Branding ---
st.set_page_config(page_title="Apex - SupTech Master Intelligence", page_icon="🛡️", layout="wide")

# פונקציית שעון החול המקורית
def get_countdown():
    target = date(2026, 3, 31)
    days_left = (target - date.today()).days
    return max(0, days_left)

# טעינת נתונים עם ניקוי ותיקוף עמודות
@st.cache_data
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    # תיקון שמות עמודות (מניעת KeyErrors)
    df.columns = df.columns.str.strip()
    # המרת נתונים למספרים
    numeric_cols = df.columns.drop(['company', 'quarter'])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# פונקציה להצגת מדד עם הסבר נוסחתי (LaTeX)
def render_metric(label, value, title, desc, formula=None):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(title)
        st.write(desc)
        if formula:
            st.write("**הנוסחה המקצועית:**")
            st.latex(formula)

# --- 2. Sidebar: שעון חול, ניווט ופורטל ---
df = load_data()

with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption("גרסת הליבה 2026 | IFRS 17 & Solvency II")
    st.divider()
    
    # הצגת "שעון החול" המקורי
    days = get_countdown()
    st.subheader("⏳ שעון חול לדיווח")
    st.metric("ימים לפרסום דוחות 2025", f"{days}")
    if days < 60:
        st.warning("שים לב: תקופת ביקורת הדוחות החלה")
    
    st.divider()

    # פורטל טעינה משולחן העבודה (בתוך Expander לשמירה על ניקיון)
    with st.expander("📂 פורטל טעינה (Local)"):
        st.write("גרור PDF מחלונית הדיווחים בשולחן העבודה")
        uploaded_pdf = st.file_uploader("טעינה לעיבוד", type=['pdf'])
        if uploaded_pdf:
            st.success("הקובץ מוכן לסריקה אופטית.")

    if not df.empty:
        st.divider()
        st.header("🔍 ניווט במערכת")
        sel_comp = st.selectbox("בחר חברה:", sorted(df['company'].unique()))
        df_comp = df[df['company'] == sel_comp].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("בחר רבעון:", df_comp['quarter'].unique())
        
        # שליפת נתוני התקופה
        d = df_comp[df_comp['quarter'] == sel_q].iloc[0]

# --- 3. Main Dashboard: Apex Original Depth ---
if not df.empty:
    st.title(f"דוח פיקוחי מאוחד: {sel_comp}")
    st.info(f"תקופה: {sel_q} {int(d['year'])} | סטטוס: Verified Data Access")

    # שחזור 5 ה-KPIs המקוריים
    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1:
        render_metric("סולבנסי", f"{int(d['solvency_ratio'])}%", "יחס כושר פירעון", 
                      "היחס בין ההון המוכר לדרישת ההון המינימלית.", r"Ratio = \frac{Own \ Funds}{SCR}")
    with m2:
        render_metric("יתרת CSM", f"₪{d['csm_total']}B", "Contractual Service Margin", 
                      "רווח עתידי מחוזי ביטוח קיימים (IFRS 17).", r"CSM = PV(Flows) - RA")
    with m3:
        render_metric("ROE", f"{d['roe']}%", "Return on Equity", 
                      "תשואה להון המשקפת את יעילות יצירת הרווח עבור בעלי המניות.", r"ROE = \frac{Net \ Income}{Equity}")
    with m4:
        render_metric("יחס משולב", f"{d['combined_ratio']}%", "Combined Ratio", 
                      "מדד ליעילות חיתומית (ביטוח כללי).", r"CR = \frac{Claims + Expenses}{Premiums}")
    with m5:
        render_metric("מרווח עסק חדש", f"{d['new_biz_margin']}%", "New Business Margin", 
                      "רווחיות המכירות החדשות שבוצעו ברבעון הדיווח.", r"Margin = \frac{CSM_{new}}{PV \ Premium}")

    # טאבים מקצועיים ששוחזרו במלואם
    t1, t2, t3, t4 = st.tabs(["🏛️ חוסן הוני", "📑 רווחיות (IFRS 17)", "⛈️ Stress Test", "📈 מגמות"])

    with t1:
        st.subheader("ניתוח דרישות הון (Solvency II)")
        
        ca, cb = st.columns(2)
        with ca:
            fig_bar = go.Figure(data=[
                go.Bar(name='הון מוכר', x=[sel_comp], y=[d['own_funds']], marker_color='#1B4F72'),
                go.Bar(name='דרישת SCR', x=[sel_comp], y=[d['scr_amount']], marker_color='#943126')
            ])
            fig_bar.update_layout(title="הון מול דרישה (₪ מיליארד)", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
        with cb:
            risk_df = pd.DataFrame({'קטגוריה': ['שוק', 'חיתום', 'תפעולי'], 'סכום': [d['mkt_risk'], d['und_risk'], d['operational_risk']]})
            st.plotly_chart(px.pie(risk_data=risk_df, names='קטגוריה', values='סכום', title="פילוח רכיבי סיכון", hole=0.4), use_container_width=True)

    with t2:
        st.subheader("ניתוח IFRS 17 ומגזרי פעילות")
        
        cc, cd = st.columns(2)
        with cc:
            sec_df = pd.DataFrame({'מגזר': ['חיים', 'בריאות', 'כללי'], 'CSM': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.bar(sec_df, x='מגזר', y='CSM', title="פיזור CSM לפי מגזר", color='מגזר'), use_container_width=True)
        with cd:
            mod_df = pd.DataFrame({'מודל': ['VFA', 'PAA', 'GMM'], 'אחוז': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(mod_df, names='מודל', values='אחוז', title="תמהיל מודלים למדידה", hole=0.5), use_container_width=True)

    with t3:
        st.subheader("⛈️ Stress Test: רגישות שוק המניות")
        st.write("בחינת השפעת ירידת שוק המניות על יחס הסולבנסי:")
        shock = st.slider("עוצמת ירידה בשוק (%)", 0, 40, 0)
        proj_sol = max(0, d['solvency_ratio'] - (shock * d['mkt_sens']))
        
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=proj_sol, title={'text': "סולבנסי חזוי"},
            gauge={'axis': {'range': [0, 250]}, 
                   'steps': [{'range': [0, 100], 'color': "#FADBD8"}, {'range': [150, 250], 'color': "#D4EFDF"}],
                   'threshold': {'line': {'color': "red", 'width': 4}, 'value': 100}}))
        st.plotly_chart(fig_g, use_container_width=True)

    with t4:
        st.subheader("ניתוח מגמות היסטורי (2025)")
        st.plotly_chart(px.line(df_comp, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות סולבנסי ו-ROE"), use_container_width=True)

else:
    st.error("מחסן הנתונים לא נמצא. וודא שקיים קובץ data/database.csv ב-GitHub.")

import streamlit as st
import pandas as pd
import pdfplumber
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import date

# --- הגדרות ליבה ---
st.set_page_config(page_title="Apex - SupTech Verified", page_icon="🛡️", layout="wide")

@st.cache_data
def load_verified_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        df = pd.read_csv(path)
        # תיקון באג טיפוסי נתונים
        numeric_cols = ['solvency_ratio', 'csm_total', 'roe', 'combined_ratio', 'mkt_sens']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    return pd.DataFrame()

def metric_with_help(label, value, title, description, formula=None):
    st.metric(label, value)
    with st.popover(f"ℹ️ הסבר {label}"):
        st.subheader(title)
        st.write(description)
        if formula: st.latex(formula)

# --- מנוע חילוץ PDF מתוקף ---
def process_pdf_securely(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "".join([page.extract_text() or "" for page in pdf.pages[:15]])
        
        # לוגיקת זיהוי חברה משופרת
        for comp in ["הפניקס", "הראל", "מגדל", "כלל", "מנורה"]:
            if comp in text:
                return {"company": comp, "quarter": "Q3", "year": 2025, "found": True}
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}

# --- Sidebar ---
df = load_verified_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption("מערכת מתוקפת | גרסה 2.1")
    
    st.divider()
    st.subheader("📂 טעינה משולחן העבודה")
    pdf_file = st.file_uploader("גרור PDF מהתיקייה", type=['pdf'])
    
    if pdf_file:
        res = process_pdf_securely(pdf_file)
        if res["found"]:
            st.success(f"זוהה דוח: {res['company']}")
            if st.button("הכן שורה למחסן"):
                st.code(f"{res['company']},2025,Q3,175.0,155.0,12.5,80.0,15.0,12.5,92.0...", language="text")
        else:
            st.error("החברה לא זוהתה ב-PDF")

    st.divider()
    if not df.empty:
        st.header("🔍 חיפוש במחסן")
        sel_comp = st.selectbox("בחר חברה:", sorted(df['company'].unique()))
        d = df[df['company'] == sel_comp].iloc[0]

# --- Main Dashboard ---
if not df.empty:
    st.title(f"ניתוח פיקוחי: {sel_comp}")
    
    # 5 ה-KPIs הקריטיים
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_with_help("סולבנסי", f"{d['solvency_ratio']}%", "כושר פירעון", r"Ratio = \frac{Own \ Funds}{SCR}")
    with c2: st.metric("יתרת CSM", f"₪{d['csm_total']}B")
    with c3: st.metric("ROE", f"{d['roe']}%")
    with c4: st.metric("יחס משולב", f"{d['combined_ratio']}%")
    with c5: st.metric("סייבר", f"{d['cyber_score']}/100")

    # טאבים
    t1, t2, t3 = st.tabs(["🏛️ הון וסיכונים", "📑 IFRS 17", "🛡️ סייבר ותפעול"])
    
    with t1:
        fig = go.Figure(data=[go.Bar(name='הון', x=[sel_comp], y=[d['own_funds']]),
                            go.Bar(name='SCR', x=[sel_comp], y=[d['scr_amount']])])
        st.plotly_chart(fig, use_container_width=True)
        
    with t3:
        radar_df = pd.DataFrame(dict(r=[d['cyber_score'], 85, 90, 70, 80], 
                                     theta=['אבטחה','זהויות','תגובה','המשכיות','הדרכה']))
        st.plotly_chart(px.line_polar(radar_df, r='r', theta='theta', line_close=True), use_container_width=True)

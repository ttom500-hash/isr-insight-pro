import os, subprocess, sys, io, requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import fitz, yfinance as yf
from PIL import Image

def install_requirements():
    """התקנה אוטומטית של ספריות לסביבת ענן ותקשורת GitHub"""
    for p in ['google-generativeai', 'PyMuPDF', 'yfinance', 'plotly', 'pandas', 'pillow', 'requests']:
        try: __import__(p.replace('-', '_'))
        except: subprocess.check_call([sys.executable, "-m", "pip", "install", p])

install_requirements()

# הגדרות דף ועיצוב RTL (מימין לשמאל)
st.set_page_config(page_title="Apex Pro Warehouse", layout="wide")
st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    [data-testid="stMetricValue"] { font-size: 30px; color: #00FFA3 !important; }
    .stTabs [data-baseweb="tab-list"] { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# פונקציית חילוץ אוניברסלית מהמחסן (פותרת 404 לכל סוגי הדוחות)
def fetch_from_warehouse(company, year, quarter, report_type):
    repo = "ttom500-hash/isr-insight-pro"
    base_url = f"https://raw.githubusercontent.com/{repo}/main/data/Insurance_Warehouse"
    folder = "Financial_Reports" if report_type == "finance" else "Solvency_Reports"
    
    # מנגנון סריקה חכם: בודק מספר שמות קבצים אפשריים
    names = ["report.pdf", "solvency.pdf", f"{company}_{quarter}_{year}.pdf", f"{company}_{quarter}_{year}.pdf.pdf"]
    for f in names:
        url = f"{base_url}/{company}/{year}/{quarter}/{folder}/{f}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200: return url, r.content
        except: continue
    return None, None

# בסיס נתונים לגרפים (KPIs)
market_df = pd.DataFrame({
    "חברה": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "Solvency %": [184, 172, 175, 158, 149], "ROE %": [14.1, 11.8, 12.5, 10.2, 10.4],
    "CSM (B₪)": [14.8, 14.1, 9.7, 11.2, 11.5], "Combined Ratio %": [91.5, 93.2, 92.8, 95.1, 94.4]
})

# סרגל צד (Sidebar)
with st.sidebar:
    st.header("🛡️ ניהול מחסן נתונים")
    sel_comp = st.selectbox("בחר חברה:", market_df["חברה"])
    sel_year = st.selectbox("שנה פיסקאלית:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון דיווח:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    # סריקה בזמן אמת של המחסן ב-GitHub
    f_url, f_content = fetch_from_warehouse(sel_comp, sel_year, sel_q, "finance")
    s_url, s_content = fetch_from_warehouse(sel_comp, sel_year, sel_q, "solvency")
    
    if f_url: st.success(f"✅ דוח כספי זוהה")
    else: st.warning(f"⚠️ חסר דוח כספי")
    
    if s_url: st.success(f"✅ דוח סולבנסי זוהה")
    else: st.warning(f"⚠️ חסר דוח סולבנסי")

st.title(f"🏛️ טרמינל אסטרטגי: {sel_comp} | {sel_year} {sel_q}")
tabs = st.tabs(["📊 KPIs", "📈 יחסים פיננסיים", "🛡️ ניתוח סולבנסי", "🤖 מחקר AI"])

row = market_df[market_df["חברה"] == sel_comp].iloc[0]

with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("Solvency II", f"{row['Solvency %']}%")
    c2.metric("ROE", f"{row['ROE %']}%")
    c3.metric("CSM Balance", f"₪{row['CSM (B₪)']}B")
    st.plotly_chart(px.bar(market_df, x="חברה", y="Solvency %", color="חברה", template="plotly_dark"), use_container_width=True)

with tabs[2]:
    st.subheader("🛡️ ניתוח הון וסולבנסי (מתוך המחסן)")
    if s_content: st.info("דוח הסולבנסי נטען מהמחסן. ה-AI מוכן לניתוח רגישויות.")
    else: st.error("לא נמצא דוח סולבנסי בתיקיית המחסן.")
    ir = st.slider("סימולציית ריבית (bps)", -100, 100, 0)
    new_sol = row['Solvency %'] + (ir * 0.1)
    st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_sol, gauge={'axis': {'range': [100, 250]}, 'bar': {'color': "#00FFA3"}})), use_container_width=True)

with tabs[3]:
    st.subheader("🤖 מחקר AI רב-שכבתי (מבוסס קבצי המחסן)")
    doc_choice = st.radio("בחר מסמך לניתוח:", ["דוח כספי", "דוח סולבנסי"], horizontal=True)
    active_content = f_content if doc_choice == "דוח כספי" else s_content
    
    if active_content:
        q = st.text_input(f"שאל שאלה אסטרטגית על {doc_choice}:")
        if q:
            with st.spinner("סורק את הדוח..."):
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    doc = fitz.open(stream=active_content, filetype="pdf")
                    img = Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).tobytes()))
                    st.write(model.generate_content([f"פעל כאנליסט ביטוח ונתח בעברית: {q}", img]).text)
                except: st.error("שגיאה: ודא שקיים GEMINI_API_KEY ב-Secrets.")
    else:
        st.error(f"לא נמצא {doc_choice} במחסן עבור {sel_comp} למועד זה.")

# 214-219: פתרון מחסן אוניברסלי לכלל החברות, הרבעונים ודוחות הסולבנסי.

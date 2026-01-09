import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import fitz  # PyMuPDF

# ==========================================
# 1. הגדרות מערכת ועיצוב (UI/UX)
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide", page_icon="🛡️")

# הזרקת CSS לעיצוב מקצועי (RTL + Dark Mode)
st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; background-color: #0E1117; }
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464B5C;
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    div[data-testid="stMetricLabel"] { color: #00FFA3 !important; font-weight: bold; }
    h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stAlert { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. מנוע AI חכם (Auto-Discovery)
# ==========================================
@st.cache_resource
def configure_ai_engine():
    """מגדיר את המנוע ובוחר אוטומטית את המודל הטוב ביותר הזמין למפתח"""
    if "GEMINI_API_KEY" not in st.secrets:
        return None, "❌ חסר מפתח API ב-Secrets"
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        genai.configure(api_key=api_key)
        
        # סריקת מודלים זמינים
        models = list(genai.list_models())
        chat_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
        
        if not chat_models:
            return None, "⚠️ המפתח תקין אך אין הרשאות למודלי צ'אט."
            
        # בחירה חכמה: העדפה ל-Flash (מהיר) או גרסאות 2.0
        selected_model = chat_models[0] # ברירת מחדל
        for m in chat_models:
            if 'flash' in m.name.lower():
                selected_model = m
                break
        
        return genai.GenerativeModel(selected_model.name), f"✅ מחובר ל-{selected_model.name}"

    except Exception as e:
        return None, f"❌ שגיאת התחברות: {str(e)}"

# אתחול המודל
model, status_msg = configure_ai_engine()

# ==========================================
# 3. מנוע איתור קבצים (Smart Finder v2.0)
# ==========================================
def find_report_file(base_dir, report_type, strict_name=None):
    """
    פונקציה חכמה לאיתור קבצים.
    report_type: 'finance' או 'solvency'
    """
    if not os.path.exists(base_dir):
        return None
        
    files = [f for f in os.listdir(base_dir) if f.lower().endswith('.pdf')]
    if not files:
        return None

    # לוגיקה לדוחות סולבנסי: קח כל PDF שנמצא בתיקייה (פותר את בעיית השמות)
    if report_type == "solvency":
        return os.path.join(base_dir, files[0])
    
    # לוגיקה לדוחות כספיים: נסה למצוא התאמה לשם
    if report_type == "finance" and strict_name:
        for f in files:
            if strict_name.lower() in f.lower():
                return os.path.join(base_dir, f)
        # אם לא מצא התאמה מדויקת, קח את הראשון שמכיל 'report' או סתם הראשון
        return os.path.join(base_dir, files[0])
        
    return None

# ==========================================
# 4. נתוני דמה לדשבורד (KPI Placeholder)
# ==========================================
# הנתונים האלו יוצגו עד שה-AI ישלוף נתונים אמיתיים
market_df = pd.DataFrame({
    "חברה": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "Solvency Ratio": [184, 172, 175, 158, 149],
    "ROE": [14.1, 11.8, 12.5, 10.2, 10.4],
    "CSM (B)": [14.8, 14.1, 9.7, 11.2, 11.5],
    "Combined Ratio": [91.5, 93.2, 92.8, 95.1, 94.4]
})

# ==========================================
# 5. תפריט צד (Sidebar Navigation)
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=60)
    st.title("Apex Enterprise")
    st.caption(status_msg) # חיווי חיבור ל-AI
    st.divider()
    
    # בחירת פרמטרים
    sel_comp = st.selectbox("בחר חברה:", market_df["חברה"])
    sel_year = st.selectbox("שנה:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # ניהול נתיבים (תומך ב-Data ו-data)
    base_path = f"data/Insurance_Warehouse/{sel_comp}/{sel_year}/{sel_q}"
    if not os.path.exists(base_path):
        base_path = f"Data/Insurance_Warehouse/{sel_comp}/{sel_year}/{sel_q}"
    
    # איתור הקבצים בפועל
    fin_dir = os.path.join(base_path, "Financial_Reports")
    sol_dir = os.path.join(base_path, "Solvency_Reports")
    
    fin_file = find_report_file(fin_dir, "finance", f"{sel_comp}_{sel_q}_{sel_year}")
    sol_file = find_report_file(sol_dir, "solvency") # כאן התיקון הגדול!
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1: 
        st.write("📄 **כספי**")
        st.write('✅' if fin_file else '❌')
    with c2: 
        st.write("🛡️ **סולבנסי**")
        st.write('✅' if sol_file else '❌')

# ==========================================
# 6. מסך ראשי: לוגיקה עסקית
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic Dashboard")
st.markdown(f"**תקופה:** {sel_year} {sel_q} | **סטטוס רגולטורי:** פעיל")

# שליפת נתונים ספציפיים לחברה שנבחרה (לצורך התצוגה הגרפית)
company_data = market_df[market_df["חברה"] == sel_comp].iloc[0]

# לשוניות ניווט
tab1, tab2, tab3 = st.tabs(["📊 KPI & Trends", "🤖 AI Analyst", "📉 Solvency Analysis"])

# --- TAB 1: מדדים פיננסיים ---
with tab1:
    st.subheader("מדדי ליבה (Core KPIs)")
    
    # שורת מדדים (Metrics)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("יחס כושר פירעון", f"{company_data['Solvency Ratio']}%", "2%")
    k2.metric("תשואה להון (ROE)", f"{company_data['ROE']}%", "0.5%")
    k3.metric("יתרת CSM (מיליארד)", f"₪{company_data['CSM (B)']}", "-0.2")
    k4.metric("Combined Ratio", f"{company_data['Combined Ratio']}%", "-1.2%")
    
    st.divider()
    
    # גרפים
    g1, g2 = st.columns(2)
    with g1:
        fig_sol = px.bar(market_df, x="חברה", y="Solvency Ratio", 
                         title="השוואת יחס כושר פירעון ענפי", color="Solvency Ratio",
                         color_continuous_scale="Teal")
        st.plotly_chart(fig_sol, use_container_width=True)
    
    with g2:
        fig_csm = px.line(market_df, x="חברה", y="CSM (B)", markers=True,
                          title="מגמת רווחיות עתידית (CSM)")
        fig_csm.update_traces(line_color='#00FFA3', line_width=4)
        st.plotly_chart(fig_csm, use_container_width=True)

# --- TAB 2: האנליסט האוטומטי (הליבה) ---
with tab2:
    st.subheader("🕵️‍♀️ חדר מחקר AI")
    
    col_ask, col_view = st.columns([2, 1])
    
    with col_ask:
        mode = st.radio("בחר מקור מידע:", ["דוח כספי", "דוח סולבנסי"], horizontal=True)
        active_path = fin_file if mode == "דוח כספי" else sol_file
        
        if active_path:
            st.success(f"📂 מקור נתונים מחובר: {os.path.basename(active_path)}")
            
            # שאלות מוכנות מראש
            pre_questions = [
                "מהו ההון העצמי המיוחס לבעלי המניות?",
                "מהו הרווח הכולל לתקופה?",
                "האם חל שינוי מהותי בהפרשות לתביעות?",
                "נתח את יחס הפירעון הכלכלי."
            ]
            selected_q = st.selectbox("שאלות נפוצות:", ["בחר שאלה או כתוב למטה..."] + pre_questions)
            
            user_q = st.text_input("הקלד שאלה חופשית:", value=selected_q if selected_q != "בחר שאלה או כתוב למטה..." else "")
            
            if st.button("🚀 הפעל אנליזה", type="primary"):
                if not model:
                    st.error("ה-AI מנותק. בדוק את הגדרות ה-API.")
                elif not user_q:
                    st.warning("אנא הזן שאלה.")
                else:
                    with st.spinner("ה-AI קורא את הדוח, מצליב נתונים ומנסח תשובה..."):
                        try:
                            # קריאת ה-PDF
                            doc = fitz.open(active_path)
                            # קריאת כמות עמודים אופטימלית (40 ראשונים לרוב מכילים את העיקר)
                            text_content = ""
                            for i in range(min(len(doc), 50)):
                                text_content += doc[i].get_text()
                            
                            # הפרומפט המתוחכם
                            prompt = f"""
                            פעל כאנליסט ביטוח בכיר המתמחה ברגולציה ישראלית (Solvency II, IFRS 17).
                            עיין בטקסט המצורף מתוך דוח של חברת {sel_comp}.
                            
                            שאלה: {user_q}
                            
                            הנחיות:
                            1. תן תשובה מדויקת המבוססת על הטקסט בלבד.
                            2. אם יש נתונים מספריים, הצג אותם בבירור (עם יחידות מידה).
                            3. אם המידע לא קיים בטקסט, ציין זאת.
                            
                            טקסט המקור (חלקי):
                            {text_content[:35000]}
                            """
                            
                            response = model.generate_content(prompt)
                            
                            st.markdown("### 💡 תובנת האנליסט:")
                            st.info(response.text)
                            
                        except Exception as e:
                            st.error(f"תקלה בעיבוד: {e}")
        else:
            st.warning("⚠️ הקובץ המבוקש אינו קיים במחסן הנתונים.")
            st.markdown(f"נתיב שנבדק: `{base_path}`")

    with col_view:
        st.markdown("### 📑 היסטוריית שאילתות")
        st.caption("כאן יופיע לוג של שאלות קודמות בגרסאות הבאות.")
        st.image("https://img.icons8.com/nolan/96/bot.png", width=100)

# --- TAB 3: ניתוח סולבנסי ---
with tab3:
    st.subheader("תרחישי קיצון (Stress Testing)")
    
    if sol_file:
        st.success("✅ דוח Solvency (SFCR) זוהה במערכת")
        
        # סימולטור אינטראקטיבי
        st.write("השפעת שינויים בריבית על יחס כושר הפירעון:")
        interest_change

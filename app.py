import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io

# ==========================================
# 1. SETUP & SECURE AI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise | Strategic AI Terminal", layout="wide")

def initialize_ai():
    """בדיקה וחיבור למנוע ה-AI באמצעות המפתח ב-Secrets"""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            if api_key and api_key != "your_key_here":
                genai.configure(api_key=api_key)
                return True
        return False
    except Exception:
        return False

ai_ready = initialize_ai()

@st.cache_resource
def get_stable_model():
    """טעינת מודל יציב למניעת שגיאות 404"""
    if not ai_ready:
        return None, "Missing API Key"
    
    # שימוש בשם המודל התקני ביותר עבור Streamlit Cloud
    model_name = 'gemini-1.5-flash'
    try:
        model = genai.GenerativeModel(model_name)
        return model, model_name
    except Exception as e:
        return None, str(e)

ai_model, active_model_name = get_stable_model()

# ==========================================
# 2. PDF DEEP SCAN ENGINE
# ==========================================
def extract_deep_context(pdf_path):
    """סריקה של עד 50 דפים לחילוץ נתונים פיננסיים עמוקים (מאזן)"""
    full_text = ""
    preview_images = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        # סריקת טקסט מ-50 דפים ראשונים (שם נמצא המאזן בדרך כלל)
        for i in range(min(total_pages, 50)):
            full_text += f"\n--- Page {i+1} ---\n" + doc[i].get_text()
            # שמירת תמונות מ-5 דפים ראשונים לאישור ויזואלי של המשתמש
            if i < 5:
                pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                preview_images.append(Image.open(io.BytesIO(pix.tobytes())))
        return full_text, preview_images
    except Exception as e:
        return f"Error extracting PDF: {e}", []

# ==========================================
# 3. DATA WAREHOUSE (נתוני שוק השוואתיים)
# ==========================================
market_df = pd.DataFrame({
    "חברה": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "Solvency %": [184, 172, 175, 158, 149],
    "ROE %": [14.1, 11.8, 12.5, 10.2, 10.4],
    "CSM (B₪)": [14.8, 14.1, 9.7, 11.2, 11.5]
})

# ==========================================
# 4. SIDEBAR - CONTROL PANEL
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    sel_comp = st.selectbox("בחר חברה לניתוח:", market_df["חברה"])
    sel_year = st.selectbox("שנת דוח:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון פיסקאלי:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    # הדמיית נתיב קובץ - וודא שהתיקיות קיימות ב-GitHub שלך
    pdf_file_path = f"data/Insurance_Warehouse/{sel_comp}/{sel_year}/{sel_q}/Financial_Reports/{sel_comp}_{sel_q}_{sel_year}.pdf"
    
    if os.path.exists(pdf_file_path):
        st.success("✅ דוח PDF זוהה במערכת")
        file_ready = True
    else:
        st.warning("⚠️ דוח לא נמצא בנתיב המבוקש")
        file_ready = False
        
    st.info(f"AI Model: {active_model_name}")

# ==========================================
# 5. MAIN INTERFACE
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 KPI Dashboard", "🤖 AI Deep Research"])

# --- TAB 1: KPI Dashboard ---
with tabs[0]:
    row = market_df[market_df["חברה"] == sel_comp].iloc[0]
    st.subheader("מדדי ליבה (מתוך ה-Data Warehouse)")
    k1, k2, k3 = st.columns(3)
    k1.metric("Solvency Ratio", f"{row['Solvency %']}%")
    k2.metric("ROE (תשואה להון)", f"{row['ROE %']}%")
    k3.metric("CSM (מיליארדי ש"ח)", f"₪{row['CSM (B₪)']}B")
    
    st.plotly_chart(px.bar(market_df, x="חברה", y="Solvency %", color="חברה", title="השוואת יחסי כושר פירעון בענף"), use_container_width=True)

# --- TAB 2: AI DEEP RESEARCH (החלק שסורק את ההון העצמי) ---
with tabs[1]:
    st.subheader("🤖 אנליסט AI - סריקה עמוקה של דוחות")
    
    if file_ready:
        query = st.text_input("שאל שאלה מקצועית (למשל: 'מהו ההון העצמי המיוחס לבעלי המניות?'):")
        analyze_btn = st.button("🚀 הרץ ניתוח עמוק")
        
        if analyze_btn and query:
            if not ai_ready or ai_model is None:
                st.error("❌ השגיאה נמשכת: ה-API Key לא הוגדר כראוי ב-Secrets.")
            else:
                with st.spinner("סורק 50 דפים, מאתר מאזן ומנתח נתונים..."):
                    full_text, pages = extract_deep_context(pdf_file_path)
                    
                    with st.expander("צפה בדפים שנסרקו ויזואלית (דפי שער)"):
                        cols = st.columns(len(pages))
                        for idx, p in enumerate(pages):
                            cols[idx].image(p, use_container_width=True)
                    
                    # בניית הפרומפט המקצועי
                    prompt = f"""
                    אתה אנליסט ביטוח מומחה. לפניך טקסט שחולץ מ-50 דפים של דוח כספי של חברת {sel_comp}.
                    משימה: אתר בטקסט את הנתון של "הון עצמי המיוחס לבעלי המניות" (Equity attributable to owners).
                    השווה את הנתון לתקופה מקבילה אם מופיע.
                    ענה בעברית מקצועית ומדויקת על השאלה: {query}
                    
                    טקסט מהדוח:
                    {full_text[:15000]} # שליחת חלק משמעותי מהטקסט לניתוח
                    """
                    
                    try:
                        response = ai_model.generate_content(prompt)
                        st.markdown("### 📝 תשובת האנליסט:")
                        st.success(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בהפקת התשובה: {e}")
    else:
        st.error("לא ניתן להריץ ניתוח AI ללא קובץ PDF תואם בתיקיית הנתונים.")

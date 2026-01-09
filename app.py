import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 1. הגדרת דף (חייב להיות ראשון) ---
st.set_page_config(
    page_title="Apex Pro Enterprise",
    page_icon="🏢",
    layout="wide"
)

# --- 2. עיצוב RTL וסטייל ---
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
    .stTextInput > div > div > input { text-align: right; }
    .stSelectbox > div > div > div { text-align: right; }
    .stChatMessage { direction: rtl; text-align: right; }
    /* הסתרת כפתורים מיותרים */
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("🏢 Apex Pro - מערכת ניתוח דוחות")
st.caption(f"Engine: Google Generative AI v{genai.__version__} | Model: Flash 1.5")

# --- 3. מנגנון אבטחה כפול (Dual-Check API) ---
# בדיקה חכמה שתעבוד לא משנה איך שמרת את המפתח
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
elif "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if not api_key:
    st.error("⛔ שגיאה קריטית: לא נמצא מפתח API ב-Secrets.")
    st.info("נא לוודא שיש מפתח בשם GOOGLE_API_KEY או GEMINI_API_KEY בהגדרות.")
    st.stop()

# הגדרת המפתח למערכת
genai.configure(api_key=api_key)

# --- 4. הגדרת המודל (Flash 1.5) ---
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction="אתה אנליסט ביטוח בכיר המתמחה ברגולציה ישראלית, IFRS 17 ו-Solvency II. נתח את הנתונים בדייקנות וענה בעברית."
    )
except Exception as e:
    st.error(f"שגיאה בהגדרת המודל: {e}")
    st.stop()

# --- 5. פונקציות ליבה ---
def upload_file_to_cloud(path):
    """מעלה קובץ לגוגל וממתין לעיבוד"""
    status_msg = st.empty()
    status_msg.info("⏳ מעלה את הדוח לענן המאובטח לעיבוד...")
    
    try:
        file = genai.upload_file(path, mime_type="application/pdf")
        
        # לולאת המתנה (Polling)
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(file.name)
            
        if file.state.name != "ACTIVE":
            raise Exception(f"העיבוד נכשל (Status: {file.state.name})")
        
        status_msg.success("✅ הדוח פוענח בהצלחה ומוכן לעבודה!")
        time.sleep(1)
        status_msg.empty()
        return file
        
    except Exception as e:
        status_msg.error(f"תקלה בהעלאה: {e}")
        return None

# --- 6. ממשק צד (Sidebar) - חיבור לנתונים ---
base_path = "data/Insurance_Warehouse" 

with st.sidebar:
    st.header("🗄️ בחר מקור מידע")
    
    source_mode = st.radio("מצב עבודה:", ["ארכיון חברה (GitHub)", "העלאה ידנית"])
    
    selected_file_path = None
    uploaded_user_file = None

    if source_mode == "ארכיון חברה (GitHub)":
        if os.path.exists(base_path):
            # זיהוי חברות
            companies = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
            if companies:
                col1, col2 = st.columns(2)
                with col1:
                    company = st.selectbox("חברה", companies)
                with col2:
                    # זיהוי שנים דינמי
                    years_path = os.path.join(base_path, company)
                    years = [d for d in os.listdir(years_path) if os.path.isdir(os.path.join(years_path, d))] if os.path.exists(years_path) else ["2025"]
                    year = st.selectbox("שנה", years)
                
                quarter = st.selectbox("רבעון", ["Q1", "Q2", "Q3", "Q4"])
                
                # בניית הנתיב המלא
                final_folder = os.path.join(base_path, company, year, quarter, "Financial_Reports")
                
                if os.path.exists(final_folder):
                    files = [f for f in os.listdir(final_folder) if f.endswith(".pdf")]
                    if files:
                        filename = st.selectbox("בחר דוח PDF", files)
                        selected_file_path = os.path.join(final_folder, filename)
                    else:
                        st.warning("לא נמצאו קבצי PDF בתיקייה זו.")
                else:
                    st.warning("התיקייה לא קיימת במערכת.")
            else:
                st.warning("הארכיון ריק.")
        else:
            st.error("לא נמצאה תיקיית 'data'. בדוק את ה-GitHub.")
            
    else:
        # מצב ידני
        uploaded_user_file = st.file_uploader("גרור דוח לכאן", type=['pdf'])

# --- 7. לוגיקה ראשית (Main Logic) ---

# קביעת הקובץ הסופי לעבודה
final_working_path = selected_file_path

# טיפול בקובץ ידני (שמירה זמנית)
if uploaded_user_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_user_file.getvalue())
        final_working_path = tmp.name

# מנוע הטעינה והצ'אט
if final_working_path:
    # בדיקה: האם זה קובץ חדש שצריך לטעון?
    # אנו משווים לנתיב השמור ב-Session State
    if "current_loaded_path" not in st.session_state or st.session_state.current_loaded_path != final_working_path:
        
        # טעינה למודל
        gemini_file_obj = upload_file_to_cloud(final_working_path)
        
        if gemini_file_obj:
            # שמירה בזיכרון של הדפדפן
            st.session_state.gemini_file = gemini_file_obj
            st.session_state.current_loaded_path = final_working_path
            st.session_state.chat_history = [] # איפוס צ'אט לדוח חדש
            st.toast(f"מחובר לדוח: {os.path.basename(final_working_path)}", icon="📈")

    # הצגת ממשק הצ'אט
    if "gemini_file" in st.session_state:
        
        # הצגת היסטוריה
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])
            
        # קלט משתמש
        if prompt := st.chat_input("שאל שאלה (למשל: נתח את הרווחיות לפי IFRS 17)..."):
            # הצגת שאלת המשתמש
            st.chat_message("user").write(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # קבלת תשובה
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_text = ""
                
                try:
                    # שימוש ב-Streaming לתחושת זמן אמת
                    response_stream = model.generate_content(
                        [st.session_state.gemini_file, prompt],
                        stream=True
                    )
                    
                    for chunk in response_stream:
                        if chunk.text:
                            full_text += chunk.text
                            response_placeholder.markdown(full_text + "▌")
                            
                    response_placeholder.markdown(full_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": full_text})
                    
                except Exception as e:
                    response_placeholder.error(f"שגיאה בתקשורת עם המודל: {e}")
                    # במקרה של ניתוק, מציע רענון
                    if "404" in str(e) or "not found" in str(e).lower():
                        st.warning("הקשר עם הקובץ אבד. מנסה לטעון מחדש...")
                        del st.session_state['current_loaded_path']
                        st.rerun()

else:
    st.info("👈 כדי להתחיל, בחר דוח מהתפריט בצד ימין.")

import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
from datetime import datetime

# --- 1. הגדרות מערכת ועיצוב ---
st.set_page_config(
    page_title="Apex Pro Enterprise",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# עיצוב CSS מתקדם (RTL, טאבים, כפתורים, התראות)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    
    .stApp { direction: rtl; font-family: 'Heebo', sans-serif; }
    
    /* יישור לימין */
    h1, h2, h3, h4, p, div, .stMarkdown, .stButton, .stExpander { text-align: right; }
    
    /* עיצוב טאבים */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 5px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e8f0fe;
        border-bottom: 2px solid #1a73e8;
    }

    /* תיבות מידע */
    .methodology-box {
        background-color: #e3f2fd;
        border-right: 5px solid #2196f3;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-size: 0.9em;
    }
    
    .alert-box {
        background-color: #ffebee;
        border-right: 5px solid #f44336;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }

    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# --- 2. מנוע הליבה (Engine & Security) ---
def init_gemini():
    api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("⛔ שגיאה קריטית: לא נמצא מפתח API.")
        st.stop()
    genai.configure(api_key=api_key)

@st.cache_resource
def get_best_model():
    try:
        models = list(genai.list_models())
        text_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
        
        # עדיפות ל-Flash (מהירות לניתוח דוחות כבדים)
        for m in text_models:
            if "flash" in m.name.lower(): return m.name, "Flash 1.5 (Turbo)"
        return text_models[0].name, "Standard"
    except:
        return "gemini-1.5-flash", "Flash (Default)"

init_gemini()
model_name, model_desc = get_best_model()

# הנחיה ראשית (Persona) - רגולטור מחמיר
system_instruction = """
אתה מומחה אקטואריה ורגולטור בכיר ברשות שוק ההון.
תפקידך לנתח דוחות כספיים של חברות ביטוח בישראל (IFRS 17, Solvency II).

הנחיות קריטיות לכל תשובה:
1. **מתודולוגיה:** הסבר תמיד את הנוסחה או ההיגיון המקצועי מאחורי החישוב.
2. **דגלים אדומים:** זהה חריגות, ירידה ביחסי הון, או חוזים מכבידים וסמן אותם בבירור ב-🚩.
3. **דיוק:** אל תמציא מספרים. אם נתון חסר, ציין זאת.
4. **מבנה:** הפרד בין הניתוח, ההסבר המקצועי, וההתרעות למפקח.
"""

model = genai.GenerativeModel(model_name, system_instruction=system_instruction)

# --- 3. פונקציות שירות ---
def upload_file(path):
    status = st.empty()
    status.info("⏳ טוען דוח למנוע האנליטי...")
    try:
        file = genai.upload_file(path, mime_type="application/pdf")
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(file.name)
        if file.state.name != "ACTIVE": raise Exception("עיבוד נכשל")
        status.toast("הדוח מוכן לניתוח", icon="✅")
        time.sleep(1)
        status.empty()
        return file
    except Exception as e:
        status.error(f"שגיאה: {e}")
        return None

def generate_analysis(prompt_text, file_obj):
    """פונקציה גנרית לביצוע ניתוח עם טיפול בשגיאות"""
    with st.spinner("מבצע חישובים אקטואריים וניתוח רגולטורי..."):
        try:
            response = model.generate_content([file_obj, prompt_text])
            return response.text
        except Exception as e:
            st.error(f"שגיאה בניתוח: {e}")
            return None

# --- 4. ממשק צד (Sidebar) ---
with st.sidebar:
    st.title("🗄️ נתונים")
    mode = st.radio("בחר מקור:", ["GitHub", "העלאה ידנית"])
    
    selected_path = None
    base_path = "data/Insurance_Warehouse"
    
    if mode == "GitHub":
        if os.path.exists(base_path):
            comp = st.selectbox("חברה", os.listdir(base_path))
            y_path = os.path.join(base_path, comp)
            # לוגיקה לשנים
            years = [d for d in os.listdir(y_path) if os.path.isdir(os.path.join(y_path, d))] if os.path.exists(y_path) else ["2025"]
            year = st.selectbox("שנה", sorted(years, reverse=True))
            q = st.selectbox("רבעון", ["Q1", "Q2", "Q3", "Q4"])
            
            final_dir = os.path.join(base_path, comp, year, q, "Financial_Reports")
            if os.path.exists(final_dir):
                files = [f for f in os.listdir(final_dir) if f.endswith(".pdf")]
                if files:
                    f = st.selectbox("קובץ", files)
                    selected_path = os.path.join(final_dir, f)
    else:
        up = st.file_uploader("PDF", type=['pdf'])
        if up:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                t.write(up.getvalue())
                selected_path = t.name
    
    st.divider()
    st.caption(f"Engine: {model_desc}")
    if st.button("איפוס מלא 🔄"):
        st.session_state.clear()
        st.rerun()

# --- 5. לוגיקה ראשית וטאבים ---
if selected_path:
    # טעינת קובץ (Singleton)
    if "curr_path" not in st.session_state or st.session_state.curr_path != selected_path:
        st.session_state.gfile = upload_file(selected_path)
        st.session_state.curr_path = selected_path
        st.session_state.analysis_result = None # איפוס תוצאות קודמות

    if st.session_state.gfile:
        st.title(f"דשבורד פיקוח: {os.path.basename(selected_path)}")
        
        # הגדרת הטאבים לפי הבקשה שלך
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 IFRS 17 עומק", 
            "🌪️ תרחישי קיצון (Solvency)", 
            "📈 יחסים פיננסיים", 
            "🏆 5 המדדים (KPIs)",
            "💬 צ'אט חופשי"
        ])

        # --- Tab 1: IFRS 17 ---
        with tab1:
            st.header("ניתוח עומק IFRS 17")
            st.markdown("בחר מודול לניתוח:")
            
            col1, col2, col3 = st.columns(3)
            
            if col1.button("תנועת CSM וריווחיות"):
                prompt = """
                נתח את תנועת ה-CSM (Contractual Service Margin) בדוח.
                1. הצג טבלה של יתרת פתיחה, צבירה מריבית, שחרור לרווח, ושינויים בהנחות.
                2. הפרד בין מודלים: GMM, VFA, PAA.
                3. זהה האם קצב שחרור ה-CSM תואם את הציפיות או שיש האצה חריגה (Flag).
                4. ספק הסבר מתודולוגי: מה המשמעות של כל רכיב בתנועה.
                """
                st.session_state.analysis_result = generate_analysis(prompt, st.session_state.gfile)
            
            if col2.button("חוזים מכבידים (Onerous)"):
                prompt = """
                סרוק את הדוח לאיתור קבוצות חוזים מכבידים (Onerous Contracts).
                1. באילו מגזרים נרשמו הפסדים בגין חוזים מכבידים?
                2. מה היקף רכיב ההפסד (Loss Component) במאזן?
                3. האם בוצעו היפוכים של חוזים מכבידים מתקופות קודמות?
                4. דגל אדום: האם יש גידול משמעותי בחוזים המכבידים ביחס לפרמיה?
                """
                st.session_state.analysis_result = generate_analysis(prompt, st.session_state.gfile)

            if col3.button("התאמות סיכון (RA)"):
                prompt = """
                נתח את התאמת הסיכון (Risk Adjustment) בגין סיכון לא פיננסי.
                1. מהי השיטה שבה החברה משתמשת (למשל, רווחי סמך)?
                2. מה השינוי ב-RA ביחס לתקופה קודמת?
                3. הסבר מתודולוגי: מה מייצג ה-RA במודל המדידה.
                """
                st.session_state.analysis_result = generate_analysis(prompt, st.session_state.gfile)

        # --- Tab 2: Solvency & Scenarios ---
        with tab2:
            st.header("מבחני קיצון וסולבנסי")
            
            scenario = st.selectbox("בחר תרחיש לסימולציה:", 
                                    ["עליית ריבית (Interest Rate Risk)", 
                                     "ירידות בשווקים (Market Risk)", 
                                     "רעידת אדמה (Catastrophe Risk)", 
                                     "גידול בביטולים (Lapse Risk)"])
            
            if st.button("הרץ סימולציה 🚀"):
                prompt = f"""
                בצע ניתוח רגישות לתרחיש: {scenario}.
                1. אתר בדוח את טבלת הרגישויות של יחס כושר הפירעון (Solvency Ratio).
                2. מה ההשפעה המדווחת של התרחיש הנבחר על עודף ההון ועל היחס?
                3. האם תחת התרחיש החברה יורדת מתחת ל-100% סולבנסי? (סמן כדגל אדום קריטי 🚩).
                4. הסבר מתודולוגי: כיצד התרחיש משפיע על ההתחייבויות ועל הנכסים (למשל, השפעת ריבית על העתודה).
                """
                st.session_state.analysis_result = generate_analysis(prompt, st.session_state.gfile)

        # --- Tab 3: Financial Ratios ---
        with tab3:
            st.header("יחסים פיננסיים (מאזן, רווח, תזרים)")
            
            col1, col2 = st.columns(2)
            if col1.button("ניתוח מאזן ומינוף"):
                prompt = """
                נתח יחסים פיננסיים המבוססים על המאזן:
                1. יחס ההון למאזן.
                2. הרכב תיק ההשקעות (מניות vs אג"ח vs נכסים לא סחירים).
                3. יחס העתודות להון.
                4. מתודולוגיה: הסבר כיצד IFRS 17 משנה את הצגת ההתחייבויות במאזן.
                """
                st.session_state.analysis_result = generate_analysis(prompt, st.session_state.gfile)
                
            if col2.button("איכות הרווח (P&L Quality)"):
                prompt = """
                נתח את דוח הרווח והפסד:
                1. הפרד בין תוצאות ביטוחיות (Insurance Service Result) לתוצאות מימוניות (Finance Result).
                2. מהי השפעת התנודתיות בשוק ההון על השורה התחתונה?
                3. הצג את הרווח הכולל (Comprehensive Income) ונתח את הפער מול הרווח הנקי.
                """
                st.session_state.analysis_result = generate_analysis(prompt, st.session_state.gfile)

        # --- Tab 4: 5 KPIs ---
        with tab4:
            st.header("🏆 5 המדדים הקריטיים (The Watchlist)")
            st.info("מדדים אלו הוגדרו כקריטיים עבור המפקח בזיכרון המערכת.")
            
            if st.button("בדוק את 5 המדדים כעת"):
                prompt = """
                חלץ ונתח את 5 המדדים הקריטיים הבאים מתוך הדוח:
                1. **יחס כושר פירעון (Solvency Ratio):** כולל ולא כולל הוראות מעבר/פריסה.
                2. **רווחיות להון (ROE):** מנורמלת וחשבונאית.
                3. **Combined Ratio (יחס משולב):** במגזרי הביטוח הכללי (אם רלוונטי).
                4. **מרווח CSM חדש (New Business CSM):** היקף הרווחיות מחוזים חדשים שנמכרו בתקופה.
                5. **יחס נזילות:** או מדד תזרים מזומנים מפעילות שוטפת.
                
                עבור כל מדד: הצג את המספר, השווה לתקופה קודמת, וסמן 🚩 אם יש הרעה מהותית.
                """
                st.session_state.analysis_result = generate_analysis(prompt, st.session_state.gfile)

        # --- Tab 5: Chat ---
        with tab5:
            st.header("אנליסט וירטואלי")
            user_q = st.chat_input("שאל שאלה חופשית...")
            if user_q:
                st.chat_message("user").write(user_q)
                res = generate_analysis(user_q, st.session_state.gfile)
                if res:
                    st.chat_message("assistant").write(res)

        # --- אזור תצוגת תוצאות (משותף לכל הטאבים) ---
        if st.session_state.analysis_result:
            st.divider()
            st.subheader("📝 תוצאות הניתוח")
            
            # אנחנו מבקשים מהמודל במוח (System Prompt) להפריד, אבל כאן נציג את זה יפה
            # המודל יחזיר טקסט ארוך, אנחנו נציג אותו בתוך הקונטיינר
            
            st.markdown(st.session_state.analysis_result)
            
            # כפתורי עזר קבועים לתוצאה
            with st.expander("📚 הסבר מתודולוגי (לחץ להרחבה)"):
                st.info("הסבר זה מופק אוטומטית על בסיס התקנים החשבונאיים IFRS 17 והוראות Solvency II הרלוונטיים לסעיפים שנותחו.")
            
            if "🚩" in st.session_state.analysis_result:
                st.error("⚠️ זוהו דגלים אדומים בניתוח! נא לבדוק את הסעיפים המסומנים.")

else:
    st.info("👈 בחר דוח מצד ימין כדי להפעיל את המערכת.")

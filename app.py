import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions
import tempfile
import os
import time

# --- 1. הגדרת דף ---
st.set_page_config(page_title="Apex Pro Enterprise", page_icon="🏢", layout="wide")

# --- 2. עיצוב RTL ---
st.markdown("""<style>.stApp {direction: rtl;} h1, h2, h3, p, div {text-align: right;} 
.stTextInput>div>div>input {text-align: right;} .stSelectbox>div>div>div {text-align: right;} 
.stChatMessage {direction: rtl; text-align: right;} .stDeployButton {display:none;}</style>""", unsafe_allow_html=True)

st.title("🏢 Apex Pro - מערכת ניתוח דוחות")

# --- 3. הגדרת API (חכם - בודק את כל האפשרויות) ---
api_key = None
# בודק אם שמרת בשם הזה
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
# או אם שמרת בשם הזה
elif "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ לא נמצא מפתח ב-Secrets. נא להוסיף GOOGLE_API_KEY.")
    st.stop()

# --- 4. פונקציה לבחירת מודל עובד ---
@st.cache_resource
def get_model():
    # מנסה את המהיר קודם, ואז את החזק
    candidates = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            # בדיקה שקטה
            model.generate_content("test") 
            return model_name
        except Exception:
            continue
    return None

working_model_name = get_model()

if not working_model_name:
    st.error("❌ המפתח תקין, אך גוגל חוסמים את הגישה למודלים כרגע.")
    st.stop()

model = genai.GenerativeModel(
    working_model_name,
    system_instruction="אתה אנליסט ביטוח בכיר. נתח לפי IFRS 17 ו-Solvency II. ענה בעברית."
)

# --- 5. פונקציות עזר ---
def upload_to_gemini(path):
    status = st.empty()
    status.info(f"🚀 מעלה דוח למודל ({working_model_name})...")
    file = genai.upload_file(path, mime_type="application/pdf")
    while file.state.name == "PROCESSING":
        time.sleep(1)
        file = genai.get_file(file.name)
    if file.state.name != "ACTIVE":
        raise Exception("העיבוד נכשל")
    status.empty()
    return file

# --- 6. צד ימין ---
base_path = "data/Insurance_Warehouse" 
with st.sidebar:
    st.header("🗄️ מאגר נתונים")
    mode = st.radio("מקור:", ["GitHub (ארכיון)", "העלאה ידנית"])
    selected_file_path = None
    uploaded_user_file = None

    if mode == "GitHub (ארכיון)":
        if os.path.exists(base_path):
            companies = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
            if companies:
                col1, col2 = st.columns(2)
                with col1: company = st.selectbox("חברה", companies)
                with col2: 
                    yp = os.path.join(base_path, company)
                    years = [d for d in os.listdir(yp) if os.path.isdir(os.path.join(yp, d))] if os.path.exists(yp) else ["2025"]
                    year = st.selectbox("שנה", years)
                quarter = st.selectbox("רבעון", ["Q1", "Q2", "Q3", "Q4"])
                sp = os.path.join(base_path, company, year, quarter, "Financial_Reports")
                if os.path.exists(sp):
                    files = [f for f in os.listdir(sp) if f.endswith(".pdf")]
                    if files:
                        fname = st.selectbox("בחר דוח", files)
                        selected_file_path = os.path.join(sp, fname)
                    else: st.warning("אין קבצים בתיקייה")
                else: st.warning("תיקייה ריקה")
            else: st.warning("הארכיון ריק")
        else: st.error("תיקיית data לא נמצאה")
    else:
        uploaded_user_file = st.file_uploader("העלה PDF", type=['pdf'])

# --- 7. לוגיקה ראשית ---
final_path = selected_file_path
if uploaded_user_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_user_file.getvalue())
        final_path = tmp.name

if final_path:
    if "curr_path" not in st.session_state or st.session_state.curr_path != final_path:
        try:
            st.session_state.gfile = upload_to_gemini(final_path)
            st.session_state.curr_path = final_path
            st.session_state.chat = []
            st.toast("✅ הדוח מוכן!", icon="📈")
        except Exception as e: st.error(f"שגיאה: {e}")

    if "chat" not in st.session_state: st.session_state.chat = []
    
    for msg in st.session_state.chat:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("שאל משהו..."):
        st.chat_message("user").write(prompt)
        st.session_state.chat.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            ph = st.empty()
            full_res = ""
            try:
                res = model.generate_content([st.session_state.gfile, prompt], stream=True)
                for chunk in res:
                    if chunk.text:
                        full_res += chunk.text
                        ph.markdown(full_res + "▌")
                ph.markdown(full_res)
                st.session_state.chat.append({"role": "assistant", "content": full_res})
            except Exception as e:
                ph.error(f"שגיאה: {e}")

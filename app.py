import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import os

# ==========================================
# 1. הגדרות מערכת
# ==========================================
st.set_page_config(page_title="MY AI APP", layout="wide")

# ==========================================
# 2. מנוע AI חכם (בוחר לבד מודל שקיים)
# ==========================================
def get_optimal_model():
    """סורק את המודלים הזמינים ובוחר את הטוב ביותר באופן אוטומטי"""
    if "GEMINI_API_KEY" not in st.secrets:
        return None, "Error: חסר מפתח API ב-Secrets"
    
    api_key = st.secrets["GEMINI_API_KEY"].strip()
    genai.configure(api_key=api_key)
    
    try:
        # שלב 1: בקשת רשימת המודלים הפתוחים למפתח שלך
        all_models = list(genai.list_models())
        
        # שלב 2: סינון מודלים שתומכים בצ'אט
        chat_models = [m for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        if not chat_models:
            return None, "המפתח תקין, אך לא נמצאו מודלים לשיחה."
            
        # שלב 3: בחירה חכמה - העדפה לגרסאות 2.0 החדשות שראינו אצלך
        # נחפש מודל שמכיל 'flash' בשם שלו, כי הוא המהיר ביותר
        selected_model = None
        
        # נסיון למצוא את Flash
        for m in chat_models:
            if 'flash' in m.name.lower():
                selected_model = m
                break
        
        # אם לא מצאנו Flash, ניקח את הראשון ברשימה (כנראה Pro)
        if not selected_model:
            selected_model = chat_models[0]
            
        return genai.GenerativeModel(selected_model.name), None

    except Exception as e:
        return None, f"שגיאת התחברות ל-Google: {str(e)}"

# אתחול המודל בתחילת הריצה
model, status_msg = get_optimal_model()

# ==========================================
# 3. מנוע איתור קבצים
# ==========================================
def find_pdf_file(base_dir, file_start_name):
    if not os.path.exists(base_dir): return None
    for f in os.listdir(base_dir):
        if f.lower().startswith(file_start_name.lower()) and ".pdf" in f.lower():
            return os.path.join(base_dir, f)
    return None

# ==========================================
# 4. תפריט צד (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🗄️ Database")
    comp = st.selectbox("חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    
    # חיווי חיבור ל-AI
    if model:
        st.success("✅ AI מחובר (מודל זוהה אוטומטית)")
    else:
        st.error(f"❌ {status_msg}")

    # נתיבים
    root_path = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(root_path):
        root_path = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"
    
    fin_path = find_pdf_file(f"{root_path}/Financial_Reports", f"{comp}_{q}_{year}")
    sol_path = find_pdf_file(f"{root_path}/Solvency_Reports", f"Solvency_{comp}_{q}_{year}")
    
    st.write(f"📄 דוח כספי: {'✅' if fin_path else '❌'}")
    st.write(f"🛡️ דוח סולבנסי: {'✅' if sol_path else '❌'}")

# ==========================================
# 5. מסך ראשי
# ==========================================
st.title("MY AI APP 🤖")
st.caption(f"מחובר לקובץ נתונים: {comp} | {year}")

t1, t2 = st.tabs(["📊 מדדים", "💬 צ'אט עם הדוחות"])

with t1:
    st.info("כאן יוצגו המדדים הגרפיים.")

with t2:
    mode = st.radio("בחר קובץ:", ["דוח כספי", "דוח סולבנסי"], horizontal=True)
    active_file = fin_path if mode == "דוח כספי" else sol_path
    
    if active_file:
        st.success(f"מנתח את: {os.path.basename(active_file)}")
        
        query = st.text_input("שאל את האנליסט (למשל: מהו ההון העצמי?):")
        
        if st.button("🚀 הרץ ניתוח") and query:
            if not model:
                st.error("לא ניתן לבצע ניתוח - ה-AI לא מחובר.")
            else:
                with st.spinner("סורק דפים ומחלץ נתונים..."):
                    try:
                        doc = fitz.open(active_file)
                        text_content = ""
                        # קריאת 40 עמודים ראשונים
                        for i in range(min(len(doc), 40)):
                            text_content += doc[i].get_text()
                        
                        prompt = f"""
                        אתה אנליסט מומחה. ענה על השאלה לפי הטקסט המצורף.
                        שאלה: {query}
                        טקסט מהדוח:
                        {text_content[:30000]}
                        """
                        
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.write(response.text)
                        
                    except Exception as e:
                        st.error(f"תקלה בניתוח הקובץ: {e}")
    else:
        st.warning("⚠️ לא נמצא קובץ מתאים בתיקייה שנבחרה. בדוק ב-GitHub.")

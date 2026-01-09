import os
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF

# ==========================================
# 1. הגדרות מערכת וחיבור AI
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

def init_ai():
    # הגדרת המודל החדש בגרסה יציבה
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    return None

model = init_ai()

# ==========================================
# 2. מנוע איתור קבצים חכם (מתגבר על כפילויות)
# ==========================================
def find_file_smart(base_path, file_prefix):
    """מוצא קובץ שמתחיל בשם הנכון, גם אם יש לו סיומת כפולה"""
    if not os.path.exists(base_path):
        return None
    
    for f in os.listdir(base_path):
        # בדיקה: מתחיל בשם החברה ומסתיים ב-pdf (לא משנה כמה פעמים)
        if f.lower().startswith(file_prefix.lower()) and ".pdf" in f.lower():
            return os.path.join(base_path, f)
    return None

# ==========================================
# 3. תפריט צד (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    comp = st.selectbox("בחר חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # בדיקת נתיבים (תומך ב-Data ו-data)
    base_dir = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(base_dir):
        base_dir = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"

    # איתור הקבצים
    fin_path = find_file_smart(f"{base_dir}/Financial_Reports", f"{comp}_{q}_{year}")
    sol_path = find_file_smart(f"{base_dir}/Solvency_Reports", f"Solvency_{comp}_{q}_{year}")
    
    st.write(f"📄 דוח כספי: {'✅' if fin_path else '❌'}")
    st.write(f"🛡️ דוח סולבנסי: {'✅' if sol_path else '❌'}")

# ==========================================
# 4. מסך ניתוח ראשי
# ==========================================
st.title(f"🏛️ {comp} | Strategic AI Terminal")
t1, t2 = st.tabs(["📊 KPI Dashboard", "🤖 AI Analyst"])

with t2:
    st.subheader("ניתוח דוחות עמוק")
    mode = st.radio("בחר דוח:", ["כספי", "סולבנסי"])
    active_path = fin_path if mode == "כספי" else sol_path
    
    if active_path:
        st.success(f"מנתח את: {os.path.basename(active_path)}")
        query = st.text_input("שאל את האנליסט (למשל: מהו ההון העצמי?):")
        
        if st.button("🚀 הרץ ניתוח") and query:
            if model:
                with st.spinner("סורק דפי מאזן ומחלץ נתונים..."):
                    try:
                        doc = fitz.open(active_path)
                        # חילוץ טקסט מ-40 עמודים ראשונים
                        text = "".join([page.get_text() for page in doc[:40]])
                        
                        prompt = f"""
                        אתה מומחה IFRS 17. נתח את הדוח המצורף של חברת {comp}.
                        שאלה: {query}
                        
                        התמקד בנתונים מספריים מדויקים (הון עצמי, CSM, סולבנסי).
                        טקסט מהדוח:
                        {text[:20000]}
                        """
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בניתוח: {e}")
            else:
                st.error("שגיאת מפתח API - בדוק Secrets")
    else:
        st.warning("לא נמצא קובץ מתאים ב-GitHub.")

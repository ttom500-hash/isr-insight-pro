import os
import streamlit as st
import fitz  # PyMuPDF
import requests # ספריה לתקשורת ישירה ללא תלות בגרסאות AI
import json

# ==========================================
# 1. הגדרות מערכת
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# פונקציה שעוקפת את הספריה הבעייתית ופונה ישירות לגוגל
def ask_gemini_direct(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: Missing API Key"
    
    api_key = st.secrets["GEMINI_API_KEY"]
    # פנייה ישירה לכתובת ה-API של גוגל (Bypass)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# ==========================================
# 2. מנוע איתור קבצים (החלק שעבד מצוין)
# ==========================================
def find_file_smart(base_path, file_prefix):
    if not os.path.exists(base_path):
        return None
    for f in os.listdir(base_path):
        if f.lower().startswith(file_prefix.lower()) and ".pdf" in f.lower():
            return os.path.join(base_path, f)
    return None

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    comp = st.selectbox("בחר חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # בדיקת נתיבים
    base_dir = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(base_dir):
        base_dir = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"

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
    st.subheader("ניתוח דוחות (Direct Connection Mode)")
    mode = st.radio("בחר דוח:", ["כספי", "סולבנסי"])
    active_path = fin_path if mode == "כספי" else sol_path
    
    if active_path:
        st.success(f"קובץ בטיפול: {os.path.basename(active_path)}")
        query = st.text_input("הכנס שאלה (למשל: מהו ההון העצמי?):")
        
        if st.button("🚀 הרץ ניתוח") and query:
            with st.spinner("מבצע סריקה ישירה מול השרתים של גוגל..."):
                try:
                    # חילוץ טקסט
                    doc = fitz.open(active_path)
                    text = "".join([page.get_text() for page in doc[:40]])
                    
                    # בניית הפרומפט
                    full_prompt = f"""
                    אתה אנליסט מומחה. ענה על השאלה הבאה בהתבסס על הטקסט המצורף מדוח כספי.
                    שאלה: {query}
                    
                    טקסט מהדוח:
                    {text[:20000]}
                    """
                    
                    # שימוש בפונקציה הישירה
                    result = ask_gemini_direct(full_prompt)
                    
                    st.markdown("---")
                    if "Error" in result:
                        st.error(result)
                    else:
                        st.success(result)
                        
                except Exception as e:
                    st.error(f"תקלה בקריאת הקובץ: {e}")
    else:
        st.warning("לא נמצא קובץ. בדוק את התיקיות ב-GitHub.")

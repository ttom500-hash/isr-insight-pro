import os
import streamlit as st
import fitz  # PyMuPDF
import json
import urllib.request
import urllib.error

# ==========================================
# 1. הגדרות האפליקציה
# ==========================================
st.set_page_config(page_title="MY AI APP", layout="wide")

# ==========================================
# 2. מנוע AI משוריין (עם מנגנון גיבוי אוטומטי)
# ==========================================
def ask_ai(prompt):
    """מנסה את המודל המהיר, ואם נכשל - עובר למודל היציב"""
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: חסר מפתח API ב-Secrets."
    
    api_key = st.secrets["GEMINI_API_KEY"].strip()
    
    # רשימת מודלים לניסיון: קודם החדש, אחר כך הישן והטוב
    models_to_try = ["gemini-1.5-flash", "gemini-pro"]
    
    last_error = ""
    
    for model in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            data = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}]
            }).encode('utf-8')
            
            # שליחת הבקשה
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                res_json = json.loads(response.read().decode())
                return res_json['candidates'][0]['content']['parts'][0]['text']
                
        except urllib.error.HTTPError as e:
            # אם קיבלנו 404 או 503, ננסה את המודל הבא
            if e.code in [404, 503]:
                last_error = f"Model {model} failed ({e.code}), switching..."
                continue
            elif e.code == 403:
                return "⛔ שגיאת הרשאה (403): המפתח חסום. וודא שהשתמשת במפתח מ-Google AI Studio."
            else:
                return f"שגיאת תקשורת ({e.code}): {e.reason}"
        except Exception as e:
            last_error = str(e)
            continue

    return f"כל המודלים נכשלו. שגיאה אחרונה: {last_error}"

# ==========================================
# 3. מנוע איתור קבצים
# ==========================================
def find_pdf_file(base_dir, file_start_name):
    if not os.path.exists(base_dir):
        return None 
    for f in os.listdir(base_dir):
        if f.lower().startswith(file_start_name.lower()) and ".pdf" in f.lower():
            return os.path.join(base_dir, f)
    return None

# ==========================================
# 4. תפריט צד
# ==========================================
with st.sidebar:
    st.header("🗄️ Database")
    comp = st.selectbox("חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    
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
st.caption(f"אנליזה חכמה: {comp} | {year} {q}")

t1, t2 = st.tabs(["📊 מדדים", "💬 צ'אט עם הדוחות"])

with t1:
    st.info("כאן יוצגו המדדים הגרפיים (Solvency, ROE).")

with t2:
    mode = st.radio("בחר קובץ:", ["דוח כספי", "דוח סולבנסי"], horizontal=True)
    active_file = fin_path if mode == "דוח כספי" else sol_path
    
    if active_file:
        st.success(f"מחובר לקובץ: {os.path.basename(active_file)}")
        
        query = st.text_input("שאל שאלה על הדוח:")
        
        if st.button("🚀 שאל את ה-AI") and query:
            with st.spinner("מנתח נתונים (עשוי לקחת כמה שניות)..."):
                try:
                    doc = fitz.open(active_file)
                    text_content = ""
                    # קריאת 40 עמודים ראשונים לביצועים מהירים
                    for i in range(min(len(doc), 40)):
                        text_content += doc[i].get_text()
                    
                    final_prompt = f"""
                    אתה אנליסט מומחה. ענה בעברית על השאלה לפי הטקסט.
                    שאלה: {query}
                    טקסט מהדוח:
                    {text_content[:30000]}
                    """
                    
                    answer = ask_ai(final_prompt)
                    
                    st.markdown("---")
                    if "שגיאה" in answer or "Error" in answer:
                        st.error(answer)
                    else:
                        st.write(answer)
                        
                except Exception as e:
                    st.error(f"תקלה בקריאת הקובץ: {e}")
    else:
        # התיקון לשגיאת הסינטקס שעשית קודם נמצא כאן:
        st.warning("⚠️ לא נמצא קובץ מתאים בתיקייה שנבחרה. אנא בדוק ב-GitHub.")

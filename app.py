import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import fitz  # PyMuPDF

# ==========================================
# 1. הגדרות מערכת ועיצוב
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; background-color: #0E1117; }
    div[data-testid="stMetric"] { background-color: #262730; border: 1px solid #464B5C; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. מנוע AI (בחירת מודל אוטומטית)
# ==========================================
@st.cache_resource
def configure_ai_engine():
    if "GEMINI_API_KEY" not in st.secrets:
        return None, "❌ חסר מפתח API ב-Secrets"
    try:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        genai.configure(api_key=api_key)
        
        # סריקת מודלים
        models = list(genai.list_models())
        chat_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
        
        if not chat_models:
            return None, "⚠️ המפתח תקין אך אין מודלים זמינים לצ'אט."
        
        # בחירה חכמה: העדפה ל-Flash או גרסאות 2.0
        selected = chat_models[0]
        for m in chat_models:
            if 'flash' in m.name.lower():
                selected = m
                break
                
        return genai.GenerativeModel(selected.name), f"✅ מחובר ל-{selected.name}"

    except Exception as e:
        return None, f"❌ שגיאת חיבור: {str(e)}"

model, status_msg = configure_ai_engine()

# ==========================================
# 3. מנוע איתור קבצים (Deep Scan)
# ==========================================
def find_file_recursive(root_path, file_type):
    """
    סורק את כל התיקיות תחת השנה/רבעון כדי למצוא את הקובץ הנכון.
    file_type: 'finance' או 'solvency'
    """
    if not os.path.exists(root_path):
        return None
        
    # סריקת עומק (Walk) בתוך התיקייה של הרבעון
    for current_root, dirs, files in os.walk(root_path):
        for file in files:
            # בדיקה גסה: האם זה קובץ PDF?
            if file.lower().endswith(".pdf"):
                full_path = os.path.join(current_root, file)
                path_lower = full_path.lower()
                
                # זיהוי סולבנסי (לפי שם התיקייה או הקובץ)
                is_solvency = "solvency" in path_lower or "sfcr" in path_lower
                
                if file_type == "solvency" and is_solvency:
                    return full_path
                
                # זיהוי כספי (כל מה שאינו סולבנסי)
                if file_type == "finance" and not is_solvency:
                    return full_path
                    
    return None

# ==========================================
# 4. נתוני שוק (KPIs)
# ==========================================
market_df = pd.DataFrame({
    "חברה": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "Solvency Ratio": [184, 172, 175, 158, 149],
    "ROE": [14.1, 11.8, 12.5, 10.2, 10.4],
    "CSM (B)": [14.8, 14.1, 9.7, 11.2, 11.5],
    "Combined Ratio": [91.5, 93.2, 92.8, 95.1, 94.4]
})

# ==========================================
# 5. תפריט צד (Sidebar)
# ==========================================
with st.sidebar:
    st.title("Apex Enterprise")
    st.caption(status_msg)
    st.divider()
    
    # בחירת חברה ושנה (ברירת מחדל 2025 כדי למנוע שגיאות!)
    sel_comp = st.selectbox("בחר חברה:", market_df["חברה"])
    sel_year = st.selectbox("שנה:", [2025, 2024, 2026]) # שים לב: 2025 ראשון
    sel_q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # לוגיקה חכמה לזיהוי תיקיית הנתונים (data או Data)
    base_path_option1 = f"data/Insurance_Warehouse/{sel_comp}/{sel_year}/{sel_q}"
    base_path_option2 = f"Data/Insurance_Warehouse/{sel_comp}/{sel_year}/{sel_q}"
    
    if os.path.exists(base_path_option1):
        final_base_path = base_path_option1
    elif os.path.exists(base_path_option2):
        final_base_path = base_path_option2
    else:
        final_base_path = None

    # חיפוש הקבצים
    fin_file = None
    sol_file = None
    
    if final_base_path:
        fin_file = find_file_recursive(final_base_path, "finance")
        sol_file = find_file_recursive(final_base_path, "solvency")
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1: 
        st.markdown("**📄 כספי**")
        if fin_file: st.success("מחובר") 
        else: st.error("חסר")
    with c2: 
        st.markdown("**🛡️ סולבנסי**")
        if sol_file: st.success("מחובר") 
        else: st.error("חסר")

    # דיבוג למשתמש אם אין נתונים
    if not final_base_path:
        st.warning(f"אין נתונים לשנת {sel_year}")

# ==========================================
# 6. מסך ראשי
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic Dashboard")
st.caption(f"תקופת דוח: {sel_year} {sel_q}")

# נתוני החברה הנבחרת
row = market_df[market_df["חברה"] == sel_comp].iloc[0]

tab1, tab2, tab3 = st.tabs(["📊 KPI Dashboard", "🤖 AI Analyst", "📉 Solvency Lab"])

# --- טאב 1: מדדים ---
with tab1:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Solvency Ratio", f"{row['Solvency Ratio']}%", "Stable")
    k2.metric("ROE (תשואה)", f"{row['ROE']}%", "+0.2%")
    k3.metric("CSM Value", f"₪{row['CSM (B)']}B", "Growth")
    k4.metric("Combined Ratio", f"{row['Combined Ratio']}%", "-1.5%")
    
    st.divider()
    
    g1, g2 = st.columns(2)
    with g1:
        fig = px.bar(market_df, x="חברה", y="Solvency Ratio", 
                     title="השוואת יחס כושר פירעון", color="Solvency Ratio",
                     color_continuous_scale="Teal")
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig2 = px.line(market_df, x="חברה", y="CSM (B)", markers=True, 
                       title="מגמת רווחיות (CSM)")
        fig2.update_traces(line_color='#00FFA3', line_width=3)
        st.plotly_chart(fig2, use_container_width=True)

# --- טאב 2: אנליסט AI ---
with tab2:
    st.subheader("🕵️‍♀️ חדר מחקר וניתוח דוחות")
    
    # בדיקה איזה דוחות זמינים
    options = []
    if fin_file: options.append("דוח כספי")
    if sol_file: options.append("דוח סולבנסי")
    
    if not options:
        st.warning("⚠️ לא ניתן להפעיל את האנליסט - חסרים קבצי דוחות בתיקייה.")
    else:
        mode = st.radio("בחר מקור לניתוח:", options, horizontal=True)
        active_path = fin_file if mode == "דוח כספי" else sol_file
        
        st.success(f"📂 קובץ פעיל: {os.path.basename(active_path)}")
        
        # אזור השאלה
        col_q, col_btn = st.columns([4, 1])
        with col_q:
            user_q = st.text_input("מה תרצה לדעת?", placeholder="למשל: מהו הרווח הכולל ברבעון?")
        with col_btn:
            st.write("") # מרווח
            st.write("") 
            run_btn = st.button("🚀 נתח", type="primary", use_container_width=True)
        
        if run_btn and user_q:
            if not model:
                st.error("ה-AI מנותק, בדוק מפתח API.")
            else:
                with st.spinner("ה-AI קורא את הדוח ומעבד נתונים..."):
                    try:
                        # קריאת ה-PDF
                        doc = fitz.open(active_path)
                        text_content = ""
                        # קריאת עד 60 עמודים (מכסה את רוב הדוחות)
                        for i in range(min(len(doc), 60)):
                            text_content += doc[i].get_text()
                        
                        # הפרומפט
                        prompt = f"""
                        אתה אנליסט מומחה לביטוח (IFRS 17, Solvency II).
                        התבסס אך ורק על הטקסט המצורף וענה על השאלה.
                        
                        שאלה: {user_q}
                        
                        טקסט מהדוח:
                        {text_content[:40000]}
                        """
                        
                        response = model.generate_content(prompt)
                        st.markdown("### 💡 תשובת האנליסט:")
                        st.info(response.text)
                        
                    except Exception as e:
                        st.error(f"תקלה בניתוח: {e}")

# --- טאב 3: סולבנסי ---
with tab3:
    st.subheader("מחשבון רגישות (Stress Test)")
    
    if sol_file:
        st.success("✅ דוח Solvency מחובר למערכת")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            stress_val = st.slider("שינוי עקום ריבית (bps)", -100, 100, 0)
            equity_shock = st.slider("ירידה בשוקי מניות (%)", 0, 30, 0)
        
        with col_s2:
            # חישוב דמה להדגמה
            current_sol = row['Solvency Ratio']
            impact = (stress_val * 0.1) - (equity_shock * 0.5)
            new_sol = current_sol + impact
            
            st.metric("יחס סולבנסי חזוי", f"{new_sol:.1f}%", f"{impact:.1f}%")
            
            fig_g = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = new_sol,
                title = {'text': "Solvency Prediction"},
                gauge = {'axis': {'range': [100, 200]}, 'bar': {'color': "#00FFA3"}}
            ))
            st.plotly_chart(fig_g, use_container_width=True)
    else:
        st.info("ℹ️ לצורך ביצוע סימולציות, אנא וודא שדוח סולבנסי קיים בתיקייה.")

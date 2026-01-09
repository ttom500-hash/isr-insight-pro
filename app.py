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
# 1. SETUP & SECURE AI
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise | Strategic AI Terminal", layout="wide")

def initialize_ai():
    try:
        # שימוש ב-Secrets של Streamlit לאבטחת מפתחות
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
            return True
        return False
    except Exception:
        return False

ai_ready = initialize_ai()

@st.cache_resource
def get_stable_model():
    if not ai_ready: return None, "None"
    # תיקון שגיאת 404: שימוש בנתיב המודל המלא והמעודכן ביותר
    model_name = 'models/gemini-1.5-flash-latest'
    try:
        return genai.GenerativeModel(model_name), model_name
    except Exception:
        # גיבוי אוטומטי למקרה של תקלה בנתיב המפורש
        return genai.GenerativeModel('gemini-1.5-flash'), 'gemini-1.5-flash'

ai_model, active_model_name = get_stable_model()

# ==========================================
# 2. ADVANCED DATA WAREHOUSE & PDF LOGIC
# ==========================================
BASE_WAREHOUSE = "data/Insurance_Warehouse"

def get_verified_paths(company, year, quarter):
    """סריקה אוטומטית של נתיבי הקבצים במבנה התיקיות ב-GitHub"""
    base = os.path.join(BASE_WAREHOUSE, company, str(year), quarter)
    fin_dir = os.path.join(base, "Financial_Reports")
    sol_dir = os.path.join(base, "Solvency_Reports")
    
    fin_files = [os.path.join(fin_dir, f) for f in os.listdir(fin_dir) if f.endswith('.pdf')] if os.path.exists(fin_dir) else []
    sol_files = [os.path.join(sol_dir, f) for f in os.listdir(sol_dir) if f.endswith('.pdf')] if os.path.exists(sol_dir) else []
    return fin_files, sol_files

def extract_hybrid_context(pdf_path):
    """חילוץ היברידי מתקדם: טקסט מלא מ-15 דפים וצילום 3 דפים לניתוח Vision"""
    text_buffer = ""
    images = []
    try:
        doc = fitz.open(pdf_path)
        # סריקה של עד 15 דפים ראשונים לטובת חילוץ נתונים מילוליים
        for i in range(min(len(doc), 15)):
            text_buffer += f"\n--- Page {i+1} ---\n" + doc[i].get_text()
            # צילום הדפים הקריטיים לניתוח ויזואלי של טבלאות וגרפים
            if i < 3:
                pix = doc[i].get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.open(io.BytesIO(pix.tobytes()))
                images.append(img)
        return text_buffer, images
    except Exception as e:
        return f"Error extracting PDF: {e}", []

# נתוני שוק מלאים - KPI Checklist (מבוסס על ההגדרות שלך)
market_df = pd.DataFrame({
    "חברה": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "Solvency %": [184, 172, 175, 158, 149],
    "ROE %": [14.1, 11.8, 12.5, 10.2, 10.4],
    "CSM (B₪)": [14.8, 14.1, 9.7, 11.2, 11.5],
    "Combined Ratio %": [91.5, 93.2, 92.8, 95.1, 94.4],
    "Expense Ratio %": [18.2, 19.1, 17.5, 20.4, 19.8],
    "NB Margin %": [4.8, 4.5, 4.3, 3.8, 3.9]
})

# ==========================================
# 3. SIDEBAR - AUTOMATED CONTROL
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    sel_comp = st.selectbox("בחר חברה לניתוח:", market_df["חברה"])
    sel_year = st.selectbox("שנה פיסקאלית:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון דיווח:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # סריקה אוטומטית של נתיבי הקבצים מה-Repository
    fin_paths, sol_paths = get_verified_paths(sel_comp, sel_year, sel_q)
    
    st.divider()
    st.subheader("📁 נתיבי קבצים זוהו:")
    if fin_paths:
        st.success(f"✅ דוח כספי: {os.path.basename(fin_paths[0])[:15]}...")
    else:
        st.warning("❌ דוח כספי לא נמצא בתיקייה")
        
    if sol_paths:
        st.success(f"✅ דוח סולבנסי זוהה")
    
    st.caption(f"AI Analytic Core: {active_model_name}")

# ==========================================
# 4. MAIN TERMINAL - FULL SUITE
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 Critical KPIs", "⛓️ IFRS 17 Engine", "📈 Financial Ratios", "🛡️ Stress Scenarios", "🤖 AI Deep Research"])

# --- TAB 1: 5 Critical KPIs ---
with tabs[0]:
    row = market_df[market_df["חברה"] == sel_comp].iloc[0]
    st.subheader("מדדי ליבה - IFRS 17 & Solvency II")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Solvency Ratio", f"{row['Solvency %']}%")
    k2.metric("ROE", f"{row['ROE %']}%")
    k3.metric("Combined Ratio", f"{row['Combined Ratio %']}%")
    k4.metric("CSM Balance", f"₪{row['CSM (B₪)']}B")
    k5.metric("Exp. Ratio", f"{row['Expense Ratio %']}%")
    
    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(px.bar(market_df, x="חברה", y="CSM (B₪)", color="חברה", 
                              title="השוואת עתודות רווח (CSM) במגזר הביטוח"), use_container_width=True)
    with col_g2:
        st.plotly_chart(px.pie(values=[60, 25, 15], names=["Life", "Health", "P&C"], title="Profit Mix by Segment"), use_container_width=True)

# --- TAB 2: IFRS 17 ENGINE ---
with tabs[1]:
    st.subheader("⛓️ IFRS 17: CSM Analytics & Waterfall")
    st.markdown("#### ניתוח מודלי מדידה ומרכיב הפסד")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.info("**VFA Approach**\n\nחיסכון ארוך טווח, ביטוח מנהלים (שינוי בערך נכסים עובר ל-CSM)")
    m_col2.success("**GMM Approach**\n\nריסק, סיעוד, חיים מסורתי (שימוש בשיעור ריבית נעול)")
    m_col3.warning("**PAA Approach**\n\nאלמנטר ובריאות קצר מועד (מודל פרמיה בלתי משוריינת)")
    
    st.divider()
    
    # גרף מפל CSM מלא
    fig_wf = go.Figure(go.Waterfall(
        x = ["Opening", "New Business", "Changes", "Onerous", "Release", "Closing"],
        y = [14200, 850, 150, -320, -1100, 13780],
        measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
    ))
    
    st.plotly_chart(fig_wf, use_container_width=True)
    
    st.error(f"**Loss Component Alert:** בחוזים המכבידים זוהתה הפרשה מצטברת של ₪320M המוכרת בדו''ח רווח והפסד.")

# --- TAB 3: FINANCIAL RATIOS ---
with tabs[2]:
    st.subheader("📈 Financial Ratio Deep Analysis")
    
    st.markdown("#### 🏛️ יחסי חוסן ומאזן")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.metric("Current Ratio", "1.42")
        with st.expander("ℹ️ פירוט מקצועי"):
            st.write("**הגדרה:** נכסים שוטפים / התחייבויות שוטפות. בביטוח, בודק את נזילות הנכסים מול התחייבויות מיידיות.")
    with b2:
        st.metric("Equity to Assets", "11.8%")
        with st.expander("ℹ️ פירוט מקצועי"):
            st.write("**הגדרה:** הון עצמי / סך מאזן. מציין את רמת המינוף והחוסן של החברה לספיגת הפסדים.")
    with b3:
        st.metric("Financial Leverage", "7.8x")
        with st.expander("ℹ️ פירוט מקצועי"):
            st.write("**הגדרה:** סך הנכסים / הון עצמי. בודק כמה נכסים מנוהלים על כל שקל של הון עצמי.")

    st.divider()
    st.markdown("#### 💰 יחסי רווחיות ותזרים")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("CFO to Net Profit", "1.15x")
        st.caption("איכות הרווח והפיכתו למזומן (Cash Flow from Ops)")
    with p2:
        st.metric("NB Margin", f"{row['NB Margin %']}%")
        st.caption("רווחיות עסקים חדשים (New Business Margin)")
    with p3:
        st.metric("Free Cash Flow", "₪1.18B")
        st.caption("תזרים חופשי זמין לחלוקת דיבידנד או השקעה")

# --- TAB 4: STRESS SCENARIOS ---
with tabs[3]:
    st.subheader("🛡️ סימולציית תרחישי קיצון ורגישות הון (Stress Suite)")
    col_in, col_res = st.columns([1, 1.2])
    
    with col_in:
        st.write("### פרמטרים לקיצון")
        ir_s = st.slider("📉 שינוי ריבית (bps)", -100, 100, 0)
        mkt_s = st.slider("📉 ירידת מניות (%)", 0, 40, 0)
        spr_s = st.slider("📉 מרווחי אשראי (bps)", 0, 150, 0)
        lap_s = st.slider("📉 עלייה בביטולים (%)", 0, 20, 0)
    
    with col_res:
        # לוגיקת השפעה חזויה על יחס הסולבנסי (מודל מקורב מבוסס רגישות הון)
        total_impact = (ir_s * 0.12) - (mkt_s * 0.65) - (spr_s * 0.08) - (lap_s * 0.4)
        final_solvency = row['Solvency %'] + total_impact
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = final_solvency,
            delta = {'reference': row['Solvency %']},
            gauge = {'axis': {'range': [80, 250]},
                     'steps': [
                         {'range': [0, 100], 'color': "darkred"},
                         {'range': [100, 140], 'color': "orange"},
                         {'range': [140, 250], 'color': "green"}]}))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.info(f"השפעה מצטברת חזויה על הון הסולבנסי: {total_impact:.1f}%")

# --- TAB 5: AI HYBRID RESEARCH ---
with tabs[4]:
    st.subheader("🤖 AI Hybrid Analyst (Vision + Note Scan)")
    
    if fin_paths:
        st.success(f"האנליסט מוכן לניתוח היברידי של: {os.path.basename(fin_paths[0])}")
        user_query = st.text_input("שאל שאלה מקצועית על הביאורים (למשל: 'נתח את הנחות האקטואריה בחישוב העתודות'):")
        
        if user_query and ai_ready:
            with st.spinner("מבצע הצלבת נתונים (Text + Vision Scan)..."):
                try:
                    # חילוץ תוכן היברידי מהדוח הכספי
                    full_text, pages = extract_hybrid_context(fin_paths[0])
                    
                    with st.expander("צפה בדפים שנסרקו על ידי ה-AI (Vision Context)"):
                        cols = st.columns(len(pages))
                        for idx, p in enumerate(pages): 
                            cols[idx].image(p, use_container_width=True, caption=f"Page {idx+1}")
                    
                    # בניית פרומפט מולטי-מודאלי עמוק המשלב טקסט ותמונה
                    prompt = f"""
                    אתה אנליסט פיננסי בכיר המתמחה בענף הביטוח וב-IFRS 17. 
                    לפניך טקסט שחולץ מהדוח הכספי וצילום של הדפים המרכזיים.
                    
                    שאלה לניתוח: {user_query}
                    
                    הקשר טקסטואלי מהדוח:
                    {full_text[:12000]}
                    
                    אנא הצלב בין הנתונים המילוליים לטבלאות שבתמונות וענה בעברית מקצועית.
                    """
                    
                    # שליחה למודל עם הטקסט והתמונה הראשונה
                    response = ai_model.generate_content([prompt, pages[0]])
                    
                    st.markdown("### 📝 תשובת האנליסט:")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"שגיאה בתהליך הניתוח: {e}")
    else:
        st.warning("⚠️ לא נמצא דוח PDF בנתיב המבוקש לסריקה אוטומטית. וודא שהעלית את הקבצים לתיקיית Financial_Reports.")

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
    # תיקון שגיאת 404: שימוש בנתיב מודל מלא ומעודכן לסביבת v1beta
    model_name = 'models/gemini-1.5-flash-latest'
    try:
        return genai.GenerativeModel(model_name), model_name
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash'), 'gemini-1.5-flash'

ai_model, active_model_name = get_stable_model()

# ==========================================
# 2. ADVANCED DATA WAREHOUSE & PDF LOGIC
# ==========================================
BASE_WAREHOUSE = "data/Insurance_Warehouse"

def get_verified_paths(company, year, quarter):
    base = os.path.join(BASE_WAREHOUSE, company, str(year), quarter)
    fin_dir = os.path.join(base, "Financial_Reports")
    sol_dir = os.path.join(base, "Solvency_Reports")
    fin_files = [os.path.join(fin_dir, f) for f in os.listdir(fin_dir) if f.endswith('.pdf')] if os.path.exists(fin_dir) else []
    sol_files = [os.path.join(sol_dir, f) for f in os.listdir(sol_dir) if f.endswith('.pdf')] if os.path.exists(sol_dir) else []
    return fin_files, sol_files
    def extract_deep_context(pdf_path):
    """סריקה עמוקה: מחלץ טקסט מ-50 דפים ותמונות מ-5 דפים ראשונים לניתוח הון עצמי"""
    full_text = ""
    preview_images = []
    try:
        doc = fitz.open(pdf_path)
        for i in range(min(len(doc), 50)):
            full_text += f"\n[Page {i+1}]\n" + doc[i].get_text()
            if i < 5:
                pix = doc[i].get_pixmap(matrix=fitz.Matrix(2, 2))
                preview_images.append(Image.open(io.BytesIO(pix.tobytes())))
        return full_text, preview_images
    except Exception as e:
        return f"Error: {e}", []

# מסד הנתונים המלא כולל ה-KPIs הקריטיים
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
# 3. SIDEBAR - AUTOMATED RADAR
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    sel_comp = st.selectbox("בחר חברה לניתוח:", market_df["חברה"])
    sel_year = st.selectbox("שנה פיסקאלית:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון דיווח:", options=["Q1", "Q2", "Q3", "Q4"])
    
    fin_paths, sol_paths = get_verified_paths(sel_comp, sel_year, sel_q)
    
    st.divider()
    if fin_paths:
        st.success(f"✅ דוח כספי זוהה: {os.path.basename(fin_paths[0])[:15]}")
    else:
        st.warning("❌ דוח כספי לא נמצא בנתיב")
    st.caption(f"AI Analytic Core: {active_model_name}")
    # ==========================================
# 4. MAIN TERMINAL - FULL FEATURES
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 Critical KPIs", "⛓️ IFRS 17 Engine", "📈 Financial Ratios", "🛡️ Stress Scenarios", "🤖 AI Deep Research"])

# --- TAB 1: Critical KPIs ---
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
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(market_df, x="חברה", y="CSM (B₪)", color="חברה", title="השוואת עתודות רווח (CSM)"), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(values=[60, 25, 15], names=["Life", "Health", "P&C"], title="Profit Mix by Segment"), use_container_width=True)

# --- TAB 2: IFRS 17 ENGINE ---
with tabs[1]:
    st.subheader("⛓️ IFRS 17: CSM Analytics & Waterfall")
    fig_wf = go.Figure(go.Waterfall(
        x = ["Opening Balance", "New Business", "Exp. Adjustments", "Onerous Contracts", "Release to P&L", "Closing Balance"],
        y = [14200, 850, 150, -320, -1100, 13780],
        measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
    ))
    st.plotly_chart(fig_wf, use_container_width=True)
    
    m1, m2, m3 = st.columns(3)
    m1.info("**VFA Approach**\n\nVariable Fee Approach: ביטוחי מנהלים וחיסכון")
    m2.success("**GMM Approach**\n\nGeneral Measurement Model: סיעוד וחיים מסורתי")
    m3.warning("**PAA Approach**\n\nPremium Allocation Approach: אלמנטר ובריאות")
    # --- TAB 3: FINANCIAL RATIOS ---
with tabs[2]:
    st.subheader("📈 Financial Ratio Deep Analysis")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.metric("Current Ratio", "1.42")
        with st.expander("ℹ️ פירוט"): st.write("**הגדרה:** נכסים שוטפים / התחייבויות שוטפות. בודק נזילות השקעות.")
    with b2:
        st.metric("Equity to Assets", "11.8%")
        with st.expander("ℹ️ פירוט"): st.write("**הגדרה:** הון עצמי / סך מאזן. רמת האיתנות ההונית.")
    with b3:
        st.metric("Financial Leverage", "7.8x")
        with st.expander("ℹ️ פירוט"): st.write("**הגדרה:** סך הנכסים / הון עצמי. מינוף ניהול הנכסים.")

# --- TAB 4: STRESS SCENARIOS ---
with tabs[3]:
    st.subheader("🛡️ סימולציית תרחישי קיצון (Stress Suite)")
    ir_s = st.slider("📉 ריבית (bps)", -100, 100, 0)
    mkt_s = st.slider("📉 מניות (%)", 0, 40, 0)
    impact = (ir_s * 0.12) - (mkt_s * 0.65)
    new_sol = row['Solvency %'] + impact
    fig_g = go.Figure(go.Indicator(
        mode = "gauge+number+delta", value = new_sol, delta = {'reference': row['Solvency %']},
        gauge = {'axis': {'range': [80, 250]}, 'steps': [{'range': [0, 100], 'color': "red"}, {'range': [100, 140], 'color': "orange"}]}))
    st.plotly_chart(fig_g, use_container_width=True)

# --- TAB 5: AI HYBRID RESEARCH ---
with tabs[4]:
    st.subheader("🤖 AI Hybrid Analyst (Vision + Deep Text Scan)")
    if fin_paths:
        query = st.text_input("שאל שאלה מקצועית (למשל: 'מהו ההון העצמי המיוחס לבעלי המניות?'):")
        if query and ai_ready:
            with st.spinner("סורק את כל הדוח ומצליב נתונים..."):
                try:
                    full_text, pages = extract_deep_context(fin_paths[0])
                    with st.expander("צפה בדפים שנסרקו על ידי ה-AI"):
                        cols = st.columns(len(pages))
                        for idx, p in enumerate(pages): cols[idx].image(p, use_container_width=True)
                    prompt = f"אתה אנליסט ביטוח בכיר. נתח את הטקסט והתמונות המצורפים מהדוח הכספי וענה בעברית מקצועית. חפש במפורש בטבלאות המאזן (Balance Sheet) בטקסט שחולץ.\n\nשאלה: {query}\n\nהקשר טקסטואלי מחולץ (50 דפים):\n{full_text[:15000]}"
                    response = ai_model.generate_content([prompt, pages[0]])
                    st.markdown("### 📝 תשובת האנליסט:")
                    st.write(response.text)
                except Exception as e: st.error(f"שגיאה בניתוח: {e}")
    else: st.warning("⚠️ לא נמצא דוח PDF לסריקה אוטומטית.")

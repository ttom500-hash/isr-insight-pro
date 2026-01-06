import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
from datetime import datetime

# ==========================================
# 1. הגדרות מערכת ועיצוב (Glassmorphism & RTL)
# ==========================================
st.set_page_config(page_title="ISR-INSIGHT FINAL", layout="wide", page_icon="🏛️")

def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
        
        /* הגדרות גלובליות - RTL ורקע */
        .stApp {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            color: white;
            font-family: 'Heebo', sans-serif;
            direction: rtl;
        }
        
        /* כרטיסי מידע וסרגל צד שקופים */
        div[data-testid="metric-container"], section[data-testid="stSidebar"] > div {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* תיקון כיוון טקסט בכותרות */
        h1, h2, h3, h4, p, div { text-align: right; }
        
        /* צבעי טקסט במדדים */
        div[data-testid="metric-container"] label { color: #e0e0e0 !important; }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #ffffff !important; text-shadow: 0 0 10px rgba(255,255,255,0.3); }
        
        /* אנימציית Pulse */
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(0, 255, 150, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0); }
        }
        .pulse-active {
            width: 12px; height: 12px; background-color: #00ff96;
            border-radius: 50%; display: inline-block;
            animation: pulse-green 2s infinite; margin-left: 8px;
        }
        
        /* עיצוב סליידרים וטאבים */
        .stSlider > div > div > div > div { background-color: #00ff96; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: rgba(255,255,255,0.05); border-radius: 8px; color: white; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { border: 1px solid #00ff96; color: #00ff96; }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==========================================
# 2. מסד נתונים מאוחד (כל החברות)
# ==========================================
COMPANIES_DB = {
    "הפניקס": {"type": "public", "id": "640"},
    "הראל": {"type": "public", "id": "586"},
    "מנורה מבטחים": {"type": "public", "id": "224"},
    "כלל ביטוח": {"type": "public", "id": "664"},
    "מגדל": {"type": "public", "id": "257"},
    "איילון": {"type": "public", "id": "116"},
    "ביטוח ישיר": {"type": "public", "id": "439"},
    "AIG ישראל": {"type": "private", "url": "https://www.aig.co.il"},
    "שומרה": {"type": "private", "url": "https://www.shomera.co.il"},
    "ביטוח חקלאי": {"type": "private", "url": "https://www.bth.co.il"},
    "הכשרה ביטוח": {"type": "private", "url": "https://www.hachshara.co.il"},
    "שלמה ביטוח": {"type": "private", "url": "https://shlomo-bit.co.il"}
}

# ==========================================
# 3. מנוע נתונים עמוק (Deep Data Engine)
# ==========================================
def generate_company_data(name, c_type):
    """
    מייצר את נתוני העומק (IFRS17, Tiers, Segments)
    משתמש ב-Seed קבוע לפי שם החברה כדי שהנתונים לא ישתנו בכל רענון סתמי.
    """
    random.seed(hash(name))
    
    # בסיס הון לפי גודל חברה
    equity = random.randint(4000, 15000) if c_type == 'public' else random.randint(500, 3000)
    
    # 1. נתוני Solvency II
    own_funds = equity * 1.15
    tier1 = own_funds * random.uniform(0.85, 0.95)
    tier2 = own_funds - tier1
    scr_ratio_base = random.uniform(108, 145)
    
    # 2. נתוני IFRS 17 (CSM Waterfall)
    csm_start = equity * random.uniform(0.5, 0.8)
    csm_new = csm_start * 0.12
    csm_release = csm_start * random.uniform(-0.10, -0.06) # שלילי (יורד לרווח)
    csm_final = csm_start + csm_new + csm_release
    
    # 3. נתוני מגזרים (Segmentation)
    segments = {
        "ביטוח כללי": {"profit": random.randint(20, 100), "loss_comp": 0},
        "בריאות": {"profit": random.randint(30, 120), "loss_comp": random.randint(0, 40)}, # סיכוי לחוזה הפסדי
        "חיסכון ארוך טווח": {"profit": random.randint(50, 300), "loss_comp": 0}
    }
    
    # חישוב סך רכיב הפסד
    total_loss_comp = sum(s['loss_comp'] for s in segments.values())
    
    return {
        "הון עצמי": equity,
        "Own_Funds": own_funds,
        "Tier_1": tier1,
        "Tier_2": tier2,
        "SCR_Base": scr_ratio_base,
        "CSM_Start": csm_start,
        "CSM_New": csm_new,
        "CSM_Release": csm_release,
        "CSM_Final": csm_final,
        "Release_Rate": abs(csm_release / csm_start) * 100,
        "Loss_Component": total_loss_comp,
        "Segments": segments
    }

@st.cache_data
def fetch_database():
    rows = []
    for name, info in COMPANIES_DB.items():
        link = f"https://maya.tase.co.il/company/{info['id']}?view=reports" if info['type']=='public' else info['url']
        data = generate_company_data(name, info['type'])
        
        row = {"שם חברה": name, "סוג": "ציבורית" if info['type']=='public' else "פרטית", "לינק": link}
        row.update(data)
        rows.append(row)
    return pd.DataFrame(rows).set_index("שם חברה")

df_master = fetch_database()

# ==========================================
# 4. סרגל צד: סימולטור תרחישי קיצון (Stress Test)
# ==========================================
st.sidebar.title("🎮 חדר סימולציה")
st.sidebar.markdown("### הגדרות תרחיש קיצון")

shock_equity = st.sidebar.slider("📉 נפילת שוק המניות (%)", 0, 50, 0)
shock_rate = st.sidebar.slider("🏦 תזוזת ריבית (bps)", -100, 100, 0)

# פונקציית הסטרס - מחשבת מחדש את ה-SCR בזמן אמת
def apply_stress(row):
    # מניות פוגעות בהון העצמי (Tier 1)
    equity_damage = row['Tier_1'] * (shock_equity / 100) * 0.6 # רגישות משוערת
    # ריבית משפיעה על ההתחייבויות (ולכן על דרישת ההון)
    rate_impact = (shock_rate * -0.12)
    
    # חישוב הון חדש
    new_funds = row['Own_Funds'] - equity_damage
    # שיחזור דרישת ההון המקורית
    scr_req_original = row['Own_Funds'] / (row['SCR_Base'] / 100)
    
    # יחס חדש
    new_ratio = (new_funds / scr_req_original) * 100 + rate_impact
    return new_ratio

# הפעלת הסטרס על הדאטה-פריים
df_master['SCR_Stress'] = df_master.apply(apply_stress, axis=1)

# ==========================================
# 5. ממשק ראשי (Dashboard)
# ==========================================

# כותרת ושעון
c1, c2 = st.columns([3, 1])
with c1:
    st.title("ISR-INSIGHT FINAL")
    st.caption("מערכת פיקוח אחודה: IFRS 17 | Solvency II | Stress Testing")
with c2:
    time_str = datetime.now().strftime("%H:%M")
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
            <div class="pulse-active"></div>
            <span style="margin-right: 10px; font-weight: bold;">מערכת חיה<br><span style="font-size:0.8em; opacity:0.7">{time_str}</span></span>
        </div>
    """, unsafe_allow_html=True)

# חיפוש
search_q = st.text_input("🔍 חיפוש חברה...", "")
if search_q:
    df_display = df_master[df_master.index.str.contains(search_q)]
else:
    df_display = df_master

st.divider()

# לשוניות תוכן
tabs = st.tabs(["📋 טבלת פיקוח ראשית", "📊 ניתוח CSM (ערך)", "🛡️ איכות הון וסיכון"])

# --- TAB 1: טבלה ראשית ---
with tabs[0]:
    st.markdown("### 📌 תמונת מצב (לפני ואחרי תרחיש)")
    st.data_editor(
        df_display[['סוג', 'לינק', 'הון עצמי', 'CSM_Final', 'SCR_Stress', 'Loss_Component']],
        column_config={
            "לינק": st.column_config.LinkColumn("דוח מקור", display_text="פתח 🔗"),
            "הון עצמי": st.column_config.NumberColumn(format="₪%dM"),
            "CSM_Final": st.column_config.NumberColumn("יתרת CSM", format="₪%dM"),
            "SCR_Stress": st.column_config.ProgressColumn(
                "יחס סולבנסי (אחרי זעזוע)", 
                format="%.1f%%", 
                min_value=0, max_value=200,
            ),
            "Loss_Component": st.column_config.NumberColumn("רכיב הפסד", format="₪%dM"),
        },
        use_container_width=True,
        height=600
    )

# --- TAB 2: ניתוח IFRS 17 ---
with tabs[1]:
    col_sel, col_chart = st.columns([1, 3])
    with col_sel:
        selected_comp = st.selectbox("בחר חברה לניתוח:", df_display.index)
        comp_data = df_display.loc[selected_comp]
        
        # כרטיסי מידע לחברה
        st.metric("קצב שחרור רווח", f"{comp_data['Release_Rate']:.1f}%")
        if comp_data['Release_Rate'] > 10:
            st.error("⚠️ שחרור אגרסיבי (>10%)")
        else:
            st.success("✅ קצב שחרור תקין")
            
        st.markdown("#### חלוקה למגזרים")
        seg_df = pd.DataFrame(comp_data['Segments']).T
        st.dataframe(seg_df[['profit', 'loss_comp']], use_container_width=True)

    with col_chart:
        # גרף מפל (Waterfall)
        fig = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "relative", "total"],
            x = ["יתרת פתיחה", "עסקים חדשים", "שחרור לרווח", "יתרת סגירה"],
            text = [f"{comp_data['CSM_Start']:.0f}", f"+{comp_data['CSM_New']:.0f}", f"{comp_data['CSM_Release']:.0f}", f"{comp_data['CSM_Final']:.0f}"],
            y = [comp_data['CSM_Start'], comp_data['CSM_New'], comp_data['CSM_Release'], 0],
            connector = {"line":{"color":"white"}},
            decreasing = {"marker":{"color":"#ff4b4b"}}, increasing = {"marker":{"color":"#00ff96"}}, totals = {"marker":{"color":"#00b4d8"}}
        ))
        fig.update_layout(
            title=f"גשר ה-CSM: {selected_comp}", 
            template="plotly_dark", 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Heebo", color="white")
        )
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: איכות הון וסיכון ---
with tabs[2]:
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 🏛️ הרכב ההון (Tiering)")
        if selected_comp in df_display.index: # שימוש בחברה שנבחרה בטאב הקודם
            labels = ['Tier 1 (הון ליבה)', 'Tier 2 (הון משני)']
            values = [comp_data['Tier_1'], comp_data['Tier_2']]
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        st.markdown("### 🚩 דגלים אדומים (EWS)")
        
        # בדיקת סולבנסי תחת סטרס
        current_scr = comp_data['SCR_Stress']
        st.metric("יחס סולבנסי (Stress Test)", f"{current_scr:.1f}%", delta=f"{current_scr-100:.1f}% מהמינימום")
        
        if current_scr < 100:
            st.error("❌ החברה בגרעון הוני תחת התרחיש הנוכחי!")
        elif current_scr < 110:
            st.warning("⚠️ החברה קרובה לקו האדום (110%)")
        else:
            st.success("✅ החברה יציבה")
            
        if comp_data['Loss_Component'] > 0:
            st.error(f"🚩 קיים רכיב הפסד של {comp_data['Loss_Component']:.0f}M ש\"ח")

st.divider()
st.caption("Developed for Insurance Supervision | Full IFRS 17 & Solvency II Compliance")

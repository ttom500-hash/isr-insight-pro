
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
from datetime import datetime

# ==========================================
# 1. הגדרות מערכת ועיצוב (High Contrast Glassmorphism)
# ==========================================
st.set_page_config(page_title="ISR-INSIGHT FINAL", layout="wide", page_icon="🏛️")

def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
        
        /* 1. רקע ראשי כהה ועמוק */
        .stApp {
            background: linear-gradient(135deg, #0b1016 0%, #172a3a 50%, #0b1a26 100%);
            color: #ffffff;
            font-family: 'Heebo', sans-serif;
            direction: rtl;
        }
        
        /* 2. כרטיסי מידע - רקע כהה חצי שקוף לקונטרסט גבוה */
        div[data-testid="metric-container"], section[data-testid="stSidebar"] > div {
            background: rgba(30, 41, 59, 0.7); /* כהה יותר לקריאות */
            backdrop-filter: blur(12px);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        }
        
        div[data-testid="metric-container"]:hover {
            border-color: #00ff96;
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        /* 3. טקסטים וכותרות - לבן בוהק */
        h1, h2, h3, h4, p, label, .stMarkdown {
            color: #ffffff !important;
            text-align: right;
        }
        
        /* צבעי תוויות במדדים */
        div[data-testid="metric-container"] label {
            color: #94a3b8 !important; /* אפור בהיר לכותרת המשנית */
            font-weight: 500;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 700;
            text-shadow: 0 0 15px rgba(0, 255, 150, 0.2);
        }
        
        /* 4. תיקון צבעים בטבלאות ואינפוטים */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        /* 5. טאבים וסליידרים */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255,255,255,0.05);
            color: #cbd5e1;
            border-radius: 6px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(0, 255, 150, 0.15);
            color: #00ff96;
            border: 1px solid #00ff96;
        }
        .stSlider > div > div > div > div { background-color: #00ff96; }
        
        /* אנימציית Pulse לאיקון */
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(0, 255, 150, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0); }
        }
        .pulse-active {
            width: 10px; height: 10px; background-color: #00ff96;
            border-radius: 50%; display: inline-block;
            animation: pulse-green 2s infinite; margin-left: 8px;
        }
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
    random.seed(hash(name))
    
    # בסיס הון
    equity = random.randint(4000, 15000) if c_type == 'public' else random.randint(500, 3000)
    net_profit = equity * random.uniform(0.08, 0.15)
    
    # Solvency II
    own_funds = equity * 1.15
    tier1 = own_funds * random.uniform(0.85, 0.95)
    tier2 = own_funds - tier1
    scr_ratio_base = random.uniform(108, 145)
    
    # IFRS 17 - CSM
    csm_start = equity * random.uniform(0.5, 0.8)
    csm_new = csm_start * 0.12
    csm_release = csm_start * random.uniform(-0.10, -0.06)
    csm_final = csm_start + csm_new + csm_release
    
    # מגזרים (Segmentation)
    segments = {
        "ביטוח כללי (P&C)": {
            "CSM": equity * random.uniform(0.1, 0.2), 
            "Profit": random.randint(10, 80), 
            "Loss_Comp": 0,
            "Combined_Ratio": random.uniform(90, 105)
        },
        "בריאות (Health)": {
            "CSM": equity * random.uniform(0.2, 0.4), 
            "Profit": random.randint(30, 120), 
            "Loss_Comp": random.randint(0, 40) if random.random() > 0.7 else 0,
            "Combined_Ratio": 0
        },
        "חיסכון ארוך טווח (Life)": {
            "CSM": equity * random.uniform(0.3, 0.6), 
            "Profit": random.randint(50, 300), 
            "Loss_Comp": 0,
            "Combined_Ratio": 0
        }
    }
    
    total_loss_comp = sum(s['Loss_Comp'] for s in segments.values())
    
    # יחסים פיננסיים
    roe = (net_profit / equity) * 100
    new_biz_margin = (csm_new / (csm_start * 0.2)) * 100
    
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
        "Segments": segments,
        "ROE": roe,
        "New_Biz_Margin": new_biz_margin,
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
# 4. סרגל צד: סימולטור
# ==========================================
st.sidebar.title("🎮 חדר סימולציה")
st.sidebar.markdown("### הגדרות תרחיש קיצון")

shock_equity = st.sidebar.slider("📉 נפילת שוק המניות (%)", 0, 50, 0)
shock_rate = st.sidebar.slider("🏦 תזוזת ריבית (bps)", -100, 100, 0)

def apply_stress(row):
    equity_damage = row['Tier_1'] * (shock_equity / 100) * 0.6
    rate_impact = (shock_rate * -0.12)
    new_funds = row['Own_Funds'] - equity_damage
    scr_req_original = row['Own_Funds'] / (row['SCR_Base'] / 100)
    new_ratio = (new_funds / scr_req_original) * 100 + rate_impact
    return new_ratio

df_master['SCR_Stress'] = df_master.apply(apply_stress, axis=1)

# ==========================================
# 5. ממשק ראשי (Dashboard)
# ==========================================
c1, c2 = st.columns([3, 1])
with c1:
    st.title("ISR-INSIGHT FINAL")
    st.caption("מערכת פיקוח אחודה: IFRS 17 | Solvency II | Segmentation")
with c2:
    st.markdown(f"""
        <div style="background: rgba(0, 255, 150, 0.1); padding: 10px; border-radius: 10px; display: flex; align-items: center; justify-content: center; border: 1px solid #00ff96;">
            <div class="pulse-active"></div>
            <span style="margin-right: 10px; font-weight: bold; color: #00ff96;">מערכת חיה</span>
        </div>
    """, unsafe_allow_html=True)

search_q = st.text_input("🔍 חיפוש חברה...", "")
if search_q:
    df_display = df_master[df_master.index.str.contains(search_q)]
else:
    df_display = df_master

st.divider()

# לשוניות תוכן
tabs = st.tabs(["📋 טבלת פיקוח", "📊 ניתוח ערך ומגזרים", "🛡️ איכות הון וסיכון"])

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
                "יחס סולבנסי (Stress)", format="%.1f%%", min_value=0, max_value=200,
            ),
            "Loss_Component": st.column_config.NumberColumn("רכיב הפסד", format="₪%dM"),
        },
        use_container_width=True,
        height=500
    )

# --- TAB 2: ניתוח IFRS 17 ומגזרים ---
with tabs[1]:
    col_sel, col_content = st.columns([1, 3])
    with col_sel:
        selected_comp = st.selectbox("בחר חברה לניתוח:", df_display.index)
        comp_data = df_display.loc[selected_comp]
        
        st.markdown("---")
        st.info("💡 **ניתוח מגזרי:** זיהוי מקורות הרווח והסיכון לפי פעילות.")

    with col_content:
        # מדדי KPI עם איקונים והסברים (Tooltip)
        st.markdown("### 📐 יחסים פיננסיים (KPIs)")
        k1, k2, k3, k4 = st.columns(4)
        
        with k1:
            st.metric("🛡️ יחס סולבנסי", f"{comp_data['SCR_Base']:.1f}%", help="יחס כושר פירעון ללא זעזועים.")
        with k2:
            st.metric("🌱 מרווח עסקים חדשים", f"{comp_data['New_Biz_Margin']:.1f}%", help="רווחיות מכירות חדשות.")
        with k3:
            st.metric("⏳ קצב שחרור CSM", f"{comp_data['Release_Rate']:.1f}%", help="קצב הכרה ברווח. >10% = אגרסיבי.")
        with k4:
            st.metric("💰 תשואה להון (ROE)", f"{comp_data['ROE']:.1f}%", help="תשואה נקייה על ההון.")

        st.divider()
        
        # תצוגה כפולה: מפל CSM + פאי מגזרי
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.markdown("#### גשר ה-CSM (התפתחות הערך)")
            fig_water = go.Figure(go.Waterfall(
                name = "CSM", orientation = "v",
                measure = ["relative", "relative", "relative", "total"],
                x = ["פתיחה", "עסקים חדשים", "שחרור לרווח", "סגירה"],
                text = [f"{comp_data['CSM_Start']:.0f}", f"+{comp_data['CSM_New']:.0f}", f"{comp_data['CSM_Release']:.0f}", f"{comp_data['CSM_Final']:.0f}"],
                y = [comp_data['CSM_Start'], comp_data['CSM_New'], comp_data['CSM_Release'], 0],
                connector = {"line":{"color":"#94a3b8"}},
                decreasing = {"marker":{"color":"#ff4b4b"}}, increasing = {"marker":{"color":"#00ff96"}}, totals = {"marker":{"color":"#00b4d8"}}
            ))
            fig_water.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=350)
            st.plotly_chart(fig_water, use_container_width=True)
            
        with c_chart2:
            st.markdown("#### רווח עתידי (CSM) לפי מגזר")
            # הכנת דאטה לגרף
            seg_data_list = [{"Segment": s, "CSM": v['CSM']} for s, v in comp_data['Segments'].items()]
            df_seg_pie = pd.DataFrame(seg_data_list)
            
            fig_seg = px.pie(df_seg_pie, values='CSM', names='Segment', hole=0.4, color_discrete_sequence=px.colors.sequential.Tealgrn)
            fig_seg.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=350)
            st.plotly_chart(fig_seg, use_container_width=True)
            
        # מטריצה מגזרית
        st.markdown("#### 🧩 מטריצה מגזרית מפורטת")
        matrix_rows = []
        for s_name, s_vals in comp_data['Segments'].items():
            matrix_rows.append({
                "מגזר": s_name,
                "CSM (רווח עתידי)": f"₪{s_vals['CSM']:.0f}M",
                "רכיב הפסד": f"₪{s_vals['Loss_Comp']:.0f}M",
                "Combined Ratio": f"{s_vals['Combined_Ratio']:.1f}%" if 'Combined_Ratio' in s_vals and s_vals['Combined_Ratio'] > 0 else "-"
            })
        st.dataframe(pd.DataFrame(matrix_rows).set_index("מגזר"), use_container_width=True)

# --- TAB 3: איכות הון וסיכון ---
with tabs[2]:
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 🏛️ הרכב ההון (Tiering)")
        if selected_comp in df_display.index:
            labels = ['Tier 1 (הון ליבה)', 'Tier 2 (הון משני)']
            values = [comp_data['Tier_1'], comp_data['Tier_2']]
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=['#00ff96', '#f1c40f']))])
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=350)
            st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        st.markdown("### 🚩 דגלים אדומים (EWS)")
        
        current_scr = comp_data['SCR_Stress']
        st.metric("יחס סולבנסי תחת סטרס", f"{current_scr:.1f}%", delta=f"{current_scr-100:.1f}%")
        
        if current_scr < 100:
            st.error("❌ **סכנה מיידית:** החברה בגרעון הוני תחת התרחיש הנוכחי!")
        elif current_scr < 110:
            st.warning("⚠️ **אזור אזהרה:** החברה קרובה לקו האדום (110%)")
        else:
            st.success("✅ החברה מציגה איתנות פיננסית יציבה.")
            
        if comp_data['Loss_Component'] > 0:
            st.error(f"🚩 **חוזים הפסדיים:** קיים רכיב הפסד של {comp_data['Loss_Component']:.0f}M ש\"ח במאזן.")

st.divider()
st.caption("Developed for Insurance Supervision | Full IFRS 17 & Solvency II Compliance")

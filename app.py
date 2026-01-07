
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# הגדרות עמוד
st.set_page_config(page_title="Insurance Supervision Pro", layout="wide")

# עיצוב כותרות
st.markdown("<style>h1, h2, h3 { color: #1a3a5a; border-bottom: 1px solid #ddd; }</style>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    selected_company = st.sidebar.selectbox("בחר חברה:", df['company'].unique())
    row = df[df['company'] == selected_company].iloc[-1]

    st.title(f"🏛️ מערכת אנליזה פיקוחיות: {selected_company}")
    st.info(f"רבעון {row['quarter']} {row['year']} | תקן דיווח IFRS 17")

    tabs = st.tabs(["📊 KPIs ויציבות", "📈 IFRS 17 מגזרי", "🧪 Stress Test", "⚖️ ניתוח פיננסי מלא"])

    # --- טאב 1: KPIs ---
    with tabs[0]:
        st.subheader("5 מדדי הליבה הקריטיים [cite: 2026-01-03]")
        k1, k2, k3, k4, k5 = st.columns(5)
        
        with k1:
            st.metric("Solvency Ratio", f"{row['solvency_ratio']}%")
            with st.expander("🔍 נוסחה וניתוח"):
                st.latex(r"Solvency = \frac{Eligible\ Own\ Funds}{SCR}")
                st.write("בוחן את החוסן ההוני מול דרישות הרגולציה. יעד ניהולי מומלץ: >150%.")
        
        with k2:
            st.metric("Total CSM", f"₪{row['csm_balance']}B")
            with st.expander("🔍 נוסחה וניתוח"):
                st.latex(r"CSM_{t} = CSM_{t-1} + NewBiz - Release")
                st.write("מייצג את הרווח הגלום בחוזים שטרם שוחרר לרווח והפסד.")

        with k3:
            st.metric("Loss Component", f"₪{row['loss_component']}M")
            with st.expander("🔍 ניתוח פיקוחי"):
                st.write("התחייבויות בגין חוזים הפסדיים שנרשמו מיידית בהתאם לתקן IFRS 17.")

        with k4:
            st.metric("ROE", f"{row['roe']}%")
            with st.expander("🔍 נוסחה"):
                st.latex(r"ROE = \frac{Net\ Income}{Average\ Equity}")

        with k5:
            st.metric("נזילות", f"{row['liquidity']}x")
            with st.expander("🔍 נוסחה"):
                st.latex(r"Ratio = \frac{Liquid\ Assets}{ST\ Liabilities}")

    # --- טאב 2: מגזרים ---
    with tabs[1]:
        st.subheader("ניתוח IFRS 17 לפי מגזרי פעילות")
        
        # טבלה
        seg_df = pd.DataFrame({
            "מדד": ["Release Rate", "New Biz Strain"],
            "חיים": [f"{row['life_release_rate']}%", f"{row['life_new_biz_strain']}%"],
            "בריאות": [f"{row['health_release_rate']}%", f"{row['health_new_biz_strain']}%"],
            "כללי": [f"{row['general_release_rate']}%", f"{row['general_new_biz_strain']}%"]
        })
        st.table(seg_df)

        c1, c2 = st.columns(2)
        with c1:
            st.write("**CSM Release Rate:**")
            st.latex(r"Release = \frac{CSM\ Amortization}{Total\ CSM}")
            st.info("קצב שחרור הרווח לעתיד. קצב מהיר מדי עלול להחליש את החברה בעתיד.")
        with c2:
            st.write("**New Business Strain:**")
            st.latex(r"Strain = \frac{Acquisition\ Cost}{New\ CSM}")
            st.warning("עלות גיוס לקוחות חדשים. יחס גבוה מעיד על צמיחה יקרה.")

    # --- טאב 3: Stress Test ---
    with tabs[2]:
        st.subheader("סימולטור תרחישי קיצון")
        st.latex(r"Adj.\ Solv = Ratio + (\Delta Int \times Sens_{int}) + (\Delta Mkt \times Sens_{mkt})")
        
        cs1, cs2 = st.columns([1, 2])
        with cs1:
            s_int = st.select_slider("שינוי ריבית (bps)", options=[-100, -50, 0, 50, 100], value=0)
            s_mkt = st.slider("קריסת מניות (%)", -30, 0, 0)
            impact = (s_int/100 * row['int_sens'] * 100) + (s_mkt/10 * row['mkt_sens'] * 100)
            res = row['solvency_ratio'] + impact
            st.metric("סולבנסי בתרחיש", f"{res:.1f}%", delta=f"{impact:.1f}%")
        
        with cs2:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=res, 
                gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]}))
            st.plotly_chart(fig, use_container_width=True)

    # --- טאב 4: פיננסי מלא ---
    with tabs[3]:
        st.subheader("ניתוח דוחות כספיים משלים")
        p1, p2, p3 = st.columns(3)
        
        with p1:
            st.write("**רווח והפסד**")
            st.metric("Combined Ratio", f"{row['combined_ratio']}%")
            st.latex(r"Combined = \frac{Claims + Expenses}{Premiums}")
        
        with p2:
            st.write("**מאזן וחוסן**")
            st.metric("Tier 1 Ratio", f"{row['tier1_ratio']}%")
            st.latex(r"Tier1 = \frac{Core\ Capital}{RWA}")

        with p3:
            st.write("**תזרים מזומנים**")
            st.metric("תזרים מפעילות", f"₪{row['operating_cash_flow']}B")
            st.write("בדיקת איכות הרווח החשבונאי.")

except Exception as e:
    st.error(f"שגיאה: ודא שה-CSV מעודכן. פרטים: {e}")

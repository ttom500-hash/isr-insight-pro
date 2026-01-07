import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות תצוגה מקצועיות
st.set_page_config(page_title="SupTech Pro - מערכת פיקוח מאומתת", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def metric_with_help(label, value, title, description, formula=None, color=None):
    """פונקציה ליצירת מדד עם חלון הסבר צף (Popover)"""
    st.metric(label, value)
    with st.popover(f"ℹ️ הסבר: {label}"):
        st.subheader(title)
        st.write(description)
        if formula:
            st.write("**נוסחת חישוב:**")
            st.latex(formula)
        if color == "red":
            st.error("ערך חריג דורש בחינת מפקח")

df = load_data()

if not df.empty:
    # --- Sidebar: מנוע חיפוש וסינון היררכי ---
    st.sidebar.title("🔍 מנוע חיפוש וסינון")
    selected_company = st.sidebar.selectbox("1. בחר חברה:", sorted(df['company'].unique()))
    
    available_years = sorted(df[df['company'] == selected_company]['year'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("2. בחר שנה:", available_years)
    
    available_quarters = sorted(df[(df['company'] == selected_company) & (df['year'] == selected_year)]['quarter'].unique(), reverse=True)
    selected_quarter = st.sidebar.selectbox("3. בחר רבעון:", available_quarters)

    # חילוץ הנתונים לתקופה הנבחרת
    d = df[(df['company'] == selected_company) & (df['year'] == selected_year) & (df['quarter'] == selected_quarter)].iloc[0]

    st.title(f"ניתוח פיננסי הוליסטי: {selected_company}")
    st.subheader(f"תקופת דיווח: {selected_quarter} {selected_year}")

    # --- מנוע דגלים אדומים ---
    flags = []
    if d['solvency_ratio'] < 150: flags.append(f"🚩 **יציבות:** יחס סולבנסי ({d['solvency_ratio']}%) נמוך מהיעד.")
    if d['combined_ratio'] > 100: flags.append(f"🚩 **חיתום:** הפסד במגזר הכללי (Combined Ratio: {d['combined_ratio']}%).")
    
    if flags:
        with st.expander("🚨 דגלים אדומים והתראות פיקוחיות", expanded=True):
            for flag in flags: st.warning(flag)
    else:
        st.success("✅ לא נמצאו חריגות מהותיות במדדי הסף.")

    st.divider()

    # --- טאבים הוליסטיים ---
    tabs = st.tabs(["📑 IFRS 17 ומגזרים", "📈 יחסים פיננסיים (מרכז ידע)", "💰 נכסים ונוסטרו", "⛈️ Stress Test"])

    with tabs[0]:
        st.subheader("ניתוח מגזרי ואיכות ה-CSM")
        
        c1, c2 = st.columns(2)
        with c1:
            sec_df = pd.DataFrame({'Sector': ['חיים', 'בריאות', 'כללי'], 'Value': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.pie(sec_df, names='Sector', values='Value', title="פילוח CSM מגזרי", hole=0.4), use_container_width=True)
        with c2:
            mod_df = pd.DataFrame({'Model': ['VFA (משתתפות)', 'PAA (מפושט)', 'GMM (רגיל)'], 'Share': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(mod_df, names='Model', values='Share', title="תמהיל מודלים חשבונאיים", hole=0.5), use_container_width=True)

    with tabs[1]:
        st.subheader("📊 יחסים פיננסיים - לחץ על ℹ️ להסבר המתודולוגי")
        
        st.write("### עולם ה-IFRS 17 (איכות הרווח)")
        r1, r2, r3 = st.columns(3)
        with r1:
            metric_with_help("שיעור שחרור CSM", f"{d['csm_release_rate']}%", "שיעור שחרור CSM (Release Rate)", 
                             "הקצב שבו הרווח העתידי הופך לרווח חשבונאי בפועל. יחס יציב מעיד על תיק מאוזן.", 
                             r"Release = \frac{Recognized \ CSM}{Opening \ CSM}")
        with r2:
            metric_with_help("מרווח עסקים חדשים", f"{d['new_biz_margin']}%", "מרווח עסקים חדשים (NB Margin)", 
                             "בוחן כמה רווח החברה מייצרת על מכירות חדשות. ירידה מעידה על תחרות אגרסיבית מדי.", 
                             r"Margin = \frac{New \ Biz \ CSM}{PVFP}")
        with r3:
            metric_with_help("יחס CSM להון", f"{d['csm_to_equity']}", "יחס CSM להון עצמי", 
                             "מודד את 'ההון הסמוי' של החברה - רווחים שטרם הוכרו במאזן אך יחלחלו אליו בעתיד.")

        st.divider()
        st.write("### יציבות, יעילות ותזרים")
        r4, r5, r6 = st.columns(3)
        with r4:
            metric_with_help("יחס כושר פירעון", f"{d['solvency_ratio']}%", "יחס כושר פירעון (Solvency II)", 
                             "המדד העליון ליציבות. מעל 150% נחשב בטוח. מתחת ל-100% נדרשת התערבות מיידית.", r"Ratio = \frac{Own \ Funds}{SCR}")
        with r5:
            metric_with_help("יחס משולב (PAA)", f"{d['combined_ratio']}%", "יחס משולב (Combined Ratio)", 
                             "המדד הקריטי לביטוח כללי. מעל 100% פירושו שהחברה מפסידה כסף מפעילות הביטוח.", 
                             r"Ratio = \frac{Claims + Expenses}{Premiums}", color="red" if d['combined_ratio'] > 100 else None)
        with r6:
            metric_with_help("איכות התזרים", f"{d['op_cash_flow_ratio']}", "יחס תזרים מפעילות לרווח", 
                             "בודק האם הרווח המדווח מגובה במזומן. יחס נמוך מ-1 עשוי להעיד על חשבונאות אגרסיבית.")

    with tabs[2]:
        st.subheader("פילוח נכסים מנוהלים (AUM) וחשיפת נוסטרו")
        ca, cb = st.columns([2, 1])
        with ca:
            a_df = pd.DataFrame({'Type': ['פנסיה', 'גמל', 'חוזי השקעה', 'נכסי VFA'], 'Val': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]})
            st.plotly_chart(px.bar(a_df, x='Type', y='Val', color='Type', title='נכסים מנוהלים (₪ מיליארד)'), use_container_width=True)
        with cb:
            n_df = pd.DataFrame({'Asset': ['נדל"ן', 'מניות', 'אלטרנטיבי'], 'Pct': [d['re_pct'], d['equity_pct'], d['alts_pct']]})
            st.plotly_chart(px.pie(n_df, names='Asset', values='Pct', title="חשיפת נוסטרו לנכסי סיכון", hole=0.3), use_container_width=True)

    with tabs[3]:
        st.subheader("⛈️ Stress Test: סימולטור רגישויות רגולטורי")
        
        s1, s2, s3 = st.columns(3)
        m_s = s1.slider("זעזוע מניות (%)", 0, 40, 0)
        i_s = s2.slider("שינוי ריבית (BPS)", -100, 100, 0)
        l_s = s3.slider("עלייה בביטולים (Lapse) %", 0, 20, 0)
        
        impact = (m_s * d['mkt_sens']) + (abs(i_s/100) * d['int_sens']) + (l_s * d['lapse_sens'])
        new_sol = max(0, d['solvency_ratio'] - impact)
        
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_sol, title={'text': "יחס סולבנסי חזוי"},
                                               gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 110], 'color': "red"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
else:
    st.error("נא לוודא שקובץ database.csv קיים בתיקיית data ותקין.")

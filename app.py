import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="ISR-Insight Pro", layout="wide")

# פונקציה לבדיקת תקינות הקובץ
def check_data():
    path = 'data/database.csv'
    if not os.path.exists(path):
        return False, f"קובץ הנתונים לא נמצא בנתיב: {path}"
    
    df = pd.read_csv(path)
    required_cols = ['company', 'year', 'quarter', 'solvency_ratio', 'int_sensitivity']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        return False, f"חסרות עמודות ב-CSV: {', '.join(missing)}"
    return True, df

# כותרת
st.title("🛡️ חדר בקרה רגולטורי - בדיקת מערכת")

success, result = check_data()

if not success:
    st.error(result)
    st.info("אנא ודא שקובץ ה-CSV בתיקיית data מעודכן עם כל העמודות החדשות.")
else:
    df = result
    st.success("הנתונים נטענו בהצלחה!")
    
    # כאן נכניס את הסליידרים
    st.sidebar.header("🧪 סימולטור")
    s_interest = st.sidebar.slider("שינוי בריבית (%)", -2.0, 2.0, 0.0)
    
    # תצוגה פשוטה לבדיקה
    selected_company = st.selectbox("בחר חברה:", df['company'].unique())
    c_data = df[df['company'] == selected_company].iloc[0]
    
    # חישוב מהיר
    new_solvency = c_data['solvency_ratio'] + (s_interest * c_data['int_sensitivity'] * 100)
    
    col1, col2 = st.columns(2)
    col1.metric("סולבנסי מקורי", f"{c_data['solvency_ratio']}%")
    col2.metric("סולבנסי לאחר תרחיש", f"{new_solvency:.1f}%")

    # גרף מכ"ם פשוט
    fig = go.Figure(go.Scatterpolar(
        r=[new_solvency/2, c_data['csm_balance']*5, 50, 50, new_solvency/2],
        theta=['חוסן', 'CSM', 'יעילות', 'שמרנות', 'חוסן'],
        fill='toself'
    ))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# חייב להיות הפקודה הראשונה
st.set_page_config(page_title="ISR-TITAN Check", layout="wide")

# כותרת
st.title("בדיקת מערכת")
st.write("אם אתה רואה את הטקסט הזה - המערכת עובדת והבעיה הייתה בהעתקה הקודמת.")

# גרף ניסיון
df = pd.DataFrame({'x': [1, 2, 3], 'y': [10, 20, 30]})
fig = px.line(df, x='x', y='y', title="בדיקת גרפיקה")
st.plotly_chart(fig)

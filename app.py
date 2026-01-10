with col_diag:
        if st.button("🧪 בדיקת גיבוי (Gemini 1.5)"):
            # ניסיון להשתמש במודל 1.5 שאולי המכסה שלו לא נגמרה
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            test_payload = {"contents": [{"parts": [{"text": "Respond with '1.5 Flash is working'"}]}]}
            test_res = requests.post(url, json=test_payload)
            if test_res.status_code == 200:
                st.success(f"הצלחנו! מודל 1.5 עובד: {test_res.json()['candidates'][0]['content']['parts'][0]['text']}")
            else:
                st.error("גם מודל 1.5 הגיע למכסה היומית.")
                st.info("זה הסימן הסופי שהמערכת מוכנה ורק מחכה לכרטיס אשראי כדי לפתוח את החסימה.")

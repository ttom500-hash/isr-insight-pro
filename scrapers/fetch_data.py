import pandas as pd
import os

def update_database():
    # נתוני בסיס לכל חברות הביטוח בישראל (נתונים ראשוניים להקמה)
    data = {
        'company': ['הפניקס', 'הראל', 'כלל', 'מגדל', 'מנורה', 'איילון', 'ביטוח ישיר', 'ליברה', 'וישור'],
        'date': ['2026-01-06'] * 9,
        'solvency_ratio': [172, 165, 158, 155, 161, 152, 148, 145, 140],
        'csm_balance': [12.5, 11.8, 9.2, 10.1, 11.0, 2.1, 1.5, 0.8, 0.6],
        'loss_component': [450, 380, 520, 410, 395, 110, 45, 20, 15]
    }
    
    df = pd.DataFrame(data)
    
    # יצירת תיקייה לנתונים אם היא לא קיימת
    os.makedirs('data', exist_ok=True)
    
    # שמירה לתוך קובץ ה-CSV שהאפליקציה תקרא
    df.to_csv('data/database.csv', index=False, encoding='utf-8-sig')
    print("הנתונים נשמרו בהצלחה!")

if __name__ == "__main__":
    update_database()

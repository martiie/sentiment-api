from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
from typing import Optional
from db import get_connection
from load_data_exchange import refresh_data
from datetime import datetime
from collections import defaultdict
import pandas as pd
import google.generativeai as genai
import os
# from pythainlp import word_tokenize
# from pythainlp.corpus.common import thai_stopwords

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # หรือ ["*"] เพื่อให้ทุก origin เข้าถึงได้ (ใช้เฉพาะช่วง dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#---------------------------------------------------------------------------------------------------------------------------------------------Regression

modelGML = joblib.load("model/GLM.pkl")

# Request schema
class PredictionInput(BaseModel):
    alb: float
    treat_embolize: int
    treat_surgery: int
    hct: float
    locbleed_left_lobe: int
    shock_No_shock: int
    loctumor_left_lobe: int
    sen: int
    sex_male: int
    sex_female: int
    hvivcinvade: int
    hepencep: int
    shock_Shock: int
    locbleed_right_lobe: int
    active: int
    pvinvade: int
    ascites: int
    treat_conservative: int
    inr: float
    tb: float
    child: int
    bclcstage: int

@app.post("/predict_survival")
def predict_survival(data: PredictionInput):
    try:
        input_df = pd.DataFrame([data.dict()])
        prediction = modelGML.predict(input_df)
        return {"predicted_days": float(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#-----------------------------------------------------------------------------------------------------------------ETL exchange
@app.get("/exchange_rates/")
def get_exchange_rates(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),):

    refresh_data()
    conn = get_connection()
    cur = conn.cursor()

    base_query = "SELECT * FROM exchange_rates"
    conditions = []
    params = []

    # Filter ตามปี
    if year:
        conditions.append("EXTRACT(YEAR FROM period) = %s")
        params.append(year)

    # Filter ตามเดือน (ต้องกรอกปีด้วย)
    if month and year:
        conditions.append("EXTRACT(MONTH FROM period) = %s")
        params.append(month)

    # Filter ตามช่วงวันที่
    if start_date:
        conditions.append("period >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("period <= %s")
        params.append(end_date)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY period"

    cur.execute(base_query, params)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results
        
@app.get("/exchange_rates/all")
def get_all_exchange_rates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT period, rate FROM exchange_rates ORDER BY period")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [[row[0].isoformat(), row[1]] for row in rows]
    
@app.get("/available_periods/")
def get_available_periods():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT period FROM exchange_rates")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # ประมวลผลเป็นโครงสร้าง {year: [month1, month2, ...]}
    periods = defaultdict(set)
    for (period,) in rows:
        dt = period  # ถ้า period เป็น datetime.date อยู่แล้ว ไม่ต้องแปลง
        periods[dt.year].add(dt.month)

    return {year: sorted(list(months)) for year, months in periods.items()}

#----------------------------------------------------------------------------------------------------------- Chatbot
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCudfoHN4vVQfH9TVlLc4d1n97nRuZ29cs")
genai.configure(api_key=GOOGLE_API_KEY)

# ✅ สร้าง model
model = genai.GenerativeModel("gemini-2.0-flash")

class Message(BaseModel):
    text: str

# ✅ ฟังก์ชันคุยกับ Gemini โดยจำกัดหัวข้อ
def chat_with_gemini(message: str):
    prompt = (
        "คุณคือผู้ช่วยเฉพาะทางด้านโรคติดต่อทางเพศสัมพันธ์หรือ HIV เท่านั้น "
        "ห้ามตอบคำถามนอกเหนือจากเรื่องโรคติดต่อทางเพศสัมพันธ์หรือ HIV\n"
        f"คำถามจากผู้ใช้: {message}"
    )
    response = model.generate_content(prompt)
    return {"response": response.text}

# ✅ สร้าง endpoint POST สำหรับ chatbot
@app.post("/chat")
def chat(message: Message):
    try:
        result = chat_with_gemini(message.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#---------------------------------------------------------------------------------------------------------------------------NLP
# lr = joblib.load('model/logistic_model.pkl')
# cvec = joblib.load('model/count_vectorizer.pkl')
class Review(BaseModel):
    text: str
    
# thai_stopwords = list(thai_stopwords())

# def text_process(text):
#     final = "".join(u for u in text if u not in ("?", ".", ";", ":", "!", '"', "ๆ", "ฯ"))
#     final = word_tokenize(final)
#     final = " ".join(word for word in final)
#     final = " ".join(word for word in final.split() 
#                      if word.lower not in thai_stopwords)
#     return final
def sentiment_with_gemini(message: str):
    prompt = (
        "คุณคือผู้ช่วยทำการวิเคราะห์ความเห็นจากผู้ใช้ "
        "ตอบได้แค่ 'neg' หรือ 'neu' หรือ 'pos' เท่านั้น \n"
        f"คำถามจากผู้ใช้: {message}"
    )
    response = model.generate_content(prompt)
    return {"response": response.text}
    
@app.post("/predict")
def predict_sentiment(review: Review):
    result = chat_with_gemini(review.text)
    my_predictions = result['response'].replace("\n", "")
    print(my_predictions)
    if my_predictions == "neg":
        label = "negative"
    elif my_predictions == "neu":
        label = "neutral"
    else:
        label = "positive"

return {"sentiment": label}
    return {"sentiment": label}


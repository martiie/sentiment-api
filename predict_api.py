from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
from typing import Optional
from db import get_connection
from load_data_exchange import refresh_data
from datetime import datetime
from collections import defaultdict

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # หรือ ["*"] เพื่อให้ทุก origin เข้าถึงได้ (ใช้เฉพาะช่วง dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = joblib.load("model/sentiment_model_3class.pkl")

class Review(BaseModel):
    text: str

@app.post("/predict")
def predict_sentiment(review: Review):
    pred = pipeline.predict([review.text])[0]
    if pred == 0:
      label = "negative"  
    elif pred ==1:
      label= "neutral"
    else:
      label="positive"
    return {"sentiment": label}


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

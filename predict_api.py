from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib

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
      label = "positive"  
    elif pred ==1:
      label= "neutral"
    else:
      label="negative"
    return {"sentiment": label}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # หรือ ["*"] เพื่อให้ทุก origin เข้าถึงได้ (ใช้เฉพาะช่วง dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = joblib.load("model/sentiment_model.pkl")

class Review(BaseModel):
    text: str

@app.post("/predict")
def predict_sentiment(review: Review):
    pred = pipeline.predict([review])[0]
    label = "positive" if pred == 1 else "negative"
    return {"sentiment": label}

from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI()

model, vectorizer = joblib.load("model/sentiment_model.pkl")

class Review(BaseModel):
    text: str

@app.post("/predict")
def predict_sentiment(review: Review):
    vec = vectorizer.transform([review.text])
    pred = model.predict(vec)[0]
    label = "positive" if pred == 1 else "negative"
    return {"sentiment": label}

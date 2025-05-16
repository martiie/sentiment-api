FROM python:3.10-slim
# ติดตั้ง system dependencies ที่จำเป็นสำหรับ OpenCV
RUN apt-get update && apt-get install -y libgl1

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn", "predict_api:app", "--host", "0.0.0.0", "--port", "80"]

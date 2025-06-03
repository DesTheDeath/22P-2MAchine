from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI()

model = joblib.load('C:/Users/user/PycharmProjects/DataBases/LL/sgdclf_fp.pkl')
vectorizer = joblib.load('C:/Users/user/PycharmProjects/DataBases/LL/vectorizer_fp.pkl')

class Text(BaseModel):
    description: str

@app.get("/")
def read_root():
    return {"message": "Проверка систем"}

@app.post("/api/predict")
def predicted(text: Text):
    text_vector = vectorizer.transform([text.description])
    prediction = model.predict(text_vector)
    #probability = model.predict_proba(text_vector)

    return {
        "text": text.description,
        "predicted_category": prediction[0]
        #"probability": np.max(probability)
    }
# >>uvicorn LL.Api:app
# In Terminal
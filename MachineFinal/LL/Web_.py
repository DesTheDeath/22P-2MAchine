import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('C:/Users/user/PycharmProjects/DataBases/LL/cleaned_combined_sentences.csv')


def get_prediction(description):
    url = "http://127.0.0.1:8000/api/predict"
    payload = {"description": description}
    response = requests.post(url, json=payload)
    return response.json()


st.title("Классификация текста")

st.header("Введите текст")
description = st.text_area("Описание")

if st.button("Классифицировать"):
    if description:
        prediction = get_prediction(description)
        print(prediction)
        st.success(f"Предсказанная категория: {prediction['predicted_category']}")
        #st.write(f"Вероятность: {prediction['probability']:.2f}")
    else:
        st.error("Пожалуйста, заполните все поля.")

st.header("Справка")
st.write("""
    Это приложение позволяет классифицировать текст по языкам.
    Введите Текст, затем нажмите кнопку "Классифицировать".
""")
# >>streamlit run C:\Users\user\PycharmProjects\DataBases\LL\Web_.py [ARGUMENTS]
# In Terminal
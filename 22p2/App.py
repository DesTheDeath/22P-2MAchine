import streamlit as st
import joblib
import numpy as np

model = joblib.load("Group1/boost_reg.pkl")

SUB_TYPES = ["Rezidans", 'Daire', 'Villa', 'Müstakil Ev', 'Kooperatif', 'Yazlık', 'Komple Bina', 'Prefabrik Ev',
               'Köşk / Konak / Yalı', 'Çiftlik Evi', 'Yalı Dairesi', 'Loft']

opt = {'Rezidans': 1, 'Daire': 2, 'Villa': 3, 'Müstakil Ev': 4, 'Kooperatif': 5, 'Yazlık': 6, 'Komple Bina': 7, 'Prefabrik Ev': 8,
               'Köşk / Konak / Yalı': 9, 'Çiftlik Evi': 10, 'Yalı Dairesi': 11, 'Loft': 12}

HEATING_TYPES = ['Fancoil', 'Yok', 'Kalorifer (Doğalgaz)', 'Kalorifer (Kömür)',
       'Kombi (Elektrikli)', 'Klima', 'Kombi (Doğalgaz)',
       'Merkezi Sistem (Isı Payı Ölçer)', 'Merkezi Sistem',
       'Soba (Kömür)', 'Yerden Isıtma', 'Soba (Doğalgaz)',
       'Güneş Enerjisi', 'Kalorifer (Akaryakıt)', 'Jeotermal',
       'Kat Kaloriferi']

st.set_page_config(page_title="Прогноз цены жилья", layout="centered")

st.title("Прогноз цены жилья")

st.markdown("Введите характеристики объекта ниже")

col1, col2 = st.columns(2)

with col1:
    floors = st.number_input("Количество этажей", min_value=0, step=1, value=1)
    rooms = st.number_input("Количество комнат", min_value=0, step=1, value=2)
with col2:
    size = st.number_input("Размер (м²)", min_value=0.0, step=0.1, value=75.0)
    sub_type = st.selectbox("Подтип жилья", SUB_TYPES)

heating_type = st.selectbox("Тип отопления", HEATING_TYPES)

if st.button("Сделать прогноз"):
    try:
        for s in SUB_TYPES:
            if sub_type == s:
                sub_vec = opt[f'{sub_type}']
                break
        heat_vec = HEATING_TYPES.index(heating_type)

        features = [1, floors,2, rooms, size , sub_vec , heat_vec]
        X = np.array(features).reshape(1, -1)

        pred = model.predict(X)

        price = float(pred)
        formatted = f"₺{price:,.2f}"

        st.success("Готово")
        st.markdown(f"### Предсказанная цена\n**{formatted}**")
    except Exception as e:
        st.error(f"Ошибка при прогнозе: {e}")
        raise
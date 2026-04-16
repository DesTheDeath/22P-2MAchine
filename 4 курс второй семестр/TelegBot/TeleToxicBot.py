import json
import telebot
import numpy as np
import pickle
import mysql.connector
import sys
import re
import nltk
from string import punctuation
from fastapi import requests
from nltk.corpus import stopwords
import pymorphy2
from keras.models import load_model
from keras.preprocessing import sequence
from collections import deque

# Загружаем стоп-слова
nltk.download('stopwords')
russian_stopwords = set(stopwords.words('russian'))

morph = pymorphy2.MorphAnalyzer()

bot = telebot.TeleBot('token')

# Загрузка модели и токенизатора
try:
    model = load_model('toxicity_model.h5')
    with open('tokenizer.pickle', 'rb') as handle:
        tokenizer = pickle.load(handle)
    print("Загружена")
except Exception as e:
    print(f"Ошибка загрузки: {e}")
    model = None
    tokenizer = None

user_history = {}
ai_mode = False  # Initial mode is toxicity classification


# Функции предобработки
def clean_text(text):
    text = str(text).lower()
    text = text.replace('ё', 'е')
    text = re.sub(r'[^а-яa-z\s]', ' ', text)
    text = re.sub(r'((www\.[^\s]+)|(https?://[^\s]+))', 'URL', text)
    text = re.sub(' +', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def lemmatize_text(text):
    words = text.split()
    lemmatized_words = []
    for word in words:
        if word not in russian_stopwords and word not in punctuation and len(word) > 2:
            try:
                lemmatized_word = morph.parse(word)[0].normal_form
                lemmatized_words.append(lemmatized_word)
            except:
                continue
    return ' '.join(lemmatized_words)


def predict_toxicity(text):
    if model is None or tokenizer is None:
        return 0.5, "Модель не загружена"

    # Очистка и лемматизация
    text_clean = clean_text(text)
    text_lema = lemmatize_text(text_clean)

    if not text_lema:
        return 0.0, "Текст слишком короткий"

    sequences = tokenizer.texts_to_sequences([text_lema])
    padded = sequence.pad_sequences(sequences, maxlen=32, padding='post', truncating='post')

    prob = model.predict(padded, verbose=0)[0][0]

    return prob, text_lema

def get_dann(zapros: str):
    try:
        conn = mysql.connector.connect(
            user="root",
            password="Deth666",
            database="deathing_both",
            host="localhost",
            port="3306"
        )
        cur = conn.cursor()
        cur.execute(zapros)

        if zapros.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
            rows = cur.rowcount
        else:
            rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows
    except mysql.connector.Error as e:
        print(e)
        return [] if not zapros.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')) else 0


def get_or_create_user(user_id, name, username):
    """Получить пользователя или создать нового"""
    name = name.replace("'", "''") if name else ""
    username = username.replace("'", "''") if username else ""

    zapr = f"SELECT * FROM user WHERE id_user = {user_id}"
    user = get_dann(zapr)

    if not user:
        zapr = f"""
            INSERT INTO user (id_user, name, username, normal, toxic, count_search)
            VALUES ({user_id}, '{name}', '{username}', 0, 0, 0)
        """
        get_dann(zapr)
        print(f"Создан новый пользователь: {name} (ID: {user_id})")


def get_user_stats(user_id):
    """Получить статистику пользователя"""
    zapr = f"""
        SELECT normal, toxic, count_search
        FROM user
        WHERE id_user = {user_id}
    """
    result = get_dann(zapr)
    return result[0] if result else None


def get_all_users_stats():
    """Получить общую статистику по всем пользователям"""
    zapr = """
        SELECT 
            COUNT(DISTINCT id_user) as total_users,
            SUM(normal) as total_normal,
            SUM(toxic) as total_toxic,
            SUM(count_search) as total_searches
        FROM user
    """
    result = get_dann(zapr)
    return result[0] if result else None


def update_user_stats(user_id, is_toxic):
    """Обновить статистику пользователя"""
    zapr = f"""
        UPDATE user 
        SET count_search = count_search + 1
        WHERE id_user = {user_id}
    """
    get_dann(zapr)

    if is_toxic:
        zapr = f"""
            UPDATE user 
            SET toxic = toxic + 1
            WHERE id_user = {user_id}
        """
        get_dann(zapr)
    else:
        zapr = f"""
            UPDATE user 
            SET normal = normal + 1
            WHERE id_user = {user_id}
        """
        get_dann(zapr)

def get_main_keyboard():
    """Создает основную клавиатуру с кнопками"""
    silent = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True,  # Автоматически подгонять размер
        row_width=2,  # 2 кнопки в ряд
        one_time_keyboard=False  # Клавиатура не исчезает после нажатия
    )


# Buttons defination
btn_start = telebot.types.KeyboardButton('/start')
btn_help = telebot.types.KeyboardButton('/help')
btn_toxic = telebot.types.KeyboardButton('/toxic')
btn_profile = telebot.types.KeyboardButton('/profile')
btn_stats = telebot.types.KeyboardButton('/stats')
btn_ai = telebot.types.KeyboardButton('/ai')

silent = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
silent.add(btn_start, btn_help)
silent.add(btn_toxic, btn_profile)
silent.add(btn_stats, btn_ai)


@bot.message_handler(commands=['ai'])
def ai_command(message):
    global ai_mode
    ai_mode = True
    bot.send_message(
        message.chat.id,
        "*NN ассистент*\n\n"
        "Теперь в режиме AI!",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['toxic'])
def toxic_command(message):
    global ai_mode
    ai_mode = False
    bot.send_message(
        message.chat.id,
        "*NN ассистент*\n\n"
        "Вернулись к классификации токсичности!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)  # Handle all messages
def handle_message(message):
    if ai_mode:
        # KoboldCPP API Endpoint
        KOBOLDCPP_API_URL = "http://127.0.0.1:5001/api/v1/generate"

        # Persona / Context
        username = "Пользователь"
        botname = "Бот"
        PERSONA = f""

        user_id = message.from_user.id
        user_text = message.text
        username = message.from_user.first_name

        conversation_history = {}

        if user_text == "/start":
            bot.reply_to(message, "Здраствуйте, чем могу помочь?")
            return

        if user_id not in conversation_history:
            conversation_history[user_id] = PERSONA  # Initialize with persona

        full_prompt = conversation_history[user_id] + "<end_of_turn>\n<start_of_turn>user\n" + user_text + "<end_of_turn>\n<start_of_turn>model\n"

        payload = {
            "prompt": full_prompt,
            "max_context_length": 1024,  # вестимость контекста в токенах
            "max_length": 256,  # максимальная длина генерации в токенах
            "temperature": 0.7,  # Креативность модели
            "top_p": 0.9,
            "top_k": 40,
            "repetition_penalty": 1.176,  # пенальти на повторение
            "use_default_badwordsids": True
        }

        try:
            response = requests.post(KOBOLDCPP_API_URL, headers={'Content-Type': 'application/json'},
                                     data=json.dumps(payload))
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            generated_text = data["results"][0]["text"]
            bot_reply = f"{generated_text}"  # Construct the reply
            bot.reply_to(message, bot_reply)
            conversation_history[user_id] += "\n" + generated_text  # Добавляет ответ бота в контест
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to KoboldCPP: {e}")
            bot.reply_to(message, "Сервер сейчас недоступен. Попробуйте позже.")

    else:
        # Toxicity Classification Mode
        try:
            bot.send_chat_action(message.chat.id, 'typing')

            probability, processed_text = predict_toxicity(message.text)

            user_id = message.from_user.id
            if user_id not in user_history:
                user_history[user_id] = deque(maxlen=10)
            user_history[user_id].append((message.text[:50], probability))

            is_toxic = probability > 0.5
            update_user_stats(user_id, is_toxic)

            if probability > 0.5:
                toxicity_level = "🔴 ТОКСИЧНО"
                advice = "А ну ка не ругаться!"
            else:
                toxicity_level = "🟢 НОРМАЛЬНО"
                advice = "Вежливый вы человек!"

            # Прогресс-бар
            bar_len = 20
            filled = int(probability * bar_len)
            bar = '█' * filled + '░' * (bar_len - filled)

            response = (
                f"*{toxicity_level}*\n\n"
                f"{advice}\n\n"
                f"📊 *Вероятность:* {probability:.1%}\n"
                f"`[{bar}]`\n"
            )

            if processed_text and processed_text != "Текст слишком короткий" and processed_text != "Модель не загружена":
                short_processed = processed_text[:100] + "..." if len(processed_text) > 100 else processed_text
                response += f"\n *Токсичные слово(-а):* _{short_processed}_"

            bot.send_message(message.chat.id, response, parse_mode='Markdown')

        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка: {str(e)}\n\nПожалуйста, попробуйте позже.")


bot.infinity_polling()
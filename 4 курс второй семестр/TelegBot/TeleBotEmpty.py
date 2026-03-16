import subprocess

import telebot
import requests
import json
from PIL import Image
import io
import os

# Telegram Bot Token (replace with yours)
TELEGRAM_BOT_TOKEN = "Telebot:Key"
# KoboldCPP API Endpoint
KOBOLDCPP_API_URL = "http://127.0.0.1:5001/api/v1/generate"

MMPROJ_COMMAND = "/path/to/mmproj"

# Persona / Context
username = "Пользователь"
botname = "Бот"
PERSONA = f""

# История диалога
conversation_history = {}


bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_text = message.text
    username = message.from_user.first_name

    if user_text == "/start":
        bot.reply_to(message, "Здраствуйте, чем могу помочь?")
        return

    if user_id not in conversation_history:
        conversation_history[user_id] = PERSONA  # Initialize with persona

    if message.content_type == 'photo':
        # Process Image
        file_info = bot.get_file(message.photo[-1].file_id)  # Get largest photo size
        downloaded_file = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded_file))

        # Run mmproj to get visual description
        process = subprocess.Popen([MMPROJ_COMMAND, "--image", "temp.png"], stdout=subprocess.PIPE)
        img.save("temp.png")
        visual_description = process.communicate()[0].decode("utf-8").strip()
        prompt = PERSONA + " The image shows: " + visual_description
        if message.caption:
            prompt += " " + message.caption  # Add caption if exists


    else:  # Text Message
        prompt = PERSONA + " " + message.text
        if user_id not in conversation_history:
            conversation_history[user_id] = prompt
        else:
            conversation_history[user_id] += "\n" + message.text

    full_prompt = conversation_history[user_id] + "<end_of_turn>\n<start_of_turn>user\n" + user_text + "<end_of_turn>\n<start_of_turn>model\n"

    payload = {
        "prompt": full_prompt,
        "max_context_length": 1024, # вестимость контекста в токенах
        "max_length": 256,  # максимальная длина генерации в токенах
        "temperature": 0.7,  # Креативность модели
        "top_p": 0.9,
        "top_k": 40,
        "repetition_penalty": 1.176, # пенальти на повторение
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


bot.infinity_polling()
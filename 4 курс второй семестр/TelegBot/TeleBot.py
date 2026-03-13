import telebot
import requests
import json

# Telegram Bot Token (replace with yours)
TELEGRAM_BOT_TOKEN = "8689380863:AAEqu7DTGqGF_AMNhsH75ThTEEfsrYv4ceA"
# KoboldCPP API Endpoint
KOBOLDCPP_API_URL = "http://127.0.0.1:5001/api/v1/generate"

# Persona / Context
username = "Пользователь"
botname = "Генадий"
PERSONA = f""

# Store conversation history for each user
conversation_history = {}


bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(func=lambda message: True)  # Handle all messages
def handle_message(message):
    user_id = message.from_user.id
    user_text = message.text
    username = message.from_user.first_name  # Get the user's first name

    if user_text == "/start":
        bot.reply_to(message, "Здраствуйте, чем могу помочь?")
        return

    if user_id not in conversation_history:
        conversation_history[user_id] = PERSONA  # Initialize with persona

    full_prompt = conversation_history[user_id] + "<end_of_turn>\n<start_of_turn>user\n" + user_text + "<end_of_turn>\n<start_of_turn>model\n"

    payload = {
        "prompt": full_prompt,
        "max_context_length": 1024,
        "max_length": 256,  # Adjust as needed
        "temperature": 0.7,  # Adjust for creativity
        "top_p": 0.9,  # Adjust for diversity
        "top_k": 40,  # Adjust for variety
        "repetition_penalty": 1.176, # Adjust to prevent repetition
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
        conversation_history[user_id] += "\n" + generated_text  # Add bot's reply to history

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to KoboldCPP: {e}")
        bot.reply_to(message, "Sorry, something went wrong!")


bot.infinity_polling()
import telebot
import sqlite3
import requests
import random

# API Configuration
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_ID = "123456789"
FIVESIM_API_KEY = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI0MjU0NDEsImlhdCI6MTc0MDg4OTQ0MSwicmF5IjoiMDE3MTcyNmMzNzFhNTI0ZGY1NTNjZmZmMWM5NzJkZWMiLCJzdWIiOjMwNjU0NDZ9.B5kVFdXAs0O25ibyP-tufwXTSglcC3mRvdbbJrEmat6pGQaKyCTFSs9rePR2Nd7yvB3gZhHfp-YUUN3IQz3LOyFyIK8bogouWi_vplB9HxIowecu0Vdet520Etn4ABrTOfHMGMoQAG3VA48ufBd9dfWIKrjbrn33UpEHJHzzuiMyAv0ZHKpuLI_dE-Rm5umLChxmRPz-O10l84kh1inty48iJKW9xtH2oHpINatCqdp-TqWhQIWa1zmtkn-08znqdD4cZgZgmWd79FpRHXN82hk6TWVTCh9UXDxX-jc0d8kwTCJcmmGrKbV0UIauOEeZR6HpBQVj052cBYLzb9j9Vg"
BHARATPE_MERCHANT_ID = "YOUR_MERCHANT_ID"
BHARATPE_SECRET_KEY = "YOUR_SECRET_KEY"

bot = telebot.TeleBot(BOT_TOKEN)

# Database Connection
def db_connect():
    conn = sqlite3.connect("database.db")
    return conn

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (telegram_id, balance) VALUES (?, ?)", (user_id, 0.0))
        conn.commit()

    bot.send_message(user_id, "Welcome! Use /buy_number to get a virtual number.")

# Buy Number Command
@bot.message_handler(commands=['buy_number'])
def buy_number(message):
    user_id = message.chat.id
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (user_id,))
    user = cursor.fetchone()

    if user and user[0] >= 10:  # Number Price = ₹10
        response = requests.get(
            "https://5sim.net/v1/user/buy/activation",
            headers={"Authorization": f"Bearer {FIVESIM_API_KEY}"},
            params={"country": "russia", "operator": "any", "product": "telegram"}
        )

        data = response.json()
        if "phone" in data:
            phone_number = data["phone"]
            order_id = data["id"]

            cursor.execute("UPDATE users SET balance = balance - 10 WHERE telegram_id=?", (user_id,))
            conn.commit()

            bot.send_message(user_id, f"✅ Number Purchased: {phone_number}\nOrder ID: {order_id}\nUse /get_otp {order_id} to check OTP.")
        else:
            bot.send_message(user_id, "❌ Failed to buy number! Try again.")
    else:
        bot.send_message(user_id, "❌ Insufficient Balance! Use /add_funds to recharge.")

# Get OTP Command
@bot.message_handler(commands=['get_otp'])
def get_otp(message):
    user_id = message.chat.id
    args = message.text.split()

    if len(args) < 2:
        bot.send_message(user_id, "❌ Invalid Format! Use: /get_otp order_id")
        return

    order_id = args[1]

    response = requests.get(
        f"https://5sim.net/v1/user/check/{order_id}",
        headers={"Authorization": f"Bearer {FIVESIM_API_KEY}"}
    )

    data = response.json()
    if "sms" in data and data["sms"]:
        otp = data["sms"][0]["code"]
        bot.send_message(user_id, f"✅ Your OTP: {otp}")
    else:
        bot.send_message(user_id, "⏳ No OTP received yet! Try again after 1 min.")

# Add Funds Command
@bot.message_handler(commands=['add_funds'])
def add_funds(message):
    user_id = message.chat.id
    payment_url = f"http://yourdomain.com/generate_qr?user_id={user_id}&amount=10"
    bot.send_message(user_id, f"🔗 Pay via BharatPe:\n{payment_url}")

# Admin Panel Command
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.chat.id
    if str(user_id) == ADMIN_ID:
        bot.send_message(user_id, "🔹 Admin Panel 🔹\n\n/check_users - View All Users\n/add_balance [user_id] [amount] - Add Balance")
    else:
        bot.send_message(user_id, "❌ Access Denied!")

# Add Balance (Admin Command)
@bot.message_handler(commands=['add_balance'])
def add_balance(message):
    user_id = message.chat.id
    if str(user_id) == ADMIN_ID:
        try:
            _, target_id, amount = message.text.split()
            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = balance + ? WHERE telegram_id=?", (float(amount), target_id))
            conn.commit()
            bot.send_message(user_id, f"✅ Added ₹{amount} to {target_id}")
            bot.send_message(target_id, f"💰 ₹{amount} added to your account by Admin!")
        except:
            bot.send_message(user_id, "❌ Invalid Format! Use: /add_balance user_id amount")
    else:
        bot.send_message(user_id, "❌ Access Denied!")

# Run Bot
bot.polling()

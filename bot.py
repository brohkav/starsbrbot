import os
import logging
import json
import time
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
from config import MIN_STARS, RATES, PAYMENT_METHODS, MESSAGES

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_errors.log'),
        logging.StreamHandler()
    ]
)

# Загрузка конфига
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
SUPPORT_CHAT_ID = "broshkav"

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
user_data = {}

def save_history(user_id: int, stars: int, amount: float):
    data = {
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "stars": stars,
        "amount": amount
    }
    with open('history.json', 'a', encoding='utf-8') as f:
        json.dump({str(user_id): data}, f)
        f.write('\n')

def get_stars_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton("50 ⭐", callback_data="stars_50"),
        InlineKeyboardButton("100 ⭐", callback_data="stars_100"),
        InlineKeyboardButton("200 ⭐", callback_data="stars_200"),
        InlineKeyboardButton("Другое", callback_data="stars_custom")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_payment_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(PAYMENT_METHODS["kaspi"]["name"]))
    keyboard.add(KeyboardButton(PAYMENT_METHODS["cryptobot"]["name"]))
    keyboard.add(KeyboardButton(PAYMENT_METHODS["tonkeeper"]["name"]))
    return keyboard

def get_paid_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ Я оплатил", callback_data="user_paid"))
    return keyboard

def get_admin_confirm_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_{user_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{user_id}")
    )
    return keyboard

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton('⭐ Купить звёзды'),
        KeyboardButton('📊 История покупок'),
        KeyboardButton('💎 Бонусы'),
        KeyboardButton('🛟 Поддержка')
    )
    return markup

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "🔹 <b>Главное меню</b>\nВыберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message_handler(text='⭐ Купить звёзды')
async def show_stars_menu(message: types.Message):
    await message.answer(MESSAGES["start"], reply_markup=get_stars_keyboard())

@dp.message_handler(text='📊 История покупок')
async def show_history(message: types.Message):
    user_id = message.from_user.id
    try:
        with open('history.json', 'r', encoding='utf-8') as f:
            history = [json.loads(line) for line in f]
            user_history = [h for h in history if str(user_id) in h]
            
        if not user_history:
            await message.answer("📭 У вас пока нет покупок")
            return
            
        text = "📅 <b>Ваши покупки:</b>\n\n"
        for item in user_history[-5:]:
            data = item[str(user_id)]
            text += f"▪ {data['date']} - {data['stars']} звёзд ({data['amount']}₸)\n"
        
        await message.answer(text, parse_mode="HTML")
    except FileNotFoundError:
        await message.answer("📭 История покупок пуста")

@dp.message_handler(text='💎 Бонусы')
async def daily_bonus(message: types.Message):
    bonus = 0
    await message.answer(
        f"🎁 Бонусная система временно недоступна\n"
        f"🔸 Сегодня вы получили: {bonus} звёзд",
        parse_mode="HTML"
    )

@dp.message_handler(text='🛟 Поддержка')
async def support_request(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Написать оператору", url=f"t.me/{SUPPORT_CHAT_ID}"))
    await message.answer(
        "📩 Напишите ваш вопрос в чат поддержки:",
        reply_markup=markup
    )

@dp.callback_query_handler(lambda c: c.data.startswith("stars_"))
async def select_stars(callback_query: types.CallbackQuery):
    action = callback_query.data.split("_")[1]
    
    if action == "custom":
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            MESSAGES["select_amount"]
        )
        return
    
    stars = int(action)
    user_data[callback_query.from_user.id] = {"stars": stars}
    await bot.send_message(
        callback_query.from_user.id,
        MESSAGES["payment_choice"],
        reply_markup=get_payment_keyboard()
    )

@dp.message_handler(lambda message: message.text.isdigit())
async def process_custom_amount(message: types.Message):
    try:
        stars = int(message.text)
        
        if stars < MIN_STARS:
            await message.answer(MESSAGES["invalid_amount"])
            return
            
        user_data[message.from_user.id] = {"stars": stars}
        await message.answer(
            f"✅ Выбрано: {stars} звёзд\n" + MESSAGES["payment_choice"],
            reply_markup=get_payment_keyboard()
        )
    except:
        await message.answer("❌ Введите целое число (например: 1276).")

@dp.message_handler(lambda m: m.text in [
    PAYMENT_METHODS["kaspi"]["name"],
    PAYMENT_METHODS["cryptobot"]["name"],
    PAYMENT_METHODS["tonkeeper"]["name"]
])
async def select_payment(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.answer("❌ Сначала выберите количество звёзд!")
        return
    
    if message.text == PAYMENT_METHODS["kaspi"]["name"]:
        method = "kaspi"
    elif message.text == PAYMENT_METHODS["cryptobot"]["name"]:
        method = "cryptobot"
    else:
        method = "tonkeeper"
    
    stars = user_data[user_id]["stars"]
    rate = RATES[method]["rate"]
    currency = RATES[method]["currency"]
    amount = (stars * rate) / 100
    
    user_data[user_id]["payment_method"] = method
    user_data[user_id]["amount"] = round(amount, 2)
    user_data[user_id]["currency"] = currency
    
    await message.answer(
        MESSAGES["payment_details"].format(
            method=PAYMENT_METHODS[method]["name"],
            amount=round(amount, 2),
            currency=currency,
            details=PAYMENT_METHODS[method]["details"]
        ),
        reply_markup=get_paid_button(),
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data == "user_paid")
async def user_paid(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        await bot.answer_callback_query(callback_query.id, "❌ Ошибка: данные не найдены.")
        return
    
    stars = user_data[user_id]["stars"]
    method = user_data[user_id]["payment_method"]
    amount = user_data[user_id]["amount"]
    currency = user_data[user_id]["currency"]
    
    save_history(user_id, stars, amount)
    
    await bot.send_message(
        ADMIN_ID,
        MESSAGES["admin_notify"].format(
            username=callback_query.from_user.username,
            stars=stars,
            method=PAYMENT_METHODS[method]["name"],
            amount=amount,
            currency=currency
        ),
        reply_markup=get_admin_confirm_keyboard(user_id),
        parse_mode="Markdown"
    )
    
    await bot.answer_callback_query(callback_query.id, "✅ Заявка отправлена админу!")

@dp.callback_query_handler(lambda c: c.data.startswith("admin_"))
async def admin_decision(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, "❌ Только админ может подтверждать платежи!")
        return
    
    action, user_id = callback_query.data.split("_")[1], int(callback_query.data.split("_")[2])
    
    if action == "confirm":
        await bot.send_message(user_id, MESSAGES["admin_confirm"])
        # Добавляем запрос отзыва после подтверждения
        await bot.send_message(
            user_id,
            "💌 Пожалуйста, оставьте отзыв: @otzivibroshka"
        )
    else:
        await bot.send_message(user_id, MESSAGES["admin_reject"])
    
    await bot.answer_callback_query(callback_query.id, "✅ Решение отправлено!")

def run_bot():
    try:
        logging.info("Запуск бота...")
        if not os.path.exists('history.json'):
            with open('history.json', 'w') as f:
                pass
        
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logging.error(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        logging.info("Попытка перезапуска через 10 секунд...")
        time.sleep(10)
        os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
    while True:
        run_bot()
        logging.warning("Бот неожиданно завершил работу. Перезапуск...")
        time.sleep(5)
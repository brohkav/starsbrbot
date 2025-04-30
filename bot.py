import os
import logging
import json
import time
import sys
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
from config import MIN_STARS, RATES, PAYMENT_METHODS, MESSAGES, REFERRAL_BONUS, REFERRAL_PERCENT, PROMOCODE_BONUS

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

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  balance INTEGER DEFAULT 0,
                  invited_by INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS promocodes
                 (code TEXT PRIMARY KEY,
                  bonus INTEGER,
                  used_by INTEGER DEFAULT 0,
                  used_at DATETIME)''')
    
    conn.commit()
    conn.close()

init_db()

def get_balance(user_id: int) -> int:
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_balance(user_id: int, amount: int):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', 
              (amount, user_id))
    conn.commit()
    conn.close()

def save_history(user_id: int, stars: int, amount: float, method: str):
    """Сохраняет историю покупок с указанием метода оплаты"""
    data = {
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "stars": stars,
        "amount": amount,
        "method": method,
        "status": "pending"
    }
    with open('history.json', 'a', encoding='utf-8') as f:
        json.dump({str(user_id): data}, f, ensure_ascii=False)
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
        KeyboardButton('💰 Мой баланс'),
        KeyboardButton('🎁 Промокод'),
        KeyboardButton('👥 Рефералы'),
        KeyboardButton('📊 История покупок'),
        KeyboardButton('🛟 Поддержка')
    )
    return markup

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    args = message.get_args()
    user_id = message.from_user.id
    
    # Реферальная система
    if args and args.startswith('ref_'):
        referrer_id = int(args.split('_')[1])
        if referrer_id != user_id:
            conn = sqlite3.connect('bot.db')
            c = conn.cursor()
            
            # Проверяем, не был ли уже приглашен
            c.execute('SELECT invited_by FROM users WHERE user_id = ?', (user_id,))
            if c.fetchone() is None:
                update_balance(referrer_id, REFERRAL_BONUS)
                c.execute('UPDATE users SET invited_by = ? WHERE user_id = ?',
                         (referrer_id, user_id))
                await bot.send_message(
                    referrer_id,
                    f"🎉 Новый реферал! На ваш баланс начислено {REFERRAL_BONUS} звезд"
                )
            
            conn.commit()
            conn.close()

    await message.answer(
        "🔹 <b>Главное меню</b>\nВыберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message_handler(text='💰 Мой баланс')
async def show_balance(message: types.Message):
    balance = get_balance(message.from_user.id)
    await message.answer(f"💎 Ваш текущий баланс: {balance} звезд")

@dp.message_handler(commands=['promo'])
async def handle_promocode(message: types.Message):
    try:
        if len(message.text.split()) < 2:
            await message.answer("ℹ️ Используйте: /promo CODE")
            return

        user_id = message.from_user.id
        code = message.text.split()[1]
        
        conn = sqlite3.connect('bot.db')
        c = conn.cursor()
        
        # Проверяем промокод
        c.execute('SELECT bonus, used_by FROM promocodes WHERE code = ?', (code,))
        result = c.fetchone()
        
        if not result:
            await message.answer(MESSAGES["promo_invalid"])
            return
            
        bonus, used_by = result
        if used_by != 0:
            await message.answer(MESSAGES["promo_used"])
            return
            
        # Активируем промокод
        update_balance(user_id, bonus)
        c.execute('UPDATE promocodes SET used_by = ?, used_at = ? WHERE code = ?',
                 (user_id, datetime.now().isoformat(), code))
        
        await message.answer(MESSAGES["promo_activated"].format(bonus=bonus))
        
    except Exception as e:
        logging.error(f"Ошибка промокода: {e}")
        await message.answer("❌ Ошибка при активации промокода")
    finally:
        conn.commit()
        conn.close()

@dp.message_handler(text='🎁 Промокод')
async def promo_handler(message: types.Message):
    await message.answer("Для активации промокода введите:\n/promo CODE")

@dp.message_handler(text='👥 Рефералы')
async def referral_info(message: types.Message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/{(await bot.me).username}?start=ref_{user_id}"
    
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE invited_by = ?', (user_id,))
    ref_count = c.fetchone()[0]
    conn.close()
    
    await message.answer(
        f"👥 <b>Реферальная система</b>\n\n"
        f"🔗 Ваша ссылка для приглашений:\n<code>{ref_link}</code>\n\n"
        f"💎 Вы получите:\n"
        f"- {REFERRAL_BONUS} звёзд за каждого приглашённого\n"
        f"- {REFERRAL_PERCENT}% от всех их покупок\n\n"
        f"📊 Статистика: {ref_count} приглашённых",
        parse_mode="HTML"
    )

@dp.message_handler(text='📊 История покупок')
async def show_history(message: types.Message):
    user_id = message.from_user.id
    try:
        history = []
        if os.path.exists('history.json'):
            with open('history.json', 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        history.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        
        user_history = [h for h in history if str(user_id) in h]
        
        if not user_history:
            await message.answer("📭 У вас пока нет покупок")
            return
            
        text = "📅 <b>Ваши покупки:</b>\n\n"
        for item in user_history[-5:]:  # Последние 5 записей
            data = item[str(user_id)]
            text += (
                f"▪ <b>{data['date']}</b>\n"
                f"   ⭐ Звёзд: {data['stars']}\n"
                f"   💰 Сумма: {data['amount']}\n"
                f"   🔧 Метод: {data.get('method', 'не указан')}\n"
                f"   🚦 Статус: {data.get('status', 'в обработке')}\n\n"
            )
        
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка при чтении истории: {e}")
        await message.answer("❌ Ошибка при загрузке истории")

@dp.message_handler(text='🛟 Поддержка')
async def support_request(message: types.Message):
    try:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            "Написать оператору", 
            url=f"https://t.me/{SUPPORT_CHAT_ID}"
        ))
        
        await message.answer(
            "📩 <b>Поддержка</b>\n\n"
            "Для быстрой помощи:\n"
            "1. Нажмите кнопку ниже\n"
            "2. Опишите вашу проблему\n"
            "3. Укажите ваш ID: <code>{}</code>".format(message.from_user.id),
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка в поддержке: {e}")
        await message.answer("❌ Ошибка при соединении с поддержкой")

# [Остальные ваши обработчики без изменений]
@dp.message_handler(text='⭐ Купить звёзды')
async def show_stars_menu(message: types.Message):
    await message.answer(MESSAGES["start"], reply_markup=get_stars_keyboard())

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
    
    payment_data = user_data[user_id]
    stars = payment_data["stars"]
    method = payment_data["payment_method"]
    amount = payment_data["amount"]
    currency = payment_data["currency"]
    
    # Сохраняем в историю с методом оплаты
    save_history(user_id, stars, amount, method)
    
    # Уведомляем админа
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

@dp.message_handler(commands=['create_promo'])
async def create_promocode(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.get_args().split()
    if len(args) != 2:
        await message.answer("Формат: /create_promo CODE BONUS")
        return
    
    code, bonus = args[0], int(args[1])
    
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO promocodes (code, bonus) VALUES (?, ?)',
                 (code, bonus))
        await message.answer(f"✅ Промокод {code} создан! Бонус: {bonus} звезд")
    except sqlite3.IntegrityError:
        await message.answer("❌ Промокод уже существует")
    finally:
        conn.commit()
        conn.close()

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
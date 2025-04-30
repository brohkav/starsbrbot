import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  balance INTEGER DEFAULT 0,
                  invited_by INTEGER DEFAULT 0)''')
    
    # Таблица промокодов
    c.execute('''CREATE TABLE IF NOT EXISTS promocodes
                 (code TEXT PRIMARY KEY,
                  bonus INTEGER,
                  used_by INTEGER DEFAULT 0,
                  used_at DATETIME)''')
    
    conn.commit()
    conn.close()

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
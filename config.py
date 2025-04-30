## Минимальное количество звезд для покупки
MIN_STARS = 50

# Бонусная система
DAILY_BONUS = 0  # Бонус за ежедневный вход (временно отключен)
PROMOCODE_BONUS = 50  # Бонус за активацию промокода
REFERRAL_BONUS = 5  # Бонус за приглашение друга
REFERRAL_PERCENT = 2  # % от покупок реферала (добавлено)

# Курсы обмена
RATES = {
    "kaspi": {"currency": "₸", "rate": 900},
    "cryptobot": {"currency": "USDT", "rate": 2.0},
    "tonkeeper": {"currency": "TON", "rate": 0.6}
}

# Платежные методы
PAYMENT_METHODS = {
    "kaspi": {
        "name": "Kaspi (₸)",
        "details": "Перевод на карту: 4400 4300 2633 1253"
    },
    "cryptobot": {
        "name": "CryptoBot (USDT)",
        "details": "Адрес: http://t.me/send?start=IVlvxcWim8ni\nСеть: TON"
    },
    "tonkeeper": {
        "name": "TON Keeper (TON)",
        "details": "Адрес: UQBFKrvkC_fyDUWp2_vvCnuDlg2mPWiaZtCHeNeMIRrAAuZr\nСеть: TON"
    }
}

# Системные сообщения
MESSAGES = {
    # Основные сообщения
    "start": "🌟 *Бот для покупки Telegram Stars*",
    "select_amount": "Выберите количество звёзд (от 50):",
    "invalid_amount": "❌ Минимум 50 звёзд!",
    "payment_choice": "Выберите способ оплаты:",
    "payment_details": "💳 *Способ:* {method}\n💰 *К оплате:* {amount} {currency}\n\n📝 *Реквизиты:*\n{details}",
    
    # Админ-уведомления
    "admin_notify": "🔔 *Новый платёж!*\n👤 @{username}\n⭐ {stars} звёзд\n💳 {method}: {amount} {currency}",
    "admin_confirm": "✅ Платёж подтверждён! Звёзды будут отправлены вручную в ближайшее время.",
    "admin_reject": "❌ Платёж отклонён. В случае вопросов свяжитесь с @broshkav.",
    
    # Реферальная система (добавлено)
    "ref_info": "👥 *Реферальная система*\n\n"
                "🔗 Ваша ссылка:\n`{link}`\n\n"
                "💎 Вы получаете:\n"
                f"- {REFERRAL_BONUS} звёзд за каждого приглашенного\n"
                f"- {REFERRAL_PERCENT}% от их покупок\n\n"
                "📊 Приглашено: {count} человек",
    
    # Промокоды (добавлено)
    "promo_activated": "🎉 Промокод активирован! +{bonus} звёзд",
    "promo_used": "❌ Этот промокод уже использован",
    "promo_invalid": "❌ Неверный промокод",
    "promo_help": "Введите /promo CODE для активации",
    
    # Баланс (добавлено)
    "balance": "💰 Ваш баланс: *{balance}* звёзд",
    
    # Уведомления для реферера (добавлено)
    "ref_earned": "💎 Вы получили {bonus} звёзд с покупки реферала!"
}

# Настройки безопасности (добавлено)
SECURITY = {
    "max_stars_per_day": 5000,  # Лимит на покупки
    "min_payment_amount": 100  # Минимальная сумма оплаты в валюте
}
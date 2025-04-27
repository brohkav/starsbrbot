MIN_STARS = 50
bonus = 0

RATES = {
    "kaspi": {"currency": "₸", "rate": 900},
    "cryptobot": {"currency": "USDT", "rate": 2.0},
    "tonkeeper": {"currency": "TON", "rate": 0.6}
}

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

MESSAGES = {
    "start": "🌟 *Бот для покупки Telegram Stars*",
    "select_amount": "Выберите количество звёзд (от 50):",
    "invalid_amount": "❌ Минимум 50 звёзд!",
    "payment_choice": "Выберите способ оплаты:",
    "payment_details": "💳 *Способ:* {method}\n💰 *К оплате:* {amount} {currency}\n\n📝 *Реквизиты:*\n{details}",
    "admin_notify": "🔔 *Новый платёж!*\n👤 @{username}\n⭐ {stars} звёзд\n💳 {method}: {amount} {currency}",
    "admin_confirm": "✅ Платёж подтверждён! Звёзды будут отправлены вручную в ближайшее время.",
    "admin_reject": "❌ Платёж отклонён. В случае вопросов свяжитесь с @broshkav."
}  
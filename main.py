
import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ===================== USER DATA STORE =====================
user_data = {}

def init_user(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {}

# ===================== MAIN MENU =====================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📈 Trading")
    return kb

def back_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Back")
    return kb

# ===================== START =====================
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "🚀 Futures Trading Bot UI", reply_markup=main_menu())

# ===================== TRADING ENTRY =====================
@bot.message_handler(func=lambda m: m.text == "📈 Trading")
def trading(msg):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📊 SMA Crossover", callback_data="strategy_sma"),
        types.InlineKeyboardButton("📈 Envelope Strategy", callback_data="strategy_env")
    )
    bot.send_message(msg.chat.id, "Pick a strategy:", reply_markup=kb)

# ===================== CALLBACK HANDLER =====================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    chat_id = call.message.chat.id
    init_user(chat_id)
    bot.answer_callback_query(call.id)

    # ===== STRATEGY PICK =====
    if call.data == "strategy_sma":
        user_data[chat_id]["strategy"] = "SMA_CROSSOVER"
        bot.send_message(chat_id, "Enter FAST SMA period:", reply_markup=back_menu())
        bot.register_next_step_handler_by_chat_id(chat_id, sma_fast)

    elif call.data == "strategy_env":
        user_data[chat_id]["strategy"] = "ENVELOPE"
        bot.send_message(chat_id, "Enter envelope percentage (e.g. 0.5):", reply_markup=back_menu())
        bot.register_next_step_handler_by_chat_id(chat_id, env_percent)

    # ===== CONFIRM SCREEN =====
    elif call.data == "confirm_trade":
        user_data[chat_id]["confirmed"] = True
        bot.send_message(chat_id, "✅ Trading configuration CONFIRMED & SAVED", reply_markup=main_menu())

    elif call.data == "cancel_trade":
        user_data.pop(chat_id, None)
        bot.send_message(chat_id, "❌ Configuration cancelled", reply_markup=main_menu())

# ===================== SMA PARAMETERS =====================
def sma_fast(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        trading(msg)
        return
    user_data[chat_id]["sma_fast"] = int(msg.text)
    bot.send_message(chat_id, "Enter SLOW SMA period:", reply_markup=back_menu())
    bot.register_next_step_handler_by_chat_id(chat_id, sma_slow)

def sma_slow(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        trading(msg)
        return
    user_data[chat_id]["sma_slow"] = int(msg.text)
    ask_symbol(chat_id)

# ===================== ENVELOPE PARAMETERS =====================
def env_percent(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        trading(msg)
        return
    user_data[chat_id]["envelope_pct"] = float(msg.text)
    ask_symbol(chat_id)

# ===================== COMMON FLOW =====================
def ask_symbol(chat_id):
    bot.send_message(chat_id, "Enter trading symbol (e.g. BTCUSDT):", reply_markup=back_menu())
    bot.register_next_step_handler_by_chat_id(chat_id, enter_symbol)

def enter_symbol(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        trading(msg)
        return
    user_data[chat_id]["symbol"] = msg.text.upper()
    bot.send_message(chat_id, "Enter timeframe (e.g. 5m, 15m, 1h):", reply_markup=back_menu())
    bot.register_next_step_handler_by_chat_id(chat_id, enter_timeframe)

def enter_timeframe(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        ask_symbol(chat_id)
        return
    user_data[chat_id]["timeframe"] = msg.text
    bot.send_message(chat_id, "Enter leverage:", reply_markup=back_menu())
    bot.register_next_step_handler_by_chat_id(chat_id, enter_leverage)

def enter_leverage(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        enter_symbol(msg)
        return
    user_data[chat_id]["leverage"] = float(msg.text)
    bot.send_message(chat_id, "Risking percent per trade (%):", reply_markup=back_menu())
    bot.register_next_step_handler_by_chat_id(chat_id, enter_risk)

def enter_risk(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        enter_leverage(msg)
        return
    user_data[chat_id]["risk_percent"] = float(msg.text)
    bot.send_message(chat_id, "Risk to Reward ratio (e.g. 1:3):", reply_markup=back_menu())
    bot.register_next_step_handler_by_chat_id(chat_id, enter_rr)

def enter_rr(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        enter_risk(msg)
        return
    user_data[chat_id]["rr"] = msg.text
    bot.send_message(chat_id, "Take Profit %:", reply_markup=back_menu())
    bot.register_next_step_handler_by_chat_id(chat_id, enter_tp)

def enter_tp(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        enter_rr(msg)
        return
    user_data[chat_id]["take_profit"] = float(msg.text)
    bot.send_message(chat_id, "Stop Loss %:", reply_markup=back_menu())
    bot.register_next_step_handler_by_chat_id(chat_id, enter_sl)

def enter_sl(msg):
    chat_id = msg.chat.id
    if msg.text == "🔙 Back":
        enter_tp(msg)
        return
    user_data[chat_id]["stop_loss"] = float(msg.text)
    review_screen(chat_id)

# ===================== REVIEW & CONFIRM =====================
def review_screen(chat_id):
    d = user_data[chat_id]
    text = "📋 *Review Trading Configuration*\n\n"
    for k, v in d.items():
        text += f"{k}: {v}\n"

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Confirm", callback_data="confirm_trade"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_trade")
    )

    bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

# ===================== RUN =====================
bot.infinity_polling()
     

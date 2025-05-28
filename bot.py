import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

API_TOKEN = '7689697850:AAFeDtgekHM6bsOT7B0A1rdsaTRCcp59VqY'
ADMIN_TG_ID = '5520224616'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_balances = {}

def draw_card():
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return random.choice(cards)

def card_value(card):
    if card in ['J', 'Q', 'K']:
        return 10
    elif card == 'A':
        return 11
    return int(card)

def total(hand):
    result = sum(card_value(card) for card in hand)
    aces = hand.count('A')
    while result > 21 and aces:
        result -= 10
        aces -= 1
    return result

@dp.message_handler(commands=['start'])
async def start_game(message: types.Message):
    user_balances.setdefault(message.from_user.id, 100)
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎮 Играть в Блэкджек", callback_data="play"))
    kb.add(InlineKeyboardButton("💎 Поддержать", callback_data="donate"))
    await message.answer("Добро пожаловать в Блэкджек-бот!\n\nУ тебя 100 монет.\nМинимальная ставка: 10 монет.", reply_markup=kb)

@dp.callback_query_handler(lambda c: True)
async def handle_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "play":
        user_balances.setdefault(user_id, 100)
        if user_balances[user_id] < 10:
            await callback_query.message.edit_text("❌ Недостаточно средств! Минимум 10 монет.")
            return
        player_hand = [draw_card(), draw_card()]
        dealer_hand = [draw_card()]
        total_player = total(player_hand)
        text = f"🃏 Твои карты: {player_hand} (сумма: {total_player})\n"
        text += f"🂠 Карта дилера: {dealer_hand}"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("➕ Взять карту", callback_data=f"hit|{','.join(player_hand)}|{dealer_hand[0]}"))
        kb.add(InlineKeyboardButton("🛑 Хватит", callback_data=f"stand|{','.join(player_hand)}|{dealer_hand[0]}"))
        await callback_query.message.edit_text(text, reply_markup=kb)

    elif data.startswith("hit") or data.startswith("stand"):
        parts = data.split("|")
        action = parts[0]
        player_hand = parts[1].split(",")
        dealer_hand = [parts[2]]

        if action == "hit":
            player_hand.append(draw_card())
            player_total = total(player_hand)
            if player_total > 21:
                user_balances[user_id] -= 10
                await callback_query.message.edit_text(f"💥 Ты проиграл! Карты: {player_hand} ({player_total}).\nБаланс: {user_balances[user_id]}")
                return
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("➕ Взять ещё", callback_data=f"hit|{','.join(player_hand)}|{dealer_hand[0]}"))
            kb.add(InlineKeyboardButton("🛑 Хватит", callback_data=f"stand|{','.join(player_hand)}|{dealer_hand[0]}"))
            await callback_query.message.edit_text(f"🃏 Твои карты: {player_hand} ({player_total})\nКарта дилера: {dealer_hand}", reply_markup=kb)

        elif action == "stand":
            while total(dealer_hand) < 17:
                dealer_hand.append(draw_card())
            dealer_total = total(dealer_hand)
            player_total = total(player_hand)
            result_text = f"🃏 Твои карты: {player_hand} ({player_total})\n🂠 Карты дилера: {dealer_hand} ({dealer_total})\n"
            if dealer_total > 21 or player_total > dealer_total:
                user_balances[user_id] += 10
                result_text += "🎉 Ты выиграл! +10 монет"
            elif player_total < dealer_total:
                user_balances[user_id] -= 10
                result_text += "😞 Ты проиграл. -10 монет"
            else:
                result_text += "😐 Ничья."
            result_text += f"\n💰 Баланс: {user_balances[user_id]}"
            await callback_query.message.edit_text(result_text)

    elif data == "donate":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💸 Перевести TON", url=f"https://t.me/crypto?start=send-{ADMIN_TG_ID}"))
        await callback_query.message.edit_text("❤️ Спасибо за поддержку! Перевести TON:", reply_markup=kb)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

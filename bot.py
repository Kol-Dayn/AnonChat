
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram import F

API_TOKEN = '7142516037:AAHgvhsGQGe44pmiKX32uB9xw0V5b-FHums'

# Создаем объект бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Хранилище пользователей
users_waiting = []
active_chats = {}

# Создаем кнопки и клавиатуру
search_button = KeyboardButton(text='🔍 Поиск собеседника')
stop_button = KeyboardButton(text='❌ Остановить')
main_keyboard = ReplyKeyboardMarkup(keyboard=[[search_button, stop_button]], resize_keyboard=True)

# Команда /start
@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Добро пожаловать в анонимный чат!\n\n"
        "Нажмите '🔍 Поиск собеседника', чтобы начать.",
        reply_markup=main_keyboard
    )

# Обработчик поиска собеседника
@router.message(F.text == '🔍 Поиск собеседника')
async def search_partner(message: Message):
    user_id = message.from_user.id

    if user_id in active_chats:
        await message.answer("Вы уже находитесь в чате.")
        return

    if users_waiting:
        partner_id = users_waiting.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await bot.send_message(partner_id, "🔗 Найден собеседник! Вы можете начать общение.")
        await message.answer("🔗 Найден собеседник! Вы можете начать общение.")
    else:
        users_waiting.append(user_id)
        await message.answer("🔍 Ищем собеседника. Пожалуйста, подождите.")

# Обработчик остановки диалога
@router.message(F.text == '❌ Остановить')
async def stop_chat(message: Message):
    user_id = message.from_user.id

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)

        await bot.send_message(partner_id, "❌ Собеседник покинул чат.")
        await message.answer("❌ Вы завершили диалог.")
    elif user_id in users_waiting:
        users_waiting.remove(user_id)
        await message.answer("❌ Вы отменили поиск собеседника.")
    else:
        await message.answer("Вы не находитесь в чате.")

# Обработчик пересылки сообщений
@router.message()
async def forward_message(message: Message):
    user_id = message.from_user.id

    if user_id in active_chats:
        partner_id = active_chats[user_id]
        await bot.send_message(partner_id, message.text)
    else:
        await message.answer("Сначала найдите собеседника, нажав '🔍 Поиск собеседника'.")

# Запуск бота
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

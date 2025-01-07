import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
import json
from cryptography.fernet import Fernet
from config import TOKEN
import os

# Установка уровеня логирования: (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logging.basicConfig(level=logging.INFO)

# Устанавливаем уровень логирования для httpx на WARNING (или ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Загрузка ключа шифрования
def load_key():
    with open('encryption.key', 'rb') as key_file:
        return key_file.read()

# Шифрование данных
def encrypt_data(data):
    key = load_key()
    fernet = Fernet(key)
    return fernet.encrypt(json.dumps(data).encode())

# Расшифровка данных
def decrypt_data(encrypted_data):
    key = load_key()
    fernet = Fernet(key)
    return json.loads(fernet.decrypt(encrypted_data).decode())

# Сохранение зашифрованных данных в файл
def save_encrypted_file(filename, data):
    try:
        encrypted_data = encrypt_data(data)
        with open(filename, 'wb') as file:
            file.write(encrypted_data)
        logging.info(f"Данные успешно сохранены в файл {filename} (зашифрованы).")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в {filename}: {e}")

# Загрузка и расшифровка данных из файла
def load_encrypted_file(filename):
    try:
        if not os.path.exists(filename):
            logging.info(f"Файл {filename} не найден. Создается новый.")
            return {}
        with open(filename, 'rb') as file:
            encrypted_data = file.read()
        decrypted_data = decrypt_data(encrypted_data)
        logging.info(f"Данные успешно расшифрованы: {decrypted_data}")
        return decrypted_data
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных из {filename}: {e}")
        return {}

# Для сохранения данных пользователей
def save_data(users):
    save_encrypted_file('users.json', users)

# Загрузка данных пользователей
def load_data():
    return load_encrypted_file('users.json')

# Для сохранения активных чатов
def save_active_chats():
    save_encrypted_file('active_chats.json', active_chats)

# Загрузка активных чатов
# def load_active_chats():
#     return load_encrypted_file('active_chats.json')

def load_active_chats():
    try:
        chats = load_encrypted_file('active_chats.json')
        
        if isinstance(chats, dict):
            # Проверяем, что все значения - словари с нужными ключами
            for user_id, chat_info in chats.items():
                if not isinstance(chat_info, dict) or "partner_id" not in chat_info:
                    logging.error(f"Некорректная структура данных для {user_id}: {chat_info}")
                    return {}
            return chats
        else:
            logging.warning("Расшифрованные данные active_chats не являются словарём. Загружается пустой словарь.")
            return {}
    except Exception as e:
        logging.error(f"Ошибка при загрузке active_chats.json: {e}")
        return {}


# Для сохранения заблокированных пользователей
def save_blocked_users(blocked_users):
    save_encrypted_file('blocked_users.json', blocked_users)

# Загрузка данных о заблокированных пользователях
def load_blocked_users():
    return load_encrypted_file('blocked_users.json')

# Проверка блокировки пользователей
def is_blocked(user1, user2):
    blocked_users = load_blocked_users()
    pair = ",".join(sorted([user1, user2]))  # Сортируем, чтобы порядок не имел значения
    
    if pair in blocked_users:
        block_time = datetime.fromisoformat(blocked_users[pair])
        if datetime.now() - block_time < timedelta(hours=1):  # Проверяем 1 час
            return True
    return False

# Загрузка данных
users = load_data()
active_chats = load_active_chats()
logging.info(f"Структура active_chats после загрузки: {active_chats}")

# Функция создания клавиатуры
def get_keyboard(is_searching=False):
    buttons = []
    if is_searching:
        buttons.append([InlineKeyboardButton("Остановить поиск", callback_data="stop_search")])
    return InlineKeyboardMarkup(buttons)

# Стартовое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in users:
        users[user_id] = {"status": "normal", "chat_with": None}
        save_data(users)

    await update.message.reply_text(
        "Добро пожаловать! Используйте /search для поиска собеседника.", 
        reply_markup=get_keyboard()
    )

# Обработчик команд поиска собеседника
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if users[user_id]["status"] == "in search":
        await update.message.reply_text("Вы уже ищете собеседника.", reply_markup=get_keyboard(True))
        return

    logging.info(f"(!) Пользователь {user_id} начал поиск собеседника. (!)") # УДАЛИТЬ

    users[user_id]["status"] = "in search"
    save_data(users)

    await update.message.reply_text("Ищу собеседника...", reply_markup=get_keyboard(True))

    for other_user in users:
        if users[other_user]["status"] == "in search" and other_user != user_id:
            if is_blocked(user_id, other_user):
                continue

            users[user_id]["chat_with"] = other_user
            users[other_user]["chat_with"] = user_id
            active_chats[user_id] = other_user
            active_chats[other_user] = user_id
            users[user_id]["status"] = "chatting"
            users[other_user]["status"] = "chatting"
            save_data(users)
            save_active_chats()

            logging.info(f"(!) Создан активный чат между пользователем {user_id} и пользователем {other_user}. (!)") # УДАЛИТЬ

            await update.message.reply_text("Собеседник найден!", reply_markup=get_keyboard(False))
            await context.bot.send_message(
                other_user,
                "Собеседник найден! Вы можете начать общение.",
                reply_markup=get_keyboard(False),
            )
            return

    await update.message.reply_text("Свободных собеседников нет.\n\nПоиск займет больше времени, чем обычно...")

# Остановка поиска
async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if users[user_id]["status"] != "in search":
        await update.callback_query.answer("Вы не в поиске собеседника.", show_alert=True)
        return

    logging.info(f"(!) Пользователь {user_id} остановил поиск собеседника. (!)") # УДАЛИТЬ

    users[user_id]["status"] = "normal"
    save_data(users)

    await update.callback_query.answer("Поиск остановлен.")
    await update.callback_query.edit_message_text("Поиск остановлен.", reply_markup=get_keyboard(False))

# Завершение чата
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in active_chats:
        await update.message.reply_text("Вы не в чате. Используйте /search для поиска собеседника.")
        return

    other_user = active_chats[user_id]
    users[user_id]["status"] = "normal"
    users[other_user]["status"] = "normal"
    users[user_id]["chat_with"] = None
    users[other_user]["chat_with"] = None
    active_chats.pop(user_id)
    active_chats.pop(other_user)

    # Сохраняем заблокированных пользователей
    blocked_users = load_blocked_users()
    pair = ",".join(sorted([user_id, other_user]))  # Форматируем ключ
    blocked_users[pair] = str(datetime.now())
    save_blocked_users(blocked_users)

    save_data(users)
    save_active_chats()

    logging.info(f"(!) Чат между пользователем {user_id} и пользователем {other_user} завершен (!)")

    await update.message.reply_text("Вы покинули чат. Используйте /search для нового собеседника.", reply_markup=get_keyboard())
    await context.bot.send_message(
        other_user,
        "Ваш собеседник покинул чат. Используйте /search для нового собеседника.",
        reply_markup=get_keyboard(),
    )

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in active_chats:
        await update.message.reply_text(
            "Вы не в чате. Используйте /search для поиска собеседника.",
            reply_markup=get_keyboard()
        )
        return

    other_user = active_chats[user_id]["partner_id"]

    # Отправляем сообщение собеседнику
    if update.message.text:
        sent_message = await context.bot.send_message(
            chat_id=other_user,
            text=update.message.text
        )
        logging.info(f"Сообщение от {user_id} к {other_user}: {update.message.text}")

        # Сохраняем ID отправленного сообщения
        active_chats[user_id]["last_message_id"] = sent_message.message_id
        active_chats[other_user]["last_message_id"] = sent_message.message_id


# Обработчик редактирования сообщений
async def handle_message_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in active_chats:
        logging.info(f"Пользователь {user_id} попытался отредактировать сообщение вне активного чата.")
        return

    other_user = active_chats[user_id]["partner_id"]
    last_message_id = active_chats[user_id].get("last_message_id")

    if update.edited_message and update.edited_message.text and last_message_id:
        try:
            # Редактируем сообщение для собеседника
            await context.bot.edit_message_text(
                chat_id=other_user,
                message_id=last_message_id,
                text=f"(Редактировано) {update.edited_message.text}"
            )
            logging.info(f"Сообщение от {user_id} для {other_user} было отредактировано: {update.edited_message.text}")
        except Exception as e:
            logging.error(f"Ошибка при редактировании сообщения от {user_id} для {other_user}: {e}")

# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CallbackQueryHandler(stop_search, pattern="^stop_search$"))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик редактирования сообщений
    application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, handle_message_edit))

    application.run_polling()

if __name__ == "__main__":
    main()
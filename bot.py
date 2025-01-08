import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import logging
import json
from cryptography.fernet import Fernet
from config import TOKEN
import os

# Установка уровеня логирования: (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logging.basicConfig(level=logging.INFO)
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
            return {}
        with open(filename, 'rb') as file:
            encrypted_data = file.read()
        return decrypt_data(encrypted_data)
    except FileNotFoundError:
        logging.info(f"Файл {filename} не найден. Создается новый.")
        return {}
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных из {filename}: {e}")
        return {}

# Для сохранения данных пользователей
def save_data(users):
    save_encrypted_file('users.json', users)

# Загрузка данных пользователей
def load_data():
    users = load_encrypted_file('users.json')
    # Если файл не найден или данные пустые, создаем новый файл с пустыми данными
    if not users:
        users = {}  # или создайте начальные данные, если необходимо
        save_data(users)
    return users

# Сохранение активных чатов с маппингом сообщений
def save_active_chats():
    try:
        with open('active_chats.json', 'wb') as file:
            encrypted_data = encrypt_data(active_chats)
            file.write(encrypted_data)
        logging.info("Активные чаты успешно сохранены.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении активных чатов: {e}")

# Загрузка активных чатов с маппингом сообщений
def load_active_chats():
    try:
        if not os.path.exists('active_chats.json'):
            return {}
        with open('active_chats.json', 'rb') as file:
            encrypted_data = file.read()
        return decrypt_data(encrypted_data)
    except FileNotFoundError:
        logging.info("Файл с активными чатами не найден.")
        return {}
    except Exception as e:
        logging.error(f"Ошибка при загрузке активных чатов: {e}")
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

# Функция создания клавиатуры
def get_keyboard(is_searching=False):
    buttons = []
    if is_searching:
        buttons.append([InlineKeyboardButton("Остановить поиск", callback_data="stop_search")])
    return InlineKeyboardMarkup(buttons)

# Стартовое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Убедитесь, что пользователь есть в словаре
    if user_id not in users:
        users[user_id] = {"status": "normal", "chat_with": None}
        save_data(users)

    # Проверяем, если пользователь уже в чате, игнорируем команду
    if users[user_id]["status"] == "chatting":
        await update.message.reply_text("Вы уже в чате. Завершите текущий чат перед тем, как начать новый.")
        return

    await update.message.reply_text(
        "Добро пожаловать! Используйте /search для поиска собеседника.", 
        reply_markup=get_keyboard()
    )

# Для создания нового чата
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Убедитесь, что пользователь есть в словаре
    if user_id not in users:
        users[user_id] = {"status": "normal", "chat_with": None}
        save_data(users)

    # Проверка, если пользователь уже в чате
    if users[user_id]["status"] == "chatting":
        await update.message.reply_text("Вы уже в чате. Завершите текущий чат перед тем, как начать новый.", reply_markup=get_keyboard())
        return

    if users[user_id]["status"] == "in search":
        await update.message.reply_text("Вы уже ищете собеседника.", reply_markup=get_keyboard(True))
        return

    logging.info(f"(!) Пользователь {user_id} начал поиск собеседника. (!)")

    users[user_id]["status"] = "in search"
    save_data(users)

    await update.message.reply_text("Ищу собеседника...", reply_markup=get_keyboard(True))

    for other_user in users:
        if users[other_user]["status"] == "in search" and other_user != user_id:
            if is_blocked(user_id, other_user):
                continue

            users[user_id]["chat_with"] = other_user
            users[other_user]["chat_with"] = user_id
            active_chats[user_id] = {
                "chat_with": other_user,
                "message_map": {}  # Маппинг сообщений для этого чата
            }
            active_chats[other_user] = {
                "chat_with": user_id,
                "message_map": {}
            }
            users[user_id]["status"] = "chatting"
            users[other_user]["status"] = "chatting"
            save_data(users)
            save_active_chats()

            logging.info(f"(!) Создан активный чат между пользователем {user_id} и пользователем {other_user}. (!)")

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

    logging.info(f"(!) Пользователь {user_id} остановил поиск собеседника. (!)")

    users[user_id]["status"] = "normal"
    save_data(users)

    await update.callback_query.answer("Поиск остановлен.")
    await update.callback_query.edit_message_text("Поиск остановлен.", reply_markup=get_keyboard(False))

# Завершение чата с удалением данных из active_chats
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in active_chats:
        await update.message.reply_text("Вы не в чате. Используйте /search для поиска собеседника.")
        return

    other_user = active_chats[user_id]["chat_with"]
    del active_chats[user_id]
    del active_chats[other_user]

    # Сохраняем заблокированных пользователей
    blocked_users = load_blocked_users()
    pair = ",".join(sorted([user_id, other_user]))  # Форматируем ключ
    blocked_users[pair] = str(datetime.now())
    save_blocked_users(blocked_users)

    save_active_chats()  # Обновляем active_chats после завершения

    logging.info(f"(!) Чат между пользователем {user_id} и пользователем {other_user} завершен (!)")

    await update.message.reply_text("Вы покинули чат. Используйте /search для нового собеседника.", reply_markup=get_keyboard())
    await context.bot.send_message(
        other_user,
        "Ваш собеседник покинул чат. Используйте /search для нового собеседника.",
        reply_markup=get_keyboard(),
    )

# Обработчик текста сообщений с обновлением маппинга сообщений в active_chats.json
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in active_chats:
        await update.message.reply_text(
            "Вы не в чате. Используйте /search для поиска собеседника.",
            reply_markup=get_keyboard()  # Клавиатура для начала поиска
        )
        return

    other_user_id = active_chats[user_id]["chat_with"]

    try:
        reply_to_message_id = None

        # Проверяем, является ли сообщение ответом
        if update.message.reply_to_message:
            replied_message_id = update.message.reply_to_message.message_id

            # Проверяем, есть ли маппинг для ответа
            if "message_map" in active_chats[user_id] and replied_message_id in active_chats[user_id]["message_map"]:
                reply_to_message_id = active_chats[user_id]["message_map"][replied_message_id]

        # Определяем тип сообщения
        if update.message.text:
            sent_message = await context.bot.send_message(
                chat_id=other_user_id,
                text=update.message.text,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        elif update.message.photo:
            sent_message = await context.bot.send_photo(
                chat_id=other_user_id,
                photo=update.message.photo[-1].file_id,  # Берём самое большое фото
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        elif update.message.video:
            sent_message = await context.bot.send_video(
                chat_id=other_user_id,
                video=update.message.video.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        elif update.message.document:
            sent_message = await context.bot.send_document(
                chat_id=other_user_id,
                document=update.message.document.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        elif update.message.audio:
            sent_message = await context.bot.send_audio(
                chat_id=other_user_id,
                audio=update.message.audio.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        elif update.message.voice:
            sent_message = await context.bot.send_voice(
                chat_id=other_user_id,
                voice=update.message.voice.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        elif update.message.sticker:
            sent_message = await context.bot.send_sticker(
                chat_id=other_user_id,
                sticker=update.message.sticker.file_id,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        elif update.message.video_note:
            sent_message = await context.bot.send_video_note(
                chat_id=other_user_id,
                video_note=update.message.video_note.file_id,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        else:
            await update.message.reply_text("Этот тип сообщения не поддерживается.")
            return

        # Обновляем маппинг сообщений в active_chats
        if "message_map" not in active_chats[user_id]:
            active_chats[user_id]["message_map"] = {}
        if "message_map" not in active_chats[other_user_id]:
            active_chats[other_user_id]["message_map"] = {}

        active_chats[user_id]["message_map"][update.message.message_id] = sent_message.message_id
        active_chats[other_user_id]["message_map"][sent_message.message_id] = update.message.message_id

        # Сохраняем обновленный маппинг в файл
        save_active_chats()

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text("Произошла ошибка при пересылке сообщения.")

# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CallbackQueryHandler(stop_search, pattern="^stop_search$"))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler((filters.TEXT | filters.ATTACHMENT) & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
import telegram
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import logging
import json
from cryptography.fernet import Fernet
from config import TOKEN, ADMIN_ID
import os
import re

# Установка уровня логирования: (DEBUG, INFO, WARNING, ERROR, CRITICAL)
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
        logging.info("Файл не найден. Создается новый.")
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
    if not users:
        users = {}
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

# Изменение функции is_blocked для проверки тайм-аутов
def is_blocked(user1, user2):
    blocked_users = load_blocked_users()
    pair = ",".join(sorted([user1, user2]))
    if pair in blocked_users:
        block_time = datetime.fromisoformat(blocked_users[pair])
        if datetime.now() < block_time:
            return True
        else:
            # Удаляем просроченные блокировки и логируем выход из тайм-аута
            del blocked_users[pair]
            save_blocked_users(blocked_users)
            logging.info(f"(!) Пользователи {user1} и {user2} вышли из тайм-аута.")
    return False

# Преобразование времени в слова
def convert_timeout_to_words(timeout_str):
    time_amount = int(timeout_str[:-1])
    time_unit = timeout_str[-1]

    if time_unit == 's':
        return f"{time_amount} сек"
    elif time_unit == 'm':
        return f"{time_amount} мин"
    elif time_unit == 'h':
        return f"{time_amount} час"
    elif time_unit == 'd':
        return f"{time_amount} день"

# Обработка команды /timeout
async def timeout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        # Если пользователь не администратор, ничего не отвечаем
        return

    if len(context.args) == 0:
        # Подгружаем актуальный тайм-аут из blocked_users.json
        blocked_users = load_blocked_users()
        last_timeout = blocked_users.get("timeout_duration", "1h")
        last_timeout_words = convert_timeout_to_words(last_timeout)
        await update.message.reply_text(f"Используйте команду в формате: /timeout <время>\nТекущий установленный тайм-аут: {last_timeout_words}")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Некорректный формат команды. Используйте команду в формате: /timeout <время>")
        return

    timeout_str = context.args[0]
    if not re.match(r'^\d+[smhd]$', timeout_str):
        await update.message.reply_text("Некорректный формат времени. Используйте s для секунд, m для минут, h для часов или d для дней. Например: /timeout 30с, /timeout 1м, /timeout 1ч, /timeout 1д")
        return

    time_amount = int(timeout_str[:-1])
    time_unit = timeout_str[-1]

    if time_unit == 's':
        timeout_duration = timedelta(seconds=time_amount)
    elif time_unit == 'm':
        timeout_duration = timedelta(minutes=time_amount)
    elif time_unit == 'h':
        timeout_duration = timedelta(hours=time_amount)
    elif time_unit == 'd':
        timeout_duration = timedelta(days=time_amount)
    else:
        await update.message.reply_text("Некорректный формат времени. Используйте s для секунд, m для минут, h для часов или d для дней.")
        return

    if timeout_duration > timedelta(days=1):
        await update.message.reply_text(f"Время {timeout_duration} слишком большое для тайм-аута, но оно будет установлено.")

    blocked_users = load_blocked_users()
    blocked_users["timeout_duration"] = timeout_str
    save_blocked_users(blocked_users)
    context.bot_data["last_timeout"] = timeout_str
    timeout_words = convert_timeout_to_words(timeout_str)
    await update.message.reply_text(f"Тайм-аут установлен на {timeout_words}.")

# Загрузка данных
users = load_data()
active_chats = load_active_chats()
blocked_users = load_blocked_users()

# Исправление функции создания клавиатуры
def get_keyboard(is_searching=False):
    buttons = []
    if not is_searching:
        buttons.append([KeyboardButton("Начать поиск собеседника")])
        buttons.append([KeyboardButton("Интересы")])
    else:
        buttons.append([KeyboardButton("Остановить поиск")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Функция создания клавиатуры для выбора интересов
def get_interests_keyboard(selected_interests=[]):
    interests = ["Знакомства", "Мемы", "Спорт", "Путешествия", "Кино", "Книги", "Одиночество", "Игры"]
    buttons = []
    for i in range(0, len(interests), 2):
        row = []
        for j in range(2):
            if i + j < len(interests):
                interest = interests[i + j]
                if interest in selected_interests:
                    row.append(InlineKeyboardButton(f"✅ {interest}", callback_data=f"interest_{interest}"))
                else:
                    row.append(InlineKeyboardButton(interest, callback_data=f"interest_{interest}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Сбросить интересы", callback_data="reset_interests")])
    return InlineKeyboardMarkup(buttons)

# Стартовое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {"status": "normal", "chat_with": None, "interests": []}
        save_data(users)
    if users[user_id]["status"] == "chatting":
        await update.message.reply_text("Вы уже в чате. Завершите текущий чат перед тем, как начать новый.")
        return
    await update.message.reply_text(
        "Добро пожаловать! Используйте кнопку ниже для поиска собеседника.", 
        reply_markup=get_keyboard()
    )

# Обработчик для кнопки "Интересы"
async def interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    selected_interests = users[user_id].get("interests", [])
    await update.message.reply_text(
        "Выберите ваши интересы:",
        reply_markup=get_interests_keyboard(selected_interests)
    )

# Команда /interests
async def interests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if users[user_id]["status"] != "normal":
        await update.message.reply_text("Эту команду можно использовать только когда ваш статус normal.")
        return
    selected_interests = users[user_id].get("interests", [])
    await update.message.reply_text(
        "Выберите ваши интересы:",
        reply_markup=get_interests_keyboard(selected_interests)
    )

# Обработчик для сброса интересов
async def reset_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if users[user_id].get("interests"):
        users[user_id]["interests"] = []
        save_data(users)
        try:
            await query.edit_message_reply_markup(reply_markup=get_interests_keyboard(users[user_id]["interests"]))
        except telegram.error.BadRequest as e:
            if str(e) == "Message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message":
                logging.info(f"Интересы пользователя {user_id} уже пусты и сообщение не изменено.")
            else:
                logging.error(f"Ошибка при сбросе интересов: {e}")
    else:
        logging.info(f"Интересы пользователя {user_id} уже пусты.")
        await query.answer("У вас уже нет интересов.", show_alert=False)

# Обработчик для выбора интересов
async def handle_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    interest = query.data.replace("interest_", "")
    if interest in users[user_id]["interests"]:
        users[user_id]["interests"].remove(interest)
    else:
        users[user_id]["interests"].append(interest)
    save_data(users)
    await query.edit_message_reply_markup(reply_markup=get_interests_keyboard(users[user_id]["interests"]))

# Обработчик завершения выбора интересов
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.edit_message_text(
        f"Ваши интересы сохранены: {', '.join(users[user_id]['interests']) or 'Нет интересов'}"
    )
    await query.message.reply_text("Интересы выбраны.", reply_markup=get_keyboard())

# Команда /search
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE, skip_searching_message=False):
    user_id = str(update.effective_user.id)

    # Проверка наличия пользователя в базе данных
    if user_id not in users:
        users[user_id] = {"status": "normal", "chat_with": None, "interests": []}
        save_data(users)

    # Проверка, заблокирован ли пользователь
    if users[user_id]["status"] == "banned":
        await update.message.reply_text("Вы были заблокированы администратором.")
        return

    # Проверка, находится ли пользователь в чате
    if users[user_id]["status"] == "chatting":
        await update.message.reply_text("Вы уже в чате. Завершите текущий чат перед тем, как начать новый.", reply_markup=get_keyboard())
        return

    # Проверка, ищет ли пользователь собеседника
    if users[user_id]["status"] == "in search":
        if not skip_searching_message:
            await update.message.reply_text("Вы уже ищете собеседника.", reply_markup=get_keyboard(True))
        return

    logging.info(f"(!) Пользователь {user_id} начал поиск собеседника. (!)")

    users[user_id]["status"] = "in search"
    save_data(users)
    if not skip_searching_message:
        await update.message.reply_text("Ищу собеседника...", reply_markup=get_keyboard(True))

    user_interests = set(users[user_id].get("interests", []))
    for other_user in users:
        if users[other_user]["status"] == "in search" and other_user != user_id:
            if is_blocked(user_id, other_user):
                continue
            other_user_interests = set(users[other_user].get("interests", []))
            common_interests = user_interests & other_user_interests
            # Проверка, чтобы пользователи без интересов соединялись только с такими же пользователями
            if (not user_interests and other_user_interests) or (user_interests and not other_user_interests) or (not common_interests and user_interests):
                continue

            users[user_id]["chat_with"] = other_user
            users[other_user]["chat_with"] = user_id
            active_chats[user_id] = {"chat_with": other_user, "message_map": {}}
            active_chats[other_user] = {"chat_with": user_id, "message_map": {}}
            users[user_id]["status"] = "chatting"
            users[other_user]["status"] = "chatting"
            save_data(users)
            save_active_chats()

            logging.info(f"(!) Создан активный чат между пользователем {user_id} и пользователем {other_user}. (!)")

            if common_interests:
                common_interests_str = ", ".join(common_interests).upper()
                await update.message.reply_text(f"Собеседник найден! Общие интересы: {common_interests_str}", reply_markup=ReplyKeyboardRemove())
                await context.bot.send_message(
                    other_user,
                    f"Собеседник найден! Общие интересы: {common_interests_str}",
                    reply_markup=ReplyKeyboardRemove(),
                )
            else:
                await update.message.reply_text("Собеседник найден!", reply_markup=ReplyKeyboardRemove())
                await context.bot.send_message(
                    other_user,
                    "Собеседник найден!",
                    reply_markup=ReplyKeyboardRemove(),
                )
            return

    await update.message.reply_text("Свободных собеседников нет.\n\nПоиск займет больше времени, чем обычно...")

# Остановка поиска
async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if users[user_id]["status"] != "in search":
        await update.message.reply_text("Вы не в поиске собеседника.", reply_markup=get_keyboard())
        return
    logging.info(f"(!) Пользователь {user_id} остановил поиск собеседника. (!)")
    users[user_id]["status"] = "normal"
    save_data(users)
    await update.message.reply_text("Поиск остановлен.", reply_markup=get_keyboard(False))

# Команда /next
async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in active_chats:
        await update.message.reply_text(
            "Вы не в чате. Используйте кнопку ниже для поиска собеседника.",
            reply_markup=get_keyboard(),
        )
        return
    other_user = active_chats[user_id]["chat_with"]
    del active_chats[user_id]
    del active_chats[other_user]

    blocked_users = load_blocked_users()
    timeout_str = blocked_users.get("timeout_duration", "1h")
    time_amount = int(timeout_str[:-1])
    time_unit = timeout_str[-1]
    
    if time_unit == 's':
        timeout_duration = timedelta(seconds=time_amount)
    elif time_unit == 'm':
        timeout_duration = timedelta(minutes=time_amount)
    elif time_unit == 'h':
        timeout_duration = timedelta(hours=time_amount)
    elif time_unit == 'd':
        timeout_duration = timedelta(days=time_amount)
    
    now = datetime.now()
    pair = ",".join(sorted([user_id, other_user]))
    blocked_users[pair] = (now + timeout_duration).isoformat()
    
    save_blocked_users(blocked_users)
    save_active_chats()
    users[other_user]["status"] = "normal"
    users[other_user]["chat_with"] = None
    save_data(users)
    try:
        await context.bot.send_message(
            other_user,
            "Ваш собеседник завершил диалог. Используйте кнопку ниже для поиска нового собеседника.",
            reply_markup=get_keyboard(),
        )
    except Exception as e:
        logging.error(f"Ошибка при уведомлении пользователя {other_user}: {e}")

    users[user_id]["status"] = "in search"
    users[user_id]["chat_with"] = None
    save_data(users)
    await update.message.reply_text(
        "Текущий чат завершен. Ищу нового собеседника...",
        reply_markup=get_keyboard(True),
    )
    await search(update, context, skip_searching_message=True)

# Команда /stop
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in active_chats:
        await update.message.reply_text("Вы не в чате. Используйте кнопку ниже для поиска собеседника.", reply_markup=get_keyboard())
        return
    other_user = active_chats[user_id]["chat_with"]
    del active_chats[user_id]
    del active_chats[other_user]

    blocked_users = load_blocked_users()
    timeout_str = blocked_users.get("timeout_duration", "1h")
    time_amount = int(timeout_str[:-1])
    time_unit = timeout_str[-1]
    
    if time_unit == 's':
        timeout_duration = timedelta(seconds=time_amount)
    elif time_unit == 'm':
        timeout_duration = timedelta(minutes=time_amount)
    elif time_unit == 'h':
        timeout_duration = timedelta(hours=time_amount)
    elif time_unit == 'd':
        timeout_duration = timedelta(days=time_amount)
    
    now = datetime.now()
    pair = ",".join(sorted([user_id, other_user]))
    blocked_users[pair] = (now + timeout_duration).isoformat()
    
    save_blocked_users(blocked_users)
    save_active_chats()
    users[user_id]["status"] = "normal"
    users[other_user]["status"] = "normal"
    users[user_id]["chat_with"] = None
    users[other_user]["chat_with"] = None
    save_data(users)
    logging.info(f"(!) Чат между пользователем {user_id} и пользователем {other_user} завершен, они занесены в блок на {timeout_duration}. (!)")

    await update.message.reply_text("Вы покинули чат. Используйте кнопку ниже для нового собеседника.", reply_markup=get_keyboard())
    await context.bot.send_message(
        other_user,
        "Ваш собеседник покинул чат. Используйте кнопку ниже для нового собеседника.",
        reply_markup=get_keyboard(),
    )

# Команда /link
async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in active_chats:
        await update.message.reply_text("Вы не в чате. Используйте кнопку ниже для поиска собеседника.")
        return
    other_user_id = active_chats[user_id]["chat_with"]
    if not update.effective_user.username:
        await update.message.reply_text("Ваше имя пользователя скрыто настройками конфиденциальности. Измените настройки, чтобы делиться аккаунтом.")
        return
    try:
        await context.bot.send_message(
            chat_id=other_user_id,
            text=f"Ваш собеседник отправил ссылку на свой профиль: @{update.effective_user.username}"
        )
        await update.message.reply_text("Ссылка на ваш профиль отправлена собеседнику.")
    except Exception as e:
        logging.error(f"Ошибка при отправке ссылки: {e}")
        await update.message.reply_text("Произошла ошибка при отправке ссылки.")

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in active_chats:
        if update.message.text == "Начать поиск собеседника":
            await search(update, context)
        elif update.message.text == "Остановить поиск":
            await stop_search(update, context)
        elif update.message.text == "Интересы":
            await interests(update, context)
        else:
            await update.message.reply_text("Вы не в чате. Используйте кнопку ниже для поиска собеседника.", reply_markup=get_keyboard())
        return

    other_user_id = active_chats[user_id]["chat_with"]
    text = update.message.text

    if text and "@" in text and not text.startswith("/link"):
        await update.message.reply_text("Отправка упоминаний запрещена. Используйте /link.")
        return
    if text and re.search(r"(https?://|www\.[a-zA-Z]|[a-zA-Z]\.[a-z]{2,})", text.replace(" ", "")):
        await update.message.reply_text("Отправка ссылок запрещена.")
        return

    try:
        reply_to_message_id = None
        if update.message.reply_to_message:
            replied_message_id = update.message.reply_to_message.message_id
            if "message_map" in active_chats[user_id] and replied_message_id in active_chats[user_id]["message_map"]:
                reply_to_message_id = active_chats[user_id]["message_map"][replied_message_id]

        if update.message.text:
            sent_message = await context.bot.send_message(
                chat_id=other_user_id,
                text=update.message.text,
                entities=update.message.entities,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
            )
        elif update.message.photo:
            sent_message = await context.bot.send_photo(
                chat_id=other_user_id,
                photo=update.message.photo[-1].file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
                caption_entities=update.message.caption_entities,
            )
        elif update.message.video:
            sent_message = await context.bot.send_video(
                chat_id=other_user_id,
                video=update.message.video.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
                caption_entities=update.message.caption_entities,
            )
        elif update.message.document:
            sent_message = await context.bot.send_document(
                chat_id=other_user_id,
                document=update.message.document.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
                caption_entities=update.message.caption_entities,
            )
        elif update.message.audio:
            sent_message = await context.bot.send_audio(
                chat_id=other_user_id,
                audio=update.message.audio.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
                caption_entities=update.message.caption_entities,
            )
        elif update.message.voice:
            sent_message = await context.bot.send_voice(
                chat_id=other_user_id,
                voice=update.message.voice.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True,
                caption_entities=update.message.caption_entities,
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

        if "message_map" not in active_chats[user_id]:
            active_chats[user_id]["message_map"] = {}
        if "message_map" not in active_chats[other_user_id]:
            active_chats[other_user_id]["message_map"] = {}
        active_chats[user_id]["message_map"][update.message.message_id] = sent_message.message_id
        active_chats[other_user_id]["message_map"][sent_message.message_id] = update.message.message_id

        save_active_chats()

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text("Произошла ошибка при пересылке сообщения.")

# Команда /ban
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        # Если пользователь не администратор, ничего не отвечаем
        return

    if len(context.args) != 1:
        await update.message.reply_text("Используйте команду в формате: /ban <id пользователя>")
        return

    target_id = context.args[0]
    if target_id not in users:
        await update.message.reply_text(f"Пользователь с id {target_id} не найден.")
        return

    users[target_id]["status"] = "banned"
    save_data(users)

    if target_id in active_chats:
        chat_with_id = active_chats[target_id]["chat_with"]
        del active_chats[target_id]
        del active_chats[chat_with_id]
        save_active_chats()
        await context.bot.send_message(
            chat_with_id,
            "Пользователь, с которым вы общались, был заблокирован администратором. Чат завершен.",
            reply_markup=get_keyboard()
        )
        await context.bot.send_message(
            target_id,
            "Вы были заблокированы администратором. Чат завершен.",
            reply_markup=get_keyboard()
        )
        # Присваиваем статус "normal" собеседнику заблокированного пользователя
        users[chat_with_id]["status"] = "normal"
        save_data(users)

    await update.message.reply_text(f"Пользователь с id {target_id} заблокирован.")

# Команда /getid
async def getid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)  # Приведение user_id к строке
    if user_id != str(ADMIN_ID):  # Приведение ADMIN_ID к строке для сравнения
        # Если пользователь не администратор, ничего не отвечаем
        return

    if user_id not in active_chats:
        await update.message.reply_text("Вы не находитесь в чате.")
        return

    chat_with_id = active_chats[user_id]["chat_with"]
    await update.message.reply_text(f"ID собеседника: {chat_with_id}")

# Команда /unban
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        # Если пользователь не администратор, ничего не отвечаем
        return

    if len(context.args) != 1:
        await update.message.reply_text("Используйте команду в формате: /unban <id пользователя>")
        return

    target_id = context.args[0]
    if target_id not in users:
        await update.message.reply_text(f"Пользователь с id {target_id} не найден.")
        return

    users[target_id]["status"] = "normal"
    save_data(users)
    await update.message.reply_text(f"Пользователь с id {target_id} разблокирован.")

# Команда /debug
async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        # Если пользователь не администратор, ничего не отвечаем
        return
    
    # Устанавливаем статус всех пользователей на "normal", кроме заблокированных
    for user in users:
        if users[user]["status"] != "banned":
            users[user]["status"] = "normal"
    
    # Сохраняем изменения в users.json
    save_data(users)
    
    # Очищаем active_chats.json
    active_chats.clear()
    save_active_chats()

    await update.message.reply_text("Дебаг успешно прошёл. Все пользователи сброшены в 'normal', активные чаты очищены.")

# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("next", next_command))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CommandHandler("link", link))
    application.add_handler(CommandHandler("interests", interests_command))
    application.add_handler(CommandHandler("debug", debug_command))
    application.add_handler(CommandHandler("ban", ban_command))  # Добавлен обработчик команды /ban
    application.add_handler(CommandHandler("unban", unban_command))  # Добавлен обработчик команды /unban
    application.add_handler(CommandHandler("getid", getid_command))  # Добавлен обработчик команды /getid
    application.add_handler(CommandHandler("timeout", timeout_command))  # Добавлен обработчик команды /timeout
    application.add_handler(CallbackQueryHandler(handle_interests, pattern="^interest_"))
    application.add_handler(CallbackQueryHandler(done, pattern="^done$"))
    application.add_handler(CallbackQueryHandler(reset_interests, pattern="^reset_interests$"))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler((filters.TEXT | filters.ATTACHMENT) & ~filters.COMMAND, handle_message))

    # Сохранение текущего тайм-аута в контекст бота при запуске
    blocked_users = load_blocked_users()
    if "timeout_duration" in blocked_users:
        application.bot_data["last_timeout"] = blocked_users["timeout_duration"]
    else:
        application.bot_data["last_timeout"] = "1h"

    application.run_polling()

if __name__ == "__main__":
    main()
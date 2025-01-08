🎭 AnonChat — Анонимный чат для общения в Telegram
=========================

Анонимный чат для общения 1 на 1 с случайным собеседником, обеспечивающий высокий уровень безопасности.
Вся база данных хранится в зашифрованном видн, что гарантирует конфиденциальность ваших данных.
Поддержка множества команд для удобного взаимодействия и расширенной функциональности.

## 📋 Лицензия
Этот проект распространяется на условиях лицензии Apache-2.0 license.  
Полный текст лицензии можно найти в файле [LICENSE](./LICENSE).

## 🤖 Команды бота
Ниже представлен полный список команд, которые поддерживает бот.
Эти команды позволят вам взаимодействовать с ботом, получать различные функции и управлять процессом общения:
```
 /start         Перезапустить бота 🔄
 /search        Начать поиск собеседника 🔎
 /next          Завершить диалог и начать поиск собеседника 🆕
 /stop          Завершить диалог 🛑
 /link          Отправить ссылку на свой Telegram аккаунт собеседнику 🔗
```
## 📁 Файлы проекта
Ниже представлен список всех файлов проекта с подробным описанием их назначения и содержимого:

* **`bot.py`** — Основной файл, содержащий код бота.  
  
* **`config.py`** — Файл, в котором хранится TOKEN вашего бота.  
  
* **`key_generator.py`** — Генератор ключа шифрования для .json файлов. Запускается только один раз при настройке бота.  
  
* **`decryptor.py`** — Дешифровщик .json файлов. Не используется в работе бота, предназначен для проверки содержимого .json файлов администратором.  
  
* **`encryption.key`** — Файл с ключом шифрования для .json файлов. Создается один раз с помощью `key_generator.py`.  
  
* **`users.json`** — База данных пользователей бота и их статусов. Этот файл создается автоматически при запуске бота.  
  
* **`active_chats.json`** — База данных активных чатов. Этот файл будет создан автоматически при появлении первого активного чата.  
  
* **`blocked_users.json`** — База данных пользователей, которые не могут попасть в чат друг с другом в течение 1 часа. Этот файл будет создан автоматически при завершении активного чата.  

## 💭 Типы сообщений
Ниже представлен список всех типов сообщений, которые поддерживает бот:

* **`Текстовые сообщения`** — простые и удобные для общения.
  
* **`Мультимедийные сообщения`** — видео, фотографии, GIF, стикеры, голосовые и видеосообщения.
  
* **`Сообщения с форматированием`** — возможность использовать **жирный**, *курсив*, ~~зачеркнутый~~ текст и другие стили.
  
* **`Отредактированные сообщения`** — бот поддерживает редактирование уже отправленных сообщений.  

## 🍀 Установка и запуск бота

**1. Установите все необходимые библиотеки из файла `requirements.txt`.**
```
cd /путь/к/вашему/проекту
pip install -r requirements.txt
```
  
**2. Запустите файл `key_generator.py`**  
```
cd /путь/к/вашему/проекту
python key_generator.py
```
После запуска файла, в командной строке появится сообщение об успешном выполнении кода.  
В папке с файлами бота должен появится файл `encryption.key`.
  
**3. Запустите основной файл `bot.py`**
```
cd /путь/к/вашему/проекту
python bot.py
```
**Поздравляю! Бот запущен. Проверьте это, отправив ему команду `/start` 👍**

## 😇 Автор проекта

Этот проект был создан с нуля, начиная с самой основы и до полноценной реализации. Автор проекта: [@ibuy](https://t.me/ibuzy).  
Разработка началась 06/01/25, и дата завершения разработки еще не определена — **я продолжаю совершенствовать и обновлять функциональность.**

*Особая благодарность людям, которые приняли участие в тестровании бота.*  
*P.S.: ChatGPT за помощь в процессе разработки.*

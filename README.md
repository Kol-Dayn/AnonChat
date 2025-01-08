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

**`bot.py`** — Основной файл, содержащий код бота.  
  
**`config.py`** — Файл, в котором хранится TOKEN вашего бота.  
  
**`key_generator.py`** — Генератор ключа шифрования для .json файлов. Запускается только один раз при настройке бота.  
  
**`decryptor.py`** — Дешифровщик .json файлов. Не используется в работе бота, предназначен для проверки содержимого .json файлов администратором.  
  
**`encryption.key`** — Файл с ключом шифрования для .json файлов. Создается один раз с помощью `key_generator.py`.  
  
**`users.json`** — База данных пользователей бота и их статусов. Этот файл создается автоматически при запуске бота.  
  
**`active_chats.json`** — База данных активных чатов. Этот файл будет создан автоматически при появлении первого активного чата.  
  
**`blocked_users.json`** — База данных пользователей, которые не могут попасть в чат друг с другом в течение 1 часа. Этот файл будет создан автоматически при завершении активного чата.  

## 💭 Типы сообщений
Ниже приведен список всех типов сообщений которые поддерживает бот:

1. Текстовые сообщения
2. Мультимедийные сообщения (Видео, фото, GIF, стикер, голосовое сообщение, видео сообщение)
3. Сообщения с форматированием (**жирный**, *курсив*, ~~зачеркнутый~~, и т.д.)
4. Отредактированные сообщения

### Passive DPI

Most Passive DPI send HTTP 302 Redirect if you try to access blocked website over HTTP and TCP Reset in case of HTTPS, faster than destination website. Packets sent by DPI usually have IP Identification field equal to `0x0000` or `0x0001`, as seen with Russian providers. These packets, if they redirect you to another website (censorship page), are blocked by GoodbyeDPI.

### Active DPI

Active DPI is more tricky to fool. Currently the software uses 7 methods to circumvent Active DPI:

* TCP-level fragmentation for first data packet
* TCP-level fragmentation for persistent (keep-alive) HTTP sessions
* Replacing `Host` header with `hoSt`
* Removing space between header name and value in `Host` header
* Adding additional space between HTTP Method (GET, POST etc) and URI
* Mixing case of Host header value
* Sending fake HTTP/HTTPS packets with low Time-To-Live value, incorrect checksum or incorrect TCP Sequence/Acknowledgement numbers to fool DPI and prevent delivering them to the destination

These methods should not break any website as they're fully compatible with TCP and HTTP standards, yet it's sufficient to prevent DPI data classification and to circumvent censorship. Additional space may break some websites, although it's acceptable by HTTP/1.1 specification (see 19.3 Tolerant Applications).

The program loads WinDivert driver which uses Windows Filtering Platform to set filters and redirect packets to the userspace. It's running as long as console window is visible and terminates when you close the window.

# How to build from source

This project can be build using **GNU Make** and [**mingw**](https://mingw-w64.org). The only dependency is [WinDivert](https://github.com/basil00/Divert).

To build x86 exe run:

`make CPREFIX=i686-w64-mingw32- WINDIVERTHEADERS=/path/to/windivert/include WINDIVERTLIBS=/path/to/windivert/x86`

And for x86_64:

`make CPREFIX=x86_64-w64-mingw32- BIT64=1 WINDIVERTHEADERS=/path/to/windivert/include WINDIVERTLIBS=/path/to/windivert/amd64`

# How to install as Windows Service

Check examples in `service_install_russia_blacklist.cmd`, `service_install_russia_blacklist_dnsredir.cmd` and `service_remove.cmd` scripts.

Modify them according to your own needs.

# Known issues

* Horribly outdated Windows 7 installations are not able to load WinDivert driver due to missing support for SHA256 digital signatures. Install KB3033929 [x86](https://www.microsoft.com/en-us/download/details.aspx?id=46078)/[x64](https://www.microsoft.com/en-us/download/details.aspx?id=46148), or better, update the whole system using Windows Update.
* Intel/Qualcomm Killer network cards: `Advanced Stream Detect` in Killer Control Center is incompatible with GoodbyeDPI, [disable it](https://github.com/ValdikSS/GoodbyeDPI/issues/541#issuecomment-2296038239).
* QUIK trading software [may interfere with GoodbyeDPI](https://github.com/ValdikSS/GoodbyeDPI/issues/677#issuecomment-2390595606). First start QUIK, then GoodbyeDPI.
* ~~Some SSL/TLS stacks unable to process fragmented ClientHello packets, and HTTPS websites won't open. Bug: [#4](https://github.com/ValdikSS/GoodbyeDPI/issues/4), [#64](https://github.com/ValdikSS/GoodbyeDPI/issues/64).~~ Fragmentation issues are fixed in v0.1.7.
* ~~ESET Antivirus is incompatible with WinDivert driver [#91](https://github.com/ValdikSS/GoodbyeDPI/issues/91). This is most probably antivirus bug, not WinDivert.~~


# Similar projects

- **[zapret](https://github.com/bol-van/zapret)** by @bol-van (for MacOS, Linux and Windows)
- **[Green Tunnel](https://github.com/SadeghHayeri/GreenTunnel)** by @SadeghHayeri (for MacOS, Linux and Windows)
- **[DPI Tunnel CLI](https://github.com/nomoresat/DPITunnel-cli)** by @zhenyolka (for Linux and routers)
- **[DPI Tunnel for Android](https://github.com/nomoresat/DPITunnel-android)** by @zhenyolka (for Android)
- **[PowerTunnel](https://github.com/krlvm/PowerTunnel)** by @krlvm (for Windows, MacOS and Linux)
- **[PowerTunnel for Android](https://github.com/krlvm/PowerTunnel-Android)** by @krlvm (for Android)
- **[SpoofDPI](https://github.com/xvzc/SpoofDPI)** by @xvzc (for macOS and Linux)
- **[SpoofDPI-Platform](https://github.com/r3pr3ss10n/SpoofDPI-Platform)** by @r3pr3ss10n (for Android, macOS, Windows)
- **[GhosTCP](https://github.com/macronut/ghostcp)** by @macronut (for Windows)
- **[ByeDPI](https://github.com/hufrea/byedpi)** for Linux/Windows + **[ByeDPIAndroid](https://github.com/dovecoteescapee/ByeDPIAndroid/)** for Android (no root)
- **[youtubeUnblock](https://github.com/Waujito/youtubeUnblock/)** by @Waujito (for OpenWRT/Entware routers and Linux)

# Kudos

Thanks @basil00 for [WinDivert](https://github.com/basil00/Divert). That's the main part of this program.

Thanks for every [BlockCheck](https://github.com/ValdikSS/blockcheck) contributor. It would be impossible to understand DPI behaviour without this utility.

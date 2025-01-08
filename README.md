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
To check if your ISP's DPI could be circumvented, first make sure that your provider does not poison DNS answers by enabling "Secure DNS (DNS over HTTPS)" option in your browser.

* **Chrome**: Settings → [Privacy and security](chrome://settings/security) → Use secure DNS → With: NextDNS
* **Firefox**: [Settings](about:preferences) → Network Settings → Enable DNS over HTTPS → Use provider: NextDNS

Then run the `goodbyedpi.exe` executable without any options. If it works — congratulations! You can use it as-is or configure further, for example by using `--blacklist` option if the list of blocked websites is known and available for your country.

If your provider intercepts DNS requests, you may want to use `--dns-addr` option to a public DNS resolver running on non-standard port (such as Yandex DNS `77.88.8.8:1253`) or configure DNS over HTTPS/TLS using third-party applications.

Check the .cmd scripts and modify it according to your preference and network conditions.

# How does it work

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

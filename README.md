# Telegram Security Bot — Advanced Cybersecurity & Threat Analysis Engine

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Aiogram](https://img.shields.io/badge/aiogram-3.17%2B-informational.svg)
![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-2.0%2B-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Telegram Security Bot** — Android APK fayllari, xavfli havolalar (URL), fishing va zararli dasturlarni (malware) tahlil qiluvchi, shuningdek Telegram kanallari va guruhlarida kiberxavfsizlik monitoringini ta'minlovchi asinxron Telegram boti.

---

## 🌟 Asosiy Xususiyatlar

- 🛡️ **Chuqurlashtirilgan APK Tahlili:**
  - Android APK fayllarining ruxsatnomalarini (permissions) statik tahlil qilish (`pyaxmlparser`).
  - Xavflilik darajasi (Risk Score: 0 - 100%) va tahdid shablonlarini aniqlash (SMS o'g'irlash, yashirin kuzatuv, xavfli ruxsatlar).
  - Obfuscation va shifrlangan segmentlarni tekshirish.
  - Parallel tahlil qilish uchun `ProcessPoolExecutor` (ko'p yadroli CPU optimizatsiyasi).
- 🔗 **Havola (URL) Xavfsizlik Skaneri:**
  - VirusTotal API integratsiyasi orqali global tahdidlar bazasidan tekshirish.
  - Google Safe Browsing API orqali fishing va fishing sahifalarini aniqlash.
- 📢 **Kanal va Guruh Monitoringi:**
  - Kanalga admin qilib biriktirilganda avtomatik xavfsizlik va yangilanish loglarini yuborish (`/setlog`).
- 🌐 **Ko'p Tilli Tizim (i18n):** O'zbek, Rus va Ingliz tillarida to'liq interfeys.
- 💎 **Premium & To'lov Tizimi:** Telegram Stars / Payment Provider orqali VIP obunalar tizimi.
- ⚙️ **Admin Boshqaruvi:** Foydalanuvchilar statistikasi, xabarnomalar yuborish (broadcast) va tizim loglari.

---

## 🏗️ Arxitektura va Texnologiyalar Steki

- **Dasturlash tili:** Python 3.11+
- **Bot Framework:** Aiogram 3.17+ (Dispatcher, Routers, Filters, FSM)
- **Ma'lumotlar Bazasi:** SQLAlchemy 2.0+ (Async ORM) + `aiosqlite`
- **Konfiguratsiya:** `pydantic-settings`
- **APK Parser:** `pyaxmlparser`
- **Tashqi Xavfsizlik API:** VirusTotal v3 API, Google Safe Browsing API v4
- **Log Menejeri:** `structlog` / Python standard logging
- **Server Xizmati:** Systemd Linux Service

---

## 📁 Loyiha Strukturasi

```
Security-bot/
├── src/
│   ├── config.py             # Pydantic muhit sozlamalari
│   ├── main.py               # Asosiy kirish nuqtasi
│   ├── database/
│   │   ├── models.py         # SQLAlchemy ORM jadvallari
│   │   └── queries.py        # Asinxron DB so'rovlari
│   ├── handlers/
│   │   ├── bot_handler.py    # Asosiy bot mantiqi va fayl tahlili
│   │   ├── admin_handler.py  # Admin buyruqlari
│   │   ├── admin_actions.py  # Admin callbacklari va boshqaruv
│   │   └── channel_handler.py # Kanal va guruh kuzatuvchisi
│   ├── services/
│   │   └── analyzer.py       # APK va havola tahlil mexanizmi
│   └── utils/
│       ├── locales.py        # Ko'p tilli matnlar (UZ, RU, EN)
│       └── logger.py         # Tizimli log yuritish
├── requirements.txt          # Kutubxonalar ro'yxati
└── README.md
```

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Repozitoriyni yuklab olish va virtual muhit yaratish

```bash
git clone https://github.com/izzatbekulkanov/telegram-security-bot.git
cd telegram-security-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Muhit parametrlarini sozlash (`.env`)

`.env` faylini quyidagicha yarating:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ADMINS=123456789,987654321
VT_API_KEY=your_virustotal_api_key
SAFE_BROWSING_KEY=your_google_safe_browsing_key
PAYMENT_TOKEN=your_payment_provider_token
```

### 3. Botni ishga tushirish

```bash
python -m src.main
```

### 4. Linux Production Service (Systemd)

`/etc/systemd/system/security-bot.service`:

```ini
[Unit]
Description=Security Bot Production Service
After=network.target

[Service]
User=superadmin
WorkingDirectory=/home/superadmin/Security-bot
Environment="PYTHONPATH=/home/superadmin/Security-bot"
ExecStart=/home/superadmin/Security-bot/venv/bin/python -m src.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 📄 Litsenziya

Ushbu loyiha [MIT](LICENSE) litsenziyasi asosida himoyalangan.

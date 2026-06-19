# ITLEO Academy — Backend API

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![DRF](https://img.shields.io/badge/DRF-3.17-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Tests](https://img.shields.io/badge/Tests-14%2F14-brightgreen)

Backend-застосунок для управління IT-академією: студенти, групи, оплати, Telegram-бот, email-розсилки, REST API.

---

## Що реалізовано

### По ТЗ
- ✅ **Студенти** — ім'я, телефон, Telegram, email, курс, статус (lead/навчається/завершив/заморозка)
- ✅ **Групи** — назва, викладач, розклад, список студентів
- ✅ **Оплати** — студент, сума, дата, статус (оплачено/очікується/борг), коментар
- ✅ **Telegram-бот** — 6 команд з FSM-діалогом і захистом доступу
- ✅ **API** — `/students/` `/groups/` `/payments/` `/notifications/` з Swagger
- ✅ **Ролі** — admin бачить все, teacher бачить тільки свої групи
- ✅ **Деплой** — Docker Compose, покрокова інструкція
- ✅ **README** — цей файл

### Понад ТЗ
- 🎁 Django Unfold адмін-панель з KPI-віджетами (студенти, боржники, групи)
- 🎁 Celery Beat — автоматичні email-нагадування про оплату щодня о 09:00
- 🎁 Token Authentication для API
- 🎁 Gmail SMTP інтеграція
- 🎁 Pagination для всіх ендпоінтів
- 🎁 14 pytest тестів (auth, ролі, CRUD, permissions, сервіси)
- 🎁 NotificationLog — історія всіх розсилок
- 🎁 Google Calendar — архітектура підготовлена (GoogleAccount модель + google_event_id поле на Schedule)
- 🎁 Мультимова — підготовка структури (uk основна, en у планах)
- 🎁 Ruff — лінтер і форматер
- 🎁 Faker seed — 40 студентів, 4 групи, ~100 оплат українською мовою

---

## Архітектура

```
├── accounts/        # Кастомний User з ролями (admin/teacher)
├── students/        # Student, Course — models, views, serializers, permissions, services, tests
├── schedule/        # Group, Schedule — моделі груп і розкладу
├── payments/        # Payment — облік оплат, список боржників
├── notifications/   # Email + Telegram сповіщення, NotificationLog, Celery tasks
├── integrations/    # Telegram-бот (aiogram)
│   └── bot/         # handlers.py (FSM), runner.py
├── dashboard/       # KPI-віджети для Unfold адмін-панелі
└── config/          # settings.py, urls.py, celery.py
```

### Шари архітектури

| Шар | Де знаходиться | Що робить |
|-----|----------------|-----------|
| **Controllers** | `*/views.py` | HTTP-запити/відповіді, ViewSets |
| **Services** | `students/services.py`, `notifications/services.py` | Бізнес-логіка (get_debtors, broadcast, remind) |
| **Database** | `*/models.py` | Моделі, FK-зв'язки, індекси |
| **Bot logic** | `integrations/bot/` | aiogram handlers, FSM-діалоги |

---

## Технології

| Технологія | Версія | Призначення |
|------------|--------|-------------|
| Python | 3.12 | Основна мова |
| Django | 5.2 LTS | Веб-фреймворк |
| Django REST Framework | 3.17 | REST API |
| PostgreSQL | 16 | База даних |
| Redis | 7 | Черга задач (Celery broker) |
| Celery | 5.x | Фонові задачі |
| aiogram | 3.x | Telegram-бот (асинхронний) |
| Django Unfold | 0.97 | Сучасна адмін-панель |
| drf-spectacular | latest | Swagger / OpenAPI документація |
| Docker Compose | — | Контейнеризація |
| Pytest | 9.x | Тестування |
| Ruff | latest | Лінтер і форматер |
| gunicorn | 26.x | Багатопроцесорний WSGI-сервер для production |
| whitenoise | 6.x | Ефективне обслуговування статичних файлів |
| django-filter | 25.x | Потужна фільтрація API-запитів |
| django-cors-headers | 4.x | CORS-заголовки для інтеграції з Frontend |

---

## Вимоги

- Docker + Docker Compose
- Python 3.12+ (для запуску бота поза Docker)
- Gmail акаунт з App Password (для email-розсилок)
- Telegram Bot Token (від @BotFather)

---

## Швидкий старт

### 1. Клонування репозиторію
```bash
git clone git@github.com:ZamotVlad/ITLEO_Test_Task.git
cd ITLEO_Test_Task
```

### 2. Налаштування змінних середовища
```bash
cp .env.example .env
```
Відкрий `.env` і заповни всі змінні (деталі в розділі [Змінні середовища](#змінні-середовища)).

### 3. Запуск контейнерів
```bash
docker-compose up -d --build
```

Запускаються 5 контейнерів:
- `web` — Django (порт 8000)
- `db` — PostgreSQL
- `redis` — Redis
- `celery_worker` — Celery worker
- `celery_beat` — Celery Beat (планувальник задач)

### 4. Міграції
```bash
docker-compose exec web python manage.py migrate
```

### 5. Створення суперкористувача (власник академії)
```bash
docker-compose exec web python manage.py createsuperuser
```
> При створенні встановлюється роль `admin` автоматично.

### 6. Заповнення тестовими даними
```bash
docker-compose exec web python manage.py seed_db
```
Створює: 4 курси, 3 викладачі, 4 групи (U13, QA Manual, LeoGame Junior, Python Pro), 40 студентів з реальними українськими іменами, ~100 оплат.

### 7. Збір статичних файлів
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 8. Отримання API токена

Через адмінку (простіше):
1. `/admin/` → **Авторизаційний токен** → **Токени** → **Додати токен**
2. Обери користувача `admin`, збережи
3. Скопіюй згенерований токен

Або через Shell:
```bash
docker-compose exec web python manage.py shell
>>> from rest_framework.authtoken.models import Token
>>> from accounts.models import User
>>> user = User.objects.get(username="admin")
>>> token, _ = Token.objects.get_or_create(user=user)
>>> print(token.key)
>>> exit()
```

---

## Зупинка проєкту

```bash
docker-compose down          # зупинити все
docker-compose down -v       # зупинити + видалити дані БД
```

---

## Доступні сервіси після запуску

| Сервіс | URL |
|--------|-----|
| Адмін-панель | http://localhost:8000/admin/ |
| Swagger UI | http://localhost:8000/api/schema/swagger-ui/ |
| ReDoc | http://localhost:8000/api/schema/redoc/ |
| Token Auth | http://localhost:8000/api/auth/token/ |
| API root | http://localhost:8000/api/ |

---

## API

### Авторизація

**Отримати токен:**
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -d "username=admin&password=yourpassword"
# Відповідь: {"token": "abc123..."}
```

**Використання:**
```bash
curl http://localhost:8000/api/students/ \
  -H "Authorization: Token abc123..."
```

### Ендпоінти

| Метод | URL | Опис |
|-------|-----|------|
| GET/POST | `/api/students/` | Студенти |
| GET/PUT/PATCH/DELETE | `/api/students/{id}/` | Студент |
| GET/POST | `/api/groups/` | Групи |
| GET/POST | `/api/schedule/` | Розклад |
| GET/POST | `/api/payments/` | Оплати |
| GET | `/api/payments/debtors/` | Боржники |
| GET | `/api/notifications/` | Логи сповіщень |
| POST | `/api/notifications/send_payment_reminders/` | Надіслати email-нагадування |
| POST | `/api/notifications/broadcast_group/` | Розсилка групі в Telegram |
| GET/POST | `/api/courses/` | Курси |

**Фільтрація і пошук:**
```bash
# Фільтр студентів за статусом
GET /api/students/?status=studying

# Пошук за ім'ям або телефоном
GET /api/students/?search=Іван

# Фільтр оплат за статусом
GET /api/payments/?status=debt
```

### Postman Collection
Імпортуй `docs/api_schema.yaml` в Postman через `File → Import`.

---

## Telegram-бот

### Запуск бота
```bash
# Запуск через Django management command
docker-compose exec web python manage.py run_bot

# Або локально (поза Docker)
python manage.py run_bot
```

> ⚠️ Бот працює в режимі polling і має запускатись окремо від основного сервера.

### Команди бота

| Команда | Опис | Доступ |
|---------|------|--------|
| `/start` | Реєстрація в системі (прив'язка Telegram до студента) | Всі |
| `/add_student` | Додати студента (покроковий FSM-діалог) | Admin/Teacher |
| `/debtors` | Список всіх боржників з сумами | Admin/Teacher |
| `/group <назва>` | Інфо про групу: викладач, розклад, студенти | Admin/Teacher |
| `/remind` | Надіслати Telegram-нагадування боржникам | Admin/Teacher |
| `/broadcast <група> \| <текст>` | Розсилка повідомлення всій групі | Admin/Teacher |

**Приклади:**
```
/group Python Pro
/broadcast U13 | Заняття перенесено на п'ятницю!
```

### Налаштування доступу
Додай свій Telegram chat_id в `.env`:
```env
TELEGRAM_ADMIN_CHAT_IDS=123456789
```
Дізнатись свій chat_id: напиши [@userinfobot](https://t.me/userinfobot)

---

## Celery Beat — автоматичні задачі

Щодня о 09:00 автоматично надсилаються email-нагадування студентам з боргом.

**Налаштування через адмінку:**
1. `/admin/` → `Periodic Tasks` → `Crontabs` → `+ Add`
   - minute: `0`, hour: `9`, решта: `*`
   - Timezone: `Europe/Kyiv`
2. `Periodic Tasks` → `Periodic tasks` → `+ Add`
   - Name: `Daily payment reminders`
   - Task: `notifications.tasks.send_payment_reminders_task`
   - Crontab: обери щойно створений
   - Enabled: ✅

**Ручний запуск для тесту:**
```bash
docker-compose exec web python manage.py shell
>>> from notifications.tasks import send_payment_reminders_task
>>> send_payment_reminders_task.delay()
>>> exit()
```

---

## Тести

```bash
docker-compose exec web pytest students/tests/ -v
```

**14 тестів покривають:**
- Авторизація (Token Auth, неавторизований доступ)
- Ролі admin/teacher (teacher бачить тільки свої групи)
- CRUD операції (студенти, оплати)
- Permissions (teacher не має доступу до чужих студентів)
- Сервісний шар (`get_debtors`, `get_bot_debtors_text`)

---

## Змінні середовища

Скопіюй `.env.example` і заповни:

```env
# Django
DJANGO_SECRET_KEY=your-very-secret-key-here
DJANGO_DEBUG=True  # False в production

# PostgreSQL
POSTGRES_DB=itleo_db
POSTGRES_USER=itleo_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Email (Gmail SMTP)
# Потрібен App Password: Google Account → Security → App passwords
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=abcdabcdabcdabcd
DEFAULT_FROM_EMAIL=your@gmail.com

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_ADMIN_CHAT_IDS=123456789
```

---

## Деплой на сервері

### Підготовка (Ubuntu 22.04)
```bash
# Встановити Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

> **Примітка**: якщо команда `docker-compose` не знайдена, використовуй `docker compose`
> (без дефіса) — сучасні версії Docker встановлюють Compose як plugin.

```bash
# Клонувати репозиторій
git clone git@github.com:ZamotVlad/ITLEO_Test_Task.git
cd ITLEO_Test_Task

# Налаштувати змінні
cp .env.example .env
nano .env
# Встановити DJANGO_DEBUG=False і реальні паролі
```

### Запуск
```bash
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py createsuperuser

# Опційно — для демонстрації роботи системи на тестових даних
docker-compose exec web python manage.py seed_db

# Запусти бота в окремому терміналі/сесії (не у фоні -d,
# бо при рестарті контейнера web бот не підніметься автоматично)
docker-compose exec web python manage.py run_bot
```

### Перевірка статусу
```bash
docker-compose ps
docker-compose logs web
docker-compose logs celery_worker
```

### Оновлення коду
```bash
git pull origin main
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

---

## Мультимова

Основна мова — **українська**. Архітектура підготовлена до англійської:

```python
# settings.py
LANGUAGES = [
    ("uk", "Українська"),
    ("en", "English"),
]
```

Для активації англійського перекладу:
```bash
django-admin makemessages -l en
# Перекласти рядки в locale/en/LC_MESSAGES/django.po
django-admin compilemessages
```

---

## Відомі обмеження

**Telegram chat_id** — бот може надсилати повідомлення лише студентам, які самі написали `/start` боту. Це обмеження Telegram API: бот не може ініціювати діалог першим. Поле `telegram_chat_id` заповнюється автоматично при першому контакті студента з ботом.

**Авторизація API** — використовується Token Authentication (достатньо для Swagger/Postman і поточного етапу). JWT через `djangorestframework-simplejwt` — наступний крок для production frontend.

**Google Calendar** — архітектура підготовлена: модель `GoogleAccount` і поле `google_event_id` на `Schedule` вже в БД. Найлогічніший сценарій реалізації — синхронізація розкладу в особистий Google Calendar кожного викладача. OAuth flow для викладачів — наступний крок розвитку продукту.

**Email у тестових даних** — Faker генерує випадкові email-адреси. У production студенти вводять реальні адреси при реєстрації.

---

## Структура проєкту

```
ITLEO_Test_Task/
├── accounts/                  # Кастомний User з ролями
├── config/                    # settings.py, urls.py, celery.py
├── dashboard/                 # KPI-віджети адмінки
├── integrations/              # Telegram-бот
│   └── bot/                   # handlers.py (FSM), runner.py
├── notifications/             # Email + Telegram сповіщення
│   ├── models.py              # NotificationLog
│   ├── services.py            # Спільна логіка (email + Telegram)
│   └── tasks.py               # Celery задачі
├── payments/                  # Облік оплат
├── schedule/                  # Групи і розклад
├── students/                  # Студенти і курси
│   ├── permissions.py         # IsAdminOrOwnTeacher
│   ├── services.py            # get_debtors()
│   └── tests/                 # 14 pytest тестів
├── templates/
│   └── admin/index.html       # Кастомний шаблон адмінки з KPI
├── docs/
│   └── api_schema.yaml        # OpenAPI схема для Postman
├── locale/                    # Файли перекладів (підготовлено)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml             # Ruff + pytest конфігурація
└── .env.example               # Приклад змінних середовища
```

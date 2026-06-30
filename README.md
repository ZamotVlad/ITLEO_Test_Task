# Academy Backend

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2_LTS-green)
![DRF](https://img.shields.io/badge/DRF-3.17-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Tests](https://img.shields.io/badge/Tests-30_passed-brightgreen)

Backend для управління IT-академією: студенти, групи, оплати, батьки, 5 ролей, Telegram-бот, Google Calendar, REST API.

---

## Що реалізовано

### Stage 1 — Ядро

- ✅ Студенти — ім'я, телефон, Telegram, email, курс, статус
- ✅ Групи — назва, викладач, розклад, список студентів
- ✅ Оплати — студент, сума, дата, статус, коментар
- ✅ Telegram-бот — 8 команд з FSM-діалогом і захистом доступу
- ✅ REST API — всі ендпоінти з Swagger / ReDoc
- ✅ Docker Compose — 5 контейнерів
- ✅ Gmail SMTP — email-нагадування
- ✅ Celery Beat — автоматичні задачі
- ✅ Token Authentication
- ✅ Django Unfold — адмін-панель з KPI-картками

### Stage 2 — Розширення

- ✅ **5 ролей** — owner, manager, teacher, parent, student
- ✅ **Батьки** — модель Parent, окрема секція в адмінці, M2M до Student
- ✅ **Матриця прав** — RoleBasedPermission, scope\_\* функції, SAFE_METHODS
- ✅ **Google Calendar** — OAuth, синхронізація по групі, Google Meet посилання
- ✅ **Експорт** — CSV/Excel для Student, Parent, User (django-import-export)
- ✅ **Admin action** — "Створити логін і надіслати запрошення" для Student/Parent
- ✅ **Сповіщення** — 5 типів (payment_reminder, welcome, schedule_change, class_reminder, broadcast)
- ✅ **CC батькам** — при нагадуваннях про оплату
- ✅ **Нові команди бота** — /schedule, /stats
- ✅ **Нові Celery tasks** — class_reminder (кожні 30 хв), schedule_change (сигнал)
- ✅ **API** — /api/users/, /api/parents/, /api/users/me/
- ✅ **30 pytest тестів** — повне покриття матриці ролей
- ✅ **Permissions в адмінці** — has_view/add/change/delete для всіх ролей

---

## Архітектура

```
├── accounts/        # User з 5 ролями, roles.py
├── students/        # Student, Parent, Course — models, views, serializers, permissions, services, tests
├── schedule/        # Group, Schedule — моделі груп і розкладу
├── payments/        # Payment — облік оплат
├── notifications/   # Email + Telegram сповіщення, NotificationLog, Celery tasks
├── integrations/    # Telegram-бот + Google Calendar
│   ├── bot/         # handlers.py (FSM, 8 команд)
│   └── services/    # calendar_sync.py
├── dashboard/       # KPI-віджети для Unfold
└── config/          # settings.py, urls.py, celery.py
```

### Шари архітектури

| Шар         | Де знаходиться                                      | Що робить                        |
| ----------- | --------------------------------------------------- | -------------------------------- |
| Controllers | `*/views.py`                                        | HTTP-запити/відповіді, ViewSets  |
| Services    | `students/services.py`, `notifications/services.py` | Бізнес-логіка, scope\_\* функції |
| Permissions | `students/permissions.py`                           | RoleBasedPermission              |
| Database    | `*/models.py`                                       | Моделі, FK-зв'язки, індекси      |
| Bot logic   | `integrations/bot/`                                 | aiogram handlers, FSM-діалоги    |
| Calendar    | `integrations/services/`                            | Google Calendar OAuth + sync     |

---

## Матриця прав

> ✅ повний доступ · ❌ немає доступу · 🔮 заплановано (Future Stage 3+)

| Дія                                  | owner |   manager   |   teacher   |   parent    | student | support |
| ------------------------------------ | :---: | :---------: | :---------: | :---------: | :-----: | :-----: |
| Бачить всіх студентів/групи          |  ✅   |     ✅      | свої групи  | своїх дітей |  себе   |   ❌    |
| Створює/редагує студентів, батьків   |  ✅   |     ✅      |     ❌      |     ❌      |   ❌    |   ❌    |
| Створює групи, оплати                |  ✅   |     ✅      |     ❌      |     ❌      |   ❌    |   ❌    |
| Видаляє записи (DELETE)              |  ✅   |     ❌      |     ❌      |     ❌      |   ❌    |   ❌    |
| Архівує записи (Soft Delete) 🔮      |  ✅   |     ✅      |     ❌      |     ❌      |   ❌    |   ❌    |
| Фінансова звітність / всі оплати     |  ✅   | ✅ перегляд |     ❌      |    свої     |  свої   |   ❌    |
| Призначає ролі (крім student/parent) |  ✅   |     ❌      |     ❌      |     ❌      |   ❌    |   ❌    |
| Призначає ролі student/parent        |  ✅   |     ✅      |     ❌      |     ❌      |   ❌    |   ❌    |
| Налаштування системи                 |  ✅   |     ❌      |     ❌      |     ❌      |   ❌    |   ❌    |
| Експорт/імпорт даних                 |  ✅   |     ✅      |     ❌      |     ❌      |   ❌    |   ❌    |
| Розклад (перегляд)                   |  всі  |     всі     | своєї групи |   дитини    |  свій   |   ❌    |
| Django Admin (is_staff)              |  ✅   |     ✅      |     ❌      |     ❌      |   ❌    |   ❌    |
| Бачить чати 🔮                       |  ✅   |     ✅      |     ✅      |    своїх    |  своїх  |   ✅    |
| Пише в чат / модерує 🔮              |  ✅   |     ✅      |     ✅      |     ✅      |   ✅    |   ✅    |
| Метрики відповіді викладачів 🔮      |  ✅   |     ✅      |     ❌      |     ❌      |   ❌    |   ✅    |
| Домашні завдання — перегляд 🔮       |  ✅   |     ✅      |    своїх    |   дитини    |  свої   |   ❌    |
| Домашні завдання — перевірка 🔮      |  ✅   |     ✅      |  ✅ своїх   |     ❌      |   ❌    |   ❌    |
| Домашні завдання — відправка 🔮      |  ✅   |     ✅      |     ❌      |     ❌      |   ✅    |   ❌    |

> Рядки з 🔮 — заплановано в майбутніх етапах. Поточна реалізація — перші 12 рядків.

---

## Технології

| Технологія            | Версія  | Призначення            |
| --------------------- | ------- | ---------------------- |
| Python                | 3.12    | Основна мова           |
| Django                | 5.2 LTS | Веб-фреймворк          |
| Django REST Framework | 3.17    | REST API               |
| PostgreSQL            | 16      | База даних             |
| Redis                 | 7       | Celery broker          |
| Celery                | 5.x     | Фонові задачі          |
| aiogram               | 3.x     | Telegram-бот           |
| Django Unfold         | latest  | Адмін-панель           |
| django-import-export  | 4.x     | Експорт CSV/Excel      |
| google-auth-oauthlib  | latest  | Google Calendar OAuth  |
| drf-spectacular       | latest  | Swagger / OpenAPI      |
| Docker Compose        | —       | Контейнеризація        |
| Pytest                | 9.x     | Тестування (30 тестів) |
| Ruff                  | latest  | Лінтер і форматер      |

---

## Вимоги

- Docker + Docker Compose
- Gmail акаунт з App Password
- Telegram Bot Token (від @BotFather)
- Google Cloud проєкт з Calendar API (для синхронізації)

---

## Швидкий старт

### 1. Клонування

```bash
git clone git@github.com:ZamotVlad/ITLEO_Test_Task.git
cd ITLEO_Test_Task
```

### 2. Змінні середовища

```bash
cp .env.example .env
# Заповни .env (деталі в розділі "Змінні середовища")
```

### 3. Запуск

```bash
docker-compose up -d --build
```

Запускаються 5 контейнерів: `web`, `db`, `redis`, `celery_worker`, `celery_beat`.

### 4. Міграції

```bash
docker-compose exec web python manage.py migrate
```

### 5. Наповнення даними

```bash
docker-compose exec web python manage.py seed_db
```

Створює власників, менеджерів, викладачів, студентів і батьків з тимчасовим паролем `academy123`.

### 6. Створення свого суперюзера

```bash
docker-compose exec web python manage.py createsuperuser
```

### 7. Збір статичних файлів

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

---

## Доступні сервіси

| Сервіс         | URL                                                |
| -------------- | -------------------------------------------------- |
| Адмін-панель   | http://localhost:8000/admin/                       |
| Swagger UI     | http://localhost:8000/api/schema/swagger-ui/       |
| ReDoc          | http://localhost:8000/api/schema/redoc/            |
| Token Auth     | http://localhost:8000/api/auth/token/              |
| API root       | http://localhost:8000/api/                         |
| Google Connect | http://localhost:8000/integrations/google/connect/ |

---

## Вхід в систему

Після `createsuperuser` відкрий адмін-панель: **http://localhost:8000/admin/**

> ⚠️ Тимчасовий пароль для власників і менеджерів зі `seed_db` — `academy123`.
> Кожен має змінити його після першого входу через адмінку.

---

## Процес реєстрації студента

Затверджений flow (вручну через менеджера):

```
1. Lead залишив заявку (телефон, Instagram тощо)
2. Manager заходить в адмінку → Студенти → Додати
3. Manager заходить в адмінку → Батьки → Додати (якщо є)
4. Вибирає студента/батька → Action "Створити логін і надіслати запрошення"
5. Система генерує пароль і надсилає на email
6. Студент/батько отримує доступ лише до своїх даних
```

> Самореєстрація через сайт/бота — планується в наступному етапі.

---

## API

### Авторизація

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -d "username=admin&password=yourpassword"
# {"token": "abc123..."}

curl http://localhost:8000/api/students/ \
  -H "Authorization: Token abc123..."
```

### Ендпоінти

| Метод                | URL                                          | Опис                             |
| -------------------- | -------------------------------------------- | -------------------------------- |
| GET/POST             | `/api/students/`                             | Студенти                         |
| GET/PUT/PATCH/DELETE | `/api/students/{id}/`                        | Студент                          |
| GET/POST             | `/api/parents/`                              | Батьки ⭐ новий                  |
| GET/POST             | `/api/users/`                                | Користувачі ⭐ новий             |
| GET                  | `/api/users/me/`                             | Профіль поточного юзера ⭐ новий |
| GET/POST             | `/api/groups/`                               | Групи                            |
| GET/POST             | `/api/schedule/`                             | Розклад                          |
| GET/POST             | `/api/payments/`                             | Оплати                           |
| GET                  | `/api/payments/debtors/`                     | Боржники                         |
| GET                  | `/api/notifications/`                        | Логи сповіщень                   |
| POST                 | `/api/notifications/send_payment_reminders/` | Email-нагадування                |
| POST                 | `/api/notifications/broadcast_group/`        | Розсилка групі                   |
| GET/POST             | `/api/courses/`                              | Курси                            |

### Фільтрація

```bash
GET /api/students/?status=studying
GET /api/students/?search=Іван
GET /api/payments/?status=debt
```

---

## Telegram-бот

### Налаштування бота (один раз)

1. Написати [@BotFather](https://t.me/BotFather) в Telegram
2. `/newbot` → задати назву → задати username
3. Скопіювати токен в `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=1234567890:ABC...
```

### Налаштування доступу адміна

1. Написати [@userinfobot](https://t.me/userinfobot) → скопіювати свій `id`
2. Додати в `.env`:

```dotenv
TELEGRAM_ADMIN_CHAT_IDS=123456789,987654321
```

### Запуск бота

```bash
# В окремому терміналі
docker-compose exec web python manage.py run_bot
```

> ⚠️ Бот працює в режимі polling — запускати в окремому терміналі.

### Як студент/викладач підключається

```
1. Знайти бота в Telegram за username
2. Написати /start
3. Бот автоматично прив'язує Telegram до акаунту по username
4. Далі приходять нагадування автоматично
```

> ⚠️ Студент має мати заповнений `telegram_username` в адмінці перед першим `/start`.

### Команди бота

| Команда                         | Опис                               | Доступ |
| ------------------------------- | ---------------------------------- | ------ |
| `/start`                        | Прив'язка Telegram до акаунту      | Всі    |
| `/add_student`                  | Додати студента (FSM-діалог)       | Admin  |
| `/debtors`                      | Список боржників                   | Admin  |
| `/group <назва>`                | Інфо про групу                     | Admin  |
| `/remind`                       | Нагадування боржникам + CC батькам | Admin  |
| `/broadcast <група> \| <текст>` | Розсилка групі                     | Admin  |
| `/schedule`                     | Розклад всіх груп                  | Admin  |
| `/stats`                        | Статистика академії                | Admin  |

---

## Google Calendar

### Налаштування (один раз)

1. Відкрий [console.cloud.google.com](https://console.cloud.google.com)
2. Новий проєкт → назва `Academy`
3. APIs & Services → Library → `Google Calendar API` → Enable
4. Google Auth Platform → Audience:
   - User Type: `External`
   - Додай свій email як Test user
5. Clients → Create OAuth client ID:
   - Application type: `Web application`
   - Authorized redirect URI: `http://localhost:8000/integrations/google/callback/`
6. Скопіюй Client ID і Client Secret в `.env`

### Підключення (один раз після деплою)

```
http://localhost:8000/integrations/google/connect/
```

Авторизуйся через Google акаунт академії → токени збережуться в БД автоматично.

### Синхронізація розкладу

```bash
# Всі групи
http://localhost:8000/integrations/google/sync/all/

# Конкретна група (group_id з адмінки)
http://localhost:8000/integrations/google/sync/group/1/
```

Кожне заняття → повторювана подія (`RRULE:FREQ=WEEKLY`) з:

- Attendees: всі студенти групи + викладач (запрошення на їх email)
- Google Meet посилання (автоматично)

### ⚠️ Production checklist для Google Calendar

1. `OAUTHLIB_INSECURE_TRANSPORT=1` — тільки для localhost. В production прибрати (буде HTTPS)
2. OAuth consent screen — зараз статус `Testing` (макс 100 користувачів). Перед production: Publishing status → `In production` + верифікація Google
3. App name — змінити в Google Console → Branding → `Academy`
4. Токени — зберігаються як plain text. Для production розглянути шифрування (Stage 3+)
5. `GOOGLE_REDIRECT_URI` — змінити на `https://admin.itleo.academy/integrations/google/callback/`

---

## Батьки — нова модель

Stage 2 додає модель `Parent` з M2M зв'язком до `Student`.

**Через адмінку:**

- `/admin/students/parent/` — список батьків
- Action "Створити логін" — генерує акаунт і надсилає запрошення на email

**Через API:**

```bash
GET /api/parents/           # список (owner/manager)
POST /api/parents/          # створити
GET /api/parents/{id}/      # деталі
```

---

## Celery Beat — автоматичні задачі

| Задача                        | Розклад       | Опис                                     |
| ----------------------------- | ------------- | ---------------------------------------- |
| `send_payment_reminders_task` | Щодня о 09:00 | Email-нагадування боржникам + CC батькам |
| `send_class_reminders_task`   | Кожні 30 хв   | Telegram за 2 год до заняття             |

Налаштування через адмінку: `/admin/django_celery_beat/periodictask/`

---

## Тести

```bash
docker-compose exec web pytest students/tests/ -v
```

**30 тестів** покривають:

- Авторизація (Token Auth)
- Матриця 5 ролей (owner/manager/teacher/parent/student)
- CRUD операції
- DELETE тільки для owner
- validate_role захист
- scope\_\* фільтрація
- /api/me/ endpoint
- Сервісний шар

---

## Змінні середовища

```dotenv
# Django
DJANGO_SECRET_KEY=your-very-secret-key-here
DJANGO_DEBUG=True  # False в production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# PostgreSQL
POSTGRES_DB=academy_db
POSTGRES_USER=academy_user
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

# Google Calendar OAuth
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/integrations/google/callback/
# В production: https://admin.itleo.academy/integrations/google/callback/
```

---

## Деплой на сервері (Ubuntu 22.04 + VPS)

```bash
# 1. Встановити Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 2. Клонувати репозиторій
git clone git@github.com:ZamotVlad/ITLEO_Test_Task.git
cd ITLEO_Test_Task

# 3. Налаштувати змінні
cp .env.example .env
nano .env
# Встановити:
# DJANGO_DEBUG=False
# ALLOWED_HOSTS=admin.itleo.academy
# GOOGLE_REDIRECT_URI=https://admin.itleo.academy/integrations/google/callback/
# Реальні паролі і токени

# 4. Запуск
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py seed_db
docker-compose exec web python manage.py createsuperuser

# 5. Бот (в окремій сесії)
docker-compose exec web python manage.py run_bot
```

### Перевірка статусу

```bash
docker-compose ps
docker-compose logs web --tail=20
docker-compose logs celery_worker --tail=20
```

### Оновлення коду

```bash
git pull origin main
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

---

## Структура проєкту

```
Academy_Backend/
├── accounts/                  # User з 5 ролями, roles.py
├── config/                    # settings.py, urls.py, celery.py
├── dashboard/                 # KPI-віджети адмінки
├── integrations/              # Telegram-бот + Google Calendar
│   ├── bot/                   # handlers.py (FSM, 8 команд)
│   └── services/              # calendar_sync.py
├── notifications/             # Email + Telegram сповіщення
│   ├── models.py              # NotificationLog (5 типів)
│   ├── services.py            # remind, broadcast, CC батькам
│   └── tasks.py               # Celery задачі
├── payments/                  # Облік оплат
├── schedule/                  # Групи і розклад
├── students/                  # Студенти, батьки, курси
│   ├── models.py              # Student, Parent, Course
│   ├── permissions.py         # RoleBasedPermission
│   ├── services.py            # scope_* функції
│   └── tests/                 # 30 pytest тестів
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml             # Ruff + pytest конфігурація
└── .env.example
```

---

## Відомі обмеження

- **Telegram chat_id** — бот може писати лише тим, хто першим написав `/start`. Обмеження Telegram API.
- **Token Auth** — для поточного етапу достатньо. JWT — наступний крок для production React-фронтенду.
- **Google Calendar** — OAuth consent screen в статусі Testing (до 100 користувачів). Перед production потрібна верифікація Google.
- **Імпорт даних** — зараз реалізовано тільки експорт. Імпорт — наступний крок після узгодження формату файлу.
- **runserver** — зараз використовується для розробки. Перед production замінити на gunicorn.

---

## TODO / Backlog

> Ці функції заплановані, але не реалізовані в поточному етапі.

### Найближчий пріоритет

- [ ] **Імпорт користувачів** — CSV/Excel через django-import-export (потребує узгодження формату)
- [ ] **Soft Delete** — архівування замість фізичного видалення (`is_archived` поле)

### Майбутні етапи (Stage 3+)

- [ ] **Інвайт flow** — студент отримує посилання для самостійного встановлення пароля
- [ ] **JWT автентифікація** — замість Token Auth для React frontend
- [ ] **Роль Support/Moderator** — доступ до чатів без фінансів
- [ ] **Самореєстрація** — батько реєструється сам через сайт/бота
- [ ] **Чат** — real-time комунікація (Django Channels або polling)
- [ ] **Домашні завдання** — відправка, перевірка, статус
- [ ] **Масштабування на студентів** — особисті кабінети через React frontend (розклад, домашні завдання, статус оплати)

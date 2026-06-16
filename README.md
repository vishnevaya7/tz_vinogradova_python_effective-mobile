# Система аутентификации и авторизации (ТЗ Effective Mobile)

Кастомная RBAC-система на Django REST Framework + PostgreSQL.
**Собственная токен-аутентификация** (без Django-сессий), **собственная модель пользователя** (AbstractBaseUser),
**собственная схема прав доступа** (Role → RolePermission ← Resource + Action, M2M user-role).

---

## 1. Быстрый старт

### Требования
- Python 3.13+
- Docker (для PostgreSQL)

### Установка и запуск

```bash
# 1. Перейти в проект
cd tz_vinogradova_python_effective-mobile

# 2. Создать виртуальное окружение и установить зависимости
python -m venv venv
venv\Scripts\pip install -r requirements.txt

# 3. Запустить PostgreSQL в Docker
docker run -d --name tz-postgres ^
  -e POSTGRES_PASSWORD=password ^
  -e POSTGRES_DB=tz_vinogradova ^
  -e POSTGRES_USER=postgres ^
  -p 5432:5432 postgres:16

# 4. Применить миграции
venv\Scripts\python manage.py migrate

# 5. Загрузить тестовые данные
venv\Scripts\python manage.py seed_data

# 6. Запустить сервер
venv\Scripts\python manage.py runserver
```

Сервер доступен на `http://127.0.0.1:8000`.

---

## 2. Тестовые данные

| Email | Роль | Пароль | Права |
|---|---|---|---|
| `admin@example.com` | admin | `password` | read/write/delete → document, report, permissions |
| `manager@example.com` | manager | `password` | read/write → document, report |
| `user@example.com` | user | `password` | read → document, report |

---

## 3. Проверка работы (по пунктам ТЗ)

### 3.1 Регистрация

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"ivan@test.com\",\"first_name\":\"Иван\",\"last_name\":\"Петров\",\"password\":\"qwerty123\",\"password_repeat\":\"qwerty123\"}"
```

**Ожидаемый ответ:** `201 Created`
```json
{"message":"Регистрация успешна","user_id":4}
```

### 3.2 Вход (login по email + паролю)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"password\"}"
```

**Ожидаемый ответ:** `200 OK`
```json
{
  "token":"a1b2c3...64_символа_hex",
  "user":{"id":1,"email":"admin@example.com","first_name":"Админ","last_name":"Админов","is_active":true,...}
}
```

Сохраните токен в переменную:
```bash
set TOKEN=a1b2c3...
```

### 3.3 Mock-объекты с доступом (admin)

```bash
curl http://127.0.0.1:8000/api/documents/ -H "Authorization: Token %TOKEN%"
```

**Ожидаемый ответ:** `200 OK` — список из 3 документов

```bash
curl http://127.0.0.1:8000/api/reports/ -H "Authorization: Token %TOKEN%"
```

**Ожидаемый ответ:** `200 OK` — список из 3 отчётов

### 3.4 401 — запрос без токена

```bash
curl http://127.0.0.1:8000/api/documents/
```

**Ожидаемый ответ:** `401 Unauthorized`
```json
{"detail":"Учётные данные не предоставлены."}
```

### 3.5 403 — нет роли (пользователь только что зарегистрирован)

```bash
# Логинимся новым пользователем (без роли)
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"ivan@test.com\",\"password\":\"qwerty123\"}"

# Сохраняем токен и пытаемся получить документы
curl http://127.0.0.1:8000/api/documents/ -H "Authorization: Token <token_ivan>"
```

**Ожидаемый ответ:** `403 Forbidden`

### 3.6 403 — пользователь не может в админку

```bash
# Логинимся как user
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@example.com\",\"password\":\"password\"}"

curl http://127.0.0.1:8000/api/admin/roles/ -H "Authorization: Token <token_user>"
```

**Ожидаемый ответ:** `403 Forbidden`

### 3.7 Администратор управляет правами (CRUD)

```bash
# Получить список ролей
curl http://127.0.0.1:8000/api/admin/roles/ -H "Authorization: Token %TOKEN%"

# Получить список прав
curl http://127.0.0.1:8000/api/admin/permissions/ -H "Authorization: Token %TOKEN%"

# Создать новое право
curl -X POST http://127.0.0.1:8000/api/admin/permissions/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Token %TOKEN%" ^
  -d "{\"role\":2,\"resource\":2,\"action\":3}"

# Назначить роль пользователю
curl -X POST http://127.0.0.1:8000/api/admin/user-roles/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Token %TOKEN%" ^
  -d "{\"user\":4,\"role\":3}"
```

### 3.8 Обновление профиля

```bash
curl -X PUT http://127.0.0.1:8000/api/auth/profile/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Token %TOKEN%" ^
  -d "{\"first_name\":\"Новое\",\"last_name\":\"Имя\"}"
```

**Ожидаемый ответ:** `200 OK`

### 3.9 Logout

```bash
curl -X POST http://127.0.0.1:8000/api/auth/logout/ ^
  -H "Authorization: Token %TOKEN%"
```

**Ожидаемый ответ:** `200 OK`
```json
{"message":"Выход выполнен"}
```

### 3.10 Мягкое удаление (soft delete)

```bash
curl -X DELETE http://127.0.0.1:8000/api/auth/delete/ ^
  -H "Authorization: Token <token_user>"

# Попытка войти снова
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@example.com\",\"password\":\"password\"}"
```

**Ожидаемый ответ:** `400 Bad Request`
```json
["Учётная запись деактивирована."]
```

---

## 4. Схема БД (RBAC)

```
┌─────────────────┐       ┌─────────────────────┐       ┌──────────┐
│      Role       │       │   RolePermission    │       │ Resource │
│    (Роль)       │──────<│  (Право доступа)    │>──────│ (Ресурс) │
├─────────────────┤       ├─────────────────────┤       ├──────────┤
│ id (PK)         │       │ id (PK)             │       │ id (PK)  │
│ name (UQ)       │       │ role_id (FK)        │       │ name (UQ)│
└─────────────────┘       │ resource_id (FK)    │       └──────────┘
        │                 │ action_id (FK)      │
        │                 │ UNIQUE(role,res,act)│
        │                 └──────────┬──────────┘
        │                            │
        │                     ┌──────┴──────┐
        │                     │   Action    │
        │                     │ (Действие)  │
        │                     ├─────────────┤
        │                     │ id (PK)     │
        │                     │ name (UQ)   │
        │                     └─────────────┘
        │
┌───────┴──────────┐     ┌──────────────────┐
│   CustomUser     │     │    UserRole      │
│  (Пользователь)  │────<│ (Роль польз-ля)  │
├──────────────────┤     ├──────────────────┤
│ id (PK)          │     │ id (PK)          │
│ email (UQ)       │     │ user_id (FK)     │
│ password         │     │ role_id (FK)     │
│ first_name       │     │ assigned_at      │
│ last_name        │     │ UNIQUE(user,role)│
│ is_active        │     └──────────────────┘
│ is_staff         │
│ created_at       │     ┌──────────────────┐
│ updated_at       │     │    AuthToken     │
└──────────────────┘     │    (Токен)       │
        │                ├──────────────────┤
        └───────────────>│ id (PK)          │
                         │ user_id (FK, UQ) │
                         │ key (UQ, 64)     │
                         │ created_at       │
                         └──────────────────┘
```

| Модель | Назначение | Ключевые поля |
|---|---|---|
| **CustomUser** | Пользователь (AbstractBaseUser) | `email` (USERNAME_FIELD), `first_name`, `last_name`, `is_active` |
| **AuthToken** | Токен аутентификации (1:1 с пользователем) | `user` (OneToOne), `key` (hex 64) |
| **Role** | Роль | `name` (уникальное) |
| **Resource** | Защищаемый ресурс | `name` (уникальное) |
| **Action** | Действие над ресурсом | `name` (уникальное) |
| **RolePermission** | Связка «роль→ресурс→действие» | `role`, `resource`, `action` (unique_together) |
| **UserRole** | M2M-связь пользователь↔роль | `user`, `role` (unique_together), `assigned_at` |

### Алгоритм проверки доступа

1. Запрос → извлечь `Authorization: Token <key>` → найти `AuthToken` → получить `user`
2. Пользователь не определён → **401**
3. Найти все `role_id` пользователя через `UserRole`
4. Ролей нет → **403**
5. Ищем `RolePermission(role_id IN [...], resource__name, action__name)` в БД
6. Не найдено → **403**
7. Найдено → доступ разрешён

---

## 5. Структура проекта

```
├── core/                  # Конфигурация Django
│   ├── settings.py         # Без django.contrib.sessions, кастомный TokenAuthentication
│   ├── urls.py             # Корневой роутинг + карта API
│   └── middleware.py        # 401/403 разграничение
├── users/                  # Пользователи и аутентификация
│   ├── models.py            # CustomUser (AbstractBaseUser), AuthToken
│   ├── authentication.py    # TokenAuthentication (свой, не DRF)
│   ├── serializers.py       # Register, Login, Profile
│   ├── views.py             # Auth-эндпоинты (токены, без сессий)
│   └── urls.py
├── access_control/         # Права доступа
│   ├── models.py            # Role, Resource, Action, RolePermission, UserRole
│   ├── permissions.py       # ResourceAccessPermission (M2M проверка)
│   ├── serializers.py       # Role, Resource, Action, Permission, UserRole
│   ├── views.py             # Mock-объекты + Admin CRUD (ViewSet'ы)
│   ├── urls.py
│   └── management/commands/seed_data.py
├── .env                     # Конфигурация (SECRET_KEY, DB_*)
└── README.md
```

---

## 6. API Endpoints (полный список)

### Аутентификация

| Метод | URL | Доступ | Описание |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Все | Регистрация |
| `POST` | `/api/auth/login/` | Все | Вход → токен + профиль |
| `POST` | `/api/auth/logout/` | Токен | Удаление токена |
| `GET` `PUT` | `/api/auth/profile/` | Токен | Просмотр/редактирование |
| `DELETE` | `/api/auth/delete/` | Токен | Мягкое удаление |

### Mock-объекты (проверка доступа)

| Метод | URL | Ресурс | Действие |
|---|---|---|---|
| `GET` | `/api/documents/` | document | read |
| `GET` | `/api/reports/` | report | read |

### Администрирование прав (только admin — роль с доступом к resource=permissions)

| Метод | URL |
|---|---|
| `GET` `POST` | `/api/admin/roles/` |
| `GET` `PUT` `DELETE` | `/api/admin/roles/{id}/` |
| `GET` `POST` | `/api/admin/resources/` |
| `GET` `PUT` `DELETE` | `/api/admin/resources/{id}/` |
| `GET` `POST` | `/api/admin/actions/` |
| `GET` `PUT` `DELETE` | `/api/admin/actions/{id}/` |
| `GET` `POST` | `/api/admin/permissions/` |
| `GET` `PUT` `DELETE` | `/api/admin/permissions/{id}/` |
| `GET` `POST` | `/api/admin/user-roles/` |
| `GET` `PUT` `DELETE` | `/api/admin/user-roles/{id}/` |

---

## 7. Кастомность (отличие от встроенных механизмов Django/DRF)

| Компонент | Стандартный подход | Реализация в проекте |
|---|---|---|
| **Модель пользователя** | `AbstractUser` (username, сессионные поля) | `AbstractBaseUser` — полностью своя, email как идентификатор |
| **Аутентификация** | `SessionAuthentication` / DRF `TokenAuthentication` | Собственный `TokenAuthentication` с `AuthToken` (1:1, `secrets.token_hex`) |
| **Хранение токенов** | DRF `Token` (автоматически создаётся) | `AuthToken` — одна активная сессия, старый токен удаляется при входе |
| **Авторизация** | `django.contrib.auth.models.Permission` + `Group` | Своя схема: `Role` → `RolePermission(resource, action)` → `UserRole` (M2M) |
| **Сессии** | `django.contrib.sessions` | **Отключены** — только токены |
| **CSRF** | `CsrfViewMiddleware` | **Отключён** — не нужен при токен-ауте |
| **Django Admin** | `django.contrib.admin` | **Отключён** — администрирование через своё API |
| **401/403** | DRF по умолчанию (403 на всё) | `AuthStatusCodeMiddleware` — 401 для неаутентифицированных, 403 для недостатка прав |

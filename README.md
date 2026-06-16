# Система аутентификации и авторизации (ТЗ Effective Mobile)

Кастомная RBAC-система на Django REST Framework + PostgreSQL.

---

## 1. Быстрый старт 

### Требования
- Python 3.13+
- Docker (для PostgreSQL)

### Установка и запуск

```bash
# 1. Клонировать / открыть проект
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
| `admin@example.com` | admin | `password` | read / write / delete → document, report |
| `manager@example.com` | manager | `password` | read / write → document, report |
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
{"id":4,"email":"ivan@test.com","first_name":"Иван","last_name":"Петров"}
```

### 3.2 Вход (login по email)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"password\"}" ^
  -c cookies.txt
```

**Ожидаемый ответ:** `200 OK`
```json
{"id":1,"email":"admin@example.com","first_name":"Админ","last_name":"Админов","role":1}
```

### 3.3 Mock-объекты с доступом (admin)

```bash
curl http://127.0.0.1:8000/api/documents/ -b cookies.txt
```

**Ожидаемый ответ:** `200 OK` — список из 3 документов
```json
[
  {"id":1,"title":"Договор №1","status":"подписан"},
  {"id":2,"title":"Счет-фактура №42","status":"оплачен"},
  {"id":3,"title":"Акт приема-передачи","status":"на согласовании"}
]
```

```bash
curl http://127.0.0.1:8000/api/reports/ -b cookies.txt
```

**Ожидаемый ответ:** `200 OK` — список из 3 отчётов
```json
[
  {"id":1,"title":"Отчет по продажам Q1","author":"Иванов И.И."},
  {"id":2,"title":"Финансовый отчет 2025","author":"Петров П.П."},
  {"id":3,"title":"Анализ рынка","author":"Сидоров С.С."}
]
```

### 3.4 401 — запрос без сессии

```bash
curl http://127.0.0.1:8000/api/documents/
```

**Ожидаемый ответ:** `401 Unauthorized`
```json
{"detail":"Authentication credentials were not provided."}
```

### 3.5 403 — нет роли (пользователь только что зарегистрирован)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"ivan@test.com\",\"password\":\"qwerty123\"}" ^
  -c new_user.txt

curl http://127.0.0.1:8000/api/documents/ -b new_user.txt
```

**Ожидаемый ответ:** `403 Forbidden`
```json
{"detail":"You do not have permission to perform this action."}
```

### 3.6 403 — пользователь не может в админку

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@example.com\",\"password\":\"password\"}" ^
  -c user_cookies.txt

curl http://127.0.0.1:8000/api/admin/roles/ -b user_cookies.txt
```

**Ожидаемый ответ:** `403 Forbidden`

### 3.7 Администратор управляет правами (CRUD)

```bash
# Получить список ролей
curl http://127.0.0.1:8000/api/admin/roles/ -b cookies.txt
# → 200 OK: [{"id":1,"name":"admin"},{"id":2,"name":"manager"},{"id":3,"name":"user"}]

# Получить список прав
curl http://127.0.0.1:8000/api/admin/permissions/ -b cookies.txt
# → 200 OK: 12 записей (admin — 6, manager — 4, user — 2)

# Создать новое право (требуется CSRF-токен из cookies.txt)
curl -X POST http://127.0.0.1:8000/api/admin/permissions/ ^
  -H "Content-Type: application/json" ^
  -H "X-CSRFToken: <токен_из_cookies.txt>" ^
  -b cookies.txt ^
  -d "{\"role\":2,\"resource\":2,\"action\":3}"
# → 201 Created
```

### 3.8 Обновление профиля

```bash
curl -X PUT http://127.0.0.1:8000/api/auth/profile/ ^
  -H "Content-Type: application/json" ^
  -H "X-CSRFToken: <токен_из_cookies.txt>" ^
  -b cookies.txt ^
  -d "{\"first_name\":\"Новое\",\"last_name\":\"Имя\"}"
```

**Ожидаемый ответ:** `200 OK`

### 3.9 Logout

```bash
curl -X POST http://127.0.0.1:8000/api/auth/logout/ ^
  -H "X-CSRFToken: <токен>" ^
  -b cookies.txt
```

**Ожидаемый ответ:** `204 No Content`

### 3.10 Мягкое удаление (soft delete)

```bash
curl -X DELETE http://127.0.0.1:8000/api/auth/delete/ ^
  -H "X-CSRFToken: <токен>" ^
  -b user_cookies.txt

# Попытка войти снова
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@example.com\",\"password\":\"password\"}"
```

**Ожидаемый ответ:** `400 Bad Request`
```json
{"email":["Учетная запись деактивирована."]}
```

---

## 4. Схема БД (RBAC)

```
┌──────────┐     ┌─────────────────────┐     ┌──────────┐
│   Role   │     │   RolePermission    │     │ Resource │
│  (Роль)  │────<│  (Право доступа)    │>────│ (Ресурс) │
└──────────┘     └─────────────────────┘     └──────────┘
     │                    │
     │              ┌─────┴──────┐
     │              │   Action   │
     │              │ (Действие) │
     │              └────────────┘
     │
┌────┴──────────┐
│  CustomUser   │
│(Пользователь) │
└───────────────┘
```

| Модель | Назначение | Поля |
|---|---|---|
| **Role** | Роль пользователя | `name` (уникальное) |
| **Resource** | Защищаемый ресурс | `name` (уникальное) |
| **Action** | Действие над ресурсом | `name` (уникальное) |
| **RolePermission** | Связка «роль→ресурс→действие» | `role`, `resource`, `action` (unique_together) |
| **CustomUser** | Пользователь | поля AbstractUser + `role` (FK→Role) |

### Алгоритм проверки доступа

1. Запрос → определить пользователя (Django-сессия)
2. Пользователь не определён → **401**
3. У пользователя нет роли → **403**
4. Ищем `RolePermission(role, resource, action)` в кастомной БД
5. Не найдено → **403**
6. Найдено → доступ разрешён

---

## 5. Структура проекта

```
├── core/                  # Конфигурация Django
│   ├── settings.py
│   ├── urls.py            # Корневой роутинг + карта API
│   └── middleware.py       # 401/403 разграничение
├── users/                 # Пользователи и аутентификация
│   ├── models.py           # CustomUser
│   ├── serializers.py      # Register, Login, Profile
│   ├── views.py            # Auth-эндпоинты
│   └── urls.py
├── access_control/        # Права доступа
│   ├── models.py           # Role, Resource, Action, RolePermission
│   ├── permissions.py      # ResourceAccessPermission, IsAdminRole
│   ├── serializers.py
│   ├── views.py            # Mock-объекты + Admin CRUD
│   ├── urls.py
│   └── management/commands/seed_data.py
└── README.md
```

---

## 6. API Endpoints (полный список)

### Аутентификация

| Метод | URL | Доступ | Описание |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Все | Регистрация |
| `POST` | `/api/auth/login/` | Все | Вход по email+паролю |
| `POST` | `/api/auth/logout/` | Авторизован | Выход |
| `GET` `PUT` | `/api/auth/profile/` | Авторизован | Просмотр/редактирование |
| `DELETE` | `/api/auth/delete/` | Авторизован | Мягкое удаление |

### Mock-объекты (проверка доступа)

| Метод | URL | Ресурс | Действие |
|---|---|---|---|
| `GET` | `/api/documents/` | document | read |
| `GET` | `/api/reports/` | report | read |

### Администрирование прав (только admin)

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

---

## 7. Кастомность (отличие от встроенных механизмов Django/DRF)

- **Аутентификация** — собственные `RegisterView`, `LoginView`, `LogoutView` (не DRF Token/Session из коробки)
- **Авторизация** — кастомные классы `ResourceAccessPermission`, `IsAdminRole` проверяют права через собственную БД (Role → RolePermission ← Resource + Action), а не через `django.contrib.auth.models.Permission`
- **Django Admin** — отключен (`django.contrib.admin` удалён из `INSTALLED_APPS`)
- **401/403** — кастомный `AuthStatusCodeMiddleware` гарантирует правильные HTTP-статусы

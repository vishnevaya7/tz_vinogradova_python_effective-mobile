---
name: windows-postgresql-port-conflict
description: Диагностика конфликта портов между нативным PostgreSQL Windows и Docker-контейнером, когда psycopg2 выдаёт UnicodeDecodeError вместо внятной ошибки подключения
source: auto-skill
extracted_at: '2026-06-16T11:33:21.378Z'
---

# Диагностика конфликта портов PostgreSQL на Windows

## Симптомы
При запуске Django-миграций или попытке подключения через `psycopg2` возникает ошибка:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc2 in position 55: invalid continuation byte
```
Ошибка возникает в `psycopg2\__init__.py`, `_connect()`. Параметры подключения выглядят корректно, сервер PostgreSQL (в Docker) запущен.

## Корневая причина (наиболее вероятная на Windows)
На порту 5432 висят **два процесса одновременно**:
- `com.docker.backend.exe` — проброс порта Docker-контейнера
- `postgres.exe` — нативная Windows-установка PostgreSQL (служба `postgresql-x64-XX`)

Нативный PostgreSQL перехватывает соединение раньше Docker, и возвращает ошибку аутентификации в кодировке `cp1251` (Windows-1251, кириллица). `psycopg2` пытается декодировать её как UTF-8 и падает с `UnicodeDecodeError`.

**Why:** Windows позволяет нескольким процессам слушать один порт (поведение `SO_REUSEADDR` отличается от Linux). Нативный `postgres.exe` и `com.docker.backend.exe` могут одновременно слушать 0.0.0.0:5432, и первым отвечает тот, кто быстрее.

**How to apply:** при любых непонятных ошибках подключения к PostgreSQL на Windows, особенно с `UnicodeDecodeError` в `psycopg2`, первым делом проверять конфликт портов.

## Пошаговая диагностика

### 1. Проверить, кто слушает порт 5432
```cmd
netstat -ano | findstr ":5432"
```
Если видны **два** PID в состоянии LISTENING — это конфликт.

### 2. Идентифицировать процессы
```cmd
tasklist /fi "PID eq <PID1>"
tasklist /fi "PID eq <PID2>"
```
Типичная пара: `postgres.exe` (нативный) и `com.docker.backend.exe` (Docker).

### 3. Найти имя службы нативного PostgreSQL
```cmd
sc query | findstr -i postgres
```
Обычно: `postgresql-x64-16`, `postgresql-x64-18` и т.д.

### 4. Остановить нативную службу (требуются права администратора)
```cmd
sc stop postgresql-x64-18
```

### 5. Альтернатива: перенастроить Docker-контейнер на другой порт
Если нативный PostgreSQL нужен — пробросить Docker на порт 5433 и обновить `.env` / `settings.py`.

## Пересоздание Docker-контейнера с сохранением данных

Docker не позволяет изменить порт у существующего контейнера. Нужно остановить, удалить и создать заново, сохранив том с данными:

```cmd
# 1. Узнать параметры существующего контейнера
docker inspect <container> --format "{{json .Mounts}}"  # имя тома
docker inspect <container> --format "{{json .NetworkSettings.Networks}}"  # имя сети
docker inspect <container> --format "{{json .Config.Env}}"  # переменные окружения

# 2. Пересоздать на новом порту (на примере порта 5433)
docker stop <container> && docker rm <container> && docker run -d --name <container> --network <network_name> -e POSTGRES_PASSWORD=<pwd> -e POSTGRES_DB=<db> -e POSTGRES_USER=<user> -v <volume_name>:/var/lib/postgresql/data -p 5433:5432 postgres:16

# 3. Обновить .env
# DB_PORT=5433

# 4. Проверить подключение
python -c "import psycopg2; conn=psycopg2.connect(dbname='testdb',user='postgres',password='password',host='127.0.0.1',port=5433); print('OK'); conn.close()"
```

Том (`-v <volume>:/var/lib/...`) сохраняет данные между пересозданиями. Без него БД будет пустой.

## Проверка освобождения порта

После удаления нативного PostgreSQL убедиться, что порт действительно свободен:

```powershell
powershell -Command "Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet"
# True — порт свободен и никто не слушает
```

Или проверить, кто именно слушает:
```cmd
netstat -ano | findstr ":5432"
# Если пусто или только один процесс — конфликта нет
```

## Дополнительные средства диагностики

### pg8000 — более читаемые ошибки
В отличие от `psycopg2`, библиотека `pg8000` (pure Python) корректно декодирует ошибки сервера и показывает реальный код ошибки (например, `28P01` — invalid password), даже если сообщение приходит в cp1251.

```python
import pg8000
conn = pg8000.connect(database='testdb', user='postgres', password='password', host='127.0.0.1', port=5432)
```

### Проверка pg_hba.conf внутри контейнера
```cmd
docker exec <container> cat /var/lib/postgresql/data/pg_hba.conf | findstr /v "^#" | findstr /v "^$"
```
Важно: правила применяются по порядку, **первое совпадение побеждает**. Правило `host all all all scram-sha-256` перехватывает всё, что идёт после него.

### Сброс пароля внутри контейнера (если утерян)
```cmd
docker exec <container> psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'newpassword';"
```

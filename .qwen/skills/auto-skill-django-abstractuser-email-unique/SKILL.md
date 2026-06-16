---
name: django-abstractuser-email-unique
description: AbstractUser.email по умолчанию не unique — при email-based логине через .get() это приводит к MultipleObjectsReturned; как правильно переопределить email с unique=True и защитить регистрацию
source: auto-skill
extracted_at: '2026-06-16T12:59:34.159Z'
---

# AbstractUser.email: обязательный unique=True при email-based логине

## Симптомы

При использовании `AbstractUser` и email-based аутентификации (поиск пользователя через `CustomUser.objects.get(email=email)` в `LoginSerializer`) **нет ошибки на этапе разработки**, но в production-условиях, если два пользователя зарегистрируются с одинаковым email, возникает:

```
django.contrib.auth.models.CustomUser.MultipleObjectsReturned:
get() returned more than one CustomUser -- it returned 2!
```

**Why:** `AbstractUser.email` не имеет `unique=True` (в отличие от `username`). Django исторически не делал email уникальным — это осознанное решение разработчиков, оставленное для обратной совместимости.

**How to apply:** в любом проекте на Django, где `AbstractUser` используется с email-based логином, **обязательно** переопределять поле `email` с `unique=True`. Это касается и промежуточных проектов, где email-аутентификация может появиться позже — лучше добавить ограничение сразу.

## Решение: три шага

### Шаг 1. Переопределить email в CustomUser

В `users/models.py`:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # ← ключевая строка
    # ... остальные поля
```

Без этого шага даже `unique_together` на уровне БД не сработает, т.к. поле наследуется от `AbstractUser` без ограничения.

### Шаг 2. Создать миграцию

```bash
python manage.py makemigrations users
```

Миграция будет содержать `AlterField` — добавление UNIQUE-ограничения на существующее поле.

⚠️ **Важно:** если в БД уже есть дубликаты email, миграция упадёт. Нужно предварительно почистить дубликаты:

```sql
-- Найти дубликаты
SELECT email, COUNT(*) FROM users_customuser GROUP BY email HAVING COUNT(*) > 1;
-- Оставить по одному пользователю на каждый email, удалить/объединить остальных
```

### Шаг 3. Добавить валидацию в RegisterSerializer

Ограничение на уровне БД выбрасывает `IntegrityError` (500), если дубликат всё же проскочил. Нужна читаемая ошибка на уровне сериализатора:

```python
class RegisterSerializer(serializers.ModelSerializer):
    # ...

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        return value
```

Полевая валидация DRF (метод `validate_<field>`) вызывается до `validate()` и до попытки сохранения — ошибка возвращается как 400 с ключом `email`.

## Что НЕ работает

1. **`unique_together` / `UniqueConstraint` в Meta** — эти варианты создают составной индекс, но не делают поле уникальным само по себе. `AbstractUser.email` остаётся без ограничения, и `.get(email=...)` всё равно может вернуть несколько записей.

2. **Только валидация в сериализаторе без unique=True** — защищает только один путь создания (регистрацию), но не защищает от прямых вставок в БД, создания через админку Django (если включена), management-команды или bulk_create.

3. **Использование `.filter(email=email).first()` вместо `.get()`** — маскирует проблему (берёт первого попавшегося), но не устраняет корневую причину. Два пользователя с одинаковым email — это нарушение бизнес-логики, даже если код не падает.

## Как проверить

```python
# Тест на дубликат email
def test_register_duplicate_email(self):
    self.client.post('/api/auth/register/', {...})
    response = self.client.post('/api/auth/register/', {...})  # тот же email
    self.assertEqual(response.status_code, 400)
    self.assertIn('email', response.data)
```

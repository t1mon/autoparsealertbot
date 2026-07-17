# Аккаунты для парсинга

## Проблема сейчас

- Непонятно, **какой** Telegram-аккаунт используется для парсинга.
- При старте берётся «первое найденное» session / запись — без явного выбора.
- Нет экрана: все аккаунты пользователя, какой активный, валиден ли.
- Админские session’ы и пользовательские смешаны по смыслу в голове пользователя.

## Целевой UX

Подменю **👤 Аккаунт**:

```
Активный: +7900… · Имя · ✅ валиден
```

- Список аккаунтов (телефон / имя / дата)
- «Сделать активным»
- «Проверить валидность»
- «Подключить новый» (.session)
- «Отключить / удалить»

На главном статусе всегда виден активный аккаунт или «не подключён».

## Задачи

- [x] P0: в welcome/статусе показывать активный аккаунт (phone / username)
- [x] P1: явный `is_active` у аккаунта в `UserAccountsTable`
- [x] P1: экран списка аккаунтов + выбор активного (`menu:accounts`)
- [x] P1: `find_session_file` / старт tracking только по активному
- [x] P1: кнопка «проверить аккаунт» с понятным результатом
- [x] P2: авто-фейлover на другой аккаунт при FloodWait (≥5 мин) / AuthKey (`_try_failover_client`)
- [ ] P2: админ: обзор, у кого какой аккаунт и статус tracking

## Текущий код

- UI: `handlers/user/connect_account.py` → `menu:accounts`
- Старт: `handlers/user/handlers.py` → `find_session_file`
- Session: `account_manager/session.py` (`get_active_account`)
- Подключение user: `.session` через `menu:accounts:connect`
- Подключение admin: `handlers/admin/connecting_account.py`
- Валидация: кнопка `menu:accounts:check` + `account_manager/session._is_session_valid`
- БД: `get_active_account`, `set_active_account`, `delete_user_account`, `get_user_accounts`

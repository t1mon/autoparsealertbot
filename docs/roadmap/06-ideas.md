# Дополнительные идеи и техдолг

## Продукт

- [x] P2: тихие часы / не слать алерты ночью (`menu:quiet_hours`, лиды пишутся)
- [x] P2: анти-спам / Redis-дедуп алертов (`core/alert_dedup.py`, TTL 7д; fallback в RAM)
- [x] P2: дайджест: N срабатываний за интервал одним сообщением (`menu:digest`)
- [x] P2: база совпадений (история/выгрузка) → [08-leads.md](08-leads.md)
- [x] P2: фильтр по типу чата (только каналы / только группы) — `menu:chat_filter`
- [x] P2: чёрный список слов (не алертить, если есть стоп-слово) — `menu:stopwords`
- [x] P2: шаблон алерта настраиваемый (`menu:alert_template`: full/compact/minimal) → [07-alerts.md](07-alerts.md)
- [x] P2: кнопка «открыть в Telegram» + «игнор канал на 24ч» под алертом

## Надёжность

- [x] P1: Redis-дедуп алертов (`alert:dedup:{user}:{chat}:{msg}`, SET NX + TTL)
- [x] P1: явный reconnect Telethon при обрыве (`run_until_disconnected` + backoff, `connection_retries=None`)
- [x] P2: метрики: uptime tracking, floodwaits, matches/hour (`core/metrics.py`, `/health`)
- [x] P2: healthcheck endpoint — `/health` + `/health/redis` + tracking count

## Админка

- [x] P2: кто сейчас в tracking, сколько каналов/ключей (`menu:admin:tracking`)
- [x] P2: принудительный stop tracking пользователя
- [ ] P2: выгрузка статистики ложных срабатываний (если будет лог причин)

## Техдолг / архитектура

- [ ] P1: общий модуль CRUD «список + файл» для keywords и channels (один UX-паттерн)
- [ ] P1: не плодить динамические SQLite-таблицы `{user_id}_keywords` без нужды — оценить одну таблицу `keywords(user_id, text)`
- [ ] P2: разнести `handlers/user/handlers.py` / `pars_ai.py` на более мелкие роутеры
- [ ] P2: docker: volume на код **или** всегда `compose up --build` в README (сейчас код в образе — легко забыть rebuild)
- [x] P2: тесты на `core/keyword_match.py` (pytest)
- [ ] P2: CI: lint + pytest

## Документация для пользователей

- [x] P1: короткая «как запустить за 3 шага» в `/start` и в инструкции
- [x] P2: обновить `doc/doc.md` под Inline и новый кабинет (блок быстрого старта)

## Не делать сейчас (сознательно)

- DB-driven menu layout как в bedolaga (`MENU_LAYOUT`) — избыточно
- ERROR→Telegram notifier — отложено по запросу
- Полный переход на SQLAlchemy — нет срочности

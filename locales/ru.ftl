# Russian localization
access_denied_full =
    🔒 <b>Бот в закрытом тестировании</b>

    Полный доступ — только по приглашению.
    Напишите разработчику: { $developer }

    Укажите, для чего нужен парсер (ниша, пример каналов).
access_denied_short =
    🔒 Доступ только по запросу. Напишите { $developer }
access_contact_developer_button = 💬 Написать разработчику
access_denied_group =
    🔒 Бот в закрытом тестировании. Управление — только в личке @{ $bot_username }

group_chat_use_private =
    🤖 Настройки и меню бота — только в личных сообщениях.

    Откройте @{ $bot_username } и нажмите /start

    В группе доступны только:
    • <code>/bind_alerts ТОКЕН</code> — привязка (из настроек)
    • <code>/leads</code> — выгрузка лидов
group_chat_use_private_short =
    Управление ботом — в личке @{ $bot_username }. Здесь: /bind_alerts и /leads
group_chat_command_private =
    Эта команда работает только в личке с @{ $bot_username }
group_chat_callback_private = Кнопки меню работают только в личке с ботом
group_chat_open_bot_button = 💬 Открыть бота

welcome_ask_language =
    🌍 Привет! Пожалуйста, выберите язык интерфейса:
welcome_message_template =
    📡 <b>Парсинг:</b> { $tracking_status }
    👤 <b>Аккаунт:</b> { $account_label }
    🔑 <b>Ключей:</b> { $keywords_count }
    📢 <b>Каналов:</b> { $channels_enabled } включено / { $channels_total } всего

    { $howto_block }{ $next_hint }

howto_3_steps =
    🚀 <b>Запуск за 3 шага</b>

    <b>1. Аккаунт</b> — «Мой парсинг» → Аккаунт → файл <code>.session</code>
    <b>2. Ключевые слова</b> — что искать в чатах (есть «Проверь сообщение»)
    <b>3. Каналы</b> — добавьте @каналы и включите парсинг ✅ в списке

    На главном экране нажмите <b>«Запустить»</b> — совпадения придут сюда.
howto_3_steps_short =
    🚀 <b>За 3 шага:</b> аккаунт → ключи → каналы → «Запустить»

next_step_account = 👉 Дальше: подключите Telegram-аккаунт (.session)
next_step_keywords = 👉 Дальше: добавьте хотя бы одно ключевое слово
next_step_channels = 👉 Дальше: добавьте канал и включите парсинг (✅ в списке)
next_step_ready_start = 👉 Всё готово — нажмите «Запустить»
next_step_tracking_on = 📬 Парсинг работает — совпадения приходят в этот чат

tracking_status_running = ▶ работает
tracking_status_stopped = ⏹ остановлен
account_not_connected = не подключён
account_connected_unknown = подключён
my_parsing_button = 📡 Мой парсинг
cabinet_account_button = 👤 Аккаунт
accounts_menu_template =
    👤 <b>Аккаунты</b>

    Активный: <code>{ $active_label }</code>
    Всего: <b>{ $count }</b>

    ● — активный · ○ — нажмите, чтобы выбрать · ✕ — удалить
accounts_connect_button = ➕ Подключить новый
accounts_check_button = ✅ Проверить активный
accounts_set_active_ok = Активный: { $phone }
accounts_deleted_ok = Аккаунт удалён
accounts_not_found = Аккаунт не найден
accounts_check_progress = Проверяю…
accounts_check_ok = ✅ <b>{ $phone }</b> — сессия валидна
accounts_check_fail = ❌ <b>{ $phone }</b> — сессия невалидна. Подключите новый .session или выберите другой аккаунт.
cabinet_message_template =
    <b>Мой парсинг</b>

    { $check_account } Аккаунт: <code>{ $account_label }</code>
    { $check_keywords } Ключевые слова: <b>{ $keywords_count }</b>
    { $check_channels } Каналы: <b>{ $channels_enabled }</b> вкл / <b>{ $channels_total }</b> всего
    🎯 Режим поиска: <b>{ $match_mode }</b>

    { $hint }
cabinet_hint_ready = ✅ Всё готово — можно запускать на главном экране.
cabinet_hint_not_ready = ⚠️ Чтобы запустить парсинг, нужны аккаунт, хотя бы одно ключевое слово и один включённый канал.

wizard_message_template =
    🚀 <b>Настройка за 3 шага</b>

    { $check_account } 1. Аккаунт: <code>{ $account_label }</code>
    { $check_keywords } 2. Ключевые слова: <b>{ $keywords_count }</b>
    { $check_channels } 3. Каналы: <b>{ $channels_enabled }</b> вкл / <b>{ $channels_total }</b> всего

    { $step_hint }
wizard_hint_account = Сейчас шаг 1: подключите Telegram-аккаунт (.session).
wizard_hint_keywords = Сейчас шаг 2: добавьте хотя бы одно ключевое слово.
wizard_hint_channels = Сейчас шаг 3: добавьте канал и включите парсинг ✅.
wizard_hint_ready = ✅ Три шага готовы — нажмите «Запустить».
wizard_cta_account = 👤 Подключить аккаунт
wizard_cta_keywords = 🔑 Добавить ключи
wizard_cta_channels = 📢 Добавить каналы
wizard_continue_button = 🚀 Продолжить настройку
wizard_skip_button = В меню

lang_selected =
    ✅ Отлично! Интерфейс теперь будет отображаться на выбранном языке.
settings_message =
    ⚙️ <b>Настройки</b>

    Здесь — фильтры алертов, язык и Stars.
    Аккаунт, ключи и каналы: «Мой парсинг» на главном экране.
connect_account =
    📱 Для подключения аккаунта Telegram отправьте файл сессии в формате:
    `+79599999999.session`

    После загрузки бот начнёт использовать этот аккаунт для отслеживания сообщений.
launching_tracking =
    🚀 Запуск отслеживания сообщений...

    Совпадения по ключевым словам будут приходить в этот чат.
tracking_launch_error =
    ⚠️ Нет включённых каналов для парсинга.

    Добавьте каналы и включите хотя бы один в <b>Мой парсинг → Каналы</b>.
tracking_not_ready =
    ⚠️ Ещё рано запускать парсинг. Не хватает:

    { $gaps }

    Откройте <b>Мой парсинг</b> и закройте пункты чеклиста.
setup_before_start_button = ⚠️ Сначала настройте
ready_gap_account = подключите Telegram-аккаунт
ready_gap_keywords = добавьте хотя бы одно ключевое слово
ready_gap_channels_none = добавьте хотя бы один канал
ready_gap_channels_disabled = включите парсинг хотя бы у одного канала (✅ в списке)
update_list =
    📥 Пришлите .txt файл или отправьте текстом список групп и каналов для отслеживания:

    ✅ Публичные: <b>@username</b> или <b>https://t.me/username</b>
    ✅ Приватные: <b>https://t.me/+invite</b> или <b>https://t.me/joinchat/...</b>
    ✅ Без username: ссылка на сообщение <b>https://t.me/c/1234567890/1</b> или <b>id:-1001234567890</b>
    ✅ Форумы и топики: добавьте саму группу — бот слушает все топики внутри неё
    ✅ Можно по одному на строке или через запятую
    ✅ Файл — только <b>.txt</b>

    📌 Примеры:
    @channel1
    https://t.me/+AbCdEfGhIjK
    https://t.me/c/1234567890/55/100
account_missing =
    ⚠️ У вас нет подключенного аккаунта Telegram.

account_missing_2 =
    ⚠️ Сессия аккаунта недействительна (session файл не валидный) — требуется повторный вход. Отправьте валидный файл сессии
enter_keyword =
    🔍 Добавьте ключевые слова:

    • текстом — каждое с новой строки или через запятую
    • файлом <code>.txt</code> — одна фраза на строку

    После отправки слова появятся в списке «Мой парсинг → Ключевые слова».
keywords_menu_message =
    🔑 <b>Ключевые слова</b>

    Сейчас сохранено: <b>{ $count }</b>
    Режим поиска: <b>{ $match_mode }</b>

    Добавляйте текстом или .txt, смотрите список, удаляйте лишнее или скачивайте файл.
keywords_menu_button = 🔑 Ключевые слова
keywords_add_button = ➕ Добавить
keywords_view_list_button = 📋 Смотреть списком
keywords_export_txt_button = 📄 .txt
keywords_export_xlsx_button = 📊 Excel
keywords_list_title =
    🔑 Ключевые слова: <b>{ $count }</b> · стр. { $page }
    Нажмите ✕ чтобы удалить:
keyword_deleted = Удалено: { $keyword }
keyword_delete_missing = Ключ уже удалён
match_mode_button = 🎯 Режим поиска
match_mode_strict_button = Строгий (только точная фраза)
match_mode_smart_button = Умный (рекомендуется)
match_mode_loose_button = Мягкий (больше срабатываний)
match_mode_strict_name = строгий
match_mode_smart_name = умный
match_mode_loose_name = мягкий
match_mode_message =
    🎯 <b>Режим поиска ключей</b>

    Сейчас: <b>{ $current }</b>

    • <b>Строгий</b> — только точное вхождение фразы
    • <b>Умный</b> — словоформы и опечатки, все слова фразы обязательны
    • <b>Мягкий</b> — больше ложных срабатываний (старое поведение)
match_mode_saved = Режим: { $mode }
match_check_button = 🧪 Проверь сообщение
match_check_no_keywords = Сначала добавьте ключевые слова
match_check_prompt =
    🧪 <b>Проверка сообщения</b>

    Ключей: <b>{ $count }</b> · режим: <b>{ $mode }</b>

    Пришлите текст (как из чата) — покажу, какие ключи сработают и почему.
    Стоп-слова тоже проверяются.
match_check_empty = Пустой текст — пришлите сообщение
match_check_need_text = Нужен обычный текст (не файл/фото)
match_check_none =
    ❌ <b>Совпадений нет</b>

    Режим: { $mode } · проверено ключей: { $checked }

    <b>Текст:</b>
    <i>{ $preview }</i>
match_check_hits =
    ✅ <b>Сработало: { $hit_count }</b> из { $checked }

    Режим: { $mode }

    { $rows }
    { $more }

    <b>Текст:</b>
    <i>{ $preview }</i>
match_check_row = { $n }. <code>{ $keyword }</code>
    → { $why }
match_check_more = …и ещё { $count }
match_check_stopword =
    🚫 Стоп-слово «{ $stopword }» — в бою алерт и лид не создались бы.
match_check_again_hint = Можете прислать ещё текст или нажать «Назад».
channels_menu_message =
    📢 <b>Каналы для парсинга</b>

    Включено: <b>{ $enabled }</b> · всего в списке: <b>{ $total }</b>

    Добавляйте текстом или .txt, включайте/выключайте в списке.
    «Проверить подписки» — видит ли активный аккаунт эти каналы.
channels_menu_button = 📢 Каналы
channels_add_button = ➕ Добавить
channels_view_list_button = 📋 Смотреть списком
channels_check_subs_button = 🔎 Проверить подписки
channels_join_missing_button = ➕ Подписать на недостающие
channels_check_no_account = Сначала подключите аккаунт
channels_check_no_enabled = Нет включённых каналов
channels_check_progress = Проверяю…
channels_check_progress_msg =
    🔎 Проверяю подписки активного аккаунта на <b>{ $count }</b> канал(ов)…
channels_check_connect_fail =
    ❌ Не удалось подключить активный аккаунт. Проверьте .session.
channels_check_error =
    ❌ Ошибка при проверке подписок. Попробуйте позже.
channels_check_report =
    🔎 <b>Подписки аккаунта</b> <code>{ $phone }</code>

    ✅ В канале: <b>{ $ok_count }</b>
    ⚠️ Нет подписки: <b>{ $missing_count }</b>
    ❌ Ошибка проверки: <b>{ $error_count }</b>

    <b>Нет подписки:</b>
    { $missing_list }

    <b>Ошибки:</b>
    { $error_list }

    Без подписки сообщения из канала могут не приходить. Можно подписать сейчас или запустить tracking — бот попробует вступить в фоне.

    <i>✅ — парсинг вкл/выкл. ⚠️ нет подписки · 🕐 ждёт одобрения · 🔒 приватный/недоступен · ❌ ошибка.</i>
channels_join_nothing = Нечего подписывать — сначала сделайте проверку
channels_join_progress =
    ➕ Подписываю на <b>{ $count }</b> канал(ов)… Это может занять время.
channels_join_progress_live =
    ➕ <b>Подписка на каналы</b> · { $done }/{ $total }

    Сейчас: <code>{ $channel }</code>
    ✅ { $joined } · уже были { $already } · ❌ { $errors }

    { $status }
channels_join_status_pause =
    ⏳ Пауза <b>{ $delay }</b> сек. перед следующим…
channels_join_status_working =
    🔄 Вступаю…
channels_join_cancel_button = ⏹ Отменить
channels_join_cancel_confirm =
    ⏹ <b>Отменить подписку?</b>

    Уже обработанные каналы останутся подписанными. Остальные можно будет продолжить позже.
channels_join_cancel_yes = ✅ Да, отменить
channels_join_cancelling_msg = ⏹ Отмена подписки…
channels_join_already_running = Подписка уже идёт — дождитесь завершения или отмените её
channels_join_background_hint = Подписка продолжается в фоне — пришлю итог отдельным сообщением
channels_join_stopped =
    ⏹ <b>Подписка отменена</b>

    Новых подписок: <b>{ $joined }</b>
    Уже были: <b>{ $already }</b>
    Ошибок: <b>{ $errors }</b>
    Не обработано: <b>{ $remaining }</b>
channels_join_done =
    ✅ Готово.

    Новых подписок: <b>{ $joined }</b>
    Уже были: <b>{ $already }</b>
    Ошибок: <b>{ $errors }</b>
    Отложено лимитом: <b>{ $skipped }</b>
channels_export_txt_button = 📄 .txt
channels_export_xlsx_button = 📊 Excel
channels_clear_button = 🗑️ Очистить всё
channels_list_title =
    📢 Каналы: <b>{ $enabled }</b> вкл / <b>{ $total }</b> · стр. { $page }
    ✅/⏸ парсинг · ⚠️🕐🔒❌ подписка · ✕ удалить
channel_deleted = Удалено: { $channel }
channel_missing = Канал уже удалён
channel_membership_ok = в канале
channel_membership_missing = нет подписки
channel_membership_pending = ждёт одобрения
channel_membership_private = приватный
channel_membership_error = ошибка подписки
membership_reason_not_member = нет подписки аккаунта
membership_reason_pending_approval = нужно одобрение админа (заявка отправлена или требуется)
membership_reason_private = чат приватный или недоступен
membership_reason_check_failed = не удалось проверить
membership_reason_invalid_ref = неверная ссылка
membership_reason_invite_expired = invite-ссылка истекла
membership_reason_unknown = не удалось вступить
channel_enabled = Включено: { $channel }
channel_disabled = Выключено: { $channel }
channel_status_on = вкл
channel_status_off = выкл
excel_header_parse_status = Парсинг
leads_menu_button = 📋 Совпадения
leads_view_list_button = 📋 Смотреть списком
leads_export_xlsx_button = 📊 Excel
leads_menu_message =
    📋 <b>Совпадения</b>

    Сохранено: <b>{ $count }</b>

    Здесь история пойманных сообщений по ключам — список и выгрузка Excel.
leads_list_title =
    📋 Совпадения: <b>{ $count }</b> · стр. { $page }
    Нажмите карточку, чтобы открыть:
leads_empty = 📭 Пока нет сохранённых совпадений. Они появятся после срабатывания ключей.
leads_missing = Запись не найдена
leads_export_caption = 📋 Экспорт совпадений. Всего: { $count }
leads_card =
    📋 <b>Совпадение</b>

    <b>Ключ:</b> <code>{ $keyword }</code>
    <b>Автор:</b> { $author }
    <b>Чат:</b> { $chat }
    <b>Время:</b> { $when }
    <b>Ссылка:</b> { $link }

    <b>Текст:</b>
    { $message_text }
excel_header_lead_time = Время
excel_header_author_name = Автор
excel_header_author_username = @username
excel_header_author_id = Author ID
excel_header_author_kind = Тип автора
excel_header_chat_title = Чат
excel_header_link = Ссылка
excel_header_message_text = Текст

ai_search_welcome =
    🤖 <b>Добро пожаловать в меню AI-поиска!</b>

    Здесь вы можете находить новые тематические группы и каналы, используя возможности искусственного интеллекта.

    🚀 <b>Доступные режимы:</b>
    • 🤖 <b>AI поиск:</b> Быстрый поиск групп по вашей базе и ключевым словам.
    • 🌐 <b>Глобальный AI поиск:</b> Расширенный поиск по всему пространству Telegram для нахождения новых площадок.

    Просто выберите нужный режим на клавиатуре или введите запрос! 👇
enter_group =
    🔜 Пересылка в группу будет добавлена позже (приватные группы и топики).

    Сейчас уведомления приходят прямо в этот чат с ботом.

    При желании можно заранее указать @username публичной группы (необязательно):
admin_panel_message =
    👋 <b>Добро пожаловать в Панель администратора!</b>

    Вот что вы можете сделать:

    📡 <b>Tracking</b> — кто сейчас парсит, ключи/каналы, принудительный stop.

    📁 <b>Получить лог-файл</b> — просмотреть журнал ошибок и событий бота за последнее время. Полезно для диагностики.

    🔄 <b>Актуализация базы данных</b> — обновить информацию о группах и каналах: проверить их текущий тип (группа/канал) и получить актуальные ID.

    🏷️ <b>Присвоить категорию</b> — автоматически классифицировать группы и каналы по темам с помощью AI.

    ✅ <b>Проверка аккаунтов</b> — проверить статус подключённых аккаунтов и их сессий.

    🌐 <b>Присвоить язык</b> — определить язык содержимого в группах и каналах.

    🔐 <b>Подключение аккаунта</b> — подключить Telegram-аккаунт через файл сессии для использования в боте.

tracking_stopped =
    ✅ Отслеживание остановлено.

instruction_caption =
    📘 <b>Инструкция по использованию</b>

    Прикреплён подробный руководство по функционалу бота.

    🔗 <b>Онлайн-документация:</b>
    • <a href="{ $gitverse_link }">GitVerse</a>
    • <a href="{ $github_link }">GitHub</a>

    Рекомендуем ознакомиться для эффективного использования всех возможностей бота.

instruction_howto_extra =
    💡 Подсказка: в «Ключевых словах» есть <b>«Проверь сообщение»</b> — можно проверить текст до запуска.

    Задайте вопрос кнопкой ниже — отвечу по возможностям бота.
instruction_ask_button = ❓ Задать вопрос
instruction_ask_prompt =
    🤖 Напишите вопрос по использованию бота — отвечу с опорой на инструкцию.
instruction_file_not_found =
    ⚠️ Файл инструкции не найден на сервере.

instruction_send_error =
    ❌ Не удалось ответить. Попробуйте позже или напишите в поддержку.
instruction_menu_error =
    ❌ Не удалось открыть инструкцию. Попробуйте /start.
instruction_ai_no_key =
    ⚠️ AI-ответы не настроены: в .env нет <code>GROQ_API_KEY</code>.

    Бесплатный ключ: https://console.groq.com/keys
    После добавления в .env перезапустите бота.
instruction_ai_auth_error =
    ⚠️ Ключ Groq неверный или отозван. Проверьте <code>GROQ_API_KEY</code> в .env.
instruction_ai_connection_error =
    ⚠️ Не удалось связаться с Groq (сеть/DNS/прокси). Проверьте интернет и PROXY_* в .env.
instruction_ai_empty =
    ⚠️ Пустой ответ от AI. Попробуйте переформулировать вопрос.
instruction_ai_error =
    ❌ Ошибка при ответе AI. Попробуйте позже.

# === Экспорт базы данных ===
database_empty =
    📭 База данных пуста.

export_all_caption =
    📦 Вся база данных Telegram-групп и каналов.

    📊 Всего записей: { $total_records }
    🧹 Дубликатов удалено перед экспортом: { $deleted_duplicates }

export_channels_caption =
    📦 База данных Telegram-каналов.

    📊 Всего записей: { $total_records }

export_groups_caption =
    📦 База данных Telegram-групп.

    📊 Всего записей: { $total_records }

export_error_generic =
    ❌ Произошла ошибка при создании файла.

get_database_menu =
    👋 Добро пожаловать в режим получения базы данных!

    Вот что вы можете сделать:

    🔹 <b>📥 Получить всю базу</b> — получите полный список всех сохранённых групп и каналов в формате Excel.
    🔹 <b>Получить базу Каналов</b> — получите список всех сохранённых каналов в формате Excel.
    🔹 <b>Получить базу Групп (супергрупп)</b> — получите список всех сохранённых супергрупп в формате Excel.
    🔹 <b>Получить базу Обычных чатов (группы старого типа)</b> — получите список всех сохранённых обычных чатов (групп старого типа) в формате Excel.
    🔹 Выбрать категорию для получения базы

    🔸 Нажмите <b>Назад</b>, чтобы вернуться в главное меню.

select_category_prompt =
    📌 Выберите категорию, по которой хотите получить список групп/каналов:

action_cancelled =
    ❌ Отменено.

invalid_category =
    ⚠️ Неверная категория. Пожалуйста, выберите из списка.

category_empty =
    📭 В категории «{ $category }» пока нет ни одной группы.

category_export_caption =
    ✅ Экспортировано { $group_count } групп/каналов по категории:
    «{ $category }»

# === AI Поиск ===
searching_groups =
    🔍 Ищу группы и каналы...

search_summary =
    ✅ <b>Поиск завершён!</b>

    📊 Найдено и сохранено: <b>{ $groups_count }</b> групп/каналов
    📁 Результаты отправлены в Excel-файле

    📍 <b>Обозначение активности:</b>
    🟢 <b>active</b> — группа активна (последнее сообщение ≤ 30 дней)
    🔴 <b>inactive</b> — группа неактивна (сообщений > 30 дней или нет вообще)
    ⚪ <b>unknown</b> — не удалось определить (ограничения Telegram)

search_results_caption =
    📄 Результаты поиска по запросу: <b>{ $query }</b>

search_no_results =
    ❌ К сожалению, по вашему запросу ничего не найдено. Попробуйте другие ключевые слова.

search_error =
    ❌ Произошла ошибка при поиске. Попробуйте ещё раз.

# === Глобальный AI поиск ===
global_search_no_terms =
    ❌ Введите хотя бы один поисковый запрос.

global_search_processing =
    🔍 Обрабатываю { $total } запросов...

global_search_skipped =
    ⚠️ Пропущено: '{ $term }' (нет доступных аккаунтов)

global_search_progress =
    🔍 Обработано { $current }/{ $total }: { $successful } успешно

global_search_results_caption =
    📄 Найдено { $total } групп по { $successful }/{ $total_queries } запросам

global_search_no_results =
    ❌ К сожалению, ничего не найдено. Попробуйте другие ключевые слова.

# === Подключение группы ===
group_added =
    ✅ Группа { $group } добавлена для отправки сообщений.

group_already_added =
    ⚠️ Эта группа уже добавлена.

group_add_error =
    ⚠️ Ошибка при добавлении группы.

# === Удаление группы ===
delete_group_prompt =
    Введите username группы / канала в формате @username для удаления из отслеживания:

group_deleted =
    ✅ Группа { $group } успешно удалена из отслеживания.

group_not_found =
    ❌ Группа @{ $group } не найдена в вашем списке отслеживаемых.

clear_all_channels_empty =
    ℹ️ Список отслеживаемых групп и каналов уже пуст.

clear_all_channels_confirm =
    ⚠️ Вы уверены, что хотите удалить <b>все</b> группы и каналы из отслеживания?

    Сейчас в списке: <b>{ $count }</b>

clear_all_channels_success =
    ✅ Список отслеживания очищен. Удалено записей: { $count }

clear_all_channels_cancelled =
    ❌ Очистка списка отменена.

confirm_btn = ✅ Да, очистить

no_accounts =
    ❌ У вас нет подключённых аккаунтов.

    Отправьте файл сессии `.session` или нажмите «Подключение аккаунта» в меню.

# === Ключевые слова ===
no_keywords_entered =
    ⚠️ Вы не указали ни одного ключевого слова.

keywords_added_count =
    Добавлено ключевых слов: { $count }

keywords_already_added =
    Уже были добавлены ({ $count })

keywords_add_errors =
    Ошибки при добавлении

keywords_and_more =
    и ещё { $count }

keywords_and_more_errors =
    и ещё { $count } ошибок

keywords_summary =
    Итого

keywords_added =
    Добавлено

keywords_skipped =
    Пропущено (дубликаты)

keywords_errors =
    Ошибки

# === Проверка группы для关键词 ===
check_group_ask_url =
    📤 Введите ссылку на группу для проверки:

check_group_ask_keyword =
    🔍 Введите ключевое слово для поиска:

check_group_started =
    🔍 Начинаю проверку группы...

check_group_new_message_with_link =
    📨 Новое сообщение с ключевым словом!

    📌 <b>{ $title }</b>
    📅 Дата: { $msg_date }
    🔗 <a href="{ $message_link }">Перейти к сообщению</a>

check_group_new_message_no_link =
    📨 Новое сообщение с ключевым словом!

    📌 <b>{ $title }</b>
    📅 Дата: { $msg_date }

check_group_summary =
    ✅ Проверка завершена!

    Найдено сообщений: { $count }
    Ключевое слово: { $keyword }
    Совпадений: { $matched_count }

check_group_parse_error =
    ❌ Произошла ошибка при парсинге группы. Проверьте ссылку и доступ к чату.

# === Parser ===
target_group_not_found =
    ❌ Не найдена целевая группа для пользователя. Подключите группу, для того, что бы я мог пересылать туда сообщения, найденные по вашим ключевым словам.

no_channels_to_track =
    📭 У вас нет добавленных каналов для отслеживания.

too_many_channels =
    ⚠️ Найдено { $total } каналов. За этот проход подписка только на первые { $limit } (лимит антибана). Остальные — при следующем запуске.

channel_subscribed =
    ✅ Подписка на { $channel } выполнена
    ⏳ Пауза { $delay } сек. перед следующей…

join_daily_limit =
    ⏸ Суточный лимит вступлений исчерпан ({ $limit }/сутки). Продолжим завтра или увеличьте JOIN_DAILY_LIMIT.

join_batch_summary =
    📊 Подписки за этот проход:
    • новых: <b>{ $joined }</b>
    • уже были: <b>{ $already }</b>
    • ошибок: <b>{ $errors }</b>
    • отложено лимитом: <b>{ $skipped }</b>

target_group_join_error =
    ❌ Аккаунту не удалось присоединиться к целевой группе, проверьте подключенную группу

target_group_not_configured =
    ❌ Не найдена целевая группа для пользователя. Подключите группу.

target_group_fetch_error =
    ❌ Не удалось получить целевую группу. Проверьте подключение.

bot_listening =
    👂 Бот слушает новые сообщения.

    Совпадения по ключевым словам будут приходить сюда, в этот чат.

keyword_match_alert =
    📥 <b>Новое совпадение</b>

    <b>Источник:</b> { $chat_title }
    <b>Чат:</b> { $chat_username }
    <b>Автор:</b> { $author }
    <b>Время:</b> { $message_time }
    <b>Ссылка:</b> { $message_link }

    <b>Ключевое слово:</b> <code>{ $matched_keyword }</code>
    <b>Почему:</b> { $match_why }

    <b>Текст сообщения:</b>
    { $message_text }

keyword_match_alert_compact =
    📥 <b>{ $matched_keyword }</b> · { $chat_title }
    { $author } · { $message_time }
    { $message_link }
    <i>{ $match_why }</i>

    { $message_text }

keyword_match_alert_minimal =
    <b>{ $matched_keyword }</b>
    <i>{ $match_why }</i>
    { $message_link }

    { $message_text }

alert_why_exact = точная фраза · режим «{ $mode }»
alert_why_tokens = слова: { $tokens } · режим «{ $mode }»
alert_why_loose = частично: { $tokens } · режим «{ $mode }»

alert_time_value = { $datetime } ({ $tz })
alert_chat_id_only = id { $chat_id }
alert_chat_id_typed = id { $chat_id } ({ $chat_type })
alert_chat_type_channel = канал
alert_chat_type_supergroup = супергруппа
alert_chat_type_group = группа
alert_chat_type_user = личный чат
alert_open_button = 🔗 Открыть
alert_mute_24h_button = 🔕 Игнор 24ч
alert_mute_ok = Канал id { $chat_id } скрыт на { $hours } ч
alert_mute_invalid = Не удалось заглушить канал

alert_author_id = · id { $id }
alert_author_id_only = id { $id }
alert_author_unknown = — (канал / anonymous)
alert_author_signed = подпись: { $name }
alert_author_channel = канал
alert_author_forward = переслано от { $name }
alert_author_forward_entity = переслано · { $author }
alert_author_forward_id = переслано · id { $id }

message_link_unavailable = Ссылка недоступна

tracking_not_active =
    ⚠️ Отслеживание не запущено или уже остановлено.

tracking_already_active =
    ℹ️ Отслеживание уже запущено. Используйте кнопку «Остановить отслеживание» в главном меню.

tracking_stop_requested =
    🛑 Команда остановки отправлена. Отслеживание будет остановлено в течение нескольких секунд.

tracking_restored =
    🔄 Отслеживание восстановлено после перезапуска сервиса.

tracking_reconnected =
    🔄 Связь с Telegram восстановлена — снова слушаю каналы.

tracking_reconnect_failed =
    ❌ Не удалось восстановить связь с Telegram. Отслеживание остановлено.
    Запустите снова, когда сеть будет доступна.

tracking_failover_ok =
    🔄 Аккаунт сменился: { $from_phone } → { $to_phone }. Продолжаю слушать.

tracking_failover_failed =
    ❌ Не удалось восстановить связь и переключиться на запасной аккаунт.
    Подключите второй .session в «Мой парсинг» → Аккаунт или запустите снова позже.

tracking_not_subscribed_warn =
    ⚠️ Аккаунт ещё не в <b>{ $count }</b> канал(ах): { $preview }

    Сейчас слушаю доступные; в фоне попробую подписаться. Можно проверить вручную: Каналы → «Проверить подписки».

search_client_error =
    ❌ Не удалось подключить аккаунт для парсинга.
    Проверьте .session или добавьте запасной аккаунт в «Мой парсинг» → Аккаунт.

search_no_available_accounts =
    ⚠️ Нет подключённого аккаунта для поиска.

    Подключите свой Telegram-аккаунт через «🔐 Подключить аккаунт» в настройках.

# === Сессия ===
session_invalid =
    ⚠️ Аккаунт `{ $phone }` больше не действителен.
    Пожалуйста, подключите аккаунт заново.

account_fetch_error =
    ⚠️ Произошла ошибка при получении аккаунта. Попробуйте позже.

# === Проверка аккаунтов ===
checking_accounts_start =
    Аккаунтов для проверки: { $count }
checking_accounts_complete =
    ✅ Проверка аккаунтов завершена

# === Проверка группы для AI ===
ai_category_select_method =
    🤖 <b>Выберите метод присвоения категорий:</b>

    ⚡️ <b>Быстро (g4f.free)</b>
    • Бесплатно, без API ключей
    • Последовательная обработка (медленнее)
    • Подходит для небольших объёмов
    • Может возвращать неточные результаты

    🚀 <b>Мощно (Groq API)</b>
    • Требует API ключ Groq
    • Параллельная обработка в 10 потоков (быстрее)
    • Подходит для больших объёмов
    • Более точные результаты

    Выберите метод:
ai_category_back =
    ↩️ Возврат в панель администратора
ai_category_checking_models =
    🔍 Проверка доступных моделей...
ai_category_model_selected =
    ✅ Выбрана модель: { $model }
ai_category_select_from_keyboard =
    Пожалуйста, выберите метод из клавиатуры ниже:
ai_category_all_have_categories =
    ✅ Все группы уже имеют категории!
ai_category_processing =
    🔄 Обрабатываю { $total } групп...
ai_category_done =
    ✅ <b>Готово!</b>
ai_category_error =
    ❌ Ошибка: { $error }
ai_category_stats_title =
    📊 <b>Статистика категорий:</b>
ai_category_no_category_count =
    🗃️ Групп без категории: { $count }
ai_category_run_ai =
    Нажмите '🏷️ Присвоить категорию' для запуска AI

# === Подключение аккаунта ===
connect_account_ask_session =
    📤 Отправьте мне файл(ы) сессии Telethon (должны заканчиваться на `.session`)

    Можно отправить сразу несколько файлов — бот обработает их по очереди.
    Когда закончите — нажмите кнопку «Назад» или отправьте /start
connect_account_invalid_file =
    ❌ Это не файл сессии! Отправьте файл с расширением `.session`
connect_account_limit_reached =
    ⚠️ Достигнут лимит: { $max } файлов за раз.
    Обработайте текущие и отправьте остальные позже.
connect_account_file_queued =
    📥 Файл принят: `{ $filename }`
    📊 В очереди: { $total } файл(ов). Обрабатываю...
connect_account_success =
    ✅ <b>{ $filename }</b> — успешно!
    📱 { $phone } | 👤 { $name }
connect_account_failed =
    ❌ <b>{ $filename }</b> — не прошёл проверку
connect_account_error =
    ⚠️ <b>{ $filename }</b> — ошибка обработки
connect_account_processing_done =
    📊 <b>Обработка завершена!</b>

# === Определение языка ===
lang_detect_no_groups =
    ❌ Нет групп для обработки
lang_detect_starting =
    🚀 Запуск обработки { $total } групп...
lang_detect_error =
    ❌ Ошибка: { $error }
lang_detect_saving =
    💾 Сохранение { $count } результатов в БД...
lang_detect_complete =
    ✅ Обработка завершена!

    📊 Статистика:
    • Всего: { $total }
    • AI определил: { $ai_success }
    • Сохранено в БД: { $db_success }
    • Ошибок AI: { $ai_fail }
    • Ошибок БД: { $db_fail }
    • Всего ошибок: { $total_fail }

lang_detect_stats_title = Статистика
lang_detect_stats_total = Всего
lang_detect_stats_ai_success = AI определил
lang_detect_stats_db_success = Сохранено в БД
lang_detect_stats_ai_fail = Ошибок AI
lang_detect_stats_db_fail = Ошибок БД
lang_detect_stats_total_fail = Всего ошибок

# === Лог файл ===
log_file_caption =
    📄 Лог файл с ошибками.

# === connect_account.py ===
account_connected_free =
    ✅ Аккаунт успешно подключен

no_free_accounts =
    ❌ Нет доступных свободных аккаунтов. Пожалуйста, попробуйте позже или обратитесь к администратору.

invalid_session_file =
    ❌ Это не файл сессии! Отправьте файл с расширением `.session`

session_file_received =
    📥 Файл получен: `{ $filename }`

    🔍 Проверяю аккаунт...

session_connected_success =
    ✅ <b>{ $filename }</b> — успешно!
    📱 { $phone } | 👤 { $name }
    💾 Сохранено в вашу персональную базу.

session_validation_failed =
    ❌ <b>{ $filename }</b> — не прошёл проверку.
    Проверьте, что файл сессии актуален и не используется в другом месте.

session_check_error =
    ⚠️ Произошла ошибка при проверке аккаунта. Попробуйте позже.

# === handlers.py (группы) ===
only_txt_files_supported =
    ⚠️ Поддерживаются только .txt файлы.

empty_file_no_usernames =
    ⚠️ Файл пуст или не содержит username-ов.

groups_upload_summary =
    ✅ Добавлено: { $added }
    ⚠️ Уже есть: { $skipped }
    ❌ Ошибок: { $errors }

# === admin.py ===
admin_found_accounts =
    🔍 Найдено аккаунтов: { $count }

admin_db_actualization_start =
    🔄 Начинаю актуализацию { $total } групп...

admin_using_account =
    📱 Используется аккаунт: { $account }

admin_account_error =
    ❌ Ошибка аккаунта { $account }: { $error }

admin_critical_error =
    ❌ Критическая ошибка: { $error }

# === Экспорт вопросов ===
no_questions_in_db =
    📭 В базе данных нет вопросов.

questions_export_caption =
    📦 Экспорт вопросов и ответов.

export_error =
    ❌ Произошла ошибка при экспорте: { $error }

# === Кнопки ===
launch_tracking_button = 🚀 Запуск отслеживания
check_group_for_keywords_button = 🔍 Проверка группы на наличие ключевых слов
ai_search_button = ✨ Поиск через AI
get_database_button = 📥 Получить базу
instruction_button = 📖 Инструкция по использованию
settings_button = ⚙️ Настройки
admin_panel_button = 🛡️ Панель администратора
admin_tracking_button = 📡 Tracking
admin_tracking_message =
    📡 <b>Активный tracking</b>: { $count }

    Совпадений за час: <b>{ $matches }</b> · FloodWait за час: <b>{ $floods }</b>

    { $rows }

    ▶ — процесс в этом инстансе · ○ — только метка в Redis
admin_tracking_empty =
    📡 <b>Активный tracking</b>: 0

    Совпадений за час: <b>{ $matches }</b> · FloodWait за час: <b>{ $floods }</b>

    Сейчас никто не парсит.
admin_tracking_row =
    • <b>{ $user }</b>
    ключи: { $keywords } · каналы: { $channels_enabled }/{ $channels_total }
    { $local } local · client { $client } · uptime { $uptime }
admin_tracking_stop_button = 🛑 Stop { $user_id }
admin_tracking_refresh_button = 🔄 Обновить
admin_tracking_refreshed = Обновлено
admin_tracking_stopped = Остановлен { $user_id }
admin_tracking_stop_invalid = Некорректный user_id
admin_tracking_stop_error = Ошибка: { $error }
get_log_file_button = 📄 Получить лог файл
update_database_button = 🔄 Актуализация базы данных
export_questions_button = Выгрузить вопросы
assign_category_button = 🏷️ Присвоить категорию
check_accounts_button = ✅ Проверка аккаунтов
assign_language_button = 🌐 Присвоить язык
connect_account_button = 🔐 Подключение аккаунта
back_button = ⬅️ Назад
fast_method_button = ⚡️ Быстро (g4f.free)
powerful_method_openrouter_button = 🚀 Мощно (Openrouter API)
powerful_method_groq_button = 🚀 Мощно (GROQ API)
all_database_button = 📥 Вся база
channels_database_button = 📥 База каналов
groups_database_button = 📥 База групп
select_category_button = 📂 Выбрать категорию
investments_button = инвестиции
finance_and_personal_budget_button = финансы и личный бюджет
crypto_and_blockchain_button = криптовалюты и блокчейн
business_and_entrepreneurship_button = бизнес и предпринимательство
marketing_and_promotion_button = маркетинг и продвижение
tech_and_it_button = технологии и it
education_and_self_development_button = образование и саморазвитие
work_and_career_button = работа и карьера
real_estate_button = недвижимость
health_and_medicine_button = здоровье и медицина
travel_button = путешествия
auto_and_transport_button = авто и транспорт
shopping_and_discounts_button = шоппинг и скидки
entertainment_and_leisure_button = развлечения и досуг
politics_and_society_button = политика и общество
science_and_research_button = наука и исследования
sports_and_fitness_button = спорт и фитнес
cooking_and_food_button = кулинария и еда
fashion_and_beauty_button = мода и красота
hobbies_and_creativity_button = хобби и творчество
russian_language_button = 🇷🇺 Русский
english_language_button = 🇬🇧 English
global_ai_search_button = 🌐 Глобальный AI поиск
stop_tracking_button = 🛑 Остановить отслеживание
update_list_button = 🔁 Обновить список
enter_keyword_button = 🔍 Ввод ключевого слова
delete_group_from_tracking_button = 🗑️ Удалить группу из отслеживания
clear_all_tracked_channels_button = 🗑️ Очистить весь список
keywords_list_button = 🔍 Список ключевых слов
tracking_links_button = 🌐 Ссылки для отслеживания
connect_group_for_messages_button = 📤 Пересылка в группу (скоро)
change_language_button = 🌐 Сменить язык
quiet_hours_button = 🌙 Тихие часы
quiet_hours_message =
    🌙 <b>Тихие часы</b>

    Статус: <b>{ $status }</b>
    Окно: <code>{ $window }</code>

    В это время совпадения сохраняются в «Лиды», но уведомления в чат не приходят.
quiet_hours_status_on = включены
quiet_hours_status_off = выключены
quiet_hours_enable_button = ✅ Включить
quiet_hours_disable_button = ⏹ Выключить
quiet_hours_preset_2308 = 23:00–08:00
quiet_hours_preset_0007 = 00:00–07:00
quiet_hours_preset_2209 = 22:00–09:00
quiet_hours_toggled_on = Тихие часы включены
quiet_hours_toggled_off = Тихие часы выключены
quiet_hours_preset_saved = Окно: { $window }
digest_button = 📦 Дайджест
digest_settings_message =
    📦 <b>Дайджест совпадений</b>

    Статус: <b>{ $status }</b>
    Интервал: <b>{ $interval }</b> мин

    Вместо каждого алерта бот копит совпадения и присылает сводку одним сообщением.
    Лиды в базе сохраняются сразу.
digest_status_on = включён
digest_status_off = выключен
digest_enable_button = ✅ Включить
digest_disable_button = ⏹ Выключить
digest_interval_15 = 15 мин
digest_interval_30 = 30 мин
digest_interval_60 = 60 мин
digest_flush_now_button = 📤 Отправить сейчас
digest_toggled_on = Дайджест включён
digest_toggled_off = Дайджест выключен
digest_flushed_on_disable = Дайджест выключен, отправлено: { $count }
digest_interval_saved = Интервал: { $interval } мин
digest_flush_ok = Отправлено совпадений: { $count }
digest_flush_empty = Буфер пуст
digest_message =
    📦 <b>Дайджест совпадений</b> ({ $count })

    { $items }
    { $more }
digest_and_more =
    …и ещё { $count }
chat_filter_button = 📢 Тип чатов
chat_filter_message =
    📢 <b>Фильтр по типу чата</b>

    Сейчас: <b>{ $current }</b>

    • Все — каналы и группы/обсуждения
    • Только каналы — посты канала (без комментов в группе обсуждений)
    • Только группы — супергруппы и обсуждения
chat_filter_all_name = все
chat_filter_channels_name = только каналы
chat_filter_groups_name = только группы
chat_filter_all_button = Все чаты
chat_filter_channels_button = Только каналы
chat_filter_groups_button = Только группы
chat_filter_saved = Фильтр: { $mode }
author_filter_button = 👤 Кто пишет
author_filter_message =
    👤 <b>Фильтр авторов</b>

    Сейчас: <b>{ $current }</b>

    • <b>Только люди</b> — сообщения от реальных пользователей (не посты каналов и ботов)
    • <b>Люди + анонимы</b> — плюс сообщения без явного автора
    • <b>Все</b> — включая посты каналов, репосты каналов и ботов
author_filter_humans_name = только люди
author_filter_humans_anon_name = люди + анонимы
author_filter_all_name = все
author_filter_humans_button = Только люди
author_filter_humans_anon_button = Люди + анонимы
author_filter_all_button = Все авторы
author_filter_saved = Авторы: { $mode }
alert_template_button = 📝 Шаблон алерта
alert_template_message =
    📝 <b>Шаблон алерта</b>

    Сейчас: <b>{ $current }</b>

    • Полный — все поля (источник, чат, автор, время, ссылка, ключ, почему, текст)
    • Компактный — ключ, источник, автор, время, ссылка, почему и текст
    • Минимальный — ключ, почему, ссылка и текст
alert_template_full_name = полный
alert_template_compact_name = компактный
alert_template_minimal_name = минимальный
alert_template_full_button = Полный
alert_template_compact_button = Компактный
alert_template_minimal_button = Минимальный
alert_template_saved = Шаблон: { $mode }

alert_destination_button = 📬 Куда слать алерты
alert_destination_message =
    📬 <b>Куда слать алерты</b>

    В личку: <b>{ $dm_status }</b>
    В группу: <b>{ $group_status }</b>

    { $group_info }
alert_destination_dm_button = В личку
alert_destination_group_button = В группу
alert_destination_on = вкл
alert_destination_off = выкл
alert_destination_group_unbound = Группа не привязана — включите «В группу» и привяжите чат.
alert_destination_group_bound = Привязано: чат <code>{ $chat_id }</code>
alert_destination_group_bound_topic = Привязано: чат <code>{ $chat_id }</code>, топик <code>{ $thread_id }</code>
alert_destination_need_one_channel = Нужен хотя бы один канал доставки (личка или группа).
alert_destination_bind_button = 🔗 Привязать группу
alert_destination_rebind_button = 🔄 Сменить группу/топик
alert_destination_unbind_button = ✂️ Отвязать группу
alert_destination_unbound = Группа отвязана
alert_destination_bind_instructions =
    <b>Привязка группы для алертов</b>

    1. Добавьте бота в supergroup (для топика — в нужный топик).
    2. В группе или <b>в нужной теме</b> напишите команду:

    <code>{ $command }</code>

    Токен действует { $ttl_min } мин. Команду может выполнить только администратор группы.
alert_destination_bind_ready_button = 🔄 Новый токен
alert_destination_bind_token_required =
    Нужен токен из настроек бота.

    Сначала: Настройки → Куда слать алерты → Привязать группу.
    Затем в группе/топике: <code>/bind_alerts ТОКЕН</code>
alert_destination_bind_bad_token = Неверный или просроченный токен. Получите новый в настройках бота.
alert_destination_bind_not_admin = Привязать группу может только администратор или создатель чата.
alert_destination_bind_chat_taken = Этот чат/топик уже привязан к другому аккаунту бота.
alert_destination_bind_success = ✅ Группа привязана: { $group_info }
alert_destination_bind_success_short = ✅ Привязано: { $group_info }
alert_destination_test_message = ✅ <b>Проверка доставки</b>\n\nАлерты в эту группу настроены.
alert_destination_group_not_bound = Группа включена, но чат не привязан. Откройте настройки и привяжите группу.
alert_group_delivery_failed =
    ⚠️ Не удалось доставить алерт в группу (в личку отправлено).
    { $error }
alert_group_delivery_failed_only =
    ⚠️ Не удалось доставить алерт в группу. Проверьте, что бот в чате и привязка актуальна.
    { $error }

leads_group_help =
    <b>Выгрузка лидов в группе</b>

    <code>/leads</code> — все лиды
    <code>/leads 2026-07-01</code> — за один день
    <code>/leads 2026-07-01 2026-07-17</code> — за период

    Даты в часовом поясе бота (TIMEZONE). Только владелец аккаунта.

    Если бот не отвечает — добавьте @username бота: <code>/leads@YourBot</code>
    Сначала привяжите группу: <code>/bind_alerts ТОКЕН</code> в этой теме.
leads_group_bad_dates = Неверный формат дат. Пример: <code>/leads 2026-07-01</code> или <code>/leads 2026-07-01 2026-07-17</code>
leads_group_not_bound =
    Группа для алертов не привязана.

    В личке: Настройки → Куда слать алерты → Привязать группу → <code>/bind_alerts ТОКЕН</code> в этой теме.
leads_group_disabled = Доставка в группу выключена. Включите «В группу» в настройках бота.
leads_group_wrong_chat =
    Эта группа не привязана к вашему аккаунту. Привязанный чат: <code>{ $chat_id }</code>
leads_group_wrong_topic =
    Команда доступна только в привязанной теме (топик <code>{ $thread_id }</code>).
    Выполните <code>/bind_alerts ТОКЕН</code> в нужной теме.
group_chat_allowed_command_failed =
    Команда не выполнена. Проверьте привязку группы (/bind_alerts ТОКЕН) и что бот добавлен в чат.
leads_group_export_day_caption = Лиды за { $date }: { $count } шт.
leads_group_export_range_caption = Лиды { $date_from } — { $date_to }: { $count } шт.

stopwords_menu_button = 🚫 Стоп-слова
stopwords_menu_message =
    🚫 <b>Стоп-слова</b>

    Всего: <b>{ $count }</b>

    Если в сообщении есть стоп-слово, алерт не отправится (даже при совпадении ключа).
stopwords_add_button = ➕ Добавить
stopwords_view_list_button = 📋 Список
stopwords_add_prompt =
    📥 Пришлите стоп-слова текстом или .txt файлом (по одному на строке или через запятую).

    Пример:
    спам
    реклама
    купи подписку
stopwords_empty_input = Пустой ввод — добавьте хотя бы одно слово.
stopwords_added_count = Добавлено стоп-слов: { $count }
stopwords_already_added = Уже были ({ $count })
stopwords_add_errors = Ошибки при добавлении
stopwords_list_empty = Список стоп-слов пуст.
stopwords_list_title = Стоп-слова: { $count } · стр. { $page }
stopwords_deleted = Удалено: { $word }
stopwords_missing = Стоп-слово не найдено
connect_free_account_button = 🔐 Подключить свободный аккаунт

# post_doc.py
instruction_question_prompt = 🤖 <b>Вы можете задать мне любой вопрос по использованию бота, и я отвечу вам!</b>
ai_support_assistant_system_prompt = Вы — квалифицированный помощник службы поддержки Telegram-бота AutoParseAlertBot. Ваша задача — отвечать на вопросы пользователей, основываясь СТРОГО на предоставленной базе знаний. Если ответа нет в базе знаний, вежливо сообщите, что вы не обладаете данной информацией и посоветуйте обратиться в поддержку. Отвечайте на языке пользователя. Используйте HTML-разметку для оформления ответа.

excel_filename_telegram_groups = telegram_groups_{ $timestamp }.xlsx
excel_header_group_link = Ссылка
excel_header_group_participants = Участники
excel_header_group_type = Тип
excel_header_group_description = Описание
excel_header_group_name = Название
excel_filename_groups_by_category = groups_{ $category }.xlsx
excel_sheet_name_groups = Группы
excel_header_date_added = Дата добавления
excel_header_link = Ссылка
excel_header_activity = Активность
excel_header_language = Язык
excel_header_type = Тип
excel_header_category = Категория
excel_header_participants = Участников
excel_header_description = Описание
excel_header_name = Название
excel_header_id = ID (Hash)
excel_sheet_name_search_results = Результаты поиска
excel_filename_groups_db = База_групп.xlsx
excel_filename_channels_db = База_каналов.xlsx
excel_filename_all_db = Вся_база.xlsx
ai_search_button_user = 🤖 AI поиск
excel_header_username = Username канала/группы / Channel/Group Username
excel_header_keyword = Ключевое слово / Keyword
excel_header_number = №
no_tracking_links_found = 📭 У вас нет ссылок для отслеживания.
tracking_links_export_caption = 🔗 Экспорт ссылок для отслеживания. Всего записей: { $count }
no_keywords_found = 📭 У вас нет сохраненных ключевых слов.
keywords_export_caption = 📋 Экспорт ключевых слов. Всего записей: { $count }


# language_detection.py
lang_detect_summary = ✅ Обработка завершена!

    📊 Статистика:
    • Всего: { $total }
    • AI определил: { $ai_success }
    • Сохранено в БД: { $db_success }
    • Ошибок AI: { $ai_fail }
    • Ошибок БД: { $db_fail }
    • Всего ошибок: { $total_fail }
name_prompt = Название
description_prompt = Описание
no_data_prompt = Нет данных
ai_lang_detect_prompt =
    Определи основной язык текста или описания сообщества.
    Ответь СТРОГО одним словом — кодом языка в формате ISO 639-1 (двухбуквенный код).
    Примеры корректных ответов: ru, en, es, zh, ar, hi, ja, ko, fr, de, pt, it, nl, sv, pl, tr, vi, th, id, fa, he, uk, cs, el, ro, hu, fi, da, no, sk, bg, hr, sr, sl, et, lv, lt, mk, sq, mt, cy, eu, gl, ga, is, ms, sw, tl, ur, bn, ta, te, mr, gu, kn, ml, si, km, lo, my, am, hy, ka, az, uz, kk, ky, tg, tk, mn, ps, ku, sd, ne, si, lo, km, my, dz, bo, ug, yi, ha, yo, ig, zu, xh, st, tn, ts, ve, nr, ss, ch, rw, rn, mg, ln, kg, sw, tn.
    Если язык невозможно определить однозначно или текст содержит смесь языков без доминирующего — ответь: unknown.
    НЕ добавляй никаких пояснений, пунктуации, пробелов или дополнительного текста. Только код языка или 'unknown'.
    
    Текст для анализа:
    { $user_input }

# checking_group_for_ai.py
get_groups_without_category_message = 📊 <b>Статистика категорий:</b>

    🗃️ Групп без категории: { $count }

    Нажмите '🏷️ Присвоить категорию' для запуска AI


# === Лимиты скачивания и Звезды ===
download_free_success = 📥 Выгрузка базы (1 раз в сутки бесплатно). Начинаем скачивание...
download_cooldown_message =
    ⚠️ Вы уже скачивали базу за последние 24 часа.
    Следующее бесплатное скачивание будет доступно через <b>{ $time }</b>.
    
    Вы можете скачать базу прямо сейчас за 5 ⭐.
    Ваш баланс звезд в боте: <b>{ $stars }</b> ⭐
pay_from_balance_btn = 🪙 Списать 5 ⭐ с баланса
pay_direct_btn = ⭐ Оплатить 5 ⭐ напрямую
cancel_btn = ❌ Отмена
download_paid_success = ✅ Оплата/списание 5 ⭐ успешно произведено. Начинаем скачивание базы...
download_insufficient_stars = ❌ Недостаточно звезд на балансе.
stars_topup_success = 🎉 Баланс успешно пополнен на { $amount } ⭐! Ваш текущий баланс: { $balance } ⭐.
stars_added_admin = ⭐ Администратор начислил вам { $amount } ⭐. Текущий баланс: { $balance } ⭐.
topup_stars_button = 💳 Пополнение звезд
stars_balance_msg = 👤 <b>Ваш профиль звезд:</b>\n\nБаланс: <b>{ $stars }</b> ⭐\n\nЗдесь вы можете пополнить баланс Telegram Stars для платных скачиваний базы данных.
stars_invoice_title = Пополнение баланса звезд
stars_invoice_desc = Покупка { $amount } Telegram Stars для использования в боте
stars_invoice_dl_title = Скачивание базы данных
stars_invoice_dl_desc = Однократное скачивание базы данных в обход суточного лимита
excel_filename_category_db = category_database.xlsx
export_category_caption = 📂 База по категории "{ $category }". Всего записей: { $total_records }.
generating_database_wait = ⏳ Формируем файл базы данных, это может занять некоторое время. Пожалуйста, подождите...





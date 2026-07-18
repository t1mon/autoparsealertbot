# English localization
access_denied_full =
    🔒 <b>Closed beta</b>

    Full access is by invitation only.
    Contact the developer: { $developer }

    Briefly describe your use case (niche, sample channels).
access_denied_short =
    🔒 Access by request only. Contact { $developer }
access_contact_developer_button = 💬 Contact developer
access_denied_group =
    🔒 Closed beta. Use the bot in private chat @{ $bot_username }

group_chat_use_private =
    🤖 Bot settings and menu are available in private chat only.

    Open @{ $bot_username } and send /start

    In groups, only these commands work:
    • <code>/bind_alerts TOKEN</code> — bind (token from settings)
    • <code>/leads</code> — export leads
group_chat_use_private_short =
    Manage the bot in private chat @{ $bot_username }. Here: /bind_alerts and /leads
group_chat_command_private =
    This command works in private chat with @{ $bot_username } only
group_chat_callback_private = Menu buttons work in private chat with the bot only
group_chat_open_bot_button = 💬 Open bot

welcome_ask_language =
    🌍 Hi! Please choose your interface language:
welcome_message_template =
    📡 <b>Tracking:</b> { $tracking_status }
    👤 <b>Account:</b> { $account_label }
    🔑 <b>Keywords:</b> { $keywords_count }
    📢 <b>Channels:</b> { $channels_enabled } enabled / { $channels_total } total

    { $howto_block }{ $next_hint }

howto_3_steps =
    🚀 <b>Start in 3 steps</b>

    <b>1. Account</b> — «My parsing» → Account → <code>.session</code> file
    <b>2. Keywords</b> — what to look for (use «Test a message»)
    <b>3. Channels</b> — add @channels and enable parsing ✅ in the list

    On the main screen tap <b>«Start»</b> — matches will arrive here.
howto_3_steps_short =
    🚀 <b>3 steps:</b> account → keywords → channels → «Start»

next_step_account = 👉 Next: connect a Telegram account (.session)
next_step_keywords = 👉 Next: add at least one keyword
next_step_channels = 👉 Next: add a channel and enable parsing (✅ in the list)
next_step_ready_start = 👉 All set — tap «Start»
next_step_tracking_on = 📬 Tracking is running — matches arrive in this chat

tracking_status_running = ▶ running
tracking_status_stopped = ⏹ stopped
account_not_connected = not connected
account_connected_unknown = connected
my_parsing_button = 📡 My parsing
cabinet_account_button = 👤 Account
accounts_menu_template =
    👤 <b>Accounts</b>

    Active: <code>{ $active_label }</code>
    Total: <b>{ $count }</b>

    ● — active · ○ — tap to select · ✕ — delete
accounts_connect_button = ➕ Connect new
accounts_check_button = ✅ Check active
accounts_set_active_ok = Active: { $phone }
accounts_deleted_ok = Account deleted
accounts_not_found = Account not found
accounts_check_progress = Checking…
accounts_check_ok = ✅ <b>{ $phone }</b> — session is valid
accounts_check_fail = ❌ <b>{ $phone }</b> — session is invalid. Upload a new .session or pick another account.
cabinet_message_template =
    <b>My parsing</b>

    { $check_account } Account: <code>{ $account_label }</code>
    { $check_keywords } Keywords: <b>{ $keywords_count }</b>
    { $check_channels } Channels: <b>{ $channels_enabled }</b> on / <b>{ $channels_total }</b> total
    🎯 Match mode: <b>{ $match_mode }</b>

    { $hint }
cabinet_hint_ready = ✅ Ready — you can start tracking from the main screen.
cabinet_hint_not_ready = ⚠️ To start tracking you need an account, at least one keyword and one enabled channel.

wizard_message_template =
    🚀 <b>Setup in 3 steps</b>

    { $check_account } 1. Account: <code>{ $account_label }</code>
    { $check_keywords } 2. Keywords: <b>{ $keywords_count }</b>
    { $check_channels } 3. Channels: <b>{ $channels_enabled }</b> on / <b>{ $channels_total }</b> total

    { $step_hint }
wizard_hint_account = Now step 1: connect a Telegram account (.session).
wizard_hint_keywords = Now step 2: add at least one keyword.
wizard_hint_channels = Now step 3: add a channel and enable parsing ✅.
wizard_hint_ready = ✅ All three steps done — tap «Start».
wizard_cta_account = 👤 Connect account
wizard_cta_keywords = 🔑 Add keywords
wizard_cta_channels = 📢 Add channels
wizard_continue_button = 🚀 Continue setup
wizard_skip_button = To menu

lang_selected =
    ✅ Great! The interface will now be displayed in your selected language.
settings_message =
    ⚙️ <b>Settings</b>

    Alert filters, language and Stars live here.
    Account, keywords and channels: «My parsing» on the main screen.
connect_account =
    📱 To connect your Telegram account, send a session file in the format:
    `+79599999999.session`

    Once uploaded, the bot will use this account to track messages.
launching_tracking =
    🚀 Launching message tracking...

    Keyword matches will be sent to this chat.
tracking_launch_error =
    ⚠️ No enabled channels to parse.

    Add channels and enable at least one in <b>My parsing → Channels</b>.
tracking_not_ready =
    ⚠️ Not ready to start yet. Missing:

    { $gaps }

    Open <b>My parsing</b> and complete the checklist.
setup_before_start_button = ⚠️ Set up first
ready_gap_account = connect a Telegram account
ready_gap_keywords = add at least one keyword
ready_gap_channels_none = add at least one channel
ready_gap_channels_disabled = enable parsing for at least one channel (✅ in the list)
update_list =
    📥 Send a .txt file or a text message with groups and channels to track:

    ✅ Public: <b>@username</b> or <b>https://t.me/username</b>
    ✅ Private: <b>https://t.me/+invite</b> or <b>https://t.me/joinchat/...</b>
    ✅ No username: message link <b>https://t.me/c/1234567890/1</b> or <b>id:-1001234567890</b>
    ✅ Forums and topics: add the group itself — the bot listens to all topics inside it
    ✅ One per line or comma-separated
    ✅ File must be <b>.txt</b>

    📌 Examples:
    @channel1
    https://t.me/+AbCdEfGhIjK
    https://t.me/c/1234567890/55/100
account_missing =
    ⚠️ You do not have a connected Telegram account.

account_missing_2 =
    ⚠️ The session file for your Telegram account is invalid — you need to log in again. Send a valid session file.
enter_keyword =
    🔍 Add keywords:

    • as text — one per line or comma-separated
    • as a <code>.txt</code> file — one phrase per line

    After submit they appear under My parsing → Keywords.
keywords_menu_message =
    🔑 <b>Keywords</b>

    Saved now: <b>{ $count }</b>
    Match mode: <b>{ $match_mode }</b>

    Add via text or .txt, browse the list, delete items, or download a file.
keywords_menu_button = 🔑 Keywords
keywords_add_button = ➕ Add
keywords_view_list_button = 📋 View list
keywords_export_txt_button = 📄 .txt
keywords_export_xlsx_button = 📊 Excel
keywords_list_title =
    🔑 Keywords: <b>{ $count }</b> · page { $page }
    Tap ✕ to delete:
keyword_deleted = Deleted: { $keyword }
keyword_delete_missing = Keyword already deleted
match_mode_button = 🎯 Match mode
match_mode_strict_button = Strict (exact phrase only)
match_mode_smart_button = Smart (recommended)
match_mode_loose_button = Loose (more matches)
match_mode_strict_name = strict
match_mode_smart_name = smart
match_mode_loose_name = loose
match_mode_message =
    🎯 <b>Keyword match mode</b>

    Current: <b>{ $current }</b>

    • <b>Strict</b> — exact phrase only
    • <b>Smart</b> — stems/typos; all phrase words required
    • <b>Loose</b> — more hits (legacy soft rules)
match_mode_saved = Mode: { $mode }
match_check_button = 🧪 Test a message
match_check_no_keywords = Add keywords first
match_check_prompt =
    🧪 <b>Message check</b>

    Keywords: <b>{ $count }</b> · mode: <b>{ $mode }</b>

    Send a sample message text — I’ll show which keywords match and why.
    Stop words are checked too.
match_check_empty = Empty text — send a message
match_check_need_text = Please send plain text (not a file/photo)
match_check_none =
    ❌ <b>No matches</b>

    Mode: { $mode } · keywords checked: { $checked }

    <b>Text:</b>
    <i>{ $preview }</i>
match_check_hits =
    ✅ <b>Matched: { $hit_count }</b> of { $checked }

    Mode: { $mode }

    { $rows }
    { $more }

    <b>Text:</b>
    <i>{ $preview }</i>
match_check_row = { $n }. <code>{ $keyword }</code>
    → { $why }
match_check_more = …and { $count } more
match_check_stopword =
    🚫 Stop word “{ $stopword }” — in production neither alert nor lead would be created.
match_check_again_hint = You can send another text or press Back.
channels_menu_message =
    📢 <b>Channels to parse</b>

    Enabled: <b>{ $enabled }</b> · total in list: <b>{ $total }</b>

    Add via text or .txt, toggle in the list.
    «Check subscriptions» — whether the active account is in these channels.
channels_menu_button = 📢 Channels
channels_add_button = ➕ Add
channels_view_list_button = 📋 View list
channels_check_subs_button = 🔎 Check subscriptions
channels_join_missing_button = ➕ Join missing
channels_check_no_account = Connect an account first
channels_check_no_enabled = No enabled channels
channels_check_progress = Checking…
channels_check_progress_msg =
    🔎 Checking active account membership for <b>{ $count }</b> channel(s)…
channels_check_connect_fail =
    ❌ Could not connect the active account. Check the .session.
channels_check_error =
    ❌ Membership check failed. Try again later.
channels_check_report =
    🔎 <b>Account membership</b> <code>{ $phone }</code>

    ✅ Joined: <b>{ $ok_count }</b>
    ⚠️ Not joined: <b>{ $missing_count }</b>
    ❌ Check errors: <b>{ $error_count }</b>

    <b>Not joined:</b>
    { $missing_list }

    <b>Errors:</b>
    { $error_list }

    Without membership, messages from that channel may not arrive. Join now or start tracking — the bot will try to join in the background.

    <i>✅/⏸ — parsing on/off. ⚠️ not joined · 🕐 pending approval · 🔒 private · ❌ error.</i>
channels_join_nothing = Nothing to join — run a check first
channels_join_progress =
    ➕ Joining <b>{ $count }</b> channel(s)… This may take a while.
channels_join_progress_live =
    ➕ <b>Joining channels</b> · { $done }/{ $total }

    Current: <code>{ $channel }</code>
    ✅ { $joined } · already { $already } · ❌ { $errors }

    { $status }
channels_join_status_pause =
    ⏳ Pause <b>{ $delay }</b> sec. before the next one…
channels_join_status_working =
    🔄 Joining…
channels_join_cancel_button = ⏹ Cancel
channels_join_cancel_confirm =
    ⏹ <b>Cancel joining?</b>

    Already processed channels will stay joined. You can resume the rest later.
channels_join_cancel_yes = ✅ Yes, cancel
channels_join_cancelling_msg = ⏹ Cancelling join…
channels_join_already_running = Join already in progress — wait or cancel it first
channels_join_background_hint = Join continues in the background — I'll send the summary separately
channels_join_stopped =
    ⏹ <b>Join cancelled</b>

    Newly joined: <b>{ $joined }</b>
    Already member: <b>{ $already }</b>
    Errors: <b>{ $errors }</b>
    Not processed: <b>{ $remaining }</b>
channels_join_done =
    ✅ Done.

    Newly joined: <b>{ $joined }</b>
    Already member: <b>{ $already }</b>
    Errors: <b>{ $errors }</b>
    Deferred by limit: <b>{ $skipped }</b>
channels_export_txt_button = 📄 .txt
channels_export_xlsx_button = 📊 Excel
channels_clear_button = 🗑️ Clear all
channels_list_title =
    📢 Channels: <b>{ $enabled }</b> on / <b>{ $total }</b> · page { $page }
    ✅/⏸ parse · ⚠️🕐🔒❌ membership · ✕ delete
channel_deleted = Deleted: { $channel }
channel_missing = Channel already deleted
channel_membership_ok = joined
channel_membership_missing = not joined
channel_membership_pending = pending approval
channel_membership_private = private
channel_membership_error = join error
membership_reason_not_member = account not a member
membership_reason_pending_approval = admin approval required (request sent or needed)
membership_reason_private = private or inaccessible chat
membership_reason_check_failed = check failed
membership_reason_invalid_ref = invalid link
membership_reason_invite_expired = invite link expired
membership_reason_unknown = could not join
channel_enabled = Enabled: { $channel }
channel_disabled = Disabled: { $channel }
channel_status_on = on
channel_status_off = off
excel_header_parse_status = Parsing
leads_menu_button = 📋 Matches
leads_view_list_button = 📋 View list
leads_export_xlsx_button = 📊 Excel
leads_menu_message =
    📋 <b>Matches</b>

    Saved: <b>{ $count }</b>

    History of keyword hits — browse the list or export Excel.
leads_list_title =
    📋 Matches: <b>{ $count }</b> · page { $page }
    Tap a card to open:
leads_empty = 📭 No saved matches yet. They appear when keywords hit.
leads_missing = Record not found
leads_export_caption = 📋 Matches export. Total: { $count }
leads_card =
    📋 <b>Match</b>

    <b>Keyword:</b> <code>{ $keyword }</code>
    <b>Author:</b> { $author }
    <b>Chat:</b> { $chat }
    <b>Time:</b> { $when }
    <b>Link:</b> { $link }

    <b>Text:</b>
    { $message_text }
excel_header_lead_time = Time
excel_header_author_name = Author
excel_header_author_username = @username
excel_header_author_id = Author ID
excel_header_author_kind = Author type
excel_header_chat_title = Chat
excel_header_link = Link
excel_header_message_text = Text

ai_search_welcome =
    🤖 <b>Welcome to the AI Search menu!</b>

    Here you can find new thematic groups and channels using the power of artificial intelligence.

    🚀 <b>Available modes:</b>
    • 🤖 <b>AI Search:</b> Fast search for groups based on your database and keywords.
    • 🌐 <b>Global AI Search:</b> Advanced search across the entire Telegram space to find new communities.

    Just select the desired mode on the keyboard or enter a request! 👇
enter_group =
    🔜 Group forwarding will be added later (private groups and topics).

    For now, notifications are sent directly in this bot chat.

    You can optionally pre-configure a public group @username:
admin_panel_message =
    👋 <b>Welcome to Admin Panel!</b>

    Here's what you can do:

    📡 <b>Tracking</b> — who is parsing now, keywords/channels, force stop.

    📁 <b>Get Log File</b> — view the error and event log of the bot for the recent period. Useful for diagnostics.

    🔄 <b>Database Actualization</b> — update information about groups and channels: check their current type (group/channel) and get actual IDs.

    🏷️ <b>Assign Category</b> — automatically classify groups and channels by topics using AI.

    ✅ <b>Check Accounts</b> — check the status of connected accounts and their sessions.

    🌐 <b>Assign Language</b> — detect the language of content in groups and channels.

    🔐 <b>Connect Account</b> — connect a Telegram account via session file for use in the bot.

tracking_stopped =
    ✅ Tracking has been stopped.

instruction_caption =
    📘 <b>Usage Instructions</b>

    Attached is a detailed guide on the bot's functionality.

    🔗 <b>Online Documentation:</b>
    • <a href="{ $gitverse_link }">GitVerse</a>
    • <a href="{ $github_link }">GitHub</a>

    We recommend reviewing it for effective use of all bot features.

instruction_howto_extra =
    💡 Tip: in Keywords there is <b>«Test a message»</b> — try a sample text before starting.

    Tap the button below to ask a question about the bot.
instruction_ask_button = ❓ Ask a question
instruction_ask_prompt =
    🤖 Type your question about using the bot — I’ll answer using the docs.
instruction_file_not_found =
    ⚠️ Instruction file not found on server.

instruction_send_error =
    ❌ Could not answer. Try again later or contact support.
instruction_menu_error =
    ❌ Could not open instructions. Try /start.
instruction_ai_no_key =
    ⚠️ AI answers are not configured: <code>GROQ_API_KEY</code> is missing in .env.

    Free key: https://console.groq.com/keys
    Add it to .env and restart the bot.
instruction_ai_auth_error =
    ⚠️ Groq key is invalid or revoked. Check <code>GROQ_API_KEY</code> in .env.
instruction_ai_connection_error =
    ⚠️ Could not reach Groq (network/DNS/proxy). Check internet and PROXY_* in .env.
instruction_ai_empty =
    ⚠️ Empty AI reply. Try rephrasing the question.
instruction_ai_error =
    ❌ AI error. Please try again later.

# === Database Export ===
database_empty =
    📭 Database is empty.

export_all_caption =
    📦 Complete database of Telegram groups and channels.

    📊 Total records: { $total_records }
    🧹 Duplicates removed before export: { $deleted_duplicates }

export_channels_caption =
    📦 Telegram channels database.

    📊 Total records: { $total_records }

export_groups_caption =
    📦 Telegram groups database.

    📊 Total records: { $total_records }

export_error_generic =
    ❌ An error occurred while creating the file.

get_database_menu =
    👋 Welcome to the database export mode!

    Here's what you can do:

    🔹 <b>📥 Get Full Database</b> — get a complete list of all saved groups and channels in Excel format.
    🔹 <b>Get Channels Database</b> — get a list of all saved channels in Excel format.
    🔹 <b>Get Groups Database (supergroups)</b> — get a list of all saved supergroups in Excel format.
    🔹 <b>Get Regular Chats Database (old-style groups)</b> — get a list of all saved regular chats (old-style groups) in Excel format.
    🔹 Choose a category for export

    🔸 Press <b>Back</b> to return to the main menu.

select_category_prompt =
    📌 Select a category for which you want to get a list of groups/channels:

action_cancelled =
    ❌ Cancelled.

invalid_category =
    ⚠️ Invalid category. Please select from the list.

category_empty =
    📭 No groups in the "{ $category }" category yet.

category_export_caption =
    ✅ Exported { $group_count } groups/channels for category:
    "{ $category }"

# === AI Search ===
searching_groups =
    🔍 Searching for groups and channels...

search_summary =
    ✅ <b>Search completed!</b>

    📊 Found and saved: <b>{ $groups_count }</b> groups/channels
    📁 Results sent in Excel file

    📍 <b>Activity indicators:</b>
    🟢 <b>active</b> — group is active (last message ≤ 30 days)
    🔴 <b>inactive</b> — group is inactive (messages > 30 days or none at all)
    ⚪ <b>unknown</b> — could not determine (Telegram limitations)

search_results_caption =
    📄 Search results for query: <b>{ $query }</b>

search_no_results =
    ❌ Unfortunately, nothing was found for your query. Try other keywords.

search_error =
    ❌ An error occurred during search. Please try again.

# === Global AI Search ===
global_search_no_terms =
    ❌ Enter at least one search term.

global_search_processing =
    🔍 Processing { $total } queries...

global_search_skipped =
    ⚠️ Skipped: '{ $term }' (no available accounts)

global_search_progress =
    🔍 Processed { $current }/{ $total }: { $successful } successful

global_search_results_caption =
    📄 Found { $total } groups from { $successful }/{ $total_queries } queries

global_search_no_results =
    ❌ Unfortunately, nothing was found. Try other keywords.

# === Group Connection ===
group_added =
    ✅ Group { $group } has been added for message forwarding.

group_already_added =
    ⚠️ This group has already been added.

group_add_error =
    ⚠️ Error adding group.

# === Group Deletion ===
delete_group_prompt =
    Enter the group/channel username in @username format to remove from tracking:

group_deleted =
    ✅ Group { $group } has been successfully removed from tracking.

group_not_found =
    ❌ Group @{ $group } not found in your tracking list.

clear_all_channels_empty =
    ℹ️ Your tracked groups and channels list is already empty.

clear_all_channels_confirm =
    ⚠️ Are you sure you want to remove <b>all</b> groups and channels from tracking?

    Currently in list: <b>{ $count }</b>

clear_all_channels_success =
    ✅ Tracking list cleared. Removed entries: { $count }

clear_all_channels_cancelled =
    ❌ List clearing cancelled.

confirm_btn = ✅ Yes, clear all

no_accounts =
    ❌ You have no connected accounts.

    Send a `.session` file or click "Connect Account" in the menu.

# === Keywords ===
no_keywords_entered =
    ⚠️ You haven't entered any keywords.

keywords_added_count =
    Keywords added: { $count }

keywords_already_added =
    Already added ({ $count })

keywords_add_errors =
    Errors adding

keywords_and_more =
    and { $count } more

keywords_and_more_errors =
    and { $count } more errors

keywords_summary =
    Summary

keywords_added =
    Added

keywords_skipped =
    Skipped (duplicates)

keywords_errors =
    Errors

# === Group Check ===
check_group_ask_url =
    📤 Enter the group link to check:

check_group_ask_keyword =
    🔍 Enter the keyword to search:

check_group_started =
    🔍 Starting group check...

check_group_new_message_with_link =
    📨 New message with keyword!

    📌 <b>{ $title }</b>
    📅 Date: { $msg_date }
    🔗 <a href="{ $message_link }">Go to message</a>

check_group_new_message_no_link =
    📨 New message with keyword!

    📌 <b>{ $title }</b>
    📅 Date: { $msg_date }

check_group_summary =
    ✅ Check completed!

    Messages found: { $count }
    Keyword: { $keyword }
    Matches: { $matched_count }

check_group_parse_error =
    ❌ Error parsing group. Please check the link and chat access.

# === Parser ===
target_group_not_found =
    ❌ Target group not found for user. Connect a group so I can forward messages found by your keywords.

no_channels_to_track =
    📭 You have no added channels to track.

too_many_channels =
    ⚠️ Found { $total } channels. This pass will only join the first { $limit } (anti-ban limit). The rest — on the next run.

channel_subscribed =
    ✅ Subscribed to { $channel }
    ⏳ Pause { $delay } sec. before the next one…

join_daily_limit =
    ⏸ Daily join limit reached ({ $limit }/day). Continue tomorrow or raise JOIN_DAILY_LIMIT.

join_batch_summary =
    📊 Joins this pass:
    • new: <b>{ $joined }</b>
    • already: <b>{ $already }</b>
    • errors: <b>{ $errors }</b>
    • deferred by limit: <b>{ $skipped }</b>

target_group_join_error =
    ❌ Account could not join the target group, check the connected group

target_group_not_configured =
    ❌ Target group not found for user. Connect a group.

target_group_fetch_error =
    ❌ Could not fetch target group. Check connection.

bot_listening =
    👂 Bot is listening for new messages.

    Keyword matches will be sent here, in this chat.

keyword_match_alert =
    📥 <b>New match</b>

    <b>Source:</b> { $chat_title }
    <b>Chat:</b> { $chat_username }
    <b>Author:</b> { $author }
    <b>Time:</b> { $message_time }
    <b>Link:</b> { $message_link }

    <b>Keyword:</b> <code>{ $matched_keyword }</code>
    <b>Why:</b> { $match_why }

    <b>Message text:</b>
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

alert_why_exact = exact phrase · mode “{ $mode }”
alert_why_tokens = words: { $tokens } · mode “{ $mode }”
alert_why_loose = partial: { $tokens } · mode “{ $mode }”

alert_time_value = { $datetime } ({ $tz })
alert_chat_id_only = id { $chat_id }
alert_chat_id_typed = id { $chat_id } ({ $chat_type })
alert_chat_type_channel = channel
alert_chat_type_supergroup = supergroup
alert_chat_type_group = group
alert_chat_type_user = private chat
alert_open_button = 🔗 Open
alert_mute_24h_button = 🔕 Mute 24h
alert_mute_ok = Channel id { $chat_id } muted for { $hours }h
alert_mute_invalid = Could not mute channel

alert_author_id = · id { $id }
alert_author_id_only = id { $id }
alert_author_unknown = — (channel / anonymous)
alert_author_signed = signed: { $name }
alert_author_channel = channel
alert_author_forward = forwarded from { $name }
alert_author_forward_entity = forwarded · { $author }
alert_author_forward_id = forwarded · id { $id }

message_link_unavailable = Link unavailable

tracking_not_active =
    ⚠️ Tracking is not started or already stopped.

tracking_already_active =
    ℹ️ Tracking is already running. Use the «Stop Tracking» button in the main menu.

tracking_stop_requested =
    🛑 Stop command sent. Tracking will be stopped within a few seconds.

tracking_restored =
    🔄 Tracking restored after service restart.

tracking_reconnected =
    🔄 Telegram connection restored — listening again.

tracking_reconnect_failed =
    ❌ Could not restore Telegram connection. Tracking stopped.
    Start again when the network is available.

tracking_failover_ok =
    🔄 Switched account: { $from_phone } → { $to_phone }. Still listening.

tracking_failover_failed =
    ❌ Could not reconnect or switch to a backup account.
    Add a second .session in «My parsing» → Account, or start again later.

tracking_not_subscribed_warn =
    ⚠️ Account is not in <b>{ $count }</b> channel(s) yet: { $preview }

    Listening to available ones now; will try to join in the background. Manual check: Channels → «Check subscriptions».

search_client_error =
    ❌ Could not connect an account for tracking.
    Check the .session or add a backup account in «My parsing» → Account.

search_no_available_accounts =
    ⚠️ No connected account for search.

    Connect your Telegram account via «🔐 Connect account» in settings.

# === Session ===
session_invalid =
    ⚠️ Account `{ $phone }` is no longer valid.
    Please reconnect the account.

account_fetch_error =
    ⚠️ An error occurred while fetching the account. Please try again later.

# === Account Checking ===
checking_accounts_start =
    Accounts to check: { $count }
checking_accounts_complete =
    ✅ Account checking completed

# === Category Assignment for AI ===
ai_category_select_method =
    🤖 <b>Select category assignment method:</b>

    ⚡️ <b>Fast (g4f.free)</b>
    • Free, no API keys
    • Sequential processing (slower)
    • Suitable for small volumes
    • May return inaccurate results

    🚀 <b>Powerful (Groq API)</b>
    • Requires Groq API key
    • Parallel processing in 10 threads (faster)
    • Suitable for large volumes
    • More accurate results

    Select a method:
ai_category_back =
    ↩️ Back to admin panel
ai_category_checking_models =
    🔍 Checking available models...
ai_category_model_selected =
    ✅ Selected model: { $model }
ai_category_select_from_keyboard =
    Please select a method from the keyboard below:
ai_category_all_have_categories =
    ✅ All groups already have categories!
ai_category_processing =
    🔄 Processing { $total } groups...
ai_category_done =
    ✅ <b>Done!</b>
ai_category_error =
    ❌ Error: { $error }
ai_category_stats_title =
    📊 <b>Category Statistics:</b>
ai_category_no_category_count =
    🗃️ Groups without category: { $count }
ai_category_run_ai =
    Press '🏷️ Assign Category' to start AI

# === Connect Account ===
connect_account_ask_session =
    📤 Send me Telethon session file(s) (must end with `.session`)

    You can send multiple files at once — the bot will process them in order.
    When done — press the "Back" button or send /start
connect_account_invalid_file =
    ❌ This is not a session file! Send a file with `.session` extension
connect_account_limit_reached =
    ⚠️ Limit reached: { $max } files at once.
    Process current files and send the rest later.
connect_account_file_queued =
    📥 File accepted: `{ $filename }`
    📊 In queue: { $total } file(s). Processing...
connect_account_success =
    ✅ <b>{ $filename }</b> — success!
    📱 { $phone } | 👤 { $name }
connect_account_failed =
    ❌ <b>{ $filename }</b> — failed validation
connect_account_error =
    ⚠️ <b>{ $filename }</b> — processing error
connect_account_processing_done =
    📊 <b>Processing completed!</b>

# === Language Detection ===
lang_detect_no_groups =
    ❌ No groups to process
lang_detect_starting =
    🚀 Starting processing of { $total } groups...
lang_detect_error =
    ❌ Error: { $error }
lang_detect_saving =
    💾 Saving { $count } results to DB...
lang_detect_complete =
    ✅ Processing completed!

    📊 Statistics:
    • Total: { $total }
    • AI detected: { $ai_success }
    • Saved to DB: { $db_success }
    • AI errors: { $ai_fail }
    • DB errors: { $db_fail }
    • Total errors: { $total_fail }

lang_detect_stats_title = Statistics
lang_detect_stats_total = Total
lang_detect_stats_ai_success = AI detected
lang_detect_stats_db_success = Saved to DB
lang_detect_stats_ai_fail = AI errors
lang_detect_stats_db_fail = DB errors
lang_detect_stats_total_fail = Total errors

# === Log File ===
log_file_caption =
    📄 Log file with errors.

# === connect_account.py ===
account_connected_free =
    ✅ Account successfully connected

no_free_accounts =
    ❌ No free accounts available. Please try again later or contact the administrator.

invalid_session_file =
    ❌ This is not a session file! Send a file with `.session` extension

session_file_received =
    📥 File received: `{ $filename }`

    🔍 Checking account...

session_connected_success =
    ✅ <b>{ $filename }</b> — successful!
    📱 { $phone } | 👤 { $name }
    💾 Saved to your personal database.

session_validation_failed =
    ❌ <b>{ $filename }</b> — validation failed.
    Please check that the session file is current and not used elsewhere.

session_check_error =
    ⚠️ An error occurred while checking the account. Please try again later.

# === handlers.py (groups) ===
only_txt_files_supported =
    ⚠️ Only .txt files are supported.

empty_file_no_usernames =
    ⚠️ File is empty or contains no usernames.

groups_upload_summary =
    ✅ Added: { $added }
    ⚠️ Already exists: { $skipped }
    ❌ Errors: { $errors }

# === admin.py ===
admin_found_accounts =
    🔍 Found accounts: { $count }

admin_db_actualization_start =
    🔄 Starting actualization of { $total } groups...

admin_using_account =
    📱 Using account: { $account }

admin_account_error =
    ❌ Account error { $account }: { $error }

admin_critical_error =
    ❌ Critical error: { $error }

# === Question Export ===
no_questions_in_db =
    📭 There are no questions in the database.

questions_export_caption =
    📦 Export of questions and answers.

export_error =
    ❌ An error occurred during export: { $error }

# === Buttons ===
launch_tracking_button = 🚀 Start Tracking
check_group_for_keywords_button = 🔍 Check Group for Keywords
ai_search_button = ✨ AI Search
get_database_button = 📥 Get Database
instruction_button = 📖 Instructions
settings_button = ⚙️ Settings
admin_panel_button = 🛡️ Admin Panel
admin_tracking_button = 📡 Tracking
admin_tracking_message =
    📡 <b>Active tracking</b>: { $count }

    Matches last hour: <b>{ $matches }</b> · FloodWaits last hour: <b>{ $floods }</b>

    { $rows }

    ▶ — running in this process · ○ — Redis mark only
admin_tracking_empty =
    📡 <b>Active tracking</b>: 0

    Matches last hour: <b>{ $matches }</b> · FloodWaits last hour: <b>{ $floods }</b>

    Nobody is parsing right now.
admin_tracking_row =
    • <b>{ $user }</b>
    keywords: { $keywords } · channels: { $channels_enabled }/{ $channels_total }
    { $local } local · client { $client } · uptime { $uptime }
admin_tracking_stop_button = 🛑 Stop { $user_id }
admin_tracking_refresh_button = 🔄 Refresh
admin_tracking_refreshed = Refreshed
admin_tracking_stopped = Stopped { $user_id }
admin_tracking_stop_invalid = Invalid user_id
admin_tracking_stop_error = Error: { $error }
get_log_file_button = 📄 Get Log File
update_database_button = 🔄 Update Database
export_questions_button = Export Questions
assign_category_button = 🏷️ Assign Category
check_accounts_button = ✅ Check Accounts
assign_language_button = 🌐 Assign Language
connect_account_button = 🔐 Connect Account
back_button = ⬅️ Back
fast_method_button = ⚡️ Fast (g4f.free)
powerful_method_openrouter_button = 🚀 Powerful (Openrouter API)
powerful_method_groq_button = 🚀 Powerful (GROQ API)
all_database_button = 📥 All Database
channels_database_button = 📥 Channels Database
groups_database_button = 📥 Groups Database
select_category_button = 📂 Select Category
investments_button = investments
finance_and_personal_budget_button = finance and personal budget
crypto_and_blockchain_button = crypto and blockchain
business_and_entrepreneurship_button = business and entrepreneurship
marketing_and_promotion_button = marketing and promotion
tech_and_it_button = technologies and it
education_and_self_development_button = education and self-development
work_and_career_button = work and career
real_estate_button = real estate
health_and_medicine_button = health and medicine
travel_button = travel
auto_and_transport_button = auto and transport
shopping_and_discounts_button = shopping and discounts
entertainment_and_leisure_button = entertainment and leisure
politics_and_society_button = politics and society
science_and_research_button = science and research
sports_and_fitness_button = sports and fitness
cooking_and_food_button = cooking and food
fashion_and_beauty_button = fashion and beauty
hobbies_and_creativity_button = hobbies and creativity
russian_language_button = 🇷🇺 Russian
english_language_button = 🇬🇧 English
global_ai_search_button = 🌐 Global AI Search
stop_tracking_button = 🛑 Stop Tracking
update_list_button = 🔁 Update List
enter_keyword_button = 🔍 Enter Keyword
delete_group_from_tracking_button = 🗑️ Delete Group from Tracking
clear_all_tracked_channels_button = 🗑️ Clear All Channels
keywords_list_button = 🔍 Keywords List
tracking_links_button = 🌐 Tracking Links
connect_group_for_messages_button = 📤 Group forwarding (soon)
change_language_button = 🌐 Change Language
quiet_hours_button = 🌙 Quiet hours
quiet_hours_message =
    🌙 <b>Quiet hours</b>

    Status: <b>{ $status }</b>
    Window: <code>{ $window }</code>

    During this time matches are saved to Leads, but chat notifications are paused.
quiet_hours_status_on = on
quiet_hours_status_off = off
quiet_hours_enable_button = ✅ Enable
quiet_hours_disable_button = ⏹ Disable
quiet_hours_preset_2308 = 23:00–08:00
quiet_hours_preset_0007 = 00:00–07:00
quiet_hours_preset_2209 = 22:00–09:00
quiet_hours_toggled_on = Quiet hours enabled
quiet_hours_toggled_off = Quiet hours disabled
quiet_hours_preset_saved = Window: { $window }
digest_button = 📦 Digest
digest_settings_message =
    📦 <b>Match digest</b>

    Status: <b>{ $status }</b>
    Interval: <b>{ $interval }</b> min

    Instead of every alert, the bot batches matches and sends one summary.
    Leads are still saved immediately.
digest_status_on = on
digest_status_off = off
digest_enable_button = ✅ Enable
digest_disable_button = ⏹ Disable
digest_interval_15 = 15 min
digest_interval_30 = 30 min
digest_interval_60 = 60 min
digest_flush_now_button = 📤 Send now
digest_toggled_on = Digest enabled
digest_toggled_off = Digest disabled
digest_flushed_on_disable = Digest off, sent: { $count }
digest_interval_saved = Interval: { $interval } min
digest_flush_ok = Matches sent: { $count }
digest_flush_empty = Buffer is empty
digest_message =
    📦 <b>Match digest</b> ({ $count })

    { $items }
    { $more }
digest_and_more =
    …and { $count } more
chat_filter_button = 📢 Chat types
chat_filter_message =
    📢 <b>Filter by chat type</b>

    Current: <b>{ $current }</b>

    • All — channels and groups/discussions
    • Channels only — channel posts (no discussion comments)
    • Groups only — supergroups and discussions
chat_filter_all_name = all
chat_filter_channels_name = channels only
chat_filter_groups_name = groups only
chat_filter_all_button = All chats
chat_filter_channels_button = Channels only
chat_filter_groups_button = Groups only
chat_filter_saved = Filter: { $mode }
author_filter_button = 👤 Who writes
author_filter_message =
    👤 <b>Author filter</b>

    Current: <b>{ $current }</b>

    • <b>Humans only</b> — real users (not channel posts or bots)
    • <b>Humans + anonymous</b> — plus messages without a clear author
    • <b>All</b> — including channel posts, channel forwards, and bots
author_filter_humans_name = humans only
author_filter_humans_anon_name = humans + anonymous
author_filter_all_name = all
author_filter_humans_button = Humans only
author_filter_humans_anon_button = Humans + anonymous
author_filter_all_button = All authors
author_filter_saved = Authors: { $mode }
alert_template_button = 📝 Alert template
alert_template_message =
    📝 <b>Alert template</b>

    Current: <b>{ $current }</b>

    • Full — all fields (source, chat, author, time, link, keyword, why, text)
    • Compact — keyword, source, author, time, link, why and text
    • Minimal — keyword, why, link and text
alert_template_full_name = full
alert_template_compact_name = compact
alert_template_minimal_name = minimal
alert_template_full_button = Full
alert_template_compact_button = Compact
alert_template_minimal_button = Minimal
alert_template_saved = Template: { $mode }

alert_destination_button = 📬 Alert destination
alert_destination_message =
    📬 <b>Where to send alerts</b>

    DM: <b>{ $dm_status }</b>
    Group: <b>{ $group_status }</b>

    { $group_info }
alert_destination_dm_button = Direct messages
alert_destination_group_button = Group
alert_destination_on = on
alert_destination_off = off
alert_destination_group_unbound = No group bound — enable Group and bind a chat.
alert_destination_group_bound = Bound: chat <code>{ $chat_id }</code>
alert_destination_group_bound_topic = Bound: chat <code>{ $chat_id }</code>, topic <code>{ $thread_id }</code>
alert_destination_need_one_channel = At least one delivery channel is required (DM or group).
alert_destination_bind_button = 🔗 Bind group
alert_destination_rebind_button = 🔄 Change group/topic
alert_destination_unbind_button = ✂️ Unbind group
alert_destination_unbound = Group unbound
alert_destination_bind_instructions =
    <b>Bind a group for alerts</b>

    1. Add the bot to a supergroup (for a topic — add it to that topic).
    2. In the group or <b>in the target topic</b>, run:

    <code>{ $command }</code>

    Token is valid for { $ttl_min } min. Only a group admin can run the command.
alert_destination_bind_ready_button = 🔄 New token
alert_destination_bind_token_required =
    A token from bot settings is required.

    First: Settings → Alert destination → Bind group.
    Then in the group/topic: <code>/bind_alerts TOKEN</code>
alert_destination_bind_bad_token = Invalid or expired token. Get a new one in bot settings.
alert_destination_bind_not_admin = Only a chat administrator or creator can bind the group.
alert_destination_bind_chat_taken = This chat/topic is already bound to another bot account.
alert_destination_bind_success = ✅ Group bound: { $group_info }
alert_destination_bind_success_short = ✅ Bound: { $group_info }
alert_destination_test_message = ✅ <b>Delivery test</b>\n\nAlerts to this group are configured.
alert_destination_group_not_bound = Group is enabled but no chat is bound. Open settings and bind a group.
alert_group_delivery_failed =
    ⚠️ Could not deliver alert to the group (DM was sent).
    { $error }
alert_group_delivery_failed_only =
    ⚠️ Could not deliver alert to the group. Check that the bot is in the chat and binding is valid.
    { $error }

leads_group_help =
    <b>Leads export in group</b>

    <code>/leads</code> — all leads
    <code>/leads 2026-07-01</code> — single day
    <code>/leads 2026-07-01 2026-07-17</code> — date range

    Dates use bot timezone (TIMEZONE). Owner only.
leads_group_bad_dates = Invalid date format. Example: <code>/leads 2026-07-01</code> or <code>/leads 2026-07-01 2026-07-17</code>
leads_group_not_bound =
    Alert group is not bound.

    In DM: Settings → Alert destination → Bind group → <code>/bind_alerts TOKEN</code> in this topic.
leads_group_disabled = Group delivery is off. Enable “Group” in bot settings.
leads_group_wrong_chat =
    This group is not bound to your account. Bound chat: <code>{ $chat_id }</code>
leads_group_wrong_topic =
    Command works only in the bound topic (thread <code>{ $thread_id }</code>).
    Run <code>/bind_alerts TOKEN</code> in the target topic.
group_chat_allowed_command_failed =
    Command failed. Check group binding (/bind_alerts TOKEN) and that the bot is in the chat.
leads_group_export_day_caption = Leads for { $date }: { $count }
leads_group_export_range_caption = Leads { $date_from } — { $date_to }: { $count }

stopwords_menu_button = 🚫 Stop words
stopwords_menu_message =
    🚫 <b>Stop words</b>

    Total: <b>{ $count }</b>

    If a message contains a stop word, the alert is skipped (even if a keyword matched).
stopwords_add_button = ➕ Add
stopwords_view_list_button = 📋 List
stopwords_add_prompt =
    📥 Send stop words as text or a .txt file (one per line or comma-separated).

    Example:
    spam
    ads
    buy subscription
stopwords_empty_input = Empty input — add at least one word.
stopwords_added_count = Stop words added: { $count }
stopwords_already_added = Already existed ({ $count })
stopwords_add_errors = Errors while adding
stopwords_list_empty = Stop-word list is empty.
stopwords_list_title = Stop words: { $count } · page { $page }
stopwords_deleted = Deleted: { $word }
stopwords_missing = Stop word not found
connect_free_account_button = 🔐 Connect Free Account

# get_dada.py
keywords_export_caption = 📋 Keywords export. Total records: { $count }
no_keywords_found = 📭 You have no saved keywords.
tracking_links_export_caption = 🔗 Tracking links export. Total records: { $count }
no_tracking_links_found = 📭 You have no tracking links.
excel_header_number = #
excel_header_keyword = Keyword
excel_header_username = Channel/Group Username

# pars_ai.py
ai_search_button_user = 🤖 AI Search
excel_filename_all_db = All_Database.xlsx
excel_filename_channels_db = Channels_Database.xlsx
excel_filename_groups_db = Groups_Database.xlsx
excel_sheet_name_search_results = Search Results
excel_header_id = ID (Hash)
excel_header_name = Name
excel_header_description = Description
excel_header_participants = Participants
excel_header_category = Category
excel_header_type = Type
excel_header_language = Language
excel_header_activity = Activity
excel_header_link = Link
excel_header_date_added = Date Added
excel_sheet_name_groups = Groups
excel_filename_groups_by_category = groups_{ $category }.xlsx
excel_header_group_name = Name
excel_header_group_description = Description
excel_header_group_type = Type
excel_header_group_participants = Participants
excel_header_group_link = Link
excel_filename_telegram_groups = telegram_groups_{ $timestamp }.xlsx

# post_doc.py
instruction_question_prompt = 🤖 <b>You can ask me any question about using the bot, and I will answer you!</b>
# post_doc.py
ai_support_assistant_system_prompt = You are a qualified support assistant for the AutoParseAlertBot Telegram bot. Your task is to answer user questions based STRICTLY on the provided knowledge base. If the answer is not in the knowledge base, politely inform the user that you do not have this information and advise them to contact support. Respond in the user's language. Use HTML markup for formatting the answer.

# language_detection.py
lang_detect_summary = ✅ Processing completed!

    📊 Statistics:
    • Total: { $total }
    • AI detected: { $ai_success }
    • Saved to DB: { $db_success }
    • AI errors: { $ai_fail }
    • DB errors: { $db_fail }
    • Total errors: { $total_fail }
name_prompt = Name
description_prompt = Description
no_data_prompt = No data
ai_lang_detect_prompt =
    Determine the main language of the text or community description.
    Respond STRICTLY with a single word — the language code in ISO 639-1 format (two-letter code).
    Examples of correct answers: ru, en, es, zh, ar, hi, ja, ko, fr, de, pt, it, nl, sv, pl, tr, vi, th, id, fa, he, uk, cs, el, ro, hu, fi, da, no, sk, bg, hr, sr, sl, et, lv, lt, mk, sq, mt, cy, eu, gl, ga, is, ms, sw, tl, ur, bn, ta, te, mr, gu, kn, ml, si, km, lo, my, am, hy, ka, az, uz, kk, ky, tg, tk, mn, ps, ku, sd, ne, si, lo, km, my, dz, bo, ug, yi, ha, yo, ig, zu, xh, st, tn, ts, ve, nr, ss, ch, rw, rn, mg, ln, kg, sw, tn.
    If the language cannot be determined unambiguously or the text contains a mixture of languages without a dominant one — answer: unknown.
    DO NOT add any explanations, punctuation, spaces, or additional text. Only the language code or 'unknown'.
    
    Text for analysis:
    { $user_input }

# checking_group_for_ai.py
get_groups_without_category_message = 📊 <b>Category Statistics:</b>

    🗃️ Groups without category: { $count }

    Press '🏷️ Assign Category' to start AI


# === Download limits and Stars ===
download_free_success = 📥 Exporting database (1 free download per day). Starting download...
download_cooldown_message =
    ⚠️ You have already downloaded the database in the last 24 hours.
    Next free download will be available in <b>{ $time }</b>.
    
    You can download the database now for 5 ⭐.
    Your star balance in the bot: <b>{ $stars }</b> ⭐
pay_from_balance_btn = 🪙 Deduct 5 ⭐ from balance
pay_direct_btn = ⭐ Pay 5 ⭐ directly
cancel_btn = ❌ Cancel
download_paid_success = ✅ Payment/deduction of 5 ⭐ successful. Starting database download...
download_insufficient_stars = ❌ Insufficient stars on your balance.
stars_topup_success = 🎉 Balance successfully topped up by { $amount } ⭐! Your current balance: { $balance } ⭐.
stars_added_admin = ⭐ Administrator credited { $amount } ⭐ to you. Current balance: { $balance } ⭐.
topup_stars_button = 💳 Top up Stars
stars_balance_msg = 👤 <b>Your Star Profile:</b>\n\nBalance: <b>{ $stars }</b> ⭐\n\nHere you can top up your Telegram Stars balance for paid database downloads.
stars_invoice_title = Top up Star Balance
stars_invoice_desc = Purchase of { $amount } Telegram Stars for use in the bot
stars_invoice_dl_title = Database Download
stars_invoice_dl_desc = One-time database download bypassing the daily limit
excel_filename_category_db = category_database.xlsx
export_category_caption = 📂 Database by category "{ $category }". Total records: { $total_records }.
generating_database_wait = ⏳ Generating database file, this might take some time. Please wait...



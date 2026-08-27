"""Two-locale string table. English is mandatory (CHPP requirement); Bulgarian
is the second locale. Skill-level denominations follow the official CHPP table
(CHPP_TECHNICAL.md §8) — in production, prefer refreshing them via the
`translations` file."""
from __future__ import annotations

LEVEL_NAMES = {
    "en": [
        "disastrous", "wretched", "poor", "weak", "inadequate", "passable", "solid",
        "excellent", "formidable", "outstanding", "brilliant", "magnificent",
        "world class", "supernatural", "titanic", "extra-terrestrial", "mythical",
        "magical", "utopian", "divine",
    ],
    "bg": [
        "бедствено", "ужасно", "лошо", "слабо", "посредствено", "задоволително",
        "стабилно", "отлично", "прекрасно", "изключително", "брилянтно",
        "великолепно", "световна класа", "свръхестествено", "титанично",
        "извънземно", "митично", "вълшебно", "легендарно", "божествено",
    ],
}

STRINGS: dict[str, dict[str, str]] = {
    # --- chrome ---
    "nav_dashboard": {"en": "Dashboard", "bg": "Табло"},
    "nav_players": {"en": "Players", "bg": "Играчи"},
    "nav_trainers": {"en": "Trainers", "bg": "Трениращи"},
    "nav_market": {"en": "Market pipeline", "bg": "Пазарен поток"},
    "nav_my_team": {"en": "My team", "bg": "Моят отбор"},
    "nav_admin": {"en": "Admin", "bg": "Админ"},
    "nav_logout": {"en": "Log out", "bg": "Изход"},
    "mock_banner": {
        "en": "MOCK MODE — no requests reach hattrick.org. Do not connect real credentials before CHPP approval.",
        "bg": "ТЕСТОВ РЕЖИМ — никакви заявки не стигат до hattrick.org. Не свързвайте реални данни преди CHPP одобрение.",
    },
    "footer_note": {
        "en": "HT Scout Bridge — NT scouting & training coordination. Read-only CHPP; messages are always sent manually in Hattrick.",
        "bg": "HT Scout Bridge — координация между скаути и трениращи. Само четене през CHPP; съобщенията винаги се пращат ръчно в Hattrick.",
    },

    # --- roles ---
    "role_head_coach": {"en": "Head coach", "bg": "Селекционер"},
    "role_assistant_coach": {"en": "Assistant coach", "bg": "Помощник-селекционер"},
    "role_master_scout": {"en": "Master scout", "bg": "Главен скаут"},
    "role_position_scout": {"en": "Position scout", "bg": "Скаут"},
    "role_trainer": {"en": "Trainer", "bg": "Трениращ"},

    # --- login ---
    "login_title": {"en": "Sign in", "bg": "Вход"},
    "login_eyebrow": {"en": "National team · scouts & trainers", "bg": "Национален отбор · скаути и трениращи"},
    "login_headline": {"en": "Every talent finds its trainer.", "bg": "Всеки талант намира своя трениращ."},
    "login_feat1_t": {"en": "Capacity at a glance", "bg": "Капацитетът на един поглед"},
    "login_feat1_d": {
        "en": "Which trainer has a slot, the budget and the right training — instead of forty HT-mails.",
        "bg": "Кой трениращ има слот, бюджет и правилната тренировка — вместо четиридесет HT-mail-а.",
    },
    "login_feat2_t": {"en": "Market pipeline", "bg": "Пазарен поток"},
    "login_feat2_d": {
        "en": "Scouts announce who is coming to market; trainers raise a hand with a bid limit.",
        "bg": "Скаутите обявяват кой излиза на пазара; трениращите заявяват интерес с лимит за наддаване.",
    },
    "login_feat3_t": {"en": "Read-only CHPP", "bg": "Само четене през CHPP"},
    "login_feat3_d": {
        "en": "Official Hattrick API access, no passwords stored. Messages are always sent manually in Hattrick.",
        "bg": "Официален достъп през Hattrick API, без съхранявани пароли. Съобщенията винаги се пращат ръчно в Hattrick.",
    },
    "login_note": {
        "en": "Signing in only identifies you. Your team data is read after you explicitly connect it, and you can revoke access at any time.",
        "bg": "Входът само те идентифицира. Данните за отбора ти се четат едва след като изрично го свържеш, и можеш да прекратиш достъпа по всяко време.",
    },
    "login_intro": {
        "en": "Connect with your Hattrick account via CHPP OAuth. The app only ever reads data — it never changes anything in your team.",
        "bg": "Свържете се с вашия Hattrick акаунт през CHPP OAuth. Приложението само чете данни — никога не променя нищо по отбора ви.",
    },
    "login_with_ht": {"en": "Connect with Hattrick", "bg": "Свързване с Hattrick"},
    "login_oauth_missing": {
        "en": "Live CHPP login is disabled (mock mode or missing consumer key). Use a demo persona below.",
        "bg": "Истинският CHPP вход е изключен (тестов режим или липсващ ключ). Използвайте демо потребител отдолу.",
    },
    "login_mock_title": {"en": "Demo personas", "bg": "Демо потребители"},
    "login_mock_hint": {
        "en": "Pick a role to explore the flows: scouts search capacity, trainers declare slots and raise interest.",
        "bg": "Изберете роля, за да разгледате процесите: скаутите търсят капацитет, трениращите декларират слотове и заявяват интерес.",
    },
    "login_as": {"en": "Sign in as", "bg": "Влез като"},

    # --- dashboard ---
    "dash_title": {"en": "Dashboard", "bg": "Табло"},
    "dash_trainers_connected": {"en": "connected trainers", "bg": "свързани трениращи"},
    "dash_open_slots": {"en": "declared open slots", "bg": "декларирани свободни слота"},
    "dash_players_tracked": {"en": "tracked players", "bg": "следени играчи"},
    "dash_pipeline": {"en": "in market pipeline", "bg": "в пазарния поток"},
    "dash_open_interests": {"en": "Open trainer interests", "bg": "Чакащи заявки от трениращи"},
    "dash_my_claims": {"en": "My claimed players", "bg": "Моите поети играчи"},
    "dash_my_declarations": {"en": "My declarations", "bg": "Моите декларации"},
    "dash_my_interests": {"en": "My interests", "bg": "Моите заявки"},
    "dash_expiring_soon": {"en": "expires soon", "bg": "изтича скоро"},
    "dash_none": {"en": "Nothing here yet.", "bg": "Все още няма нищо."},

    # --- common ---
    "save": {"en": "Save", "bg": "Запази"},
    "cancel": {"en": "Cancel", "bg": "Отказ"},
    "actions": {"en": "Actions", "bg": "Действия"},
    "status": {"en": "Status", "bg": "Статус"},
    "created": {"en": "Created", "bg": "Създадено"},
    "notes": {"en": "Notes", "bg": "Бележки"},
    "name": {"en": "Name", "bg": "Име"},
    "age": {"en": "Age", "bg": "Възраст"},
    "view": {"en": "View", "bg": "Виж"},
    "price_est": {"en": "Est. price", "bg": "Очаквана цена"},
    "coach_level": {"en": "Coach", "bg": "Треньор"},
    "sync_now": {"en": "Refresh from CHPP", "bg": "Обнови от CHPP"},
    "renew": {"en": "Renew", "bg": "Поднови"},
    "withdraw": {"en": "Withdraw", "bg": "Оттегли"},
    "compose_mail": {"en": "Write HT-mail", "bg": "Пиши HT-mail"},
    "hattrick_page": {"en": "Hattrick page", "bg": "Страница в Hattrick"},

    # --- skills / specialties / statuses ---
    # Bulgarian labels follow the official in-game terminology.
    "skill_goalkeeping": {"en": "Goalkeeping", "bg": "Пазене"},
    "skill_defending": {"en": "Defending", "bg": "Защита"},
    "skill_playmaking": {"en": "Playmaking", "bg": "Разиграване"},
    "skill_winger": {"en": "Winger", "bg": "Крило"},
    "skill_passing": {"en": "Passing", "bg": "Подаване"},
    "skill_scoring": {"en": "Scoring", "bg": "Голов нюх"},
    "skill_set_pieces": {"en": "Set pieces", "bg": "Статични положения"},
    "skill_other": {"en": "Other / general", "bg": "Друго / общо"},
    "skill_any": {"en": "Any skill", "bg": "Без значение"},
    "spec_id_0": {"en": "—", "bg": "—"},
    "spec_id_1": {"en": "Technical", "bg": "Техничен"},
    "spec_id_2": {"en": "Quick", "bg": "Бърз"},
    "spec_id_3": {"en": "Powerful", "bg": "Сила"},
    "spec_id_4": {"en": "Unpredictable", "bg": "Непредвидим"},
    "spec_id_5": {"en": "Head specialist", "bg": "Игра с глава"},
    "spec_id_6": {"en": "Regainer", "bg": "Възстановяващ се"},
    "spec_id_7": {"en": "(unused)", "bg": "(неизползвано)"},
    "spec_id_8": {"en": "Support", "bg": "Подкрепящ"},
    "status_watching": {"en": "Watching", "bg": "Наблюдаван"},
    "status_planned": {"en": "Planned for market", "bg": "Планиран за пазара"},
    "status_listed": {"en": "Listed now", "bg": "Обявен сега"},
    "status_transferred": {"en": "Transferred", "bg": "Трансфериран"},
    "squad_senior": {"en": "Men's NT", "bg": "Мъже"},
    "squad_u21": {"en": "U21", "bg": "U21"},
    "timing_immediate": {"en": "Immediately", "bg": "Веднага"},
    "timing_after_cycle": {"en": "After current cycle", "bg": "След текущия цикъл"},
    "timing_after_age": {"en": "After age threshold", "bg": "След определена възраст"},
    "int_open": {"en": "Pending", "bg": "Чакаща"},
    "int_accepted": {"en": "Accepted", "bg": "Приета"},
    "int_declined": {"en": "Declined", "bg": "Отказана"},
    "int_withdrawn": {"en": "Withdrawn", "bg": "Оттеглена"},
    "decl_active": {"en": "Active", "bg": "Активна"},
    "decl_expired": {"en": "Expired", "bg": "Изтекла"},
    "decl_withdrawn": {"en": "Withdrawn", "bg": "Оттеглена"},
    "decl_valid_until": {"en": "valid until", "bg": "валидна до"},

    # --- budget bands ---
    "band_0": {"en": "under 500k", "bg": "под 500 хил."},
    "band_1": {"en": "500k – 2M", "bg": "500 хил. – 2 млн."},
    "band_2": {"en": "2M – 5M", "bg": "2 – 5 млн."},
    "band_3": {"en": "5M – 10M", "bg": "5 – 10 млн."},
    "band_4": {"en": "over 10M", "bg": "над 10 млн."},
    "band_unknown": {"en": "unknown", "bg": "неизвестен"},

    # --- trainers registry ---
    "trainers_title": {"en": "Trainer capacity registry", "bg": "Регистър на капацитета на трениращите"},
    "filter_training_type": {"en": "Training type", "bg": "Тип тренировка"},
    "filter_only_free": {"en": "Only with declared slots", "bg": "Само с декларирани слотове"},
    "filter_min_budget": {"en": "Min budget", "bg": "Мин. бюджет"},
    "filter_slot_skill": {"en": "Declared slot for", "bg": "Деклариран слот за"},
    "filter_timing": {"en": "Timing", "bg": "Кога"},
    "decl_selling": {"en": "selling: {name}", "bg": "продава: {name}"},
    "filter_include_stale": {"en": "Include inactive/bots", "bg": "Включи неактивни/ботове"},
    "filter_apply": {"en": "Apply", "bg": "Приложи"},
    "th_trainer": {"en": "Trainer", "bg": "Трениращ"},
    "th_training": {"en": "Training", "bg": "Тренировка"},
    "th_squad_occupancy": {"en": "Occupancy", "bg": "Заетост"},
    "th_budget": {"en": "Budget", "bg": "Бюджет"},
    "th_slots": {"en": "Declared slots", "bg": "Декларирани слотове"},
    "th_last_login": {"en": "Last login", "bg": "Последен вход"},
    "occupancy_line": {"en": "{trained} in training / {total} squad", "bg": "{trained} тренирани / {total} в състава"},
    "slot_summary": {"en": "{n} active", "bg": "{n} активни"},
    "slots_none": {"en": "none", "bg": "няма"},

    # --- players registry ---
    "players_title": {"en": "Player registry", "bg": "Регистър на играчите"},
    "players_add": {"en": "Add player", "bg": "Добави играч"},
    "filter_status": {"en": "Market status", "bg": "Пазарен статус"},
    "filter_squad": {"en": "Squad", "bg": "Гарнитура"},
    "filter_skill": {"en": "Target skill", "bg": "Целево умение"},
    "th_player": {"en": "Player", "bg": "Играч"},
    "th_target": {"en": "Target skill", "bg": "Целево умение"},
    "th_status": {"en": "Status", "bg": "Статус"},
    "th_claim": {"en": "Handled by", "bg": "Поет от"},
    "unclaimed": {"en": "unclaimed", "bg": "свободен"},
    "interests_n": {"en": "{n} pending", "bg": "{n} чакащи"},

    # --- player add/edit ---
    "player_new_title": {"en": "Add player to registry", "bg": "Добавяне на играч в регистъра"},
    "help_public_autofill": {
        "en": "Enter the Hattrick player ID — public data (age, TSI, owner, transfer status) fills in automatically via CHPP.",
        "bg": "Въведете Hattrick ID на играча — публичните данни (възраст, TSI, собственик, трансферен статус) се попълват автоматично през CHPP.",
    },
    "f_ht_player_id": {"en": "Hattrick player ID", "bg": "Hattrick ID на играча"},
    "f_age_years": {"en": "Age (years)", "bg": "Възраст (години)"},
    "f_age_days": {"en": "Age (days)", "bg": "Възраст (дни)"},
    "f_specialty": {"en": "Specialty", "bg": "Специалитет"},
    "skills_title": {"en": "Current skills", "bg": "Текущи умения"},
    "skills_hint": {
        "en": "Skills are visible to the owner only in CHPP — enter what the current manager shared (1–20, leave blank if unknown).",
        "bg": "Уменията се виждат само от собственика в CHPP — въведете каквото е споделил текущият мениджър (1–20, оставете празно, ако не знаете).",
    },
    "skill_stamina": {"en": "Stamina", "bg": "Издръжливост"},
    "f_name_opt": {"en": "Name (optional, auto-filled)", "bg": "Име (по избор, попълва се автоматично)"},
    "f_squad": {"en": "National squad", "bg": "Гарнитура"},
    "f_target_skill": {"en": "Target training skill", "bg": "Целево умение за трениране"},
    "f_est_price": {"en": "Estimated price", "bg": "Очаквана цена"},
    "f_market_status": {"en": "Market status", "bg": "Пазарен статус"},
    "f_expected_listing": {"en": "Expected listing date", "bg": "Очаквана дата на обявяване"},
    "f_notes": {"en": "Scout notes", "bg": "Бележки на скаута"},
    "submit_add": {"en": "Add player", "bg": "Добави играча"},

    # --- player detail ---
    "pd_public_data": {"en": "Public data (CHPP)", "bg": "Публични данни (CHPP)"},
    "pd_age": {"en": "Age", "bg": "Възраст"},
    "pd_salary": {"en": "Salary", "bg": "Заплата"},
    "pd_specialty": {"en": "Specialty", "bg": "Специалитет"},
    "pd_owner": {"en": "Current club", "bg": "Настоящ клуб"},
    "pd_caps": {"en": "Caps", "bg": "Мачове за националния"},
    "pd_nt": {"en": "National team", "bg": "Национален отбор"},
    "pd_asking_price": {"en": "Asking price", "bg": "Начална цена"},
    "pd_deadline": {"en": "Deadline", "bg": "Краен срок"},
    "pd_last_sync": {"en": "Last refresh", "bg": "Последно обновяване"},
    "pd_scout_fields": {"en": "Scout assessment", "bg": "Оценка на скаута"},
    "pd_claim_title": {"en": "Claim", "bg": "Поемане"},
    "pd_claim_btn": {"en": "Claim this player", "bg": "Поеми този играч"},
    "pd_release_btn": {"en": "Release claim", "bg": "Освободи"},
    "pd_claimed_by": {"en": "Handled by", "bg": "Поет от"},
    "pd_interests_title": {"en": "Trainer interests", "bg": "Заявки от трениращи"},
    "pd_no_interests": {"en": "No trainer has raised a hand yet.", "bg": "Все още никой трениращ не е заявил интерес."},
    "pd_accept": {"en": "Accept", "bg": "Приеми"},
    "pd_decline": {"en": "Decline", "bg": "Откажи"},
    "pd_matching_title": {"en": "Matching trainers", "bg": "Подходящи трениращи"},
    "pd_score": {"en": "Score", "bg": "Оценка"},
    "pd_draft_toggle": {"en": "Show message draft", "bg": "Покажи чернова на съобщение"},
    "pd_copy_hint": {
        "en": "Hattrick's mail form only pre-fills the recipient — copy the subject and message here, open the compose link and paste. Sending is always manual, one message at a time.",
        "bg": "Формата на Hattrick попълва само получателя — копирайте темата и текста оттук, отворете линка и поставете. Изпращането е винаги ръчно, по едно съобщение.",
    },
    "copy_subject": {"en": "Copy subject", "bg": "Копирай темата"},
    "copy_message": {"en": "Copy message", "bg": "Копирай текста"},
    "copied": {"en": "Copied ✓", "bg": "Копирано ✓"},
    "pd_interest_title": {"en": "Take this player", "bg": "Вземи този играч"},
    "pd_interest_btn": {"en": "I want to train him", "bg": "Искам да го тренирам"},
    "pd_interest_note_ph": {"en": "Optional note to the scouts…", "bg": "Бележка към скаутите (по избор)…"},
    "pd_my_interest_status": {"en": "Your interest", "bg": "Вашата заявка"},
    "pd_contact_scout": {"en": "write to the scout", "bg": "пиши на скаута"},

    # --- training plan ---
    "plan_title": {"en": "Training plan", "bg": "Тренировъчен план"},
    "plan_hint": {
        "en": "What the buying trainer should train, step by step — trainers see this in the market pipeline and in the message draft.",
        "bg": "Какво трябва да тренира купувачът, стъпка по стъпка — трениращите го виждат в пазарния поток и в черновата на съобщението.",
    },
    "plan_col_skill": {"en": "Training", "bg": "Тренировка"},
    "plan_col_weeks": {"en": "≈ weeks", "bg": "≈ седмици"},
    "plan_col_stamina": {"en": "Stamina %", "bg": "Издръжливост %"},
    "plan_add": {"en": "Add step", "bg": "Добави ред"},
    "plan_none": {"en": "No plan yet.", "bg": "Още няма план."},
    "plan_weeks_short": {"en": "wk", "bg": "седм."},
    "delete": {"en": "Remove", "bg": "Премахни"},

    # --- comments ---
    "comments_title": {"en": "Comments", "bg": "Коментари"},
    "comments_none": {"en": "No comments yet — start the discussion.", "bg": "Още няма коментари — започнете дискусията."},
    "comment_placeholder": {"en": "Write a comment…", "bg": "Напишете коментар…"},
    "comment_submit": {"en": "Post", "bg": "Публикувай"},
    "comment_reply": {"en": "Reply", "bg": "Отговори"},
    "comment_write_mail": {"en": "HT-mail about this comment", "bg": "HT-mail за този коментар"},
    "comment_mail_hint": {
        "en": "The [playerid=…] code becomes a clickable player link inside HT-mail. Copy subject and message, open the compose link and paste.",
        "bg": "Кодът [playerid=…] става кликаем линк към играча в HT-mail. Копирайте темата и текста, отворете линка и поставете.",
    },
    "comment_mail_body": {
        "en": (
            "Hi {author},\n\n"
            "About your comment on [playerid={playerid}] in HT Scout Bridge:\n\n"
            "\"{quote}\"\n\n"
        ),
        "bg": (
            "Здравей, {author},\n\n"
            "Относно коментара ти за [playerid={playerid}] в HT Scout Bridge:\n\n"
            "\"{quote}\"\n\n"
        ),
    },
    "modal_close": {"en": "Close", "bg": "Затвори"},

    # --- trainer own page ---
    "me_title": {"en": "My team", "bg": "Моят отбор"},
    "me_not_connected": {
        "en": "Your team is not connected yet. Connecting reads your squad, training and budget via CHPP — read-only.",
        "bg": "Отборът ви още не е свързан. Свързването чете състава, тренировката и бюджета през CHPP — само за четене.",
    },
    "me_connect_hint": {
        "en": "Connect your team first (My team → refresh from CHPP).",
        "bg": "Първо свържете отбора си (Моят отбор → обнови от CHPP).",
    },
    "me_connect_btn": {"en": "Connect my team", "bg": "Свържи моя отбор"},
    "me_profile": {"en": "Team facts", "bg": "Факти за отбора"},
    "me_training_type": {"en": "Training type", "bg": "Тип тренировка"},
    "me_intensity": {"en": "Intensity", "bg": "Интензивност"},
    "me_stamina": {"en": "Stamina share", "bg": "Дял издръжливост"},
    "me_cash": {"en": "Cash", "bg": "Наличност"},
    "me_expected_cash": {"en": "Expected cash (next week)", "bg": "Очаквана наличност (следваща седмица)"},
    "me_last_sync": {"en": "Last refresh", "bg": "Последно обновяване"},
    "me_squad_title": {"en": "Squad snapshot", "bg": "Състав"},
    "me_in_training": {"en": "In trained slot", "bg": "В трениран слот"},
    "me_declarations_title": {"en": "Slot declarations", "bg": "Декларации за слотове"},
    "me_new_declaration": {"en": "New declaration", "bg": "Нова декларация"},
    "f_slot_type": {"en": "Slot for skill", "bg": "Слот за умение"},
    "f_max_price": {"en": "Max I can pay for the player", "bg": "Максимум, който мога да дам за играча"},
    "f_max_price_short": {"en": "max", "bg": "макс."},
    "f_min_age": {"en": "Min age", "bg": "Мин. възраст"},
    "f_max_age": {"en": "Max age", "bg": "Макс. възраст"},
    "f_req_specialty": {"en": "Required specialty", "bg": "Желан специалитет"},
    "spec_any": {"en": "no requirement", "bg": "без изискване"},
    "req_skills_legend": {
        "en": "Skill requirements — fill in only where you have a min/max",
        "bg": "Изисквания за умения — попълни само където имаш мин/макс",
    },
    "req_min_ph": {"en": "min", "bg": "мин"},
    "req_max_ph": {"en": "max", "bg": "макс"},
    "decl_requirements": {"en": "Requirements", "bg": "Изисквания"},
    "decl_age": {"en": "age", "bg": "възраст"},
    "f_quality_threshold": {"en": "Min quality (1–20)", "bg": "Мин. качество (1–20)"},
    "f_player_to_move": {"en": "Player I would move", "bg": "Играч, когото бих продал"},
    "f_expected_sale_price": {"en": "Expected sale price", "bg": "Очаквана продажна цена"},
    "f_timing": {"en": "Timing", "bg": "Кога"},
    "f_conditional": {"en": "only after a sale", "bg": "само след продажба"},
    "f_note": {"en": "Note", "bg": "Бележка"},
    "f_valid_days": {"en": "Valid for (days)", "bg": "Валидна за (дни)"},
    "f_training_weeks": {
        "en": "Weeks on this training (blank = indefinitely)",
        "bg": "Седмици на тази тренировка (празно = безсрочно)",
    },
    "decl_weeks_n": {"en": "{n} more weeks on this training", "bg": "още {n} седмици на тази тренировка"},
    "decl_indefinite": {"en": "indefinitely", "bg": "безсрочно"},
    "f_max_bid": {"en": "Bid limit", "bg": "Лимит за наддаване"},
    "me_revoke_title": {"en": "Disconnect", "bg": "Прекратяване"},
    "me_revoke_hint": {
        "en": "Revokes access and deletes your synced team data, squad snapshot and declarations from the registry.",
        "bg": "Прекратява достъпа и изтрива синхронизираните данни за отбора, състава и декларациите от регистъра.",
    },
    "me_revoke_btn": {"en": "Disconnect & purge my data", "bg": "Прекрати и изтрий данните ми"},
    "me_change_team": {"en": "Change team", "bg": "Смени отбора"},
    "teams_title": {"en": "Choose a team", "bg": "Избери отбор"},
    "teams_hint": {
        "en": "You manage more than one team — pick which one to connect to the registry. Its training, squad and budget will be what scouts see.",
        "bg": "Управляваш повече от един отбор — избери кой да свържеш към регистъра. Неговата тренировка, състав и бюджет ще виждат скаутите.",
    },
    "teams_current": {"en": "Connected", "bg": "Свързан"},
    "teams_pick": {"en": "Connect this team", "bg": "Свържи този отбор"},
    "teams_switch_warning": {
        "en": "Switching teams removes the current team's declarations, interests and squad snapshot from the registry — they belong to that team.",
        "bg": "Смяната на отбора премахва декларациите, заявките и състава на текущия отбор от регистъра — те принадлежат на него.",
    },
    "fl_choose_team": {"en": "Choose which team to connect.", "bg": "Изберете кой отбор да свържете."},

    # --- market pipeline ---
    "market_title": {"en": "Market pipeline", "bg": "Пазарен поток"},
    "market_intro": {
        "en": "Players the scouts plan to bring to market (or already listed). Raise a hand instead of waiting for an HT-mail.",
        "bg": "Играчи, които скаутите планират да изкарат на пазара (или вече обявени). Заявете интерес, вместо да чакате HT-mail.",
    },
    "market_only_mine": {"en": "Only my training type", "bg": "Само моя тип тренировка"},
    "market_scout": {"en": "Scout", "bg": "Скаут"},
    "market_interest": {"en": "I want him", "bg": "Искам го"},
    "market_no_players": {"en": "No players in the pipeline right now.", "bg": "В момента няма играчи в потока."},

    # --- admin ---
    "admin_title": {"en": "Roles", "bg": "Роли"},
    "admin_role": {"en": "Role", "bg": "Роля"},
    "admin_save": {"en": "Save", "bg": "Запази"},
    "admin_add_title": {"en": "Pre-add a user", "bg": "Предварително добавяне на потребител"},
    "admin_add_hint": {
        "en": "Add a manager by Hattrick user ID before they log in — on their first \"Connect with Hattrick\" they get this role instead of the trainer default. The ID is in the URL of their Hattrick profile (userId=…).",
        "bg": "Добавете мениджър по Hattrick ID преди да е влизал — при първото си свързване получава тази роля вместо „трениращ“ по подразбиране. ID-то е в адреса на Hattrick профила му (userId=…).",
    },
    "f_ht_user_id": {"en": "Hattrick user ID", "bg": "Hattrick ID на потребителя"},
    "f_login_name": {"en": "Login name (optional)", "bg": "Потребителско име (по избор)"},
    "admin_add_btn": {"en": "Add user", "bg": "Добави потребител"},
    "fl_user_added": {"en": "User added — the role applies when they first log in.", "bg": "Потребителят е добавен — ролята важи от първото му влизане."},
    "fl_user_exists": {"en": "A user with this Hattrick ID already exists.", "bg": "Потребител с това Hattrick ID вече съществува."},

    # --- flashes ---
    "fl_no_access": {"en": "You don't have access to that page.", "bg": "Нямате достъп до тази страница."},
    "fl_not_found": {"en": "Not found.", "bg": "Не е намерено."},
    "fl_unknown_persona": {"en": "Unknown demo persona.", "bg": "Непознат демо потребител."},
    "fl_oauth_unavailable": {"en": "Live CHPP login is not available.", "bg": "Истинският CHPP вход не е достъпен."},
    "fl_player_exists": {"en": "This player is already in the registry.", "bg": "Този играч вече е в регистъра."},
    "fl_player_deleted": {"en": "Player removed from the registry.", "bg": "Играчът е премахнат от регистъра."},
    "confirm_delete": {
        "en": "Remove {name} from the registry? Claims, interests and the training plan are deleted too.",
        "bg": "Премахване на {name} от регистъра? Изтриват се и поеманията, заявките и тренировъчният план.",
    },
    "fl_player_added": {"en": "Player added; public data loaded from CHPP.", "bg": "Играчът е добавен; публичните данни са заредени от CHPP."},
    "fl_public_synced": {"en": "Public data refreshed.", "bg": "Публичните данни са обновени."},
    "fl_public_sync_failed": {
        "en": "Player saved, but public data could not be loaded (CHPP unavailable for this ID).",
        "bg": "Играчът е запазен, но публичните данни не можаха да се заредят (CHPP недостъпен за това ID).",
    },
    "fl_throttled": {"en": "Already refreshed within the last 24h (CHPP fetch policy).", "bg": "Вече е обновявано през последните 24 ч. (CHPP политика)."},
    "fl_saved": {"en": "Saved.", "bg": "Запазено."},
    "fl_claimed": {"en": "Player claimed — other scouts will see you handle him.", "bg": "Играчът е поет — другите скаути ще виждат, че вие го водите."},
    "fl_claim_exists": {"en": "Someone already handles this player.", "bg": "Някой вече е поел този играч."},
    "fl_released": {"en": "Claim released.", "bg": "Поемането е освободено."},
    "fl_interest_decided": {"en": "Interest updated.", "bg": "Заявката е обновена."},
    "fl_interest_sent": {"en": "Interest sent — the handling scout will see it.", "bg": "Заявката е изпратена — водещият скаут ще я види."},
    "fl_interest_exists": {"en": "You already raised interest for this player.", "bg": "Вече сте заявили интерес за този играч."},
    "fl_interest_withdrawn": {"en": "Interest withdrawn.", "bg": "Заявката е оттеглена."},
    "fl_need_profile": {"en": "Connect your team first.", "bg": "Първо свържете отбора си."},
    "fl_decl_created": {"en": "Declaration published — scouts can now find your slot.", "bg": "Декларацията е публикувана — скаутите вече могат да намерят слота ви."},
    "fl_decl_renewed": {"en": "Declaration renewed for 28 days.", "bg": "Декларацията е подновена за 28 дни."},
    "fl_decl_withdrawn": {"en": "Declaration withdrawn.", "bg": "Декларацията е оттеглена."},
    "fl_synced": {"en": "Team data refreshed from CHPP.", "bg": "Данните за отбора са обновени от CHPP."},
    "fl_sync_failed": {"en": "Refresh failed: {err}", "bg": "Обновяването се провали: {err}"},
    "fl_revoked": {"en": "Access revoked and derived data purged.", "bg": "Достъпът е прекратен и данните са изтрити."},
    "fl_role_saved": {"en": "Role updated.", "bg": "Ролята е обновена."},

    # --- matching reasons ---
    "reason_training_match": {"en": "Training type matches the target skill", "bg": "Типът тренировка съвпада с целевото умение"},
    "warn_training_mismatch": {"en": "Trains a different skill", "bg": "Тренира друго умение"},
    "reason_slot_declared": {"en": "{n} matching slot declaration(s)", "bg": "{n} съвпадащи декларации за слот"},
    "reason_slot_immediate": {"en": "Slot available immediately", "bg": "Слотът е свободен веднага"},
    "warn_conditional": {"en": "Slot conditional on a sale", "bg": "Слотът зависи от продажба"},
    "warn_no_slot": {"en": "No active slot declaration", "bg": "Няма активна декларация за слот"},
    "reason_budget_ok": {"en": "Budget covers the estimated price", "bg": "Бюджетът покрива очакваната цена"},
    "reason_budget_after_sale": {"en": "Budget covers it after the declared sale", "bg": "Бюджетът стига след декларираната продажба"},
    "warn_budget_short": {"en": "Budget likely short of the estimate", "bg": "Бюджетът вероятно не стига"},
    "warn_budget_unknown": {"en": "Budget unknown", "bg": "Бюджетът е неизвестен"},
    "reason_requirements_ok": {"en": "Meets the declared requirements", "bg": "Покрива декларираните изисквания"},
    "warn_req_age": {"en": "Below the declared min age ({limit})", "bg": "Под декларираната мин. възраст ({limit})"},
    "warn_req_age_max": {"en": "Above the declared max age ({limit})", "bg": "Над декларираната макс. възраст ({limit})"},
    "warn_req_spec": {"en": "Specialty differs from the requirement", "bg": "Специалитетът се разминава с изискването"},
    "warn_req_skill_low": {"en": "{skill} below the required minimum ({limit})", "bg": "{skill} е под искания минимум ({limit})"},
    "warn_req_skill_high": {"en": "{skill} above the required maximum ({limit})", "bg": "{skill} е над искания максимум ({limit})"},
    "warn_req_price": {"en": "Estimate exceeds the trainer's max ({limit})", "bg": "Оценката надхвърля максимума на трениращия ({limit})"},
    "reason_login_recent": {"en": "Active in the last 3 days", "bg": "Активен през последните 3 дни"},
    "reason_login_ok": {"en": "Active in the last 2 weeks", "bg": "Активен през последните 2 седмици"},
    "warn_login_stale": {"en": "No login for {days} days", "bg": "Без вход от {days} дни"},
    "warn_horizon_short": {
        "en": "Declared training horizon ({declared} wk) is shorter than the plan ({needed} wk)",
        "bg": "Декларираният хоризонт ({declared} седм.) е по-кратък от плана ({needed} седм.)",
    },
    "reason_top_coach": {"en": "High-level coach", "bg": "Треньор на високо ниво"},

    # --- outreach draft ---
    "outreach_subject": {
        "en": "NT scouting — training place for {player} ({skill})",
        "bg": "НО скаутинг — място за трениране на {player} ({skill})",
    },
    "draft_price_part": {"en": ", estimated price around {price}", "bg": ", очаквана цена около {price}"},
    "outreach_draft": {
        "en": (
            "Hi {trainer},\n\n"
            "I'm {scout} from the {squad} scouting staff. {player} ({age} years, target: {skill}{price_part}) "
            "needs a training place and your setup looks like a fit.\n\n"
            "Player page: {url}{plan_part}\n\n"
            "Would you be open to taking him? Happy to share our full assessment and training target.\n\n"
            "Thanks in advance!"
        ),
        "bg": (
            "Здравей, {trainer},\n\n"
            "Аз съм {scout} от скаутския щаб на {squad}. {player} ({age} години, цел: {skill}{price_part}) "
            "има нужда от място за трениране и твоята подготовка изглежда подходяща.\n\n"
            "Страница на играча: {url}{plan_part}\n\n"
            "Би ли го взел? С удоволствие ще споделя пълната ни оценка и тренировъчната цел.\n\n"
            "Благодаря предварително!"
        ),
    },
    "draft_plan_part": {
        "en": "\n\nSuggested training plan: {plan}",
        "bg": "\n\nПредложен тренировъчен план: {plan}",
    },
    "plan_step_fmt": {
        "en": "{skill} ~{weeks} wk ({stamina}% stamina)",
        "bg": "{skill} ~{weeks} седм. ({stamina}% издръжливост)",
    },
}


def t(locale: str, key: str, **params) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(locale) or entry.get("en") or key
    if params:
        try:
            return text.format(**params)
        except (KeyError, IndexError):
            return text
    return text

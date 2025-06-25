import os
import re
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import psycopg2


def connect_db():
    """Establish a PostgreSQL connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "botdb"),
        user=os.getenv("DB_USER", "botuser"),
        password=os.getenv("DB_PASSWORD", "botpass"),
    )

openai.api_key = os.getenv("OPENAI_API_KEY", "")
PHRASE_TOPIC = os.getenv("PHRASE_TOPIC", "")

ALLOWED_USERNAME = "i_doktorova"

def is_allowed(update: Update) -> bool:
    """Return True if the message is from the allowed user."""
    user = update.effective_user
    return bool(user and user.username == ALLOWED_USERNAME)


def save_user(user) -> None:
    """Store the user's public info and registration time in the database."""
    conn = connect_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (telegram_id, username, registered_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (telegram_id) DO NOTHING
                """,
                (user.id, user.username or ""),
            )
    conn.close()


def get_user_id(telegram_id: int) -> int | None:
    """Return internal user id for the given telegram id."""
    conn = connect_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE telegram_id = %s",
                (telegram_id,),
            )
            row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_phrase_by_id(phrase_id: int):
    """Fetch a phrase by its id."""
    conn = connect_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, original, translation, difficulty FROM phrases WHERE id = %s",
                (phrase_id,),
            )
            row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "original": row[1],
            "translation": row[2],
            "difficulty": row[3],
        }
    return None


def get_next_phrase(user_id: int):
    """Return the next phrase for a user or None if finished."""
    conn = connect_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.original, p.translation, p.difficulty
                FROM phrase_view p
                WHERE p.id NOT IN (
                    SELECT phrase_id FROM progress WHERE user_id = %s
                )
                ORDER BY p.difficulty ASC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "original": row[1],
            "translation": row[2],
            "difficulty": row[3],
        }
    return None


def record_progress(user_id: int, phrase_id: int, correct: bool) -> None:
    """Insert a progress record."""
    conn = connect_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO progress (user_id, phrase_id, answered_at, correct)
                VALUES (%s, %s, NOW(), %s)
                """,
                (user_id, phrase_id, correct),
            )
    conn.close()


def get_recent_incorrect_phrases(user_id: int, limit: int = 20) -> list[dict]:
    """Return phrases the user answered incorrectly most recently."""
    conn = connect_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (p.id) p.id, p.original, p.translation, p.difficulty
                FROM progress pr
                JOIN phrases p ON p.id = pr.phrase_id
                WHERE pr.user_id = %s AND pr.correct = false
                ORDER BY p.id, pr.answered_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "original": row[1],
            "translation": row[2],
            "difficulty": row[3],
        }
        for row in rows
    ]


def save_phrase(original: str, translation: str, difficulty: int = 1) -> None:
    """Insert a new phrase into the database."""
    conn = connect_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO phrases (original, translation, difficulty)
                VALUES (%s, %s, %s)
                """,
                (original, translation, difficulty),
            )
    conn.close()


def request_phrases_from_api(topic: str | None = None, limit: int = 20) -> list[tuple[str, str]]:
    """Request new phrases from ChatGPT API."""
    if not openai.api_key:
        return []
    if topic:
        prompt = (
            f"Сгенерируй {limit} сербских фраз на тему '{topic}'. "
            "В ответе должны быть только фразы: оригинал и перевод через '|' без какого-либо дополнительного текста"
        )
    else:
        prompt = (
            f"Сгенерируй {limit} сербских фраз. "
            "В ответе должны быть только фразы: оригинал и перевод через '|' без какого-либо дополнительного текста"
        )
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        return []

    text = response.choices[0].message.content
    phrases = []
    for line in text.splitlines():
        if "|" in line:
            original, translation = line.split("|", 1)
            phrases.append((original.strip(), translation.strip()))
    return phrases


def _normalize(text: str) -> list[str]:
    """Return list of word tokens in lowercase."""
    return re.findall(r"\w+", text.lower())


def translations_match(user_text: str, reference: str) -> bool:
    """Compare translations by lexemes."""
    return _normalize(user_text) == _normalize(reference)


async def send_next_phrase(user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch the next phrase and send it to the user."""
    queue: list[dict] = context.user_data.get("error_queue", [])
    if queue:
        phrase = queue.pop(0)
    else:
        phrase = get_next_phrase(user_id)
        if not phrase:
            errors = get_recent_incorrect_phrases(user_id)
            if errors:
                context.user_data["error_queue"] = errors
                phrase = context.user_data["error_queue"].pop(0)
            else:
                new_phrases = request_phrases_from_api(PHRASE_TOPIC or None)
                for original, translation in new_phrases:
                    save_phrase(original, translation)
                phrase = get_next_phrase(user_id)
                if not phrase:
                    context.user_data.pop("current_phrase_id", None)
                    return

    context.user_data["current_phrase_id"] = phrase["id"]
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Переведите: {phrase['original']}",
    )


async def receive_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user's translation answer."""
    if not is_allowed(update):
        return

    phrase_id = context.user_data.get("current_phrase_id")
    if not phrase_id:
        return

    user_id = get_user_id(update.effective_user.id)
    if user_id is None:
        return

    user_text = update.message.text or ""
    phrase = get_phrase_by_id(phrase_id)
    if phrase is None:
        return

    correct = translations_match(user_text, phrase["translation"])
    record_progress(user_id, phrase_id, correct)

    if correct:
        await update.message.reply_text("Верно!")
    else:
        await update.message.reply_text(
            f"Неверно. Правильный перевод: {phrase['translation']}"
        )

    await send_next_phrase(user_id, update.effective_chat.id, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized user.")
        return

    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data="register_yes"),
            InlineKeyboardButton("Нет", callback_data="register_no"),
        ]
    ]
    await update.message.reply_text(
        "Это бот обучения сербскому языку, хотите начать обучение?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized user.")
        return
    await update.message.reply_text("Send /start to test this bot.")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses from the start message."""
    query = update.callback_query
    await query.answer()

    if not is_allowed(update):
        await query.edit_message_text("Unauthorized user.")
        return

    if query.data == "register_yes":
        save_user(query.from_user)
        keyboard = [
            [InlineKeyboardButton("Начать перевод", callback_data="start_translation")]
        ]
        await query.edit_message_text(
            "Регистрация завершена. Выберите активность.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif query.data == "register_no":
        await query.edit_message_text("уходите, вам здесь не рады")
    elif query.data == "start_translation":
        user_id = get_user_id(query.from_user.id)
        if user_id is not None:
            await send_next_phrase(user_id, query.message.chat_id, context)


def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("Please set the TELEGRAM_TOKEN environment variable.")

    # Ensure the database is reachable on startup
    try:
        conn = connect_db()
        conn.close()
    except Exception as exc:
        raise RuntimeError("Database connection failed") from exc

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), receive_translation)
    )

    application.run_polling()


if __name__ == "__main__":
    main()

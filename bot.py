import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
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
        await query.edit_message_text("Регистрация завершена. Начнем обучение!")
    elif query.data == "register_no":
        await query.edit_message_text("уходите, вам здесь не рады")


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

    application.run_polling()


if __name__ == "__main__":
    main()

import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized user.")
        return
    await update.message.reply_text("Hello! I'm a skeleton bot.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized user.")
        return
    await update.message.reply_text("Send /start to test this bot.")


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

    application.run_polling()


if __name__ == "__main__":
    main()

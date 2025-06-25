# Telegram Bot Skeleton

This repository contains a basic skeleton for a Telegram bot written in Python using the `python-telegram-bot` library.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a bot via BotFather and obtain your API token.
3. Set the `TELEGRAM_TOKEN` environment variable to your token.
4. For automatic phrase generation set `OPENAI_API_KEY` to a valid OpenAI key.
5. Optionally specify `PHRASE_TOPIC` to influence generated phrases.
6. Database settings can be overridden with `DB_HOST`, `DB_PORT`, `DB_NAME`,
   `DB_USER` and `DB_PASSWORD`.

## Running

Start the bot with:
```bash
python bot.py
```

The bot currently supports `/start` and `/help`. When `/start` is issued by the allowed user the bot asks whether to begin the Serbian course. Selecting **Да** saves the user's public information in the database together with the registration timestamp, while **Нет** ends the conversation. Additional handlers can be added in `bot.py`.
When all phrases are completed, the bot repeats those answered incorrectly and then fetches new ones from ChatGPT if an `OPENAI_API_KEY` is provided.
ChatGPT is instructed to reply only with phrases, each phrase and its translation separated by `|`.

## Docker

This repository includes a `Dockerfile` and `docker-compose.yml` to run the bot together with a PostgreSQL database. The database is initialized with a simple `users` table defined in `db_init/init.sql`.

1. Create a `.env` file with `TELEGRAM_TOKEN`, optionally `OPENAI_API_KEY` and
   other variables described above.
2. Launch the services:
   ```bash
   docker-compose up --build
   ```

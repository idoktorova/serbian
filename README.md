# Telegram Bot Skeleton

This repository contains a basic skeleton for a Telegram bot written in Python using the `python-telegram-bot` library.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a bot via BotFather and obtain your API token.
3. Set the `TELEGRAM_TOKEN` environment variable to your token.

## Running

Start the bot with:
```bash
python bot.py
```

The bot currently supports `/start` and `/help`. When `/start` is issued by the allowed user the bot asks whether to begin the Serbian course. Selecting **Да** saves the user's public information in the database together with the registration timestamp, while **Нет** ends the conversation. Additional handlers can be added in `bot.py`.

## Docker

This repository includes a `Dockerfile` and `docker-compose.yml` to run the bot together with a PostgreSQL database. The database is initialized with a simple `users` table defined in `db_init/init.sql`.

1. Create a `.env` file with `TELEGRAM_TOKEN` inside.
2. Launch the services:
   ```bash
   docker-compose up --build
   ```

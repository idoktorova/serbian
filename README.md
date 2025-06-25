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

The bot currently supports `/start` and `/help` commands and can be extended by adding more handlers in `bot.py`.

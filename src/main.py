"""Entry point del bot Telegram buySellBot."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler

from bot.handlers import binance_status, help_command
from bot.menus import build_main_menu_conversation
from utils.config import load_settings


def main() -> None:
	"""Avvia l'applicazione Telegram con handler base."""
	logging.basicConfig(
		format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
		level=logging.INFO,
	)

	try:
		settings = load_settings()
	except ValueError as exc:
		raise SystemExit(f"Configurazione non valida: {exc}") from exc

	application = Application.builder().token(settings.telegram_bot_token).build()

	application.add_handler(build_main_menu_conversation())
	application.add_handler(CommandHandler("help", help_command))
	application.add_handler(CommandHandler("binance_status", binance_status))

	application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
	main()

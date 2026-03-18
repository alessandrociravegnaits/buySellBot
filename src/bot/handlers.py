"""Handler Telegram per la verifica autenticazione Binance."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from binance_client.client import (
	BinanceAuthError,
	BinanceConnectionError,
	init_and_test_client,
)
from utils.config import load_settings


async def binance_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Testa connettivita' e credenziali Binance tramite comando Telegram."""
	if update.effective_user is None or update.effective_message is None:
		return

	try:
		settings = load_settings()
	except ValueError as exc:
		await update.effective_message.reply_text(
			f"Configurazione mancante: {exc}"
		)
		return

	if update.effective_user.id != settings.telegram_allowed_user_id:
		await update.effective_message.reply_text("Accesso non autorizzato.")
		return

	try:
		init_and_test_client(settings)
	except BinanceAuthError as exc:
		await update.effective_message.reply_text(str(exc))
	except BinanceConnectionError as exc:
		await update.effective_message.reply_text(str(exc))
	except Exception:
		await update.effective_message.reply_text(
			"Errore inatteso durante la verifica Binance."
		)
	else:
		await update.effective_message.reply_text(
			"Binance OK: connessione e credenziali valide."
		)

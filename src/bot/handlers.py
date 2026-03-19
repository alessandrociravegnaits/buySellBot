"""Handler Telegram per la verifica autenticazione Binance e comandi base."""

from __future__ import annotations

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from binance_client.client import (
	BinanceAuthError,
	BinanceConnectionError,
	init_and_test_client,
)
from bot.keyboards import MAIN_MENU_KEYBOARD
from utils.config import Settings, load_settings


async def get_settings_or_reply(update: Update) -> Optional[Settings]:
	"""Carica le impostazioni e notifica l'utente in caso di errore."""
	if update.effective_message is None:
		return None

	try:
		return load_settings()
	except ValueError as exc:
		await update.effective_message.reply_text(
			f"Configurazione mancante: {exc}"
		)
		return None


async def ensure_authorized(update: Update, settings: Settings) -> bool:
	"""Verifica che l'utente Telegram sia autorizzato."""
	if update.effective_user is None or update.effective_message is None:
		return False

	if update.effective_user.id != settings.telegram_allowed_user_id:
		await update.effective_message.reply_text("Accesso non autorizzato.")
		return False

	return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Gestisce il comando /start con menu base."""
	settings = await get_settings_or_reply(update)
	if settings is None:
		return

	if not await ensure_authorized(update, settings):
		return

	if update.effective_message is None:
		return

	await update.effective_message.reply_text(
		"Benvenuto in buySellBot. Usa il menu per iniziare.",
		reply_markup=MAIN_MENU_KEYBOARD,
	)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Gestisce il comando /help con elenco comandi."""
	settings = await get_settings_or_reply(update)
	if settings is None:
		return

	if not await ensure_authorized(update, settings):
		return

	if update.effective_message is None:
		return

	await update.effective_message.reply_text(
		"Comandi disponibili:\n"
		"/start - Mostra il menu principale\n"
		"/help - Mostra questo aiuto\n"
		"/binance_status - Verifica connessione e credenziali Binance"
	)


async def binance_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Testa connettivita' e credenziali Binance tramite comando Telegram."""
	settings = await get_settings_or_reply(update)
	if settings is None:
		return

	if not await ensure_authorized(update, settings):
		return

	if update.effective_message is None:
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

"""ConversationHandler base per il bot Telegram."""

from __future__ import annotations

from telegram import Update
from telegram.ext import (
	CommandHandler,
	ContextTypes,
	ConversationHandler,
	MessageHandler,
	filters,
)

from bot.handlers import ensure_authorized, get_settings_or_reply
from bot.keyboards import MAIN_MENU_KEYBOARD

STATE_MAIN_MENU = 1


async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Avvia il menu principale con /start."""
	settings = await get_settings_or_reply(update)
	if settings is None:
		return ConversationHandler.END

	if not await ensure_authorized(update, settings):
		return ConversationHandler.END

	if update.effective_message is None:
		return ConversationHandler.END

	await update.effective_message.reply_text(
		"Menu principale: scegli un'opzione.",
		reply_markup=MAIN_MENU_KEYBOARD,
	)
	return STATE_MAIN_MENU


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Gestisce le scelte del menu principale."""
	settings = await get_settings_or_reply(update)
	if settings is None:
		return ConversationHandler.END

	if not await ensure_authorized(update, settings):
		return ConversationHandler.END

	if update.effective_message is None or update.effective_message.text is None:
		return STATE_MAIN_MENU

	selection = update.effective_message.text.strip().lower()
	if selection == "stato binance":
		await update.effective_message.reply_text(
			"Usa /binance_status per la verifica completa."
		)
	elif selection == "aiuto":
		await update.effective_message.reply_text(
			"Usa /help per vedere tutti i comandi."
		)
	elif selection == "annulla":
		await update.effective_message.reply_text("Operazione annullata.")
		return ConversationHandler.END
	else:
		await update.effective_message.reply_text(
			"Comando non riconosciuto. Usa il menu o /help."
		)

	return STATE_MAIN_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Annulla la conversazione in corso."""
	if update.effective_message is not None:
		await update.effective_message.reply_text("Operazione annullata.")
	return ConversationHandler.END


def build_main_menu_conversation() -> ConversationHandler:
	"""Costruisce il ConversationHandler base del bot."""
	return ConversationHandler(
		entry_points=[CommandHandler("start", start_menu)],
		states={
			STATE_MAIN_MENU: [
				MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
			]
		},
		fallbacks=[CommandHandler("cancel", cancel)],
		name="main_menu",
		persistent=False,
	)

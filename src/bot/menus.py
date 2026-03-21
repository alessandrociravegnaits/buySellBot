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

from binance_client.client import BinanceConnectionError
from binance_client.order_types import (
	BinanceOrderError,
	BinanceOrderValidationError,
	place_market_order,
)
from bot.handlers import ensure_authorized, get_settings_or_reply
from bot.keyboards import MAIN_MENU_KEYBOARD
from db.dao import OrdersDAO
from db.database import Database

STATE_MAIN_MENU = 1
STATE_ORDER_MARKET_INPUT = 2
STATE_ORDER_MARKET_CONFIRM = 3


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
	if selection == "ordini":
		await update.effective_message.reply_text(
			"Inserisci ordine market nel formato: MARKET BUY BTCUSDT 0.001"
		)
		return STATE_ORDER_MARKET_INPUT
	elif selection == "stato":
		await update.effective_message.reply_text(
			"Sezione Stato in arrivo."
		)
	elif selection == "config":
		await update.effective_message.reply_text(
			"Sezione Config in arrivo."
		)
	elif selection == "monitor":
		await update.effective_message.reply_text(
			"Sezione Monitor in arrivo."
		)
	elif selection == "annulla":
		await update.effective_message.reply_text("Operazione annullata.")
		return ConversationHandler.END
	else:
		await update.effective_message.reply_text(
			"Comando non riconosciuto. Usa il menu o /help."
		)

	return STATE_MAIN_MENU


def _parse_market_order_input(user_text: str) -> tuple[str, str, float]:
	"""Parsa il comando testuale ordine market.

	Args:
		user_text: Testo inserito dall'utente.

	Returns:
		tuple[str, str, float]: Side, symbol, quantity.

	Raises:
		ValueError: Se il formato non e' valido.
	"""

	parts = user_text.strip().split()
	if len(parts) != 4:
		raise ValueError("Formato non valido.")

	order_kind, side, symbol, quantity_raw = parts
	if order_kind.upper() != "MARKET":
		raise ValueError("Solo ordini MARKET supportati in questa fase.")

	try:
		quantity = float(quantity_raw)
	except ValueError as exc:
		raise ValueError("Quantity deve essere un numero valido.") from exc

	if quantity <= 0:
		raise ValueError("Quantity deve essere maggiore di zero.")

	return side.upper(), symbol.upper(), quantity


async def handle_market_order_input(
	update: Update,
	context: ContextTypes.DEFAULT_TYPE,
) -> int:
	"""Gestisce input ordine market e chiede conferma esplicita."""
	settings = await get_settings_or_reply(update)
	if settings is None:
		return ConversationHandler.END

	if not await ensure_authorized(update, settings):
		return ConversationHandler.END

	if update.effective_message is None or update.effective_message.text is None:
		return STATE_ORDER_MARKET_INPUT

	try:
		side, symbol, quantity = _parse_market_order_input(update.effective_message.text)
	except ValueError as exc:
		await update.effective_message.reply_text(
			f"Input non valido: {exc}\nRiprova: MARKET BUY BTCUSDT 0.001"
		)
		return STATE_ORDER_MARKET_INPUT

	context.user_data["pending_market_order"] = {
		"side": side,
		"symbol": symbol,
		"quantity": quantity,
	}

	await update.effective_message.reply_text(
		"Conferma ordine: "
		f"MARKET {side} {symbol} {quantity}. "
		"Rispondi CONFERMA per inviare oppure ANNULLA per annullare."
	)
	return STATE_ORDER_MARKET_CONFIRM


async def handle_market_order_confirm(
	update: Update,
	context: ContextTypes.DEFAULT_TYPE,
) -> int:
	"""Conferma e invia l'ordine market verso Binance."""
	settings = await get_settings_or_reply(update)
	if settings is None:
		return ConversationHandler.END

	if not await ensure_authorized(update, settings):
		return ConversationHandler.END

	if update.effective_message is None or update.effective_message.text is None:
		return STATE_ORDER_MARKET_CONFIRM

	answer = update.effective_message.text.strip().upper()
	if answer == "ANNULLA":
		context.user_data.pop("pending_market_order", None)
		await update.effective_message.reply_text("Ordine annullato.")
		return STATE_MAIN_MENU

	if answer != "CONFERMA":
		await update.effective_message.reply_text(
			"Risposta non valida. Scrivi CONFERMA o ANNULLA."
		)
		return STATE_ORDER_MARKET_CONFIRM

	pending = context.user_data.get("pending_market_order")
	if not pending:
		await update.effective_message.reply_text(
			"Nessun ordine in attesa. Riparti da 'Ordini'."
		)
		return STATE_MAIN_MENU

	side = str(pending["side"])
	symbol = str(pending["symbol"])
	quantity = float(pending["quantity"])

	try:
		response = place_market_order(settings, symbol=symbol, side=side, quantity=quantity)
	except BinanceOrderValidationError as exc:
		await update.effective_message.reply_text(f"Ordine non valido: {exc}")
		return STATE_MAIN_MENU
	except BinanceConnectionError as exc:
		await update.effective_message.reply_text(f"Errore connessione Binance: {exc}")
		return STATE_MAIN_MENU
	except BinanceOrderError as exc:
		await update.effective_message.reply_text(str(exc))
		return STATE_MAIN_MENU

	database = Database(settings.db_path)
	database.initialize()
	dao = OrdersDAO(database)
	status = str(response.get("status", "NEW"))
	order_id = dao.create_order(
		symbol=symbol,
		side=side,
		quantity=quantity,
		status=status,
		price=None,
		note=f"binance_order_id={response.get('orderId')}",
	)

	context.user_data.pop("pending_market_order", None)
	await update.effective_message.reply_text(
		"Ordine inviato con successo. "
		f"DB id={order_id}, Binance id={response.get('orderId')}, status={status}."
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
			],
			STATE_ORDER_MARKET_INPUT: [
				MessageHandler(filters.TEXT & ~filters.COMMAND, handle_market_order_input)
			],
			STATE_ORDER_MARKET_CONFIRM: [
				MessageHandler(filters.TEXT & ~filters.COMMAND, handle_market_order_confirm)
			],
		},
		fallbacks=[CommandHandler("cancel", cancel)],
		name="main_menu",
		persistent=False,
	)

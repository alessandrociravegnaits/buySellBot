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
	place_stop_loss_limit_order,
	place_trailing_stop_order,
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
			"Inserisci ordine nel formato:\n"
			"- MARKET BUY BTCUSDT 0.001\n"
			"- STOP_LIMIT BUY BTCUSDT 0.001 65000 64000\n"
			"- TRAILING_STOP BUY BTCUSDT 0.001 100"
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


def _parse_stop_limit_order_input(user_text: str) -> tuple[str, str, float, float, float]:
	"""Parsa il comando testuale ordine STOP_LIMIT.

	Args:
		user_text: Testo inserito dall'utente.

	Returns:
		tuple[str, str, float, float, float]: Side, symbol, quantity, price, stop_price.

	Raises:
		ValueError: Se il formato non e' valido.
	"""

	parts = user_text.strip().split()
	if len(parts) != 6:
		raise ValueError("Formato non valido.")

	order_kind, side, symbol, quantity_raw, price_raw, stop_price_raw = parts
	if order_kind.upper() != "STOP_LIMIT":
		raise ValueError("Solo ordini STOP_LIMIT supportati in questa fase.")

	try:
		quantity = float(quantity_raw)
		price = float(price_raw)
		stop_price = float(stop_price_raw)
	except ValueError as exc:
		raise ValueError("Quantity, price e stop_price devono essere numeri validi.") from exc

	if quantity <= 0:
		raise ValueError("Quantity deve essere maggiore di zero.")
	if price <= 0:
		raise ValueError("Price deve essere maggiore di zero.")
	if stop_price <= 0:
		raise ValueError("Stop price deve essere maggiore di zero.")

	return side.upper(), symbol.upper(), quantity, price, stop_price


def _parse_trailing_stop_order_input(user_text: str) -> tuple[str, str, float, int]:
	"""Parsa il comando testuale ordine TRAILING_STOP.

	Args:
		user_text: Testo inserito dall'utente.

	Returns:
		tuple[str, str, float, int]: Side, symbol, quantity, trailing_delta.

	Raises:
		ValueError: Se il formato non e' valido.
	"""

	parts = user_text.strip().split()
	if len(parts) != 5:
		raise ValueError("Formato non valido.")

	order_kind, side, symbol, quantity_raw, trailing_delta_raw = parts
	if order_kind.upper() != "TRAILING_STOP":
		raise ValueError("Solo ordini TRAILING_STOP supportati in questa fase.")

	try:
		quantity = float(quantity_raw)
		trailing_delta = int(trailing_delta_raw)
	except ValueError as exc:
		raise ValueError("Quantity e trailing_delta devono essere numeri validi.") from exc

	if quantity <= 0:
		raise ValueError("Quantity deve essere maggiore di zero.")
	if trailing_delta <= 0:
		raise ValueError("Trailing delta deve essere maggiore di zero.")

	return side.upper(), symbol.upper(), quantity, trailing_delta


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

	input_text = update.effective_message.text.strip()
	input_parts = input_text.split(maxsplit=1)
	order_kind = input_parts[0].upper() if input_parts else ""

	try:
		if order_kind == "MARKET":
			side, symbol, quantity = _parse_market_order_input(input_text)
			context.user_data["pending_market_order"] = {
				"kind": "MARKET",
				"side": side,
				"symbol": symbol,
				"quantity": quantity,
			}
			confirm_message = (
				"Conferma ordine: "
				f"MARKET {side} {symbol} {quantity}. "
				"Rispondi CONFERMA per inviare oppure ANNULLA per annullare."
			)
		elif order_kind == "STOP_LIMIT":
			side, symbol, quantity, price, stop_price = _parse_stop_limit_order_input(input_text)
			context.user_data["pending_market_order"] = {
				"kind": "STOP_LOSS_LIMIT",
				"side": side,
				"symbol": symbol,
				"quantity": quantity,
				"price": price,
				"stop_price": stop_price,
			}
			confirm_message = (
				"Conferma ordine: "
				f"STOP_LIMIT {side} {symbol} {quantity} {price} {stop_price}. "
				"Rispondi CONFERMA per inviare oppure ANNULLA per annullare."
			)
		elif order_kind == "TRAILING_STOP":
			side, symbol, quantity, trailing_delta = _parse_trailing_stop_order_input(input_text)
			context.user_data["pending_market_order"] = {
				"kind": "TRAILING_STOP",
				"side": side,
				"symbol": symbol,
				"quantity": quantity,
				"trailing_delta": trailing_delta,
			}
			confirm_message = (
				"Conferma ordine: "
				f"TRAILING_STOP {side} {symbol} {quantity} {trailing_delta}. "
				"Rispondi CONFERMA per inviare oppure ANNULLA per annullare."
			)
		else:
			raise ValueError("Tipo ordine non supportato. Usa MARKET, STOP_LIMIT o TRAILING_STOP.")
	except ValueError as exc:
		await update.effective_message.reply_text(
			f"Input non valido: {exc}\n"
			"Riprova con uno dei formati:\n"
			"- MARKET BUY BTCUSDT 0.001\n"
			"- STOP_LIMIT BUY BTCUSDT 0.001 65000 64000\n"
			"- TRAILING_STOP BUY BTCUSDT 0.001 100"
		)
		return STATE_ORDER_MARKET_INPUT

	await update.effective_message.reply_text(confirm_message)
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

	kind = str(pending.get("kind", "MARKET"))
	side = str(pending["side"])
	symbol = str(pending["symbol"])
	quantity = float(pending["quantity"])
	price = float(pending["price"]) if "price" in pending else None
	stop_price = float(pending["stop_price"]) if "stop_price" in pending else None
	trailing_delta = int(pending["trailing_delta"]) if "trailing_delta" in pending else None

	try:
		if kind == "STOP_LOSS_LIMIT":
			if price is None or stop_price is None:
				raise BinanceOrderValidationError("Price e stop price sono obbligatori.")
			response = place_stop_loss_limit_order(
				settings,
				symbol=symbol,
				side=side,
				quantity=quantity,
				price=price,
				stop_price=stop_price,
			)
		elif kind == "TRAILING_STOP":
			if trailing_delta is None:
				raise BinanceOrderValidationError("Trailing delta obbligatorio.")
			response = place_trailing_stop_order(
				settings,
				symbol=symbol,
				side=side,
				quantity=quantity,
				trailing_delta=trailing_delta,
			)
		else:
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
	note = f"binance_order_id={response.get('orderId')};order_type={kind}"
	if stop_price is not None:
		note = f"{note};stop_price={stop_price}"
	if trailing_delta is not None:
		note = f"{note};trailing_delta={trailing_delta}"
	order_id = dao.create_order(
		symbol=symbol,
		side=side,
		quantity=quantity,
		status=status,
		price=price,
		note=note,
	)

	context.user_data.pop("pending_market_order", None)
	await update.effective_message.reply_text(
		"Ordine inviato con successo. "
		f"Tipo={kind}, DB id={order_id}, Binance id={response.get('orderId')}, status={status}."
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

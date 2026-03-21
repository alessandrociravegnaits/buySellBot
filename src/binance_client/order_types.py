"""Funzioni per esecuzione ordini Binance."""

from __future__ import annotations

from typing import Final

import requests
from binance.enums import (
	ORDER_TYPE_MARKET,
	ORDER_TYPE_STOP_LOSS_LIMIT,
	SIDE_BUY,
	SIDE_SELL,
	TIME_IN_FORCE_GTC,
)
from binance.exceptions import BinanceAPIException, BinanceRequestException

from binance_client.client import BinanceConnectionError, create_client
from utils.config import Settings

ALLOWED_SIDES: Final[set[str]] = {"BUY", "SELL"}


class BinanceOrderError(RuntimeError):
	"""Errore durante la creazione dell'ordine Binance."""


class BinanceOrderValidationError(BinanceOrderError):
	"""Input ordine non valido."""


def place_market_order(
	settings: Settings,
	symbol: str,
	side: str,
	quantity: float,
) -> dict:
	"""Invia un ordine MARKET buy/sell su Binance.

	Args:
		settings: Configurazione runtime.
		symbol: Simbolo trading Binance (es. BTCUSDT).
		side: Lato ordine (BUY o SELL).
		quantity: Quantita' da ordinare.

	Returns:
		dict: Risposta ordine Binance.

	Raises:
		BinanceOrderValidationError: Se i parametri ordine non sono validi.
		BinanceConnectionError: Se la connessione verso Binance fallisce.
		BinanceOrderError: Se Binance rifiuta l'ordine.
	"""

	normalized_symbol = symbol.strip().upper()
	normalized_side = side.strip().upper()

	if not normalized_symbol:
		raise BinanceOrderValidationError("Symbol obbligatorio.")
	if normalized_side not in ALLOWED_SIDES:
		raise BinanceOrderValidationError("Side non valido. Usa BUY oppure SELL.")
	if quantity <= 0:
		raise BinanceOrderValidationError("Quantity deve essere maggiore di zero.")

	binance_side = SIDE_BUY if normalized_side == "BUY" else SIDE_SELL
	client = create_client(settings)

	try:
		return client.create_order(
			symbol=normalized_symbol,
			side=binance_side,
			type=ORDER_TYPE_MARKET,
			quantity=quantity,
		)
	except BinanceAPIException as exc:
		raise BinanceOrderError(f"Ordine rifiutato da Binance: {exc.message}") from exc
	except (BinanceRequestException, requests.exceptions.RequestException) as exc:
		raise BinanceConnectionError("Connessione Binance non disponibile") from exc


def place_stop_loss_limit_order(
	settings: Settings,
	symbol: str,
	side: str,
	quantity: float,
	price: float,
	stop_price: float,
) -> dict:
	"""Invia un ordine STOP_LOSS_LIMIT buy/sell su Binance.

	Args:
		settings: Configurazione runtime.
		symbol: Simbolo trading Binance (es. BTCUSDT).
		side: Lato ordine (BUY o SELL).
		quantity: Quantita' da ordinare.
		price: Prezzo limit dell'ordine.
		stop_price: Prezzo trigger (stop price).

	Returns:
		dict: Risposta ordine Binance.

	Raises:
		BinanceOrderValidationError: Se i parametri ordine non sono validi.
		BinanceConnectionError: Se la connessione verso Binance fallisce.
		BinanceOrderError: Se Binance rifiuta l'ordine.
	"""

	normalized_symbol = symbol.strip().upper()
	normalized_side = side.strip().upper()

	if not normalized_symbol:
		raise BinanceOrderValidationError("Symbol obbligatorio.")
	if normalized_side not in ALLOWED_SIDES:
		raise BinanceOrderValidationError("Side non valido. Usa BUY oppure SELL.")
	if quantity <= 0:
		raise BinanceOrderValidationError("Quantity deve essere maggiore di zero.")
	if price <= 0:
		raise BinanceOrderValidationError("Price deve essere maggiore di zero.")
	if stop_price <= 0:
		raise BinanceOrderValidationError("Stop price deve essere maggiore di zero.")

	binance_side = SIDE_BUY if normalized_side == "BUY" else SIDE_SELL
	client = create_client(settings)

	try:
		return client.create_order(
			symbol=normalized_symbol,
			side=binance_side,
			type=ORDER_TYPE_STOP_LOSS_LIMIT,
			timeInForce=TIME_IN_FORCE_GTC,
			quantity=quantity,
			price=price,
			stopPrice=stop_price,
		)
	except BinanceAPIException as exc:
		raise BinanceOrderError(f"Ordine rifiutato da Binance: {exc.message}") from exc
	except (BinanceRequestException, requests.exceptions.RequestException) as exc:
		raise BinanceConnectionError("Connessione Binance non disponibile") from exc

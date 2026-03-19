"""Client Binance e utilita' di autenticazione."""

from __future__ import annotations

import requests
from binance import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from utils.config import Settings


class BinanceClientError(RuntimeError):
	"""Errore generico lato Binance."""


class BinanceConnectionError(BinanceClientError):
	"""Errore di rete o connessione verso Binance."""


class BinanceAuthError(BinanceClientError):
	"""Credenziali Binance non valide o accesso negato."""


def create_client(settings: Settings) -> Client:
	"""Crea un client python-binance usando le credenziali fornite."""
	return Client(
		settings.binance_api_key,
		settings.binance_api_secret,
		testnet=settings.binance_testnet,
	)


def ping_client(client: Client) -> None:
	"""Verifica la connettivita' con l'API Binance."""
	try:
		client.ping()
	except (BinanceRequestException, requests.exceptions.RequestException) as exc:
		raise BinanceConnectionError("Ping Binance fallito") from exc


def verify_credentials(client: Client) -> None:
	"""Verifica che le credenziali siano valide con una chiamata autenticata."""
	try:
		client.get_account()
	except BinanceAPIException as exc:
		raise BinanceAuthError(
			f"Autenticazione Binance fallita: {exc.message}"
		) from exc
	except (BinanceRequestException, requests.exceptions.RequestException) as exc:
		raise BinanceConnectionError("Connessione Binance non disponibile") from exc


def init_and_test_client(settings: Settings) -> Client:
	"""Crea il client e valida connettivita' e credenziali."""
	client = create_client(settings)
	ping_client(client)
	verify_credentials(client)
	return client

"""Utility per il caricamento e la validazione della configurazione runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

ENV_FILE_NAME = ".env"
PLACEHOLDER_PREFIX = "inserisci"
TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Settings:
	"""Configurazione applicativa centralizzata.

	Attributes:
		binance_api_key: API key Binance.
		binance_api_secret: API secret Binance.
		binance_testnet: Flag per forzare testnet in ambiente dev.
		telegram_bot_token: Token del bot Telegram.
		telegram_allowed_user_id: Utente Telegram autorizzato a usare il bot.
		db_path: Percorso del file SQLite.
	"""

	binance_api_key: str
	binance_api_secret: str
	binance_testnet: bool
	telegram_bot_token: str
	telegram_allowed_user_id: int
	db_path: str


def load_settings(dotenv_path: Path | None = None) -> Settings:
	"""Carica e valida le impostazioni dal file `.env`.

	Args:
		dotenv_path: Percorso esplicito del file `.env`. Se omesso usa la root progetto.

	Returns:
		Settings: Configurazione validata.

	Raises:
		ValueError: Se una variabile obbligatoria e' assente o non valida.
	"""

	env_path = dotenv_path or _default_env_path()
	load_dotenv(dotenv_path=env_path, override=False)

	return Settings(
		binance_api_key=_get_required_str("BINANCE_API_KEY"),
		binance_api_secret=_get_required_str("BINANCE_API_SECRET"),
		binance_testnet=_get_bool("BINANCE_TESTNET", default=True),
		telegram_bot_token=_get_required_str("TELEGRAM_BOT_TOKEN"),
		telegram_allowed_user_id=_get_required_int("TELEGRAM_ALLOWED_USER_ID"),
		db_path=_get_optional_str("DB_PATH", default="./data/orders.db"),
	)


def _default_env_path() -> Path:
	return Path(__file__).resolve().parents[2] / ENV_FILE_NAME


def _get_required_str(name: str) -> str:
	raw_value = os.getenv(name)
	if raw_value is None:
		raise ValueError(f"Variabile ambiente obbligatoria mancante: {name}")

	value = raw_value.strip()
	if not value or value.lower().startswith(PLACEHOLDER_PREFIX):
		raise ValueError(f"Variabile ambiente non configurata correttamente: {name}")
	return value


def _get_optional_str(name: str, default: str) -> str:
	raw_value = os.getenv(name)
	if raw_value is None:
		return default

	value = raw_value.strip()
	return value or default


def _get_required_int(name: str) -> int:
	value = _get_required_str(name)
	try:
		return int(value)
	except ValueError as exc:
		raise ValueError(f"Variabile ambiente {name} deve essere un intero valido") from exc


def _get_bool(name: str, default: bool) -> bool:
	raw_value = os.getenv(name)
	if raw_value is None:
		return default

	value = raw_value.strip().lower()
	if value in TRUE_VALUES:
		return True
	if value in FALSE_VALUES:
		return False

	raise ValueError(
		f"Variabile ambiente {name} deve essere booleana (true/false, 1/0, yes/no)"
	)

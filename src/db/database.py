"""Utility per connessione e inizializzazione SQLite."""

from __future__ import annotations

from pathlib import Path
import sqlite3
import threading


class Database:
	"""Gestisce connessione e bootstrap schema SQLite.

	Args:
		db_path: Percorso del file database SQLite.
		schema_path: Percorso del file SQL con schema.
		lock: Lock condiviso per serializzare accessi concorrenti.
	"""

	def __init__(
		self,
		db_path: str,
		schema_path: str | None = None,
		lock: threading.Lock | None = None,
	) -> None:
		self._db_path = Path(db_path)
		self._schema_path = (
			Path(schema_path)
			if schema_path is not None
			else Path(__file__).with_name("schema.sql")
		)
		self._lock = lock or threading.Lock()

	@property
	def db_path(self) -> Path:
		"""Restituisce il path del database."""
		return self._db_path

	def initialize(self) -> None:
		"""Crea il database e applica lo schema se necessario."""
		self._db_path.parent.mkdir(parents=True, exist_ok=True)
		schema_sql = self._schema_path.read_text(encoding="utf-8")

		with self._lock:
			with self.connect() as connection:
				connection.executescript(schema_sql)

	def connect(self) -> sqlite3.Connection:
		"""Apre una connessione SQLite con row factory dizionario-like."""
		connection = sqlite3.connect(self._db_path)
		connection.row_factory = sqlite3.Row
		return connection

	@property
	def lock(self) -> threading.Lock:
		"""Restituisce il lock condiviso del database."""
		return self._lock

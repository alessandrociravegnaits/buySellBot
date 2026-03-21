"""Data Access Object per tabella orders."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any

from .database import Database


@dataclass(frozen=True)
class OrderRow:
	"""Rappresenta una riga della tabella orders.

	Attributes:
		id: Identificativo ordine.
		symbol: Simbolo di trading (es. BTCUSDT).
		side: Lato ordine (BUY/SELL).
		quantity: Quantita' ordine.
		price: Prezzo ordine (nullable per market).
		status: Stato ordine.
		note: Nota opzionale.
		created_at: Timestamp creazione.
		updated_at: Timestamp ultimo aggiornamento.
	"""

	id: int
	symbol: str
	side: str
	quantity: float
	price: float | None
	status: str
	note: str | None
	created_at: str
	updated_at: str


class OrdersDAO:
	"""DAO CRUD per la gestione ordini su SQLite."""

	def __init__(self, database: Database) -> None:
		self._database = database

	def create_order(
		self,
		symbol: str,
		side: str,
		quantity: float,
		status: str,
		price: float | None = None,
		note: str | None = None,
	) -> int:
		"""Inserisce un nuovo ordine e restituisce il suo ID."""
		query = (
			"INSERT INTO orders(symbol, side, quantity, price, status, note) "
			"VALUES(?, ?, ?, ?, ?, ?)"
		)

		with self._database.lock:
			with self._database.connect() as connection:
				cursor = connection.execute(
					query,
					(symbol, side, quantity, price, status, note),
				)
				return int(cursor.lastrowid)

	def get_order_by_id(self, order_id: int) -> OrderRow | None:
		"""Recupera un ordine per ID."""
		query = "SELECT * FROM orders WHERE id = ?"

		with self._database.lock:
			with self._database.connect() as connection:
				row = connection.execute(query, (order_id,)).fetchone()

		if row is None:
			return None

		return self._row_to_order(row)

	def list_orders(self, status: str | None = None, limit: int = 100) -> list[OrderRow]:
		"""Elenca ordini per stato opzionale con limite massimo."""
		safe_limit = max(1, min(limit, 1000))
		if status:
			query = (
				"SELECT * FROM orders WHERE status = ? "
				"ORDER BY id DESC LIMIT ?"
			)
			params: tuple[Any, ...] = (status, safe_limit)
		else:
			query = "SELECT * FROM orders ORDER BY id DESC LIMIT ?"
			params = (safe_limit,)

		with self._database.lock:
			with self._database.connect() as connection:
				rows = connection.execute(query, params).fetchall()

		return [self._row_to_order(row) for row in rows]

	def update_order_status(
		self,
		order_id: int,
		status: str,
		note: str | None = None,
	) -> bool:
		"""Aggiorna stato (e nota opzionale) di un ordine."""
		if note is None:
			query = (
				"UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP "
				"WHERE id = ?"
			)
			params: tuple[Any, ...] = (status, order_id)
		else:
			query = (
				"UPDATE orders SET status = ?, note = ?, "
				"updated_at = CURRENT_TIMESTAMP WHERE id = ?"
			)
			params = (status, note, order_id)

		with self._database.lock:
			with self._database.connect() as connection:
				cursor = connection.execute(query, params)
				return cursor.rowcount > 0

	def delete_order(self, order_id: int) -> bool:
		"""Elimina un ordine per ID."""
		query = "DELETE FROM orders WHERE id = ?"

		with self._database.lock:
			with self._database.connect() as connection:
				cursor = connection.execute(query, (order_id,))
				return cursor.rowcount > 0

	@staticmethod
	def _row_to_order(row: sqlite3.Row) -> OrderRow:
		return OrderRow(
			id=int(row["id"]),
			symbol=str(row["symbol"]),
			side=str(row["side"]),
			quantity=float(row["quantity"]),
			price=(float(row["price"]) if row["price"] is not None else None),
			status=str(row["status"]),
			note=(str(row["note"]) if row["note"] is not None else None),
			created_at=str(row["created_at"]),
			updated_at=str(row["updated_at"]),
		)

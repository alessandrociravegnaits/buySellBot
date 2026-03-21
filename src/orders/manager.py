"""Gestione centralizzata dei thread attivi per ordine."""

from __future__ import annotations

from dataclasses import dataclass
import threading

from orders.thread_worker import run_order_worker


@dataclass(frozen=True)
class ManagedOrderThread:
	"""Contesto thread associato a un ordine.

	Attributes:
		order_id: Identificativo ordine.
		thread: Thread worker dell'ordine.
		stop_event: Evento usato per fermare il worker.
		pause_event: Evento usato per mettere in pausa il worker.
	"""

	order_id: int
	thread: threading.Thread
	stop_event: threading.Event
	pause_event: threading.Event


ACTIVE_ORDER_THREADS: dict[int, ManagedOrderThread] = {}
_ACTIVE_THREADS_LOCK = threading.Lock()


def _prune_dead_threads() -> None:
	"""Rimuove dal dizionario i thread terminati."""
	dead_order_ids = [
		order_id
		for order_id, managed in ACTIVE_ORDER_THREADS.items()
		if not managed.thread.is_alive()
	]
	for order_id in dead_order_ids:
		ACTIVE_ORDER_THREADS.pop(order_id, None)


def start_order_thread(order_id: int) -> bool:
	"""Avvia il thread worker per un ordine se non gia' attivo.

	Args:
		order_id: Identificativo ordine.

	Returns:
		bool: True se il thread viene avviato, False se era gia' attivo.
	"""

	with _ACTIVE_THREADS_LOCK:
		_prune_dead_threads()
		existing = ACTIVE_ORDER_THREADS.get(order_id)
		if existing is not None and existing.thread.is_alive():
			return False

		stop_event = threading.Event()
		pause_event = threading.Event()
		thread = threading.Thread(
			target=run_order_worker,
			kwargs={
				"order_id": order_id,
				"stop_event": stop_event,
				"pause_event": pause_event,
			},
			name=f"order-worker-{order_id}",
			daemon=False,
		)
		ACTIVE_ORDER_THREADS[order_id] = ManagedOrderThread(
			order_id=order_id,
			thread=thread,
			stop_event=stop_event,
			pause_event=pause_event,
		)

	thread.start()
	return True


def pause_order_thread(order_id: int) -> bool:
	"""Mette in pausa il thread di un ordine attivo.

	Args:
		order_id: Identificativo ordine.

	Returns:
		bool: True se trovato e messo in pausa, False altrimenti.
	"""

	with _ACTIVE_THREADS_LOCK:
		managed = ACTIVE_ORDER_THREADS.get(order_id)
		if managed is None or not managed.thread.is_alive():
			return False
		managed.pause_event.set()
		return True


def resume_order_thread(order_id: int) -> bool:
	"""Riprende il thread di un ordine in pausa.

	Args:
		order_id: Identificativo ordine.

	Returns:
		bool: True se trovato e ripreso, False altrimenti.
	"""

	with _ACTIVE_THREADS_LOCK:
		managed = ACTIVE_ORDER_THREADS.get(order_id)
		if managed is None or not managed.thread.is_alive():
			return False
		managed.pause_event.clear()
		return True


def stop_order_thread(order_id: int, timeout_seconds: float = 5.0) -> bool:
	"""Ferma il thread di un ordine e attende la terminazione.

	Args:
		order_id: Identificativo ordine.
		timeout_seconds: Timeout massimo di join.

	Returns:
		bool: True se fermato con successo o non presente, False se ancora vivo dopo timeout.
	"""

	with _ACTIVE_THREADS_LOCK:
		managed = ACTIVE_ORDER_THREADS.pop(order_id, None)

	if managed is None:
		return True

	managed.stop_event.set()
	managed.thread.join(timeout=timeout_seconds)

	if managed.thread.is_alive():
		with _ACTIVE_THREADS_LOCK:
			ACTIVE_ORDER_THREADS[order_id] = managed
		return False

	return True


def stop_all_order_threads(timeout_seconds: float = 5.0) -> bool:
	"""Ferma tutti i thread ordine attivi.

	Args:
		timeout_seconds: Timeout massimo di join per singolo thread.

	Returns:
		bool: True se tutti fermati correttamente, False se almeno uno resta vivo.
	"""

	with _ACTIVE_THREADS_LOCK:
		order_ids = list(ACTIVE_ORDER_THREADS.keys())

	all_stopped = True
	for order_id in order_ids:
		stopped = stop_order_thread(order_id, timeout_seconds=timeout_seconds)
		if not stopped:
			all_stopped = False

	return all_stopped


def list_active_order_threads() -> list[int]:
	"""Restituisce gli ID ordine con thread attivo."""
	with _ACTIVE_THREADS_LOCK:
		_prune_dead_threads()
		return sorted(ACTIVE_ORDER_THREADS.keys())

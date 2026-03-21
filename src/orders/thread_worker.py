"""Worker thread dedicato al ciclo vita di un singolo ordine."""

from __future__ import annotations

import threading

DEFAULT_WORKER_SLEEP_SECONDS = 1.0


def run_order_worker(
	order_id: int,
	stop_event: threading.Event,
	pause_event: threading.Event,
	sleep_seconds: float = DEFAULT_WORKER_SLEEP_SECONDS,
) -> None:
	"""Esegue il loop del worker ordine finche' non arriva lo stop.

	Args:
		order_id: Identificativo ordine associato al worker.
		stop_event: Evento di stop graceful del thread.
		pause_event: Evento di pausa del worker (set => pausa attiva).
		sleep_seconds: Intervallo base di attesa fra due cicli.
	"""

	_ = order_id
	while not stop_event.is_set():
		if pause_event.is_set():
			stop_event.wait(timeout=sleep_seconds)
			continue

		stop_event.wait(timeout=sleep_seconds)

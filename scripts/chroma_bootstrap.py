"""Bootstrap e healthcheck del contesto ChromaDB per buySellBot."""

from __future__ import annotations

import argparse
from typing import Final

import chromadb

COLLECTION_NAME: Final[str] = "buySellBot_context"
DEFAULT_DOCS: Final[list[tuple[str, str]]] = [
    (
        "ctx_architettura",
        "Architettura: thread per ordine, monitor BTC dedicato, menu Telegram testuale",
    ),
    (
        "ctx_stack",
        "Stack: Python 3.10, python-binance 1.0.x, python-telegram-bot 20.x async, SQLite",
    ),
    (
        "ctx_sicurezza",
        "Sicurezza: BINANCE_TESTNET=true in dev, validazione TELEGRAM_ALLOWED_USER_ID",
    ),
    (
        "ctx_pattern",
        "Pattern: threading.Event per pause, threading.Lock su DB, async handlers",
    ),
    ("ctx_binance_testnet_url", "Binance testnet URL: https://testnet.binance.vision"),
]


def build_client(host: str, port: int) -> chromadb.HttpClient:
    """Crea il client HTTP ChromaDB."""
    return chromadb.HttpClient(host=host, port=port)


def ensure_collection(
    client: chromadb.HttpClient,
    collection_name: str,
    init_defaults: bool,
) -> None:
    """Verifica collection e opzionalmente inizializza i documenti default."""
    collection = client.get_or_create_collection(name=collection_name)
    count_before = collection.count()
    print(f"Collection '{collection_name}' presente. count={count_before}")

    if not init_defaults:
        peek = collection.peek(limit=5)
        print(f"Peek IDs: {peek.get('ids', [])}")
        return

    ids = [doc_id for doc_id, _ in DEFAULT_DOCS]
    documents = [document for _, document in DEFAULT_DOCS]
    existing = set(collection.get(ids=ids).get("ids", []))

    ids_to_add: list[str] = []
    docs_to_add: list[str] = []
    for doc_id, doc_text in DEFAULT_DOCS:
        if doc_id not in existing:
            ids_to_add.append(doc_id)
            docs_to_add.append(doc_text)

    if ids_to_add:
        collection.add(ids=ids_to_add, documents=docs_to_add)
        print(f"Aggiunti {len(ids_to_add)} documenti di default.")
    else:
        print("Documenti default già presenti: nessuna aggiunta necessaria.")

    count_after = collection.count()
    peek = collection.peek(limit=5)
    print(f"Count finale: {count_after}")
    print(f"Peek IDs: {peek.get('ids', [])}")


def parse_args() -> argparse.Namespace:
    """Parsa gli argomenti CLI."""
    parser = argparse.ArgumentParser(description="Healthcheck/bootstrap ChromaDB")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--collection", default=COLLECTION_NAME)
    parser.add_argument(
        "--init-defaults",
        action="store_true",
        help="Aggiunge i 5 documenti default se mancanti.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point script."""
    args = parse_args()
    client = build_client(args.host, args.port)
    ensure_collection(client, args.collection, args.init_defaults)


if __name__ == "__main__":
    main()

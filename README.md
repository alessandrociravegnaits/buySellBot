# buySellBot

## ChromaDB: uso consigliato (sviluppo vs produzione)

### Sviluppo (manuale)
- Avvia ChromaDB in persistenza locale:
	- `./venv/bin/chroma run --host localhost --port 8000 --path ./chroma_data`
- Verifica/bootstrap manuale del contesto:
	- `./venv/bin/python scripts/chroma_bootstrap.py --host localhost --port 8000 --collection buySellBot_context --init-defaults`

### Produzione
- Non usare auto-inizializzazione (`--init-defaults`) all'avvio applicativo.
- Consentito solo healthcheck read-only (no add/update/delete).
- Mantieni path persistente stabile per ChromaDB e verifica tenant/database corretti.

### Nota operativa
- Se il server si riavvia e il contesto non compare, controlla prima:
	- endpoint API v2 (`/api/v2/heartbeat`)
	- path dati (`--path`)
	- collection nel tenant/database attivo.

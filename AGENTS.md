# AGENTS.md — buySellBot


## Identita del Progetto
- Nome: buySellBot
- Tipo: Bot Python per trading automatico Binance con interfaccia Telegram
- Uso: Applicazione personale, single-user


## Stack e Versioni
- Python 3.10
- python-binance 1.0.x
- python-telegram-bot 20.x (async API)
- python-dotenv 1.0.x
- SQLite 3 (via sqlite3 stdlib)
- sentry-sdk 1.x


## Struttura Cartelle
src/
  main.py            # Entry point, avvia bot e monitor
  bot/
    handlers.py      # Handler comandi e messaggi Telegram
    menus.py         # Logica navigazione menu
    keyboards.py     # ReplyKeyboard e InlineKeyboard
  binance_client/
    client.py        # Wrapper python-binance, init con testnet support
    order_types.py   # Funzioni per ogni tipo di ordine
  orders/
    order.py         # Dataclass Order
    manager.py       # Gestione dizionario ordini attivi
    thread_worker.py # Worker thread per ogni ordine
  monitor/
    btc_monitor.py   # Thread BTC dedicato
    threshold.py     # Logica superamento soglie
    trailing.py      # Logica trailing
  db/
    database.py      # Connessione SQLite, init schema
    dao.py           # Data Access Object ordini
    schema.sql       # DDL tabelle
  utils/
    logger.py        # Logger strutturato
    config.py        # Caricamento .env
    enums.py         # Enum OrderType, Timeframe, OrderStatus


## Workflow Obbligatorio (seguilo sempre)
0. Leggi AGENTS.md (questo file)
1. Identifica issue GitHub corrente
2. Crea un branch dedicato per ogni issue, con naming convention issue-N-titolo (es: issue-6-ordine-mercato)
3. context7: resolve-library-id per librerie usate nell'issue
4. context7: get-library-docs per API rilevanti
5. filesystem: leggi file esistenti coinvolti
6. chromadb: query per contesto issue simili precedenti
7. Scrivi/modifica codice
8. filesystem: salva modifiche
9. github: commit su branch issue-N (es: issue-6-ordine-mercato)
10. Fai push del branch issue-N su origin
11. Apri una pull request collegata all'issue

Regola operativa: quando un'issue e' completata, chiudi sempre il ciclo nello stesso turno con commit + push + PR (salvo blocchi esterni).


## Convenzioni di Codice Python
- PEP8 obbligatorio
- Type hints su tutte le funzioni pubbliche
- Docstring Google style su classi e metodi pubblici
- Async/await per handlers Telegram (python-telegram-bot 20.x e' async)
- threading.Thread per worker ordini, threading.Event per pause
- sqlite3 con context manager (with conn:) per transazioni
- f-string per interpolazione, mai % o .format()
- Costanti in UPPER_SNAKE_CASE in utils/config.py


## Regole di Sicurezza
- ZERO credenziali hardcoded: tutto da os.getenv()
- Validare TELEGRAM_ALLOWED_USER_ID su ogni update prima di processarlo
- Usare BINANCE_TESTNET=true durante sviluppo
- .env e .vscode/mcp.json non vanno mai committati
- .vscode/mcp.json e' locale: non va stashed; usa .vscode/mcp.example.json come template
- ChromaDB: per verifiche usa solo list/get/peek/count; non usare delete come ping
- Logging: non loggare mai chiavi API o token
- Ordini reali: doppia conferma via Telegram prima di esecuzione


## Gestione Thread
- Ogni ordine ha il proprio threading.Thread
- Usa threading.Event per stop e pause
- Accesso condiviso a DB: usa threading.Lock
- BTC monitor: thread dedicato sempre attivo se BTC_MONITOR_ENABLED=true
- Non terminare thread brutalmente: usa Event.set() e join()


## Quando Fermarsi e Chiedere
- Prima di eseguire ordini REALI su Binance
- Se la logica di singolarita BTC non e' chiara
- Se una modifica tocca piu di 3 file contemporaneamente
- Prima di modificare lo schema DB (migration needed)
- Se un thread solleva eccezione non gestita

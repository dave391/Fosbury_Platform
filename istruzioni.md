PROBLEMA
Ogni volta che un utente apre /dashboard o /strategy, il sistema chiama gli exchange
(Deribit, Bitmex) via CCXT per fetchare i balance. Ogni chiamata richiede 500ms-2s.
Con più strategie attive, il page load arriva a 3-6 secondi.
I punti esatti dove succede:

build_active_strategy_rows in strategy_service.py: crea task async con semaphore,
apre client CCXT per ogni account, chiama fetch_usdc_balance, poi chiude il client.
Questo viene chiamato sia dalla dashboard che dalla strategy page.
get_strategy_page_data in strategy_service.py: apre un client CCXT per leggere
il balance da mostrare nella pagina strategy.

OBIETTIVO
Spostare il fetch dei balance in un cronjob dedicato. Le pagine web leggono solo dal database.
COSA FARE
A. Migrazione schema
Aggiungere due colonne alla tabella exchange_accounts in core/models.py:

cached_balance_usdc (Float, nullable, default None)
balance_updated_at (DateTime con timezone, nullable, default None)

Creare uno script di migrazione in scripts/ seguendo lo stesso pattern degli script
esistenti (migrate_add_decision_log.py, migrate_add_strategies_tables.py).
Usare ALTER TABLE ... ADD COLUMN IF NOT EXISTS per renderlo idempotente.
B. Nuovo cronjob run_balance_cache.py
Creare scripts/cronjob/run_balance_cache.py come file NUOVO e SEPARATO.
NON modificare run_equity_snapshot_batch.py — sono due job con responsabilità diverse:

equity_snapshot gira 1 volta al giorno, fotografa l'equity delle strategie
balance_cache gira ogni 5-10 minuti, aggiorna il balance degli account

Seguire esattamente lo stesso pattern strutturale di run_equity_snapshot_batch.py:

Usa AsyncSessionLocal da core.database
Stessa struttura: load → loop → try/except per account → commit → log riepilogativo
Eseguibile con: python -m scripts.cronjob.run_balance_cache

Logica del cronjob:

Caricare TUTTI gli ExchangeAccount con disabled_at IS NULL
Per ogni account, determinare quale strategy_key usare per fetch_usdc_balance:

Cercare le Strategy attive (status=ACTIVE) su quell'account
Se ci sono strategy attive: usare la strategy_key della prima trovata.
(In pratica ogni account ha una sola strategy_key attiva — il sistema lo impone
in start_strategy. Il "prima trovata" è solo un fallback difensivo.)
Se NON ci sono strategy attive: usare DEFAULT_STRATEGY_KEY dal registry
(cash_funding). Questo serve perché un utente potrebbe avere un account
collegato senza strategie attive, e la pagina /strategy deve comunque
mostrare il balance disponibile.


Ottenere la strategy_impl dal registry con quella key
Aprire il client CCXT tramite ExchangeService.get_exchange_client_by_account
Chiamare strategy_impl.fetch_usdc_balance(exchange, adapter) per ottenere il balance
Salvare il risultato:

account.cached_balance_usdc = balance
account.balance_updated_at = datetime.now(timezone.utc)


Chiudere SEMPRE il client CCXT (nel finally)
Se un account fallisce (errore CCXT, credenziali invalide, timeout), loggare
l'errore e continuare con il prossimo account. Mai bloccare il job.
A fine ciclo, stampare un log riepilogativo come fa run_equity_snapshot_batch:
totale account, aggiornati con successo, saltati per errore.

C. Rimuovere le chiamate exchange da build_active_strategy_rows
In strategy_service.py, nel metodo build_active_strategy_rows:
ELIMINARE tutta la sezione che contiene:

La variabile available_by_pair
Il semaphore = asyncio.Semaphore(4)
La funzione interna async def fetch_balance
Il set account_strategy_pairs
La lista tasks
Il asyncio.gather(*tasks)

SOSTITUIRE con una lettura diretta dal campo cache. L'oggetto account è già
caricato in accounts_by_id. Per ogni account, il balance è semplicemente:
account.cached_balance_usdc or 0.0
Il campo exchange_available_usdc nella riga viene popolato da questo valore
invece che da available_by_pair.
D. Rimuovere la chiamata exchange da get_strategy_page_data
In strategy_service.py, nel metodo get_strategy_page_data:
ELIMINARE la sezione che fa:

exchange = await self.exchange_service.get_exchange_client_by_account(...)
usdc_balance = await strategy_impl.fetch_usdc_balance(exchange, adapter)
Il blocco try/except/finally con exchange.close()

SOSTITUIRE con: caricare l'ExchangeAccount selezionato e leggere
account.cached_balance_usdc or 0.0 come usdc_balance.
L'account selezionato è già identificato dalla logica esistente (selected_account).
Basta fare una query per l'ExchangeAccount con quell'id (o aggiungerlo al
dizionario exchange_accounts che già viene costruito).
E. NON TOCCARE le operazioni live
Le seguenti funzioni DEVONO continuare a chiamare l'exchange in tempo reale:

start_strategy — verifica il balance reale prima di aprire posizioni
add_capital — verifica il balance reale prima di aggiungere capitale
remove_capital — esegue operazioni sull'exchange
stop_strategy — esegue operazioni sull'exchange

Queste sono azioni utente che richiedono dati live. Il cache è solo per
la visualizzazione. Se il balance cachato non corrisponde a quello reale al momento
dell'azione, l'utente riceve un messaggio di errore ("Insufficient balance") —
che è il comportamento corretto e sicuro.
NOTA SUL DATABASE
Questo cambiamento NON fa crescere il database. Non aggiungiamo righe — aggiungiamo
due colonne a una tabella esistente. Il cronjob AGGIORNA le colonne, non crea
nuove righe. Se ci sono 10 account, restano 10 righe.
VINCOLI

Codice snello, non verboso
Segui lo stesso stile del resto della codebase
Il cronjob è un file nuovo e separato, non va nel cronjob esistente
Non aggiungere dipendenze
Non toccare le operazioni live (start/add/remove/stop)

TEST DI VERIFICA

Lo script di migrazione gira senza errori e aggiunge le colonne
python -m scripts.cronjob.run_balance_cache gira e popola cached_balance_usdc
su tutti gli account attivi (con e senza strategie attive)
GET /dashboard risponde sotto 500ms senza chiamate exchange (nessun log CCXT)
GET /strategy mostra il balance corretto letto dal cache
start/add/remove/stop continuano a funzionare con chiamate exchange live
Se un account ha credenziali invalide, il cronjob logga l'errore e continua
con gli altri account senza bloccarsi
Nella pagina /strategy c'è un wizard a 3 step per lanciare una nuova strategia.
Allo step 3 ("Capital to deploy") c'è il campo "Available: x.xx USDT/USDC" che
mostra il saldo di stablecoin disponibili sull'exchange per aprire nuove posizioni.
Oggi quel dato viene dal campo cached_balance_usdc nel database, aggiornato dal
cronjob ogni 5-10 minuti. Ma questo dato può essere stale: se l'utente ha appena
fermato una strategia, le stablecoin si liberano immediatamente sull'exchange ma
il cache non lo sa ancora.
Il campo "Available" deve mostrare il dato LIVE dall'exchange, non il cache.
OBIETTIVO
Creare un endpoint API leggero che restituisce il balance live delle stablecoin
da un exchange account specifico. Il JS chiama questo endpoint quando l'utente
arriva allo step 3 del wizard.
COSA FARE
A. Nuovo endpoint in app/routers/strategy.py
Aggiungere un endpoint GET /strategy/live-balance che:

Riceve come query params: exchange_account_id (int) e strategy_key (string)
Carica l'ExchangeAccount e verifica che appartenga all'utente
Crea il client CCXT tramite exchange_service.get_exchange_client_by_account
Ottiene la strategy_impl dal registry con la strategy_key
Chiama strategy_impl.fetch_usdc_balance(exchange, adapter) — questo restituisce
il saldo delle stablecoin (USDC su Deribit, USDT su Bitmex) disponibili per
aprire nuove posizioni, NON il balance complessivo dell'account
Chiude il client CCXT (nel finally)
Restituisce JSON: {"balance": <float>, "quote_currency": <string>}

In caso di errore (account non trovato, credenziali mancanti, exchange timeout):
restituire {"balance": 0.0, "quote_currency": "USD", "error": "..."} con status 200
(non 500 — il JS deve gestirlo in modo semplice).
L'endpoint deve essere snello. Non deve caricare strategie attive, non deve
calcolare metriche, non deve fare query complesse. Solo: apri connessione exchange →
leggi balance stablecoin → chiudi → rispondi.
Per ricavare la quote_currency, usa la stessa logica già presente in strategy_service:
self._get_quote_currency(strategy_impl, exchange_name). Puoi anche usare direttamente
le rules della strategy: ogni strategy ha get_exchange_rules(exchange_id) che
restituisce un dict con la chiave "quote" (es. "USDC" o "USDT").
B. Modificare il JS in app/static/strategy.js

Aggiungere una funzione fetchLiveBalance() che:

Legge exchange_account_id dal dropdown account attualmente selezionato
Legge strategy_key dalla card strategy selezionata
Se uno dei due manca, non fa nulla
Chiama fetch("/strategy/live-balance?exchange_account_id=X&strategy_key=Y")
Aggiorna gli elementi [data-usdc-balance] con il balance ricevuto
Aggiorna gli elementi [data-usdc-max] con il balance come max
Aggiorna latestBalance con il nuovo valore


Nel wizard, quando l'utente arriva allo step 3 (cioè dentro setStep
quando currentStep diventa l'ultimo step):

Mostrare temporaneamente "Loading..." nel campo balance
Chiamare fetchLiveBalance()
Quando la risposta arriva, aggiornare il campo con il valore reale


Il balance mostrato da /strategy/data (cache) resta per il caricamento
iniziale della pagina. Il fetch live SOVRASCRIVE quel valore solo quando
l'utente arriva allo step 3.

C. NON modificare il caricamento iniziale della pagina
/strategy/data continua a restituire il balance dal cache per il render iniziale.
Il fetch live è un'aggiunta, non una sostituzione. La pagina si apre veloce
(cache), e il dato viene rinfrescato quando serve (step 3).
VINCOLI

L'endpoint deve essere leggero: solo balance stablecoin, niente query extra
Timeout ragionevole: se l'exchange non risponde in 6 secondi, restituire
il balance dal cache come fallback
Non aggiungere dipendenze
Non modificare il cronjob o il balance cache
Non rompere il flusso esistente del wizard

TEST DI VERIFICA

Aprire /strategy — la pagina si carica velocemente con il balance dal cache
Navigare nel wizard fino allo step 3 — il campo "Available" mostra brevemente
"Loading..." e poi si aggiorna con il balance live
Fermare una strategia, tornare su /strategy, andare allo step 3 — il balance
riflette immediatamente le stablecoin liberate, senza aspettare il cronjob
Se l'exchange non risponde, il campo mostra comunque un valore (dal cache)
e non resta bloccato su "Loading..."
Cambiare account nel dropdown e tornare allo step 3 — il balance si aggiorna
per il nuovo account
Nessun errore nella console JS
CONTESTO
Fosbury Platform. Hai tutta la codebase in contesto.
Quando un utente tenta stop o remove su una strategia HLP durante
il lock-up di 4 giorni, Hyperliquid ritorna un errore specifico.
Ma la UI mostra solo "Error stopping strategy" generico.

OBIETTIVO
Far arrivare il messaggio di errore dell'exchange fino alla UI,
senza creare eccezioni speciali o ramificazioni.

COSA FARE

1. In app/services/strategies/hlp/__init__.py, nel metodo _vault_transfer:
   quando response.get("status") != "ok", il messaggio di errore è in
   response.get("response") (è una stringa con il messaggio di Hyperliquid).
   Assicurati che il ValueError che viene sollevato includa quel messaggio.
   Es: raise ValueError(response.get("response") or "Vault transfer failed")

2. Verifica in app/routers/strategy.py come vengono gestiti gli errori
   di stop_strategy e remove_capital. Attualmente i ValueError dovrebbero
   già propagarsi alla UI come messaggio di errore visibile (stesso
   pattern di "Insufficient balance" o "Minimum amount is X"). Se il
   router cattura ValueError e mostra str(e) all'utente, non serve
   nessuna modifica al router.

   Se invece il router cattura Exception generica e mostra un messaggio
   fisso ("Error stopping strategy"), cambia solo il blocco except per
   i ValueError — mostrali come messaggio all'utente (come già fa per
   start e add). Le Exception generiche restano con il messaggio fisso.

COSA NON FARE
- Non aggiungere logica specifica per HLP nel router
- Non creare classi di eccezione custom
- Non modificare strategy_service.py
- La fix deve essere universale: qualsiasi ValueError con messaggio
  parlante da qualsiasi strategia deve arrivare alla UI

TEST DI VERIFICA
- Avvia una strategia HLP con deposito
- Prova stop prima dei 4 giorni di lock-up
- La UI deve mostrare il messaggio di errore specifico di Hyperliquid
  (es. "Vault withdrawal locked until...") invece di "Error stopping strategy"
- Prova la stessa cosa con remove
- Verifica che stop/remove su Bitmex/Deribit continuano a funzionare
  normalmente (nessuna regressione)
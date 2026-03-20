CONTESTO
Abbiamo verificato con script di debug che su Hyperliquid il margine
removibile da una posizione isolata si calcola come:

  required = max(notional / leverage, 0.1 * notional)
  max_withdrawable = max(collateral - required, 0.0)

dove collateral è il margine totale (include unrealized PnL), notional
è size * mark_price, e leverage è la leva impostata. La formula è
verificata con dati reali e il reduce_margin funziona.

Il problema attuale: la funzione scale_up in logic.py usa una formula
per max_removable che funziona per Bitmex ma non per Hyperliquid,
perché i campi margin/initialMargin hanno semantica diversa.

La soluzione concordata: l'adapter Hyperliquid calcola max_withdrawable
e lo ritorna nel dict di fetch_position_info. scale_up lo usa se
presente, altrimenti usa la formula esistente per Bitmex/Deribit.

OBIETTIVO
Implementare max_withdrawable nell'adapter e usarlo in scale_up.

COSA FARE

1. In app/services/exchanges/hyperliquid.py, nel metodo fetch_position_info:

   Dopo aver estratto tutti i campi, calcola max_withdrawable:

   collateral_val = float(margin or 0.0)  # margin è già letto da collateral
   leverage_val = float(leverage or 1.0)
   mark = float(mark_price or 0.0)
   size_val = float(size or 0.0)
   notional = size_val * mark if mark > 0 else 0.0
   required = max(notional / leverage_val, 0.1 * notional) if leverage_val > 0 and notional > 0 else collateral_val
   max_withdrawable = max(collateral_val - required, 0.0)

   Aggiungi al dict ritornato:
   "max_withdrawable": float(max_withdrawable),

   Nota: mark_price potrebbe essere 0 (Hyperliquid non lo include
   in fetch_positions). In quel caso max_withdrawable sarà 0.0 —
   è un fallback conservativo accettabile perché scale_up riceverà
   il mark_price dall'orchestrator e potrà comunque operare.

   CORREZIONE: per avere il mark_price nel calcolo, usa il fetch_ticker
   che abbiamo già aggiunto per risolvere il problema mark_price=null.
   Il mark_price nel dict dovrebbe già essere popolato dal fetch_ticker.
   Usa quello per il calcolo di notional.

2. In app/services/strategies/nv1/logic.py, nella funzione scale_up:

   DOPO il calcolo esistente di max_removable (non toccarlo), aggiungi:

   # Use adapter-reported max_withdrawable if available
   adapter_max = float((position_info or {}).get("max_withdrawable") or 0.0)
   if adapter_max > 0:
       max_removable = min(float(margin_to_use), float(adapter_max)) * float(removable_factor)

   SUBITO DOPO aggiungi il check per evitare chiamate con amount=0:

   if max_removable <= 0:
       return {"executed": False, "reason": "no removable margin available",
               "strategy": strategy}

   Questo blocco va inserito DOPO il calcolo di max_removable e PRIMA
   della chiamata a adapter.remove_margin.

   Il log esistente "nv1_scale_up_removable" deve stampare il valore
   finale di max_removable (dopo l'eventuale override da adapter_max).

COSA NON FARE
- Non modificare la formula esistente di max_removable (serve per Bitmex)
- Non aggiungere max_withdrawable agli adapter Bitmex o Deribit
- Non aggiungere if per exchange_id in logic.py
- Non toccare altri metodi in logic.py (add, remove, stop, scale_down)

TEST DI VERIFICA
- python -m compileall app (nessun errore)
- Con una posizione Hyperliquid con margine in eccesso, l'orchestrator
  deve: calcolare max_withdrawable > 0, eseguire scale_up con successo
- Con una posizione Bitmex, scale_up deve funzionare come prima
  (max_withdrawable non presente nel dict, usa formula esistente)
- Non devono più apparire errori "Update to isolated margin cannot be zero"
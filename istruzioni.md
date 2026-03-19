Hyperliquid non include markPrice nella risposta di fetch_positions.
L'adapter ritorna mark_price: 0.0, e l'orchestrator non riesce a
calcolare liquidation_distance_pct e excess_margin.

OBIETTIVO
Nell'adapter Hyperliquid, se markPrice è null dopo fetch_positions,
recupera il prezzo da fetch_ticker.

COSA FARE

In app/services/exchanges/hyperliquid.py, modifica fetch_position_info.

Dopo aver estratto mark_price dalla posizione, se è None o 0,
fetcha il ticker per quel symbol e usa il prezzo:

    mark_price = to_float(position.get("markPrice"))
    if not mark_price:
        try:
            ticker = await exchange.fetch_ticker(symbol)
            mark_price = to_float(
                ticker.get("last")
                or ticker.get("close")
                or ticker.get("mark")
            )
        except Exception:
            mark_price = None

Il resto del metodo resta invariato.

COSA NON FARE
- Non toccare logic.py, orchestrator, o position_manager
- Non aggiungere retry o logica complessa
- Se anche fetch_ticker fallisce, mark_price resta 0.0 — il position_manager
  gestisce già il caso con il warning

Su Hyperliquid c'è un mismatch tra la size spot e perp perché
_align_base_to_perp_precision in common.py scatta solo per Bitmex.
Per gli altri exchange ritorna base_amount invariato, e poi
spot_amount_to_precision e perp_amount_to_precision arrotondano
indipendentemente con precision diverse.

OBIETTIVO
Fare in modo che _align_base_to_perp_precision applichi l'arrotondamento
alla precision del perp per TUTTI gli exchange, non solo Bitmex.
Questo garantisce che spot e perp partano dalla stessa base amount.

COSA FARE

In app/services/strategies/common.py, modifica _align_base_to_perp_precision.

Il comportamento attuale per Bitmex (che gestisce contractSize e multiplier)
deve restare. Ma DOPO il check Bitmex, invece di ritornare base_amount
invariato, arrotonda alla precision del perp:

def _align_base_to_perp_precision(
    exchange, perp_symbol: str, base_amount: float, perp_price: float
) -> float:
    # logica Bitmex esistente (non toccare)
    if exchange_id(exchange) == "bitmex":
        ... (codice esistente invariato) ...

    # Per tutti gli altri exchange: arrotonda alla precision del perp
    precise = exchange.amount_to_precision(perp_symbol, base_amount)
    try:
        return float(precise)
    except (TypeError, ValueError):
        return base_amount

In questo modo base_amount viene prima arrotondato alla precision del perp,
e poi spot_amount_to_precision lo arrotonderà ulteriormente alla precision
dello spot — ma siccome il perp ha tipicamente la precision più grossolana,
lo spot riceverà un numero già compatibile.

COSA NON FARE
- Non toccare la logica Bitmex esistente
- Non toccare logic.py
- Non aggiungere logica specifica per Hyperliquid
Questo fix è universale — migliorerà l'allineamento anche su Deribit, non solo su Hyperliquid.
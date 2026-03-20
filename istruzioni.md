CONTESTO
Fosbury Platform. Hai tutta la codebase in contesto.

La funzione scale_up in logic.py calcola:
    max_removable = (current_margin - initial_margin - unrealized_pnl) * factor

Dove current_margin viene da position_info["margin"], initial_margin
da position_info["initial_margin"], e unrealized_pnl da
position_info["unrealized_pnl"].

Su Bitmex questo funziona perché "margin" (posMargin) NON include
l'unrealized PnL — sono valori separati.

Su Hyperliquid il campo "collateral" (che mappiamo a "margin") GIÀ
INCLUDE l'unrealized PnL. Quindi sottrarre unrealized_pnl lo toglie
due volte, e max_removable è sempre ~0.

La documentazione Hyperliquid dice che da una posizione isolata puoi
rimuovere margine purché resti:
    transfer_margin_required = max(initial_margin, 0.1 * notional)

OBIETTIVO
Fare in modo che fetch_position_info di Hyperliquid ritorni il campo
"margin" SENZA l'unrealized PnL incluso, così la formula di scale_up
funziona correttamente senza modifiche a logic.py.

COSA FARE

In app/services/exchanges/hyperliquid.py, nel metodo fetch_position_info,
dopo aver estratto i campi dalla posizione CCXT:

    margin = to_float(position.get("collateral"))
    unrealized_pnl = to_float(position.get("unrealizedPnl"))

Aggiungi: se entrambi sono disponibili, sottrai l'unrealized PnL dal
margin per restituire il margine "puro" (senza PnL), coerente con
come Bitmex espone posMargin:

    if margin is not None and unrealized_pnl is not None:
        margin = margin - unrealized_pnl

In questo modo:
- margin ritornato = collateral - unrealized_pnl = margine puro allocato
- La formula in scale_up: (margin - initial_margin - unrealized_pnl)
  diventa: (collateral - upnl - initial_margin - upnl)

No, aspetta. Questo non è corretto perché scale_up sottrae di nuovo
unrealized_pnl.

CORREZIONE — approccio diverso:

Non modificare fetch_position_info. Invece, il problema è che la formula
di scale_up assume che "margin" non includa unrealized_pnl. Su Hyperliquid
lo include. La soluzione corretta è nella formula.

In app/services/strategies/nv1/logic.py, nella funzione scale_up,
la formula attuale è:

    max_removable = max(
        float((current_margin - initial_margin - unrealized_pnl) * removable_factor),
        0.0
    )

Questa formula funziona per Bitmex dove margin non include unrealized_pnl.
Per Hyperliquid dove margin (collateral) include unrealized_pnl, la
formula corretta è:

    max_removable = max(
        float((current_margin - initial_margin) * removable_factor),
        0.0
    )

Perché current_margin già include unrealized_pnl, e initial_margin è
il requisito minimo. La differenza è il margine removibile.

Ma non possiamo mettere un if per exchange in logic.py.

SOLUZIONE PULITA:
Fai sì che fetch_position_info dell'adapter Hyperliquid ritorni un
campo "margin" che rappresenta il margine ALLOCATO SENZA unrealized PnL,
coerente con quello che ritorna Bitmex. Così la formula di scale_up
funziona senza modifiche.

In app/services/exchanges/hyperliquid.py, fetch_position_info:

    collateral = to_float(position.get("collateral"))
    unrealized_pnl = to_float(position.get("unrealizedPnl"))
    
    # Hyperliquid "collateral" includes unrealized PnL.
    # Subtract it to return pure allocated margin, consistent with Bitmex.
    margin = collateral
    if collateral is not None and unrealized_pnl is not None:
        margin = collateral - unrealized_pnl

Verifica con i numeri dai log:
- collateral = 19.46
- unrealized_pnl = 2.65
- margin restituito = 19.46 - 2.65 = 16.81
- initial_margin = 16.80
- scale_up formula: (16.81 - 16.80 - 2.65) * 0.99 = ancora negativo!

No, non funziona neanche così. Il problema è che scale_up sottrae
SEMPRE unrealized_pnl nella formula.

APPROCCIO DEFINITIVO — il più semplice e corretto:

Il vero campo che serve è quanto margine puoi rimuovere dalla posizione.
Su Hyperliquid è: collateral - max(initial_margin, 0.1 * notional).
Su Bitmex è: margin - initial_margin - abs(unrealized_pnl).

Sono formule diverse. La formula in scale_up è specifica per Bitmex.

La soluzione più pulita: aggiungi un campo "max_withdrawable" nel dict
ritornato da fetch_position_info. Ogni adapter lo calcola a modo suo.
scale_up usa quel campo quando è presente, altrimenti usa la formula
attuale.

In app/services/exchanges/hyperliquid.py, fetch_position_info:

    collateral = to_float(position.get("collateral")) or 0.0
    initial_margin = to_float(position.get("initialMargin")) or 0.0
    size = abs(to_float(position.get("contracts")) or 0.0)
    mark_price = ... (già fetchato)
    notional = size * mark_price if mark_price else 0.0
    transfer_margin_req = max(initial_margin, 0.1 * notional)
    max_withdrawable = max(collateral - transfer_margin_req, 0.0)

    Aggiungi al dict ritornato:
    "max_withdrawable": float(max_withdrawable),

In app/services/strategies/nv1/logic.py, nella funzione scale_up,
DOPO il calcolo di max_removable esistente, aggiungi:

    # Use adapter-reported max_withdrawable if available (e.g. Hyperliquid)
    adapter_max = float((position_info or {}).get("max_withdrawable") or 0.0)
    if adapter_max > 0:
        max_removable = min(float(margin_to_use), float(adapter_max)) * removable_factor

    Subito dopo aggiungi il check:
    if max_removable <= 0:
        return {"executed": False, "reason": "no removable margin available",
                "strategy": strategy}

Questo è universale:
- Su Bitmex/Deribit: max_withdrawable non è nel dict → viene ignorato →
  usa la formula esistente
- Su Hyperliquid: max_withdrawable è nel dict → usa quello

COSA NON FARE
- Non modificare la formula esistente di max_removable (serve per Bitmex)
- Non aggiungere if per exchange_id in logic.py
- Non aggiungere max_withdrawable agli adapter Bitmex/Deribit (non serve)

TEST DI VERIFICA
- Con una posizione ETH isolata su Hyperliquid in profitto
- fetch_position_info deve ritornare max_withdrawable > 0
- L'orchestrator deve eseguire scale_up con successo (rimuovere margine,
  comprare spot, vendere perp)
- Su Bitmex tutto deve continuare a funzionare come prima
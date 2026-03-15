CORREZIONI DA APPLICARE
Correzione 1 — Estrarre funzioni helper condivise da logic.py
Il file app/services/strategies/nv1/logic.py è 764 righe. Le righe 1-270 circa sono funzioni helper (resolve_symbol, get_last_price, amount_to_precision, _market_cost_step, _perp_notional_step, _align_base_amount, _align_base_to_perp_precision, spot_amount_to_precision, to_perp_amount, perp_amount_to_precision, _log_sizes, weighted_avg, _exchange_id, _get_rules, _validate_asset, _pick_market, build_strategy_config, ensure_strategy_config) che sono copiate quasi identiche da cash_funding/logic.py.
Cosa fare:

Creare il file app/services/strategies/common.py
Spostare tutte le funzioni helper che sono identiche o quasi identiche tra cash_funding e nv1 in questo file
In nv1/logic.py, sostituire le funzioni spostate con import da common.py
NON toccare cash_funding/logic.py — cash_funding continua a usare le sue copie locali. In futuro potrebbe importare da common.py, ma quel refactor non è per oggi.

Le funzioni da spostare in common.py sono quelle che non hanno dipendenze dalle rules specifiche della strategia:

resolve_symbol
get_last_price
amount_to_precision
_market_cost_step
_perp_notional_step
_align_base_amount
_align_base_to_perp_precision
spot_amount_to_precision
to_perp_amount
perp_amount_to_precision
_log_sizes
weighted_avg
_exchange_id
_pick_market
build_strategy_config — questa usa _get_rules che dipende dalle rules della strategia. Valuta se è possibile passare le rules come parametro invece di importarle. Se complica troppo, lasciala in logic.py.
ensure_strategy_config

Le funzioni che devono restare in nv1/logic.py perché usano costanti specifiche di NV1 (FEE_BUFFER, DEFAULT_LEVERAGE, MARGIN_SAFETY_BUFFER, ecc.):

start, stop, add, remove, scale_up, scale_down
_get_rules, _validate_asset — queste importano da nv1/rules.py, quindi restano in logic.py

Dopo lo spostamento, nv1/logic.py dovrebbe contenere solo le funzioni operative (start, stop, add, remove, scale_up, scale_down) più gli helper strettamente legati a NV1. Le righe dovrebbero scendere significativamente.
Verifica: dopo la modifica, tutti i test precedenti devono continuare a funzionare. L'orchestratore importa get_last_price e ensure_strategy_config da logic.py — se vengono spostati in common.py, aggiorna gli import nell'orchestratore.
Correzione 2 — Rimuovere log di debug residui
Verifica che in questi file non ci siano log di debug aggiunti durante la fase di diagnostica:

scripts/orchestrator/run_loop.py — rimuovi qualsiasi log che stampa "BitMEX position raw margin fields", "SCALE_UP debug", "BitMEX margin transfer debug", "SCALE_UP remove_margin result", "cooldown timestamp"
app/services/exchanges/bitmex.py — rimuovi log di debug aggiunti durante i test
app/services/strategies/nv1/logic.py — rimuovi log di debug aggiunti durante i test

Mantieni solo i log operativi:

In run_loop.py: il log INFO della decisione e il log di successo/errore dell'esecuzione
In logic.py: il log _log_sizes (che è già DEBUG, va bene) e i log di stop (che sono INFO operativi)
In bitmex.py: nessun log di debug

Correzione 3 — Verificare coerenza allocated_capital_usdc dopo scale_down
In nv1/logic.py, la funzione scale_down non aggiorna strategy.allocated_capital_usdc. Questo è corretto concettualmente (è un ribilanciamento, non una rimozione di capitale). Però verifica che il calcolo del PnL alla chiusura (nella funzione stop) funzioni correttamente in questo scenario:

L'utente alloca 100 USDT → allocated_capital_usdc = 100
Scale_down riduce la size ma allocated_capital_usdc resta 100
Stop chiude tutto: il realized_pnl si calcola come (exit - entry) * qty

Il PnL sarà corretto perché si basa su prezzi e quantità, non su allocated_capital. Ma il campo allocated_capital_usdc nel DB potrebbe non riflettere il valore reale restituito all'utente. Se dopo diversi scale_down hai size piccola ma allocated_capital grande, la dashboard potrebbe mostrare dati fuorvianti.
Cosa fare: nella funzione scale_down, dopo aver ridotto la size, aggiorna allocated_capital_usdc proporzionalmente:
pythonif strategy.total_quantity > 0 and total_qty > 0:
    reduction_ratio = strategy.total_quantity / total_qty  # nuova qty / vecchia qty
    strategy.allocated_capital_usdc = strategy.allocated_capital_usdc * reduction_ratio
Dove total_qty è la quantità prima della riduzione e strategy.total_quantity è quella dopo.
Nota: scale_up NON dovrebbe aggiornare allocated_capital_usdc perché sta redistribuendo margine esistente, non aggiungendo capitale. Verifica che scale_up non lo tocchi (dal codice attuale sembra che non lo faccia — confermalo).
Correzione 4 — Rendere ensure_isolated_margin universale
In nv1/logic.py, funzione start, righe 652-657:
pythonif exchange_id == "bitmex":
    isolated_result = await adapter.ensure_isolated_margin(...)
Questo if exchange-specifico viola il principio di universalità.
Cosa fare:

In app/services/exchanges/base.py, il metodo ensure_isolated_margin esiste già come metodo con implementazione default (restituisce {"success": True}). Perfetto.
In nv1/logic.py, rimuovi l'if exchange_id == "bitmex" e chiama adapter.ensure_isolated_margin(exchange, perp_symbol, DEFAULT_LEVERAGE) sempre, indipendentemente dall'exchange. Su Deribit restituirà il default {"success": True} senza fare nulla. Su Bitmex farà il lavoro reale.
Il codice diventa:

pythonisolated_result = await adapter.ensure_isolated_margin(exchange, perp_symbol, float(DEFAULT_LEVERAGE))
if isinstance(isolated_result, dict) and not isolated_result.get("success", False):
    raise ValueError(isolated_result.get("error") or "cannot set isolated margin")

VINCOLI

Crea: app/services/strategies/common.py
Modifica: nv1/logic.py, scripts/orchestrator/run_loop.py (import + rimozione debug log), bitmex.py (rimozione debug log se presenti)
NON toccare cash_funding/logic.py né nessun altro file di cash_funding
NON toccare base.py (ensure_isolated_margin è già implementato correttamente)
Dopo le modifiche, verifica che l'orchestratore si avvii senza errori di import
Verifica: PYTHONPATH=. python -c "from scripts.orchestrator.run_loop import run_orchestrator; print('OK')"
Verifica: PYTHONPATH=. python -c "from app.services.strategies.nv1.logic import start, stop, add, remove, scale_up, scale_down; print('OK')"
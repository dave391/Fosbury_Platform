bitmex
Kind: global class
Extends: Exchange

fetchCurrencies
fetchMarkets
fetchBalance
fetchOrderBook
fetchOrder
fetchOrders
fetchOpenOrders
fetchClosedOrders
fetchMyTrades
fetchLedger
fetchDepositsWithdrawals
fetchTicker
fetchTickers
fetchOHLCV
fetchTrades
createOrder
cancelOrder
cancelOrders
cancelAllOrders
cancelAllOrdersAfter
fetchLeverages
fetchPositions
withdraw
fetchFundingRates
fetchFundingRateHistory
setLeverage
setMarginMode
fetchDepositAddress
fetchDepositWithdrawFees
fetchLiquidations
watchTicker
watchTickers
watchLiquidations
watchLiquidationsForSymbols
watchBalance
watchTrades
watchPositions
watchOrders
watchMyTrades
watchOrderBook
watchOrderBookForSymbols
watchTradesForSymbols
watchOHLCV

fetchCurrencies
fetches all available currencies on an exchange

Kind: instance method of bitmex
Returns: object - an associative dictionary of currencies

See: https://www.bitmex.com/api/explorer/#!/Wallet/Wallet_getAssetsConfig

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchCurrencies ([params])
Copy to clipboardErrorCopied

fetchMarkets
retrieves data on all markets for bitmex

Kind: instance method of bitmex
Returns: Array<object> - an array of objects representing market data

See: https://www.bitmex.com/api/explorer/#!/Instrument/Instrument_getActive

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchMarkets ([params])
Copy to clipboardErrorCopied

fetchBalance
query for balance and get the amount of funds available for trading or funds locked in orders

Kind: instance method of bitmex
Returns: object - a balance structure

See: https://www.bitmex.com/api/explorer/#!/User/User_getMargin

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchBalance ([params])
Copy to clipboardErrorCopied

fetchOrderBook
fetches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of bitmex
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://www.bitmex.com/api/explorer/#!/OrderBook/OrderBook_getL2

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchOrderBook (symbol[, limit, params])
Copy to clipboardErrorCopied

fetchOrder
fetches information on an order made by the user

Kind: instance method of bitmex
Returns: object - An order structure

See: https://www.bitmex.com/api/explorer/#!/Order/Order_getOrders

Param	Type	Required	Description
id	string	Yes	the order id
symbol	string	Yes	unified symbol of the market the order was made in
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchOrder (id, symbol[, params])
Copy to clipboardErrorCopied

fetchOrders
fetches information on multiple orders made by the user

Kind: instance method of bitmex
Returns: Array<Order> - a list of order structures

See: https://www.bitmex.com/api/explorer/#!/Order/Order_getOrders

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	the earliest time in ms to fetch orders for
params.paginate	boolean	No	default false, when true will automatically paginate by calling this endpoint multiple times. See in the docs all the availble parameters
bitmex.fetchOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchOpenOrders
fetch all unfilled currently open orders

Kind: instance method of bitmex
Returns: Array<Order> - a list of order structures

See: https://www.bitmex.com/api/explorer/#!/Order/Order_getOrders

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchOpenOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchClosedOrders
fetches information on multiple closed orders made by the user

Kind: instance method of bitmex
Returns: Array<Order> - a list of order structures

See: https://www.bitmex.com/api/explorer/#!/Order/Order_getOrders

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchClosedOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchMyTrades
fetch all trades made by the user

Kind: instance method of bitmex
Returns: Array<Trade> - a list of trade structures

See: https://www.bitmex.com/api/explorer/#!/Execution/Execution_getTradeHistory

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trades structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.paginate	boolean	No	default false, when true will automatically paginate by calling this endpoint multiple times. See in the docs all the availble parameters
bitmex.fetchMyTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchLedger
fetch the history of changes, actions done by the user or operations that altered the balance of the user

Kind: instance method of bitmex
Returns: object - a ledger structure

See: https://www.bitmex.com/api/explorer/#!/User/User_getWalletHistory

Param	Type	Required	Description
code	string	No	unified currency code, default is undefined
since	int	No	timestamp in ms of the earliest ledger entry, default is undefined
limit	int	No	max number of ledger entries to return, default is undefined
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchLedger ([code, since, limit, params])
Copy to clipboardErrorCopied

fetchDepositsWithdrawals
fetch history of deposits and withdrawals

Kind: instance method of bitmex
Returns: object - a list of transaction structure

See: https://www.bitmex.com/api/explorer/#!/User/User_getWalletHistory

Param	Type	Required	Description
code	string	No	unified currency code for the currency of the deposit/withdrawals, default is undefined
since	int	No	timestamp in ms of the earliest deposit/withdrawal, default is undefined
limit	int	No	max number of deposit/withdrawals to return, default is undefined
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchDepositsWithdrawals ([code, since, limit, params])
Copy to clipboardErrorCopied

fetchTicker
fetches a price ticker, a statistical calculation with the information calculated over the past 24 hours for a specific market

Kind: instance method of bitmex
Returns: object - a ticker structure

See: https://www.bitmex.com/api/explorer/#!/Instrument/Instrument_get

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchTicker (symbol[, params])
Copy to clipboardErrorCopied

fetchTickers
fetches price tickers for multiple markets, statistical information calculated over the past 24 hours for each market

Kind: instance method of bitmex
Returns: object - a dictionary of ticker structures

See: https://www.bitmex.com/api/explorer/#!/Instrument/Instrument_getActiveAndIndices

Param	Type	Required	Description
symbols	Array<string>, undefined	Yes	unified symbols of the markets to fetch the ticker for, all market tickers are returned if not assigned
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchTickers (symbols[, params])
Copy to clipboardErrorCopied

fetchOHLCV
fetches historical candlestick data containing the open, high, low, and close price, and the volume of a market

Kind: instance method of bitmex
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://www.bitmex.com/api/explorer/#!/Trade/Trade_getBucketed

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.paginate	boolean	No	default false, when true will automatically paginate by calling this endpoint multiple times. See in the docs all the availble parameters
bitmex.fetchOHLCV (symbol, timeframe[, since, limit, params])
Copy to clipboardErrorCopied

fetchTrades
get the list of most recent trades for a particular symbol

Kind: instance method of bitmex
Returns: Array<Trade> - a list of trade structures

See: https://www.bitmex.com/api/explorer/#!/Trade/Trade_get

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch trades for
since	int	No	timestamp in ms of the earliest trade to fetch
limit	int	No	the maximum amount of trades to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.paginate	boolean	No	default false, when true will automatically paginate by calling this endpoint multiple times. See in the docs all the availble parameters
bitmex.fetchTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

createOrder
create a trade order

Kind: instance method of bitmex
Returns: object - an order structure

See: https://www.bitmex.com/api/explorer/#!/Order/Order_new

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.triggerPrice	object	No	the price at which a trigger order is triggered at
params.triggerDirection	object	No	the direction whenever the trigger happens with relation to price - 'ascending' or 'descending'
params.trailingAmount	float	No	the quote amount to trail away from the current market price
bitmex.createOrder (symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

cancelOrder
cancels an open order

Kind: instance method of bitmex
Returns: object - An order structure

See: https://www.bitmex.com/api/explorer/#!/Order/Order_cancel

Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	not used by bitmex cancelOrder ()
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.cancelOrder (id, symbol[, params])
Copy to clipboardErrorCopied

cancelOrders
cancel multiple orders

Kind: instance method of bitmex
Returns: object - an list of order structures

See: https://www.bitmex.com/api/explorer/#!/Order/Order_cancel

Param	Type	Required	Description
ids	Array<string>	Yes	order ids
symbol	string	Yes	not used by bitmex cancelOrders ()
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.cancelOrders (ids, symbol[, params])
Copy to clipboardErrorCopied

cancelAllOrders
cancel all open orders

Kind: instance method of bitmex
Returns: Array<object> - a list of order structures

See: https://www.bitmex.com/api/explorer/#!/Order/Order_cancelAll

Param	Type	Required	Description
symbol	string	Yes	unified market symbol, only orders in the market of this symbol are cancelled when symbol is not undefined
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.cancelAllOrders (symbol[, params])
Copy to clipboardErrorCopied

cancelAllOrdersAfter
dead man's switch, cancel all orders after the given timeout

Kind: instance method of bitmex
Returns: object - the api result

See: https://www.bitmex.com/api/explorer/#!/Order/Order_cancelAllAfter

Param	Type	Required	Description
timeout	number	Yes	time in milliseconds, 0 represents cancel the timer
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.cancelAllOrdersAfter (timeout[, params])
Copy to clipboardErrorCopied

fetchLeverages
fetch the set leverage for all contract markets

Kind: instance method of bitmex
Returns: object - a list of leverage structures

See: https://www.bitmex.com/api/explorer/#!/Position/Position_get

Param	Type	Required	Description
symbols	Array<string>	No	a list of unified market symbols
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchLeverages ([symbols, params])
Copy to clipboardErrorCopied

fetchPositions
fetch all open positions

Kind: instance method of bitmex
Returns: Array<object> - a list of position structure

See: https://www.bitmex.com/api/explorer/#!/Position/Position_get

Param	Type	Required	Description
symbols	Array<string>, undefined	Yes	list of unified market symbols
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchPositions (symbols[, params])
Copy to clipboardErrorCopied

withdraw
make a withdrawal

Kind: instance method of bitmex
Returns: object - a transaction structure

See: https://www.bitmex.com/api/explorer/#!/User/User_requestWithdrawal

Param	Type	Required	Description
code	string	Yes	unified currency code
amount	float	Yes	the amount to withdraw
address	string	Yes	the address to withdraw to
tag	string	Yes	
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.withdraw (code, amount, address, tag[, params])
Copy to clipboardErrorCopied

fetchFundingRates
fetch the funding rate for multiple markets

Kind: instance method of bitmex
Returns: Array<object> - a list of funding rate structures, indexed by market symbols

See: https://www.bitmex.com/api/explorer/#!/Instrument/Instrument_getActiveAndIndices

Param	Type	Required	Description
symbols	Array<string>, undefined	Yes	list of unified market symbols
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchFundingRates (symbols[, params])
Copy to clipboardErrorCopied

fetchFundingRateHistory
Fetches the history of funding rates

Kind: instance method of bitmex
Returns: Array<object> - a list of funding rate structures

See: https://www.bitmex.com/api/explorer/#!/Funding/Funding_get

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the funding rate history for
since	int	No	timestamp in ms of the earliest funding rate to fetch
limit	int	No	the maximum amount of funding rate structures to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms for ending date filter
params.reverse	bool	No	if true, will sort results newest first
params.start	int	No	starting point for results
params.columns	string	No	array of column names to fetch in info, if omitted, will return all columns
params.filter	string	No	generic table filter, send json key/value pairs, such as {"key": "value"}, you can key on individual fields, and do more advanced querying on timestamps, see the timestamp docs for more details
bitmex.fetchFundingRateHistory (symbol[, since, limit, params])
Copy to clipboardErrorCopied

setLeverage
set the level of leverage for a market

Kind: instance method of bitmex
Returns: object - response from the exchange

See: https://www.bitmex.com/api/explorer/#!/Position/Position_updateLeverage

Param	Type	Required	Description
leverage	float	Yes	the rate of leverage
symbol	string	Yes	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.setLeverage (leverage, symbol[, params])
Copy to clipboardErrorCopied

setMarginMode
set margin mode to 'cross' or 'isolated'

Kind: instance method of bitmex
Returns: object - response from the exchange

See: https://www.bitmex.com/api/explorer/#!/Position/Position_isolateMargin

Param	Type	Required	Description
marginMode	string	Yes	'cross' or 'isolated'
symbol	string	Yes	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.setMarginMode (marginMode, symbol[, params])
Copy to clipboardErrorCopied

fetchDepositAddress
fetch the deposit address for a currency associated with this account

Kind: instance method of bitmex
Returns: object - an address structure

See: https://www.bitmex.com/api/explorer/#!/User/User_getDepositAddress

Param	Type	Required	Description
code	string	Yes	unified currency code
params	object	No	extra parameters specific to the exchange API endpoint
params.network	string	No	deposit chain, can view all chains via this.publicGetWalletAssets, default is eth, unless the currency has a default chain within this.options['networks']
bitmex.fetchDepositAddress (code[, params])
Copy to clipboardErrorCopied

fetchDepositWithdrawFees
fetch deposit and withdraw fees

Kind: instance method of bitmex
Returns: object - a list of fee structures

See: https://www.bitmex.com/api/explorer/#!/Wallet/Wallet_getAssetsConfig

Param	Type	Required	Description
codes	Array<string>, undefined	Yes	list of unified currency codes
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.fetchDepositWithdrawFees (codes[, params])
Copy to clipboardErrorCopied

fetchLiquidations
retrieves the public liquidations of a trading pair

Kind: instance method of bitmex
Returns: object - an array of liquidation structures

See: https://www.bitmex.com/api/explorer/#!/Liquidation/Liquidation_get

Param	Type	Required	Description
symbol	string	Yes	unified CCXT market symbol
since	int	No	the earliest time in ms to fetch liquidations for
limit	int	No	the maximum number of liquidation structures to retrieve
params	object	No	exchange specific parameters for the bitmex api endpoint
params.until	int	No	timestamp in ms of the latest liquidation
params.paginate	boolean	No	default false, when true will automatically paginate by calling this endpoint multiple times. See in the docs all the availble parameters
bitmex.fetchLiquidations (symbol[, since, limit, params])
Copy to clipboardErrorCopied

watchTicker
watches a price ticker, a statistical calculation with the information calculated over the past 24 hours for a specific market

Kind: instance method of bitmex
Returns: object - a ticker structure

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchTicker (symbol[, params])
Copy to clipboardErrorCopied

watchTickers
watches a price ticker, a statistical calculation with the information calculated over the past 24 hours for all markets of a specific list

Kind: instance method of bitmex
Returns: object - a ticker structure

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
symbols	Array<string>	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchTickers (symbols[, params])
Copy to clipboardErrorCopied

watchLiquidations
watch the public liquidations of a trading pair

Kind: instance method of bitmex
Returns: object - an array of liquidation structures

See: https://www.bitmex.com/app/wsAPI#Liquidation

Param	Type	Required	Description
symbol	string	Yes	unified CCXT market symbol
since	int	No	the earliest time in ms to fetch liquidations for
limit	int	No	the maximum number of liquidation structures to retrieve
params	object	No	exchange specific parameters for the bitmex api endpoint
bitmex.watchLiquidations (symbol[, since, limit, params])
Copy to clipboardErrorCopied

watchLiquidationsForSymbols
watch the public liquidations of a trading pair

Kind: instance method of bitmex
Returns: object - an array of liquidation structures

See: https://www.bitmex.com/app/wsAPI#Liquidation

Param	Type	Required	Description
symbols	Array<string>	Yes	
since	int	No	the earliest time in ms to fetch liquidations for
limit	int	No	the maximum number of liquidation structures to retrieve
params	object	No	exchange specific parameters for the bitmex api endpoint
bitmex.watchLiquidationsForSymbols (symbols[, since, limit, params])
Copy to clipboardErrorCopied

watchBalance
watch balance and get the amount of funds available for trading or funds locked in orders

Kind: instance method of bitmex
Returns: object - a balance structure

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchBalance ([params])
Copy to clipboardErrorCopied

watchTrades
get the list of most recent trades for a particular symbol

Kind: instance method of bitmex
Returns: Array<object> - a list of trade structures

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch trades for
since	int	No	timestamp in ms of the earliest trade to fetch
limit	int	No	the maximum amount of trades to fetch
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

watchPositions
watch all open positions

Kind: instance method of bitmex
Returns: Array<object> - a list of position structure

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
symbols	Array<string>, undefined	Yes	list of unified market symbols
since	int	No	the earliest time in ms to watch positions for
limit	int	No	the maximum number of positions to retrieve
params	object	Yes	extra parameters specific to the exchange API endpoint
bitmex.watchPositions (symbols[, since, limit, params])
Copy to clipboardErrorCopied

watchOrders
watches information on multiple orders made by the user

Kind: instance method of bitmex
Returns: Array<object> - a list of order structures

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

watchMyTrades
watches information on multiple trades made by the user

Kind: instance method of bitmex
Returns: Array<object> - a list of trade structures

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market trades were made in
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trade structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchMyTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

watchOrderBook
watches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of bitmex
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://www.bitmex.com/app/wsAPI#OrderBookL2

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchOrderBook (symbol[, limit, params])
Copy to clipboardErrorCopied

watchOrderBookForSymbols
watches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of bitmex
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://www.bitmex.com/app/wsAPI#OrderBookL2

Param	Type	Required	Description
symbols	Array<string>	Yes	unified array of symbols
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchOrderBookForSymbols (symbols[, limit, params])
Copy to clipboardErrorCopied

watchTradesForSymbols
get the list of most recent trades for a list of symbols

Kind: instance method of bitmex
Returns: Array<object> - a list of trade structures

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
symbols	Array<string>	Yes	unified symbol of the market to fetch trades for
since	int	No	timestamp in ms of the earliest trade to fetch
limit	int	No	the maximum amount of trades to fetch
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchTradesForSymbols (symbols[, since, limit, params])
Copy to clipboardErrorCopied

watchOHLCV
watches historical candlestick data containing the open, high, low, and close price, and the volume of a market

Kind: instance method of bitmex
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://www.bitmex.com/app/wsAPI#Subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
bitmex.watchOHLCV (symbol, timeframe[, since, limit, params])
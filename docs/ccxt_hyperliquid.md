hyperliquid
Kind: global class
Extends: Exchange

fetchStatus
fetchTime
fetchCurrencies
fetchMarkets
fetchHip3Markets
fetchSwapMarkets
calculatePricePrecision
fetchSpotMarkets
fetchBalance
fetchOrderBook
fetchTickers
fetchFundingRates
fetchOHLCV
fetchTrades
isUnifiedEnabled
setUserAbstraction
enableUserDexAbstraction
setAgentAbstraction
createOrder
createTwapOrder
createOrders
createOrdersRequest
cancelOrder
cancelOrders
cancelTwapOrder
cancelOrdersRequest
cancelOrdersForSymbols
cancelAllOrdersAfter
editOrder
editOrders
createVault
fetchFundingRateHistory
fetchOpenOrders
fetchClosedOrders
fetchCanceledOrders
fetchCanceledAndClosedOrders
fetchOrders
fetchOrder
fetchMyTrades
fetchPosition
fetchPositions
setMarginMode
setLeverage
addMargin
reduceMargin
transfer
withdraw
fetchTradingFee
fetchLedger
fetchDeposits
fetchWithdrawals
fetchOpenInterests
fetchOpenInterest
fetchFundingHistory
reserveRequestWeight
createAccount
createOrdersWs
createOrderWs
editOrderWs
cancelOrdersWs
cancelOrderWs
watchOrderBook
unWatchOrderBook
watchTicker
watchTickers
unWatchTickers
watchMyTrades
unWatchMyTrades
watchTrades
unWatchTrades
watchOHLCV
unWatchOHLCV
watchOrders
unWatchOrders

fetchStatus
the latest known information on the availability of the exchange API

Kind: instance method of hyperliquid
Returns: object - a status structure

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchStatus ([params])
Copy to clipboardErrorCopied

fetchTime
fetches the current integer timestamp in milliseconds from the exchange server

Kind: instance method of hyperliquid
Returns: int - the current integer timestamp in milliseconds from the exchange server

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchTime ([params])
Copy to clipboardErrorCopied

fetchCurrencies
fetches all available currencies on an exchange

Kind: instance method of hyperliquid
Returns: object - an associative dictionary of currencies

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-metadata

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchCurrencies ([params])
Copy to clipboardErrorCopied

fetchMarkets
retrieves data on all markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot#retrieve-spot-asset-contexts
Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchMarkets ([params])
Copy to clipboardErrorCopied

fetchHip3Markets
retrieves data on all hip3 markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-all-perpetual-dexs
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc
Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchHip3Markets ([params])
Copy to clipboardErrorCopied

fetchSwapMarkets
retrieves data on all swap markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchSwapMarkets ([params])
Copy to clipboardErrorCopied

calculatePricePrecision
Helper function to calculate the Hyperliquid DECIMAL_PLACES price precision

Kind: instance method of hyperliquid
Returns: int - The calculated price precision

Param	Type	Description
price	float	the price to use in the calculation
amountPrecision	int	the amountPrecision to use in the calculation
maxDecimals	int	the maxDecimals to use in the calculation
hyperliquid.calculatePricePrecision (price, amountPrecision, maxDecimals[])
Copy to clipboardErrorCopied

fetchSpotMarkets
retrieves data on all spot markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot#retrieve-spot-asset-contexts

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchSpotMarkets ([params])
Copy to clipboardErrorCopied

fetchBalance
query for balance and get the amount of funds available for trading or funds locked in orders

Kind: instance method of hyperliquid
Returns: object - a balance structure

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot#retrieve-a-users-token-balances
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-users-perpetuals-account-summary
Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
params.type	string	No	wallet type, ['spot', 'swap'], defaults to swap
params.marginMode	string	No	'cross' or 'isolated', for margin trading, uses this.options.defaultMarginMode if not passed, defaults to undefined/None/null
params.dex	string	No	for hip3 markets, the dex name, eg: 'xyz'
params.subAccountAddress	string	No	sub account user address
params.enableUnifiedMargin	boolean	No	enable unified margin, CCXT tries to auto-detects this value but you can override it
hyperliquid.fetchBalance ([params])
Copy to clipboardErrorCopied

fetchOrderBook
fetches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of hyperliquid
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#l2-book-snapshot

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchOrderBook (symbol[, limit, params])
Copy to clipboardErrorCopied

fetchTickers
fetches price tickers for multiple markets, statistical information calculated over the past 24 hours for each market

Kind: instance method of hyperliquid
Returns: object - a dictionary of ticker structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot#retrieve-spot-asset-contexts
Param	Type	Required	Description
symbols	Array<string>	No	unified symbols of the markets to fetch the ticker for, all market tickers are returned if not assigned
params	object	No	extra parameters specific to the exchange API endpoint
params.type	string	No	'spot' or 'swap', by default fetches both
params.hip3	boolean	No	set to true to fetch hip3 markets only
hyperliquid.fetchTickers ([symbols, params])
Copy to clipboardErrorCopied

fetchFundingRates
retrieves data on all swap markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc

Param	Type	Required	Description
symbols	Array<string>	No	list of unified market symbols
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchFundingRates ([symbols, params])
Copy to clipboardErrorCopied

fetchOHLCV
fetches historical candlestick data containing the open, high, low, and close price, and the volume of a market

Kind: instance method of hyperliquid
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#candle-snapshot

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents, support '1m', '15m', '1h', '1d'
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest candle to fetch
hyperliquid.fetchOHLCV (symbol, timeframe[, since, limit, params])
Copy to clipboardErrorCopied

fetchTrades
get the list of most recent trades for a particular symbol

Kind: instance method of hyperliquid
Returns: Array<Trade> - a list of trade structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-fills
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-fills-by-time
Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trades structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest trade
params.address	string	No	wallet address that made trades
params.user	string	No	wallet address that made trades
params.subAccountAddress	string	No	sub account user address
hyperliquid.fetchTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

isUnifiedEnabled
returns enableUnifiedMargin so the user can check if unified account is enabled

Kind: instance method of hyperliquid
Returns: bool - enableUnifiedMargin

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#query-a-users-abstraction-state

Param	Type	Required	Description
method	string	Yes	the method for which we want to check if unified margin is enabled, this is used to check options for specific methods (e.g. fetchBalance can have a specific option to enable unified margin)
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.isUnifiedEnabled (method[, params])
Copy to clipboardErrorCopied

setUserAbstraction
set user abstraction mode

Kind: instance method of hyperliquid
Returns: dictionary response from the exchange

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#set-user-abstraction

Param	Type	Required	Description
abstraction	string	Yes	one of the strings ["disabled", "unifiedAccount", "portfolioMargin"],
params	object	No	
params.type	string	No	'userSetAbstraction' or 'agentSetAbstraction' default is 'userSetAbstraction'
hyperliquid.setUserAbstraction (abstraction[, params])
Copy to clipboardErrorCopied

enableUserDexAbstraction
If set, actions on HIP-3 perps will automatically transfer collateral from validator-operated USDC perps balance for HIP-3 DEXs where USDC is the collateral token, and spot otherwise

Kind: instance method of hyperliquid
Returns: dictionary response from the exchange

Param	Type	Required	Description
enabled		Yes	
params		Yes	
params.type	string	No	'userDexAbstraction' or 'agentEnableDexAbstraction' default is 'userDexAbstraction'
hyperliquid.enableUserDexAbstraction (enabled, params[])
Copy to clipboardErrorCopied

setAgentAbstraction
set agent abstraction mode

Kind: instance method of hyperliquid
Returns: dictionary response from the exchange

Param	Type	Required	Description
abstraction	string	Yes	one of the strings ["i", "u", "p"] where "i" is "disabled", "u" is "unifiedAccount", and "p" is "portfolioMargin"
params	object	No	
hyperliquid.setAgentAbstraction (abstraction[, params])
Copy to clipboardErrorCopied

createOrder
create a trade order

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.timeInForce	string	No	'Gtc', 'Ioc', 'Alo'
params.postOnly	bool	No	true or false whether the order is post-only
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.triggerPrice	float	No	The price at which a trigger order is triggered at
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.slippage	string	No	the slippage for market order
params.vaultAddress	string	No	the vault address for order
params.subAccountAddress	string	No	sub account user address
hyperliquid.createOrder (symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

createTwapOrder
create a trade order that is executed as a TWAP order over a specified duration.

Kind: instance method of hyperliquid
Returns: object - an order structure

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to create an order in
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
duration	int	Yes	the duration of the TWAP order in milliseconds
params	object	No	extra parameters specific to the exchange API endpoint
params.randomize	bool	No	whether to randomize the time intervals of the TWAP order slices (default is false, meaning equal intervals)
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.expiresAfter	int	No	time in ms after which the twap order expires
params.vaultAddress	string	No	the vault address for order
hyperliquid.createTwapOrder (symbol, side, amount, duration[, params])
Copy to clipboardErrorCopied

createOrders
create a list of trade orders

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Required	Description
orders	Array	Yes	list of orders to create, each object should contain the parameters required by createOrder, namely symbol, type, side, amount, price and params
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.createOrders (orders[, params])
Copy to clipboardErrorCopied

createOrdersRequest
create a list of trade orders

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Description
orders	Array	list of orders to create, each object should contain the parameters required by createOrder, namely symbol, type, side, amount, price and params
hyperliquid.createOrdersRequest (orders, [undefined])
Copy to clipboardErrorCopied

cancelOrder
cancels an open order

Kind: instance method of hyperliquid
Returns: object - An order structure

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s-by-cloid
Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	unified symbol of the market the order was made in
params	object	No	extra parameters specific to the exchange API endpoint
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.vaultAddress	string	No	the vault address for order
params.subAccountAddress	string	No	sub account user address
params.twap	boolean	No	whether the order to cancel is a twap order, (default is false)
hyperliquid.cancelOrder (id, symbol[, params])
Copy to clipboardErrorCopied

cancelOrders
cancel multiple orders

Kind: instance method of hyperliquid
Returns: object - an list of order structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s-by-cloid
Param	Type	Required	Description
ids	Array<string>	Yes	order ids
symbol	string	No	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
params.clientOrderId	string, Array<string>	No	client order ids, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.vaultAddress	string	No	the vault address
params.subAccountAddress	string	No	sub account user address
hyperliquid.cancelOrders (ids[, symbol, params])
Copy to clipboardErrorCopied

cancelTwapOrder
cancels a running twap order

Kind: instance method of hyperliquid
Returns: object - An order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-a-twap-order

Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	unified symbol of the market the order was made in
params	object	No	extra parameters specific to the exchange API endpoint
params.expiresAfter	int	No	time in ms after which the twap order expires
params.vaultAddress	string	No	the vault address for order
hyperliquid.cancelTwapOrder (id, symbol[, params])
Copy to clipboardErrorCopied

cancelOrdersRequest
build the request payload for cancelling multiple orders

Kind: instance method of hyperliquid
Returns: object - the raw request object to be sent to the exchange

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s-by-cloid
Param	Type	Required	Description
ids	Array<string>	Yes	order ids
symbol	string	Yes	unified market symbol
params	object	No	
hyperliquid.cancelOrdersRequest (ids, symbol[, params])
Copy to clipboardErrorCopied

cancelOrdersForSymbols
cancel multiple orders for multiple symbols

Kind: instance method of hyperliquid
Returns: object - an list of order structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s-by-cloid
Param	Type	Required	Description
orders	Array<CancellationRequest>	Yes	each order should contain the parameters required by cancelOrder namely id and symbol, example [{"id": "a", "symbol": "BTC/USDT"}, {"id": "b", "symbol": "ETH/USDT"}]
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	the vault address
params.subAccountAddress	string	No	sub account user address
hyperliquid.cancelOrdersForSymbols (orders[, params])
Copy to clipboardErrorCopied

cancelAllOrdersAfter
dead man's switch, cancel all orders after the given timeout

Kind: instance method of hyperliquid
Returns: object - the api result

Param	Type	Required	Description
timeout	number	Yes	time in milliseconds, 0 represents cancel the timer
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	the vault address
params.subAccountAddress	string	No	sub account user address
hyperliquid.cancelAllOrdersAfter (timeout[, params])
Copy to clipboardErrorCopied

editOrder
edit a trade order

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#modify-multiple-orders

Param	Type	Required	Description
id	string	Yes	cancel order id
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.timeInForce	string	No	'Gtc', 'Ioc', 'Alo'
params.postOnly	bool	No	true or false whether the order is post-only
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.triggerPrice	float	No	The price at which a trigger order is triggered at
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.vaultAddress	string	No	the vault address for order
params.subAccountAddress	string	No	sub account user address
hyperliquid.editOrder (id, symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

editOrders
edit a list of trade orders

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#modify-multiple-orders

Param	Type	Required	Description
orders	Array	Yes	list of orders to create, each object should contain the parameters required by createOrder, namely symbol, type, side, amount, price and params
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.editOrders (orders[, params])
Copy to clipboardErrorCopied

createVault
creates a value

Kind: instance method of hyperliquid
Returns: object - the api result

Param	Type	Required	Description
name	string	Yes	The name of the vault
description	string	Yes	The description of the vault
initialUsd	number	Yes	The initialUsd of the vault
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.createVault (name, description, initialUsd[, params])
Copy to clipboardErrorCopied

fetchFundingRateHistory
fetches historical funding rate prices

Kind: instance method of hyperliquid
Returns: Array<object> - a list of funding rate structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-historical-funding-rates

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the funding rate history for
since	int	No	timestamp in ms of the earliest funding rate to fetch
limit	int	No	the maximum amount of funding rate structures to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest funding rate
hyperliquid.fetchFundingRateHistory (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchOpenOrders
fetch all unfilled currently open orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-open-orders

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
params.method	string	No	'openOrders' or 'frontendOpenOrders' default is 'frontendOpenOrders'
params.subAccountAddress	string	No	sub account user address
params.dex	string	No	perp dex name. default is null
hyperliquid.fetchOpenOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchClosedOrders
fetch all unfilled currently closed orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchClosedOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchCanceledOrders
fetch all canceled orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchCanceledOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchCanceledAndClosedOrders
fetch all closed and canceled orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchCanceledAndClosedOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchOrders
fetch all orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
params.subAccountAddress	string	No	sub account user address
params.dex	string	No	perp dex name. default is null
hyperliquid.fetchOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchOrder
fetches information on an order made by the user

Kind: instance method of hyperliquid
Returns: object - An order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#query-order-status-by-oid-or-cloid

Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	unified symbol of the market the order was made in
params	object	No	extra parameters specific to the exchange API endpoint
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.user	string	No	user address, will default to this.walletAddress if not provided
params.subAccountAddress	string	No	sub account user address
hyperliquid.fetchOrder (id, symbol[, params])
Copy to clipboardErrorCopied

fetchMyTrades
fetch all trades made by the user

Kind: instance method of hyperliquid
Returns: Array<Trade> - a list of trade structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-fills
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-fills-by-time
Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trades structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest trade
params.subAccountAddress	string	No	sub account user address
hyperliquid.fetchMyTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchPosition
fetch data on an open position

Kind: instance method of hyperliquid
Returns: object - a position structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-users-perpetuals-account-summary

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market the position is held in
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchPosition (symbol[, params])
Copy to clipboardErrorCopied

fetchPositions
fetch all open positions

Kind: instance method of hyperliquid
Returns: Array<object> - a list of position structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-users-perpetuals-account-summary

Param	Type	Required	Description
symbols	Array<string>	No	list of unified market symbols
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
params.subAccountAddress	string	No	sub account user address
params.dex	string	No	perp dex name, eg: XYZ
hyperliquid.fetchPositions ([symbols, params])
Copy to clipboardErrorCopied

setMarginMode
set margin mode (symbol)

Kind: instance method of hyperliquid
Returns: object - response from the exchange

Param	Type	Required	Description
marginMode	string	Yes	margin mode must be either [isolated, cross]
symbol	string	Yes	unified market symbol of the market the position is held in, default is undefined
params	object	No	extra parameters specific to the exchange API endpoint
params.leverage	string	No	the rate of leverage, is required if setting trade mode (symbol)
params.vaultAddress	string	No	the vault address
params.subAccountAddress	string	No	sub account user address
hyperliquid.setMarginMode (marginMode, symbol[, params])
Copy to clipboardErrorCopied

setLeverage
set the level of leverage for a market

Kind: instance method of hyperliquid
Returns: object - response from the exchange

Param	Type	Required	Description
leverage	float	Yes	the rate of leverage
symbol	string	Yes	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
params.marginMode	string	No	margin mode must be either [isolated, cross], default is cross
hyperliquid.setLeverage (leverage, symbol[, params])
Copy to clipboardErrorCopied

addMargin
add margin

Kind: instance method of hyperliquid
Returns: object - a margin structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#update-isolated-margin

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
amount	float	Yes	amount of margin to add
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	the vault address
params.subAccountAddress	string	No	sub account user address
hyperliquid.addMargin (symbol, amount[, params])
Copy to clipboardErrorCopied

reduceMargin
remove margin from a position

Kind: instance method of hyperliquid
Returns: object - a margin structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#update-isolated-margin

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
amount	float	Yes	the amount of margin to remove
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	the vault address
params.subAccountAddress	string	No	sub account user address
hyperliquid.reduceMargin (symbol, amount[, params])
Copy to clipboardErrorCopied

transfer
transfer currency internally between wallets on the same account

Kind: instance method of hyperliquid
Returns: object - a transfer structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#l1-usdc-transfer

Param	Type	Required	Description
code	string	Yes	unified currency code
amount	float	Yes	amount to transfer
fromAccount	string	Yes	account to transfer from spot, swap
toAccount	string	Yes	account to transfer to swap, spot or address
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	the vault address for order
hyperliquid.transfer (code, amount, fromAccount, toAccount[, params])
Copy to clipboardErrorCopied

withdraw
make a withdrawal (only support USDC)

Kind: instance method of hyperliquid
Returns: object - a transaction structure

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#initiate-a-withdrawal-request
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#deposit-or-withdraw-from-a-vault
Param	Type	Required	Description
code	string	Yes	unified currency code
amount	float	Yes	the amount to withdraw
address	string	Yes	the address to withdraw to
tag	string	Yes	
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	vault address withdraw from
hyperliquid.withdraw (code, amount, address, tag[, params])
Copy to clipboardErrorCopied

fetchTradingFee
fetch the trading fees for a market

Kind: instance method of hyperliquid
Returns: object - a fee structure

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
params.subAccountAddress	string	No	sub account user address
hyperliquid.fetchTradingFee (symbol[, params])
Copy to clipboardErrorCopied

fetchLedger
fetch the history of changes, actions done by the user or operations that altered the balance of the user

Kind: instance method of hyperliquid
Returns: object - a ledger structure

Param	Type	Required	Description
code	string	No	unified currency code
since	int	No	timestamp in ms of the earliest ledger entry
limit	int	No	max number of ledger entries to return
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest ledger entry
params.subAccountAddress	string	No	sub account user address
hyperliquid.fetchLedger ([code, since, limit, params])
Copy to clipboardErrorCopied

fetchDeposits
fetch all deposits made to an account

Kind: instance method of hyperliquid
Returns: Array<object> - a list of transaction structures

Param	Type	Required	Description
code	string	Yes	unified currency code
since	int	No	the earliest time in ms to fetch deposits for
limit	int	No	the maximum number of deposits structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	the latest time in ms to fetch withdrawals for
params.subAccountAddress	string	No	sub account user address
params.vaultAddress	string	No	vault address
hyperliquid.fetchDeposits (code[, since, limit, params])
Copy to clipboardErrorCopied

fetchWithdrawals
fetch all withdrawals made from an account

Kind: instance method of hyperliquid
Returns: Array<object> - a list of transaction structures

Param	Type	Required	Description
code	string	Yes	unified currency code
since	int	No	the earliest time in ms to fetch withdrawals for
limit	int	No	the maximum number of withdrawals structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	the latest time in ms to fetch withdrawals for
params.subAccountAddress	string	No	sub account user address
params.vaultAddress	string	No	vault address
hyperliquid.fetchWithdrawals (code[, since, limit, params])
Copy to clipboardErrorCopied

fetchOpenInterests
Retrieves the open interest for a list of symbols

Kind: instance method of hyperliquid
Returns: object - an open interest structurehttps://docs.ccxt.com/?id=open-interest-structure

Param	Type	Required	Description
symbols	Array<string>	No	Unified CCXT market symbol
params	object	No	exchange specific parameters
hyperliquid.fetchOpenInterests ([symbols, params])
Copy to clipboardErrorCopied

fetchOpenInterest
retrieves the open interest of a contract trading pair

Kind: instance method of hyperliquid
Returns: object - an open interest structure

Param	Type	Required	Description
symbol	string	Yes	unified CCXT market symbol
params	object	No	exchange specific parameters
hyperliquid.fetchOpenInterest (symbol[, params])
Copy to clipboardErrorCopied

fetchFundingHistory
fetch the history of funding payments paid and received on this account

Kind: instance method of hyperliquid
Returns: object - a funding history structure

Param	Type	Required	Description
symbol	string	No	unified market symbol
since	int	No	the earliest time in ms to fetch funding history for
limit	int	No	the maximum number of funding history structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.subAccountAddress	string	No	sub account user address
hyperliquid.fetchFundingHistory ([symbol, since, limit, params])
Copy to clipboardErrorCopied

reserveRequestWeight
Instead of trading to increase the address based rate limits, this action allows reserving additional actions for 0.0005 USDC per request. The cost is paid from the Perps balance.

Kind: instance method of hyperliquid
Returns: object - a response object

Param	Type	Required	Description
weight	number	Yes	the weight to reserve, 1 weight = 1 action, 0.0005 USDC per action
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.reserveRequestWeight (weight[, params])
Copy to clipboardErrorCopied

createAccount
creates a sub-account under the main account

Kind: instance method of hyperliquid
Returns: object - a response object

Param	Type	Required	Description
name	string	Yes	the name of the sub-account
params	object	No	extra parameters specific to the exchange API endpoint
params.expiresAfter	int	No	time in ms after which the sub-account will expire
hyperliquid.createAccount (name[, params])
Copy to clipboardErrorCopied

createOrdersWs
create a list of trade orders using WebSocket post request

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Required	Description
orders	Array	Yes	list of orders to create, each object should contain the parameters required by createOrder, namely symbol, type, side, amount, price and params
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.createOrdersWs (orders[, params])
Copy to clipboardErrorCopied

createOrderWs
create a trade order using WebSocket post request

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.timeInForce	string	No	'Gtc', 'Ioc', 'Alo'
params.postOnly	bool	No	true or false whether the order is post-only
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.triggerPrice	float	No	The price at which a trigger order is triggered at
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.slippage	string	No	the slippage for market order
params.vaultAddress	string	No	the vault address for order
hyperliquid.createOrderWs (symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

editOrderWs
edit a trade order

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#modify-multiple-orders

Param	Type	Required	Description
id	string	Yes	cancel order id
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.timeInForce	string	No	'Gtc', 'Ioc', 'Alo'
params.postOnly	bool	No	true or false whether the order is post-only
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.triggerPrice	float	No	The price at which a trigger order is triggered at
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.vaultAddress	string	No	the vault address for order
hyperliquid.editOrderWs (id, symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

cancelOrdersWs
cancel multiple orders using WebSocket post request

Kind: instance method of hyperliquid
Returns: Array<object> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/post-requests

Param	Type	Required	Description
ids	Array<string>	Yes	list of order ids to cancel
symbol	string	Yes	unified symbol of the market the orders were made in
params	object	No	extra parameters specific to the exchange API endpoint
params.clientOrderId	Array<string>	No	list of client order ids to cancel instead of order ids
params.vaultAddress	string	No	the vault address for order cancellation
hyperliquid.cancelOrdersWs (ids, symbol[, params])
Copy to clipboardErrorCopied

cancelOrderWs
cancel a single order using WebSocket post request

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/post-requests

Param	Type	Required	Description
id	string	Yes	order id to cancel
symbol	string	Yes	unified symbol of the market the order was made in
params	object	No	extra parameters specific to the exchange API endpoint
params.clientOrderId	string	No	client order id to cancel instead of order id
params.vaultAddress	string	No	the vault address for order cancellation
hyperliquid.cancelOrderWs (id, symbol[, params])
Copy to clipboardErrorCopied

watchOrderBook
watches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of hyperliquid
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.watchOrderBook (symbol[, limit, params])
Copy to clipboardErrorCopied

unWatchOrderBook
unWatches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of hyperliquid
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.unWatchOrderBook (symbol[, params])
Copy to clipboardErrorCopied

watchTicker
watches a price ticker, a statistical calculation with the information calculated over the past 24 hours for a specific market

Kind: instance method of hyperliquid
Returns: object - a ticker structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
params.channel	string	No	'webData2' or 'allMids', default is 'webData2'
hyperliquid.watchTicker (symbol[, params])
Copy to clipboardErrorCopied

watchTickers
watches a price ticker, a statistical calculation with the information calculated over the past 24 hours for all markets of a specific list

Kind: instance method of hyperliquid
Returns: object - a ticker structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbols	Array<string>	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
params.channel	string	No	'webData2' or 'allMids', default is 'webData2'
params.dex	string	No	for for hip3 tokens subscription, eg: 'xyz' or 'flx`, if symbols are provided we will infer it from the first symbol's market
hyperliquid.watchTickers (symbols[, params])
Copy to clipboardErrorCopied

unWatchTickers
unWatches a price ticker, a statistical calculation with the information calculated over the past 24 hours for all markets of a specific list

Kind: instance method of hyperliquid
Returns: object - a ticker structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbols	Array<string>	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
params.channel	string	No	'webData2' or 'allMids', default is 'webData2'
hyperliquid.unWatchTickers (symbols[, params])
Copy to clipboardErrorCopied

watchMyTrades
watches information on multiple trades made by the user

Kind: instance method of hyperliquid
Returns: Array<object> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.watchMyTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

unWatchMyTrades
unWatches information on multiple trades made by the user

Kind: instance method of hyperliquid
Returns: Array<object> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.unWatchMyTrades (symbol[, params])
Copy to clipboardErrorCopied

watchTrades
watches information on multiple trades made in a market

Kind: instance method of hyperliquid
Returns: Array<object> - a list of trade structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market trades were made in
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trade structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.watchTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

unWatchTrades
unWatches information on multiple trades made in a market

Kind: instance method of hyperliquid
Returns: Array<object> - a list of trade structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market trades were made in
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.unWatchTrades (symbol[, params])
Copy to clipboardErrorCopied

watchOHLCV
watches historical candlestick data containing the open, high, low, close price, and the volume of a market

Kind: instance method of hyperliquid
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.watchOHLCV (symbol, timeframe[, since, limit, params])
Copy to clipboardErrorCopied

unWatchOHLCV
watches historical candlestick data containing the open, high, low, close price, and the volume of a market

Kind: instance method of hyperliquid
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.unWatchOHLCV (symbol, timeframe[, params])
Copy to clipboardErrorCopied

watchOrders
watches information on multiple orders made by the user

Kind: instance method of hyperliquid
Returns: Array<object> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.watchOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

unWatchOrders
unWatches information on multiple orders made by the user

Kind: instance method of hyperliquid
Returns: Array<object> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.unWatchOrders (symbol[, params])
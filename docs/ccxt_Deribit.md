deribit
Kind: global class
Extends: Exchange

fetchTime
fetchCurrencies
fetchStatus
fetchAccounts
fetchMarkets
fetchBalance
createDepositAddress
fetchDepositAddress
fetchTicker
fetchTickers
fetchOHLCV
fetchTrades
fetchTradingFees
fetchOrderBook
fetchOrder
createOrder
editOrder
cancelOrder
cancelAllOrders
fetchOpenOrders
fetchClosedOrders
fetchOrderTrades
fetchMyTrades
fetchDeposits
fetchWithdrawals
fetchPosition
fetchPositions
fetchVolatilityHistory
fetchTransfers
transfer
withdraw
fetchDepositWithdrawFees
fetchFundingRate
fetchFundingRateHistory
fetchLiquidations
fetchMyLiquidations
fetchGreeks
fetchOption
fetchOptionChain
fetchOpenInterest
watchBalance
watchTicker
watchTickers
watchBidsAsks
watchTrades
watchTradesForSymbols
watchMyTrades
watchOrderBook
watchOrderBookForSymbols
watchOrders
watchOHLCV
watchOHLCVForSymbols

fetchTime
fetches the current integer timestamp in milliseconds from the exchange server

Kind: instance method of deribit
Returns: int - the current integer timestamp in milliseconds from the exchange server

See: https://docs.deribit.com/#public-get_time

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchTime ([params])
Copy to clipboardErrorCopied

fetchCurrencies
fetches all available currencies on an exchange

Kind: instance method of deribit
Returns: object - an associative dictionary of currencies

See: https://docs.deribit.com/#public-get_currencies

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchCurrencies ([params])
Copy to clipboardErrorCopied

fetchStatus
the latest known information on the availability of the exchange API

Kind: instance method of deribit
Returns: object - a status structure

See: https://docs.deribit.com/#public-status

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchStatus ([params])
Copy to clipboardErrorCopied

fetchAccounts
fetch all the accounts associated with a profile

Kind: instance method of deribit
Returns: object - a dictionary of account structures indexed by the account type

See: https://docs.deribit.com/#private-get_subaccounts

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchAccounts ([params])
Copy to clipboardErrorCopied

fetchMarkets
retrieves data on all markets for deribit

Kind: instance method of deribit
Returns: Array<object> - an array of objects representing market data

See

https://docs.deribit.com/#public-get_currencies
https://docs.deribit.com/#public-get_instruments
Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchMarkets ([params])
Copy to clipboardErrorCopied

fetchBalance
query for balance and get the amount of funds available for trading or funds locked in orders

Kind: instance method of deribit
Returns: object - a balance structure

See

https://docs.deribit.com/#private-get_account_summary
https://docs.deribit.com/#private-get_account_summaries
Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
params.code	string	No	unified currency code of the currency for the balance, if defined 'privateGetGetAccountSummary' will be used, otherwise 'privateGetGetAccountSummaries' will be used
deribit.fetchBalance ([params])
Copy to clipboardErrorCopied

createDepositAddress
create a currency deposit address

Kind: instance method of deribit
Returns: object - an address structure

See: https://docs.deribit.com/#private-create_deposit_address

Param	Type	Required	Description
code	string	Yes	unified currency code of the currency for the deposit address
params	object	No	extra parameters specific to the exchange API endpoint
deribit.createDepositAddress (code[, params])
Copy to clipboardErrorCopied

fetchDepositAddress
fetch the deposit address for a currency associated with this account

Kind: instance method of deribit
Returns: object - an address structure

See: https://docs.deribit.com/#private-get_current_deposit_address

Param	Type	Required	Description
code	string	Yes	unified currency code
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchDepositAddress (code[, params])
Copy to clipboardErrorCopied

fetchTicker
fetches a price ticker, a statistical calculation with the information calculated over the past 24 hours for a specific market

Kind: instance method of deribit
Returns: object - a ticker structure

See: https://docs.deribit.com/#public-ticker

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchTicker (symbol[, params])
Copy to clipboardErrorCopied

fetchTickers
fetches price tickers for multiple markets, statistical information calculated over the past 24 hours for each market

Kind: instance method of deribit
Returns: object - a dictionary of ticker structures

See: https://docs.deribit.com/#public-get_book_summary_by_currency

Param	Type	Required	Description
symbols	Array<string>	No	unified symbols of the markets to fetch the ticker for, all market tickers are returned if not assigned
params	object	No	extra parameters specific to the exchange API endpoint
params.code	string	No	required the currency code to fetch the tickers for, eg. 'BTC', 'ETH'
deribit.fetchTickers ([symbols, params])
Copy to clipboardErrorCopied

fetchOHLCV
fetches historical candlestick data containing the open, high, low, and close price, and the volume of a market

Kind: instance method of deribit
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://docs.deribit.com/#public-get_tradingview_chart_data

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.paginate	boolean	No	whether to paginate the results, set to false by default
params.until	int	No	the latest time in ms to fetch ohlcv for
deribit.fetchOHLCV (symbol, timeframe[, since, limit, params])
Copy to clipboardErrorCopied

fetchTrades
get the list of most recent trades for a particular symbol.

Kind: instance method of deribit
Returns: Array<Trade> - a list of trade structures

See

https://docs.deribit.com/#public-get_last_trades_by_instrument
https://docs.deribit.com/#public-get_last_trades_by_instrument_and_time
Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch trades for
since	int	No	timestamp in ms of the earliest trade to fetch
limit	int	No	the maximum amount of trades to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	the latest time in ms to fetch trades for
deribit.fetchTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchTradingFees
fetch the trading fees for multiple markets

Kind: instance method of deribit
Returns: object - a dictionary of fee structures indexed by market symbols

See: https://docs.deribit.com/#private-get_account_summary

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchTradingFees ([params])
Copy to clipboardErrorCopied

fetchOrderBook
fetches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of deribit
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://docs.deribit.com/#public-get_order_book

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchOrderBook (symbol[, limit, params])
Copy to clipboardErrorCopied

fetchOrder
fetches information on an order made by the user

Kind: instance method of deribit
Returns: object - An order structure

See: https://docs.deribit.com/#private-get_order_state

Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	unified symbol of the market the order was made in
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchOrder (id, symbol[, params])
Copy to clipboardErrorCopied

createOrder
create a trade order

Kind: instance method of deribit
Returns: object - an order structure

See

https://docs.deribit.com/#private-buy
https://docs.deribit.com/#private-sell
Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much you want to trade in units of the base currency. For perpetual and inverse futures the amount is in USD units. For options it is in the underlying assets base currency.
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.trigger	string	No	the trigger type 'index_price', 'mark_price', or 'last_price', default is 'last_price'
params.trailingAmount	float	No	the quote amount to trail away from the current market price
deribit.createOrder (symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

editOrder
edit a trade order

Kind: instance method of deribit
Returns: object - an order structure

See: https://docs.deribit.com/#private-edit

Param	Type	Required	Description
id	string	Yes	edit order id
symbol	string	No	unified symbol of the market to edit an order in
type	string	No	'market' or 'limit'
side	string	No	'buy' or 'sell'
amount	float	Yes	how much you want to trade in units of the base currency. For perpetual and inverse futures the amount is in USD units. For options it is in the underlying assets base currency.
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.trailingAmount	float	No	the quote amount to trail away from the current market price
deribit.editOrder (id[, symbol, type, side, amount, price, params])
Copy to clipboardErrorCopied

cancelOrder
cancels an open order

Kind: instance method of deribit
Returns: object - An order structure

See: https://docs.deribit.com/#private-cancel

Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	not used by deribit cancelOrder ()
params	object	No	extra parameters specific to the exchange API endpoint
deribit.cancelOrder (id, symbol[, params])
Copy to clipboardErrorCopied

cancelAllOrders
cancel all open orders

Kind: instance method of deribit
Returns: Array<object> - a list of order structures

See

https://docs.deribit.com/#private-cancel_all
https://docs.deribit.com/#private-cancel_all_by_instrument
Param	Type	Required	Description
symbol	string	Yes	unified market symbol, only orders in the market of this symbol are cancelled when symbol is not undefined
params	object	No	extra parameters specific to the exchange API endpoint
deribit.cancelAllOrders (symbol[, params])
Copy to clipboardErrorCopied

fetchOpenOrders
fetch all unfilled currently open orders

Kind: instance method of deribit
Returns: Array<Order> - a list of order structures

See

https://docs.deribit.com/#private-get_open_orders_by_currency
https://docs.deribit.com/#private-get_open_orders_by_instrument
Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchOpenOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchClosedOrders
fetches information on multiple closed orders made by the user

Kind: instance method of deribit
Returns: Array<Order> - a list of order structures

See

https://docs.deribit.com/#private-get_order_history_by_currency
https://docs.deribit.com/#private-get_order_history_by_instrument
Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchClosedOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchOrderTrades
fetch all the trades made from a single order

Kind: instance method of deribit
Returns: Array<object> - a list of trade structures

See: https://docs.deribit.com/#private-get_user_trades_by_order

Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trades to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchOrderTrades (id, symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchMyTrades
fetch all trades made by the user

Kind: instance method of deribit
Returns: Array<Trade> - a list of trade structures

See

https://docs.deribit.com/#private-get_user_trades_by_currency
https://docs.deribit.com/#private-get_user_trades_by_currency_and_time
https://docs.deribit.com/#private-get_user_trades_by_instrument
https://docs.deribit.com/#private-get_user_trades_by_instrument_and_time
Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trades structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchMyTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchDeposits
fetch all deposits made to an account

Kind: instance method of deribit
Returns: Array<object> - a list of transaction structures

See: https://docs.deribit.com/#private-get_deposits

Param	Type	Required	Description
code	string	Yes	unified currency code
since	int	No	the earliest time in ms to fetch deposits for
limit	int	No	the maximum number of deposits structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchDeposits (code[, since, limit, params])
Copy to clipboardErrorCopied

fetchWithdrawals
fetch all withdrawals made from an account

Kind: instance method of deribit
Returns: Array<object> - a list of transaction structures

See: https://docs.deribit.com/#private-get_withdrawals

Param	Type	Required	Description
code	string	Yes	unified currency code
since	int	No	the earliest time in ms to fetch withdrawals for
limit	int	No	the maximum number of withdrawals structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchWithdrawals (code[, since, limit, params])
Copy to clipboardErrorCopied

fetchPosition
fetch data on a single open contract trade position

Kind: instance method of deribit
Returns: object - a position structure

See: https://docs.deribit.com/#private-get_position

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market the position is held in, default is undefined
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchPosition (symbol[, params])
Copy to clipboardErrorCopied

fetchPositions
fetch all open positions

Kind: instance method of deribit
Returns: Array<object> - a list of position structure

See: https://docs.deribit.com/#private-get_positions

Param	Type	Required	Description
symbols	Array<string>, undefined	Yes	list of unified market symbols
params	object	No	extra parameters specific to the exchange API endpoint
params.currency	string	No	currency code filter for positions
params.kind	string	No	market type filter for positions 'future', 'option', 'spot', 'future_combo' or 'option_combo'
params.subaccount_id	int	No	the user id for the subaccount
deribit.fetchPositions (symbols[, params])
Copy to clipboardErrorCopied

fetchVolatilityHistory
fetch the historical volatility of an option market based on an underlying asset

Kind: instance method of deribit
Returns: Array<object> - a list of volatility history objects

See: https://docs.deribit.com/#public-get_historical_volatility

Param	Type	Required	Description
code	string	Yes	unified currency code
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchVolatilityHistory (code[, params])
Copy to clipboardErrorCopied

fetchTransfers
fetch a history of internal transfers made on an account

Kind: instance method of deribit
Returns: Array<object> - a list of transfer structures

See: https://docs.deribit.com/#private-get_transfers

Param	Type	Required	Description
code	string	Yes	unified currency code of the currency transferred
since	int	No	the earliest time in ms to fetch transfers for
limit	int	No	the maximum number of transfers structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchTransfers (code[, since, limit, params])
Copy to clipboardErrorCopied

transfer
transfer currency internally between wallets on the same account

Kind: instance method of deribit
Returns: object - a transfer structure

See

https://docs.deribit.com/#private-submit_transfer_to_user
https://docs.deribit.com/#private-submit_transfer_to_subaccount
Param	Type	Required	Description
code	string	Yes	unified currency code
amount	float	Yes	amount to transfer
fromAccount	string	Yes	account to transfer from
toAccount	string	Yes	account to transfer to
params	object	No	extra parameters specific to the exchange API endpoint
deribit.transfer (code, amount, fromAccount, toAccount[, params])
Copy to clipboardErrorCopied

withdraw
make a withdrawal

Kind: instance method of deribit
Returns: object - a transaction structure

See: https://docs.deribit.com/#private-withdraw

Param	Type	Required	Description
code	string	Yes	unified currency code
amount	float	Yes	the amount to withdraw
address	string	Yes	the address to withdraw to
tag	string	Yes	
params	object	No	extra parameters specific to the exchange API endpoint
deribit.withdraw (code, amount, address, tag[, params])
Copy to clipboardErrorCopied

fetchDepositWithdrawFees
fetch deposit and withdraw fees

Kind: instance method of deribit
Returns: object - a list of fee structures

See: https://docs.deribit.com/#public-get_currencies

Param	Type	Required	Description
codes	Array<string>, undefined	Yes	list of unified currency codes
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchDepositWithdrawFees (codes[, params])
Copy to clipboardErrorCopied

fetchFundingRate
fetch the current funding rate

Kind: instance method of deribit
Returns: object - a funding rate structure

See: https://docs.deribit.com/#public-get_funding_rate_value

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
params.start_timestamp	int	No	fetch funding rate starting from this timestamp
params.end_timestamp	int	No	fetch funding rate ending at this timestamp
deribit.fetchFundingRate (symbol[, params])
Copy to clipboardErrorCopied

fetchFundingRateHistory
fetch the current funding rate

Kind: instance method of deribit
Returns: object - a funding rate structure

See: https://docs.deribit.com/#public-get_funding_rate_history

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch funding rate history for
limit	int	No	the maximum number of entries to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	fetch funding rate ending at this timestamp
params.paginate	boolean	No	default false, when true will automatically paginate by calling this endpoint multiple times. See in the docs all the availble parameters
deribit.fetchFundingRateHistory (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchLiquidations
retrieves the public liquidations of a trading pair

Kind: instance method of deribit
Returns: object - an array of liquidation structures

See: https://docs.deribit.com/#public-get_last_settlements_by_currency

Param	Type	Required	Description
symbol	string	Yes	unified CCXT market symbol
since	int	No	the earliest time in ms to fetch liquidations for
limit	int	No	the maximum number of liquidation structures to retrieve
params	object	No	exchange specific parameters for the deribit api endpoint
params.paginate	boolean	No	default false, when true will automatically paginate by calling this endpoint multiple times. See in the docs all the availble parameters
deribit.fetchLiquidations (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchMyLiquidations
retrieves the users liquidated positions

Kind: instance method of deribit
Returns: object - an array of liquidation structures

See: https://docs.deribit.com/#private-get_settlement_history_by_instrument

Param	Type	Required	Description
symbol	string	Yes	unified CCXT market symbol
since	int	No	the earliest time in ms to fetch liquidations for
limit	int	No	the maximum number of liquidation structures to retrieve
params	object	No	exchange specific parameters for the deribit api endpoint
deribit.fetchMyLiquidations (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchGreeks
fetches an option contracts greeks, financial metrics used to measure the factors that affect the price of an options contract

Kind: instance method of deribit
Returns: object - a greeks structure

See: https://docs.deribit.com/#public-ticker

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch greeks for
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchGreeks (symbol[, params])
Copy to clipboardErrorCopied

fetchOption
fetches option data that is commonly found in an option chain

Kind: instance method of deribit
Returns: object - an option chain structure

See: https://docs.deribit.com/#public-get_book_summary_by_instrument

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchOption (symbol[, params])
Copy to clipboardErrorCopied

fetchOptionChain
fetches data for an underlying asset that is commonly found in an option chain

Kind: instance method of deribit
Returns: object - a list of option chain structures

See: https://docs.deribit.com/#public-get_book_summary_by_currency

Param	Type	Required	Description
code	string	Yes	base currency to fetch an option chain for
params	object	No	extra parameters specific to the exchange API endpoint
deribit.fetchOptionChain (code[, params])
Copy to clipboardErrorCopied

fetchOpenInterest
Retrieves the open interest of a symbol

Kind: instance method of deribit
Returns: object - an open interest structurehttps://docs.ccxt.com/#/?id=open-interest-structure

See: https://docs.deribit.com/?shell#public-get_book_summary_by_instrument

Param	Type	Required	Description
symbol	string	Yes	unified CCXT market symbol
params	object	No	exchange specific parameters
deribit.fetchOpenInterest (symbol[, params])
Copy to clipboardErrorCopied

watchBalance
watch balance and get the amount of funds available for trading or funds locked in orders

Kind: instance method of deribit
Returns: object - a balance structure

See: https://docs.deribit.com/#user-portfolio-currency

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
deribit.watchBalance ([params])
Copy to clipboardErrorCopied

watchTicker
watches a price ticker, a statistical calculation with the information for a specific market.

Kind: instance method of deribit
Returns: object - a ticker structure

See: https://docs.deribit.com/#ticker-instrument_name-interval

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
params.interval	str	No	specify aggregation and frequency of notifications. Possible values: 100ms, raw
deribit.watchTicker (symbol[, params])
Copy to clipboardErrorCopied

watchTickers
watches a price ticker, a statistical calculation with the information calculated over the past 24 hours for all markets of a specific list

Kind: instance method of deribit
Returns: object - a ticker structure

See: https://docs.deribit.com/#ticker-instrument_name-interval

Param	Type	Required	Description
symbols	Array<string>	No	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
params.interval	str	No	specify aggregation and frequency of notifications. Possible values: 100ms, raw
deribit.watchTickers ([symbols, params])
Copy to clipboardErrorCopied

watchBidsAsks
watches best bid & ask for symbols

Kind: instance method of deribit
Returns: object - a ticker structure

See: https://docs.deribit.com/#quote-instrument_name

Param	Type	Required	Description
symbols	Array<string>	No	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
deribit.watchBidsAsks ([symbols, params])
Copy to clipboardErrorCopied

watchTrades
get the list of most recent trades for a particular symbol

Kind: instance method of deribit
Returns: Array<object> - a list of trade structures

See: https://docs.deribit.com/#trades-instrument_name-interval

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch trades for
since	int	No	timestamp in ms of the earliest trade to fetch
limit	int	No	the maximum amount of trades to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.interval	str	No	specify aggregation and frequency of notifications. Possible values: 100ms, raw
deribit.watchTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

watchTradesForSymbols
get the list of most recent trades for a list of symbols

Kind: instance method of deribit
Returns: Array<object> - a list of trade structures

See: https://docs.deribit.com/#trades-instrument_name-interval

Param	Type	Required	Description
symbols	Array<string>	Yes	unified symbol of the market to fetch trades for
since	int	No	timestamp in ms of the earliest trade to fetch
limit	int	No	the maximum amount of trades to fetch
params	object	No	extra parameters specific to the exchange API endpoint
deribit.watchTradesForSymbols (symbols[, since, limit, params])
Copy to clipboardErrorCopied

watchMyTrades
get the list of trades associated with the user

Kind: instance method of deribit
Returns: Array<object> - a list of trade structures

See: https://docs.deribit.com/#user-trades-instrument_name-interval

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch trades for. Use 'any' to watch all trades
since	int	No	timestamp in ms of the earliest trade to fetch
limit	int	No	the maximum amount of trades to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.interval	str	No	specify aggregation and frequency of notifications. Possible values: 100ms, raw
deribit.watchMyTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

watchOrderBook
watches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of deribit
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://docs.deribit.com/#book-instrument_name-group-depth-interval

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
params.interval	string	No	Frequency of notifications. Events will be aggregated over this interval. Possible values: 100ms, raw
deribit.watchOrderBook (symbol[, limit, params])
Copy to clipboardErrorCopied

watchOrderBookForSymbols
watches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of deribit
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://docs.deribit.com/#book-instrument_name-group-depth-interval

Param	Type	Required	Description
symbols	Array<string>	Yes	unified array of symbols
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
deribit.watchOrderBookForSymbols (symbols[, limit, params])
Copy to clipboardErrorCopied

watchOrders
watches information on multiple orders made by the user

Kind: instance method of deribit
Returns: Array<object> - a list of order structures

See: https://docs.deribit.com/#user-orders-instrument_name-raw

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
deribit.watchOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

watchOHLCV
watches historical candlestick data containing the open, high, low, and close price, and the volume of a market

Kind: instance method of deribit
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://docs.deribit.com/#chart-trades-instrument_name-resolution

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
deribit.watchOHLCV (symbol, timeframe[, since, limit, params])
Copy to clipboardErrorCopied

watchOHLCVForSymbols
watches historical candlestick data containing the open, high, low, and close price, and the volume of a market

Kind: instance method of deribit
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://docs.deribit.com/#chart-trades-instrument_name-resolution

Param	Type	Required	Description
symbolsAndTimeframes	Array<Array<string>>	Yes	array of arrays containing unified symbols and timeframes to fetch OHLCV data for, example [['BTC/USDT', '1m'], ['LTC/USDT', '5m']]
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
deribit.watchOHLCVForSymbols (symbolsAndTimeframes[, since, limit, params])
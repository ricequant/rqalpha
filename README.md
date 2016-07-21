# rqalpha

![Architecture](https://raw.githubusercontent.com/ricequant/rqalpha/master/docs/QQ20160713-1.jpeg)

## install
You can install from PyPI:

```
# install
pip install rqalpha

# upgrade
pip install -U rqalpha
```

## Dependencies

### TA-Lib Installation

You can install from PyPI:

```
$ pip install TA-Lib
```

To use [TA-Lib](https://github.com/mrjbq7/ta-lib) for python, you need to have the
[TA-Lib](http://ta-lib.org/hdr_dw.html) already installed:

##### Mac OS X

```
$ brew install ta-lib
```

##### Windows

Download [ta-lib-0.4.0-msvc.zip](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip)
and unzip to ``C:\ta-lib``

##### Linux

Download [ta-lib-0.4.0-src.tar.gz](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz) and:
```
$ untar and cd
$ ./configure --prefix=/usr
$ make
$ sudo make install
```

> If you build ``TA-Lib`` using ``make -jX`` it will fail but that's OK!
> Simply rerun ``make -jX`` followed by ``[sudo] make install``.


## Usage

```
Usage: rqalpha [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose
  --help         Show this message and exit.

Commands:
  generate_examples  generate example strategies to target folder
  run                run strategy from file
  update_bundle      update data bundle, download if not found
```

```
Usage: rqalpha run [OPTIONS]

  run strategy from file

Options:
  -f, --strategy-file PATH        [required]
  -s, --start-date DATE           [required]
  -e, --end-date DATE             [required]
  -o, --output-file PATH
  --draw-result / --no-draw-result
  --help                          Show this message and exit.
```

### Download data bundle
```
rqalpha update_bundle
```

### examples
```
rqalpha generate_examples -d ./
```

### run backtest
```
rqalpha run -f examples/simple_macd.py -s 2014-01-04 -e 2015-01-05 -o /tmp/a.pkl
```

## API Documentation
### Methods to be implemented
Your strategy algorithm has to implement at least two methods now: init and handle_bar

#### init
```python
init(context)
```
Called only once at the start of a backtest / paper trading. Your algorithm can use this method to set up any initial configuration or information that you'd like.
The context object will be passed to all other methods in your algorithm listed below as well.

> Parameters | Type | Notes
> -- | -- | --
> context | a plain object | Will be used globally in the whole algorithm. Properties are accessed using dot notation as well and also the traditional bracket notation.

**Returns**
None

**Example:**
```python
def init(context):
	# the naming of "cash_limit" is arbitrary, our engine
	# does not assume any special names on the context object
	context.cash_limit = 5000
```

#### handle_bar
```python
handle_bar(context, bar)
```
Triggered whenever a bar market event happens for any of your algorithm interested securities. It could be historical day bar, minute bar and real time minute bar. Refer to the table below for details about [Bar object](#bar-object).

> Parameters | Type | Notes
> -- | -- | --
> context | Same context object in init(context), stores any state/setup defined, and stores the portfolio object |
> bar | A dictionary containing all the bar data keyed by order_book_id. It represents a snapshot of the current market's bar data when this method is called. Market bar data snapshot information about each security interested are all available in this object.

**Returns**
None

**Examples**
```python
def handle_bar(context, bar):
	# put all your algorithm main logic here.
	# ...
	order_shares('000001.XSHE', 500)
	# ...
```

### Order Methods
In your own algorithm, you can use the order methods listed below. We provide quite a few order related APIs to make you to be able to place orders easily. We also provide some risk and position management when you are using advanced order methods like ```order_percent```.

#### order_shares
Place an order by specified number of shares. Order type is also passed in as parameters if needed. If style is omitted, it fires a market order by default.

```python
order_shares(id_or_ins, amount, style=MarketOrder())
```

> Parameters | Type | Notes
> -- | -- | --
> id_or_ins | str or instrument object -required | order_book_id or symbol or instrument object.
> amount | float-required | Number of shares to order. Positive means buy, negative means sell. It will be rounded down to the closest integral multiple of the lot size
> style | OrderType-optional | Order type and default is market order. The available order types are:
>> - style=MarketOrder()
>> - style=LimitOrder(limit_price)


**Returns**
A unique order id of int type.

**Examples**

- Buy 2000 shares  of pingan stock as market order:

```python
order_shares('000001.XSHE', 2000)
```

- Sell 2000 shares of pingan stock as market order:

```python
order_shares('000001.XSHE', -2000)
```

- Buy 1000 shares of pingan stock as limit order with price=10:

```python
order_shares('000001.XSHGE', 1000, style=LimitOrder(10))
```

#### order_lots
Place an order by specified number of lots. Order type is also passed in as parameters if needed. If style is omitted, it fires a market order by default.

```python
order_lots(id_or_ins, amount, style=OrderType)
```

> Parameters | Type | Notes
> -- | -- | --
> id_or_ins | str or instrument object -required | order_book_id or symbol or instrument object.
> amount | float-required | Number of lots to order. Positive means buy, negative means sell.
> style | OrderType-optional | Order type and default is market order. The available order types are:
>> - style=MarketOrder()
>> - style=LimitOrder(limit_price)
>
**Returns**
A unique order id of int type.

**Examples**

- Buy 20 lots of pingan stock as market order:

```python
order_lots('000001.XSHE', 20)
```

- Buy 10 lots of pingan stock as limit order with price=10:

```python
order_lots('000001.XSHGE', 10, style=LimitOrder(10))
```

#### order_value

Place ann order by specified value amount rather than specific number of shares/lots. Negative cash_amount results in selling the given amount of value, if the cash_amount is larger than you current security's position, then it will sell all shares of this security. Orders are always truncated to whole lot shares.

```python
order_value(id_or_ins, cash_amount, style=OrderType)
```

> Parameters | Type | Notes
> -- | -- | --
> id_or_ins | str or instrument object -required | order_book_id or symbol or instrument object.
> cash_amount | float-required | Cash amount to buy / sell the given value of securities. Positive means buy, negative means sell.
> style | OrderType-optional | Order type and default is market order. The available order types are:
>> - style=MarketOrder()
>> - style=LimitOrder(limit_price)
>

**Returns**
A unique order id of int type.

**Examples**

- Place a order for buying ￥10000 amount of pingan stock as market order. If the current price of pingan stock is ￥7.5, then the below code will buy 1300 shares since less than 100 shares will be truncated.

```python
order_value('000001.XSHE', 10000)
```

- Place an order for selling ￥ 10000 amount of pingan stock currently holding:

```python
order_value('000001.XSHE', -10000)
```


#### order_percent

Place an order for a security for a given percent of the current portfolio value, which is the sum of the positions value and ending cash balance. A negative percent order will result in selling given percent of current portfolio value. Orders are always truncated to whole shares. Percent should be a decimal number (0.50 means 50%), and its absolute value is <= 1.

```python
order_percent(id_or_ins, percent, style=OrderType)
```

> Parameters | Type | Notes
> -- | -- | --
> id_or_ins | str or instrument object -required | order_book_id or symbol or instrument object.
> percent | float-required | Percent of the current portfolio value. Positive means buy, negative means selling give percent of the current portfolio value. Orders are always truncated according to lot size.
> style | OrderType-optional | Order type and default is market order. The available order types are:
>> - style=MarketOrder()
>> - style=LimitOrder(limit_price)
>

**Returns**
A unique order id of int type.

**Sample**

- Order pingan stock shares worth 50% of current portfolio value. If pingan's price is currently ￥10/share and current portfolio's total value is ￥2000, then it will buy 200 shares of pingan stock. (Not including transaction cost and slippage.)

```python
order_percent('000001.XSHGE', 0.5)
```

#### order_target_value

Place an order to adjust a position to a target value. If there is no position for the security, an order is placed for the whole amount of target value. If there is already a position for the security, an order is placed for the difference between target value and current position value.

```python
order_target_value(id_or_ins, cash_amount, style=OrderType)
```

> Parameters | Type | Notes
> -- | -- | --
> id_or_ins | str or instrument object -required | order_book_id or symbol or instrument object.
> cash_amount | float-required | Target cash value for the adjusted position after placing order.
> style | OrderType-optional | Order type and default is market order. The available order types are:
>> - style=MarketOrder()
>> - style=LimitOrder(limit_price)
>

**Returns**
A unique order id of int type.

**Examples**
- If current portfolio already has pingan stock's position worth￥3000 , and cash_amount is set to ￥10000 in order_target_value, then the below code will buy pingan stock's woth ￥7000. (Shares truncated to multiple of lot size)

```python
order_target_value('000001.XSHE', 10000)
```

#### order_target_percent

Place an order to adjust position to a target percent of the portfolio value, so that your final position value takes the percentage you defined of your whole portfolio.

```
position_to_adjust = target_position - current_position
```

Portfolio value is calculated as sum of positions value and ending cash balance. The order quantity will be rounded down to integral multiple of lot size. Percent should be a decimal number (0.50 means 50%), and its absolute value is <= 1.

If the ```position_to_adjust``` calculated is positive, then it fires buy orders, otherwise it fires sell orders.

```python
order_target_percent(id_or_ins, percent, style=OrderType)
```

> Parameters | Type | Notes
> -- | -- | --
> id_or_ins | str or instrument object -required | order_book_id or symbol or instrument object.
> percent | float-required | Portfolio percentage allocated to the security. Positive means buy, negative means sell.
> style | OrderType-optional | Order type and default is market order. The available order types are:
>> - style=MarketOrder()
>> - style=LimitOrder(limit_price)
>

**Returns**
A unique order id of int type.

**Examples**

- If there's an existing position for pingan stock and occupies 10% of the current portfolio value, then our target is to allocate 15% of the portfolio value to pingan stock:

```python
order_target_percent('平安银行', 0.15)
```

#### cancel_order

TODO

#### get_order

Get a specified order by the unique order_id. The order object will be discarded at end of handle_bar.

```python
get_order(order_id)
```

> Parameters | Type | Notes
> -- | -- | --
> order_id | int-required | order's unique identifier

#### get_open_orders

TODO


### Other Methods

#### update_universe

```python
update_universe(id_or_symbols)
```

This method takes one or a list of id_or_symbol(s) as argument(s), to update the current subscription set of the instruments. It takes effect on the next bar event.

> Parameters | Type | Notes
> -- | -- | --
> id_or_symbols | str or iterable of strings | one or a list of id_or_symbol(s).

#### instruments
```python
instruments(id_or_symbols)
```
Convert a string or a list of strings as order_book_id to instrument object(s).

> Parameters | Type | Notes
> -- | -- | --
> id_or_symbols | str or iterable of strings | Passed in strings / iterable of strings are interpreted as order_book_ids. China market's order_book_ids are like '000001.XSHE' while US's market's order_book_ids are like 'AAPL.US'

Returns : one / a list of instrument(s) object(s) - by the id_or_symbol(s) requested.

##### Examples
- Get only one instrument - stock's information:
```python
[In]instruments('000001.XSHE')
[Out]
Instrument(order_book_id=000001.XSHE, symbol=平安银行, abbrev_symbol=PAYH, listed_date=19910403, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active)
```

- Get a list of instruments - China stocks' information:

```python
[In]instruments(['平安银行', '000024.XSHE'])
[Out]
[Instrument(order_book_id=000001.XSHE, symbol=平安银行, abbrev_symbol=PAYH, listed_date=19910403, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active), Instrument(order_book_id=000024.XSHE, symbol=招商地产, abbrev_symbol=ZSDC, listed_date=19930607, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active)]
```

### Bar object
Ricequant backend trading system (hammer) processes all the referenced securities in your strategy, it sends the bar events and also other events in the futures. (e.g.: tick data). Each time any of the securities has a bar event(could be day bar or minute bar, etc), [python]handle_bar[python] is called and the Bar object contains all the market data for securities.

For example, if you want to access the market data event bar data for 000001.XSHE, use TODO. The following properties in Bar object are supported:

TODO: if open is collision with python keyword?

> Properties | Type | Notes
> -- | -- | --
> `order_book_id` | str | Securities' unique identifier, e.g. "000001.XSHE"
> `symbol` | str | Securities' unique symbol, e.g. "平安银行"
> `datetime` | DateTime | The UTC timestamp of the bar market data event.
> `open` | float | The opening price of a security of a give bar.
> `close` | float | The closing price of a security of a given bar.
> `high` | float | The highest price of the security within the given bar.
> `low` | float | The lowest price of the security within the given bar.
> `volume`  | float | Total number of shares traded in the most recent bar event for this security.

There're also transforms provided:

```python
mavg(intervals, frequency='day')
```

Moving average price for the given security for a give number of intervals for a frequency, by default to day.

> Parameters | Type | Notes
> -- | -- | --
> intervals | int | a given number of intervals, e.g. given number of days
> frequency | str | frequency of the give number of intervals, by default as 'day'.


### Order object

Several properties in the Order object:

> Properties | Type | Notes
> -- | -- | --
> `instrument` | instrument object | The security which placed order at
> `filled_shares` | float | Total shares bought / sold for this order
> `quantity` | float | Total shares ordered.
> `last_price` | float | TODO: there is no support in Java yet.  The order's last filled price. If order is rejected, then it will return 0.

### Portfolio object
The portfolio object contains the whole strategy's portfolio information. In day bar backtest, this means the portfolio information after each day closing. The portfolio object is accessed using: `context.portfolio`

And has the following properties:

> Properties | Type | Notes
> -- | -- | --
> `starting_cash` | float | Starting cash allocated for the strategy for backtest or live trading.
> `cash` | float | Current amount of cash in your portfolio.
> `total_returns` | float | Cumulative percentage returns for the entire portfolio up to this point. Calculated as current portfolio value / starting value of the portfolio. The returns calculation includes cash and market_value. The return number is a percentage as 0.1
> `daily_returns` | float | The current date's portfolio's day returns.
> `market_value` | float | Current portfolio's market value (unrealized value).
> `portfolio_value` | float | Current portfolio's total value, includes both market_value and cash.
> `pnl` | float | Current portfolio's profit and loss.
> `start_date` | DateTime | Starting date of the portfolio's backtest / real trading.
> `annualized_returns` | float | Portfolio's annualized returns.
> `positions` | Dictionary | A dictionary of all the open positions, keyed by id_or_symbol. More details about position object could be found in the below section.
> `dividend_receivable` | float | Portfolio's dividend receivable before dividend cash allocated to portfolio. Explained in details in [Dividend Part](#dividends-splits-header)

### Position object
The position object represents the current open position for a security. And it is contained inside the positions dictionary. e.g. if your portfolio has an open pingan (000001.XSHE) position, you could get it by using:

```python
context.portfolio.positions['000001.XSHE']
```
And the position object has following properties:

> Properties | Type | Notes
> -- | -- | --
> `quantity` | int | Total number of shares in this position which means the non-closed position.
> `bought_quantity` | int | Total bought shares for a security. e.g. "If your portfolio has no trade for '000001.XSHE', then it returns 0"
> `sold_quantity` | int | Total sold shares for a security. e.g. "If your portfolio has 200 shares sold for '000001.XSHE' and 100 shares bought for '000001.XSHE'" Then it will return 200.
> `bought_value` | float | Total value of security bought. It equals sum every trade's bought price * bought shares, always positive.
> `sold_value` | float | Total value of security sold. It equals sum every trade's sold price * sold shares, always positive.
> `total_orders` | int | This position's total placed orders amount.
> `total_trades` | int | This position's total filled trades amount.

### Instrument object
Instrument represents all kinds of finance securities, e.g. Could be a stock, ETF, index or even futures contract in the future. There're several properties:

> Properties | Type | Notes
> -- | -- | --
> `order_book_id` | str | Unique identifier for a instrument/security.
> `symbol` | str | Security's human readable name.
> `abbrev_symbol` | str | Security's abbreviation symbol, e.g. Security's pinyin in China market, like: 'PAYH' for '000001.XSHE'.
> `round_lot` | int | How many shares for one lot.
> `sector_code` | str | Sector code abbreviation for a security, used globally.
> `sector_name` | str | Full sector code in local language.


## Develop
```
pyvenv venv
source venv/bin/activate
pip install -e .
```

## run unittest
```
py.test
```

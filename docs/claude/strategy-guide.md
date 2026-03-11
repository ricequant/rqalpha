# Strategy Writing Guide

## Documentation Reference

### When Writing Strategies

**IMPORTANT**: Before writing or modifying strategies, consult the documentation in `docs/source/` to understand the correct API usage and patterns.

### Key Documentation Files

1. **Tutorial** (`docs/source/intro/tutorial.rst`)
   - 10-minute quick start guide
   - Strategy lifecycle explanation (init, before_trading, handle_bar, after_trading)
   - Complete examples with data queries and trading operations
   - Read this first when learning strategy structure

2. **API Reference** (`docs/source/api/base_api.rst`)
   - Complete API documentation with function signatures
   - 约定函数 (Required Functions):
     - `init(context)` - Strategy initialization
     - `handle_bar(context, bar_dict)` - Bar data update handler
     - `handle_tick(context, tick)` - Tick data update handler
     - `before_trading(context)` - Pre-market handler
     - `after_trading(context)` - Post-market handler
     - `open_auction(context, bar_dict)` - Opening auction handler
   - Data query APIs (all_instruments, history_bars, current_snapshot, etc.)
   - Trading APIs (order_shares, order_value, order_target_percent, etc.)
   - **Always check this file for correct API signatures and parameters**

3. **Strategy Examples** (`docs/source/intro/examples.rst`)
   - Buy and hold strategy
   - Golden cross (moving average) strategy
   - Multiple complete working examples
   - Use these as templates for new strategies

4. **Running Algorithms** (`docs/source/intro/run_algorithm.rst`)
   - Detailed command-line options
   - Configuration file usage
   - Advanced execution modes

5. **Extended API** (`docs/source/api/extend_api.rst`)
   - Ricequant financial data APIs
   - Additional data sources and interfaces

### Documentation Reading Workflow

When writing strategies, follow this workflow:

1. **Start with examples** (`docs/source/intro/examples.rst`)
   - Find a similar strategy pattern
   - Copy the basic structure

2. **Check API reference** (`docs/source/api/base_api.rst`)
   - Verify function signatures
   - Check parameter types and return values
   - Understand context object properties

3. **Review tutorial** (`docs/source/intro/tutorial.rst`)
   - Understand strategy lifecycle
   - Learn data access patterns
   - See complete working examples

4. **Test incrementally**
   - Start with minimal code
   - Add features one at a time
   - Use assertions to verify behavior

## Common API Patterns

### Data Access
```python
# Get historical bars
prices = history_bars(order_book_id, bar_count, frequency, fields)

# Get current position
position = get_position(order_book_id)

# Access bar data
bar = bar_dict[order_book_id]
current_price = bar.close
```

### Trading Operations
```python
# Order by shares
order_shares(order_book_id, amount)

# Order by value
order_value(order_book_id, cash_amount)

# Target position percentage
order_target_percent(order_book_id, percent)

# Target position value
order_target_value(order_book_id, cash_amount)
```

### Context Object
```python
# Portfolio information
context.portfolio.cash
context.portfolio.positions

# Custom variables
context.my_variable = value

# Current time
context.now
```

## Simple Strategy Template

```python
from rqalpha.apis import *

def init(context):
    """初始化策略"""
    logger.info("策略初始化")
    context.stock = "000001.XSHE"  # 平安银行
    update_universe(context.stock)

def before_trading(context):
    """每日开盘前执行"""
    logger.info(f"日期: {context.now.date()}")

def handle_bar(context, bar_dict):
    """每个bar执行一次 - 主要交易逻辑"""
    # 获取历史数据
    prices = history_bars(context.stock, 20, '1d', 'close')

    if prices is not None:
        avg_price = prices.mean()
        current_price = bar_dict[context.stock].close

        # 简单的均值回归策略
        if current_price < avg_price * 0.98:
            order_value(context.stock, 30000)
            logger.info(f"买入 {context.stock}")
        elif current_price > avg_price * 1.02:
            position = get_position(context.stock)
            if position.quantity > 0:
                order_target_percent(context.stock, 0)
                logger.info(f"卖出 {context.stock}")

def after_trading(context):
    """每日收盘后执行"""
    positions = context.portfolio.positions
    if len(positions) > 0:
        logger.info(f"持仓: {[p.order_book_id for p in positions.values()]}")
```

## Documentation Build

To build and view the full documentation locally:

```bash
cd docs
pip install -r requirements.txt
make html
# Open docs/build/html/index.html in browser
```

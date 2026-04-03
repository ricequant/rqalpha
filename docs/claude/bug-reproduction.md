# Bug Reproduction Guide

## Writing Backtests for Bug Reproduction

**IMPORTANT**: This project focuses on running backtests. When encountering bugs, you may need to write a backtest to reproduce the issue.

## Quick Start: Writing a Simple Backtest

Create a strategy file (e.g., `test_strategy.py`):

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

## Running the Backtest

```bash
# Basic run
rqalpha run -f test_strategy.py -s 2023-01-01 -e 2023-03-31 --account stock 100000

# Save results to file
rqalpha run -f test_strategy.py -s 2023-01-01 -e 2023-03-31 --account stock 100000 -o result.pkl

# With detailed logging
rqalpha run -f test_strategy.py -s 2023-01-01 -e 2023-03-31 --account stock 100000 --log-level debug

# Generate report
rqalpha run -f test_strategy.py -s 2023-01-01 -e 2023-03-31 --account stock 100000 --report report.csv
```

## Writing Test Cases for Bug Reproduction

Create a test file (e.g., `test_bug_reproduction.py`):

```python
"""
Bug 复现测试模板

用于复现和验证 bug 修复
"""
import pytest
from rqalpha import run


def test_bug_order_execution():
    """
    Bug描述: [在这里描述bug]
    复现步骤: [列出复现步骤]
    预期行为: [描述预期行为]
    实际行为: [描述实际行为]
    """
    strategy_code = """
from rqalpha.apis import *

def init(context):
    context.stock = "000001.XSHE"
    context.order_placed = False

def handle_bar(context, bar_dict):
    # 复现bug的最小代码
    if not context.order_placed:
        order_id = order_shares(context.stock, 100)
        logger.info(f"订单ID: {order_id}")
        context.order_placed = True

        # 添加断言来验证预期行为
        assert order_id is not None, "订单ID不应该为None"
"""

    config = {
        "base": {
            "start_date": "2023-01-01",
            "end_date": "2023-01-10",
            "accounts": {"stock": 100000}
        }
    }

    # 运行回测
    result = run(config, source_code=strategy_code)

    # 验证结果
    assert result is not None


def test_bug_position_calculation():
    """测试持仓计算bug"""
    strategy_code = """
from rqalpha.apis import *

def init(context):
    context.stock = "000001.XSHE"

def handle_bar(context, bar_dict):
    if context.now.date().day == 3:
        order_value(context.stock, 50000)

    position = get_position(context.stock)
    if position.quantity > 0:
        logger.info(f"持仓: {position.quantity}, 市值: {position.market_value}")

        # 验证持仓计算
        assert position.market_value > 0, "持仓市值应该大于0"
        assert position.quantity > 0, "持仓数量应该大于0"
"""

    config = {
        "base": {
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "accounts": {"stock": 100000}
        }
    }

    result = run(config, source_code=strategy_code)
    assert result is not None


# 运行测试
if __name__ == "__main__":
    import sys

    test_bug_order_execution()
    sys.stderr.write("✓ 订单执行测试通过\n")

    test_bug_position_calculation()
    sys.stderr.write("✓ 持仓计算测试通过\n")
```

## Running Test Cases

```bash
# Run with pytest
pytest test_bug_reproduction.py -v

# Run specific test
pytest test_bug_reproduction.py::test_bug_order_execution -v

# Run directly
python test_bug_reproduction.py
```

## Common Backtest Patterns

### 1. Testing Order Execution
```python
def handle_bar(context, bar_dict):
    # 市价单
    order_id = order_shares("000001.XSHE", 100)

    # 限价单
    order_id = order_shares("000001.XSHE", 100, style=LimitOrder(10.5))

    # 目标仓位
    order_target_percent("000001.XSHE", 0.3)  # 30%仓位

    # 目标金额
    order_target_value("000001.XSHE", 50000)
```

### 2. Testing Position Management
```python
def handle_bar(context, bar_dict):
    # 获取单个持仓
    position = get_position("000001.XSHE")
    logger.info(f"数量: {position.quantity}, 市值: {position.market_value}")

    # 获取所有持仓
    positions = get_positions()
    for order_book_id, position in positions.items():
        logger.info(f"{order_book_id}: {position.quantity}")
```

### 3. Testing Historical Data
```python
def handle_bar(context, bar_dict):
    # 获取历史K线
    prices = history_bars("000001.XSHE", 20, '1d', 'close')

    # 获取多个字段
    bars = history_bars("000001.XSHE", 20, '1d', ['open', 'high', 'low', 'close'])

    # 验证数据
    assert prices is not None, "历史数据不应该为None"
    assert len(prices) <= 20, "数据长度不应超过请求长度"
```

### 4. Testing Multiple Accounts
```python
def init(context):
    # 多账户配置
    pass

def handle_bar(context, bar_dict):
    # 访问股票账户
    stock_account = context.portfolio.accounts['stock']
    logger.info(f"股票账户现金: {stock_account.cash}")

    # 访问期货账户
    if 'future' in context.portfolio.accounts:
        future_account = context.portfolio.accounts['future']
        logger.info(f"期货账户现金: {future_account.cash}")
```

## Debugging Backtest Issues

### 1. Check Logs
```bash
# Run with debug logging
rqalpha run -f strategy.py -s 2023-01-01 -e 2023-01-31 --account stock 100000 --log-level debug 2>&1 | tee debug.log

# Filter specific logs
rqalpha run -f strategy.py ... 2>&1 | grep "ERROR"
rqalpha run -f strategy.py ... 2>&1 | grep "订单"
```

### 2. Add Logging in Strategy
```python
def handle_bar(context, bar_dict):
    # 打印调试信息
    logger.info(f"当前时间: {context.now}")
    logger.info(f"账户现金: {context.portfolio.cash}")
    logger.info(f"持仓数量: {len(context.portfolio.positions)}")

    # 打印bar数据
    for stock in bar_dict:
        bar = bar_dict[stock]
        logger.info(f"{stock}: 开{bar.open} 高{bar.high} 低{bar.low} 收{bar.close}")
```

### 3. Use Assertions
```python
def handle_bar(context, bar_dict):
    position = get_position("000001.XSHE")

    # 添加断言验证预期
    assert position.quantity >= 0, "持仓数量不能为负"
    assert context.portfolio.cash >= 0, "现金不能为负"

    # 验证数据完整性
    prices = history_bars("000001.XSHE", 20, '1d', 'close')
    assert prices is not None, "历史数据不应该为None"
    assert len(prices) > 0, "历史数据不应该为空"
```

## Best Practices for Bug Reproduction

1. **Minimal Reproducible Example**: Write the smallest possible strategy that reproduces the bug
2. **Clear Documentation**: Add comments explaining what the bug is and expected vs actual behavior
3. **Specific Date Ranges**: Use short date ranges (1-3 months) for faster iteration
4. **Assertions**: Add assertions to verify expected behavior
5. **Logging**: Use `logger.info()` to track execution flow
6. **Isolation**: Test one thing at a time - don't mix multiple features in one test

## Common Pitfalls

1. **Using `print()` after backtest**: Use `sys.stderr.write()` or `logger.info()` instead
2. **Accessing undefined APIs**: Check API availability in `rqalpha/api.py`
3. **Wrong date format**: Use 'YYYY-MM-DD' format for dates
4. **Missing bundle**: Ensure bundle is downloaded before running
5. **Incorrect stock codes**: Use format like "000001.XSHE" (stock code + exchange)

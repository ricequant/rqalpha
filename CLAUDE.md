# CLAUDE.md

RQAlpha is an algorithmic trading system for quantitative trading with backtesting and live trading capabilities.

**License**: Non-commercial use only (Apache 2.0). Commercial use requires authorization from Ricequant.

## Quick Commands

```bash
# Run backtest
rqalpha run -f strategy.py -s 2014-01-01 -e 2016-01-01 --account stock 100000

# With RQData connection
rqalpha run --rqdatac-uri tcp://user:password@host:port -f strategy.py -s 2014-01-01 -e 2016-01-01 --account stock 100000

# Download bundle data
rqalpha download-bundle

# Update bundle
rqalpha update-bundle --rqdatac-uri tcp://user:password@host:port

# Generate examples
rqalpha examples -d ./examples

# Run tests
pytest
pytest tests/unittest/
pytest tests/integration_tests/
```

## Project-Specific Rules

### When Writing Strategies

1. **Always consult documentation first**: Read `docs/source/intro/tutorial.rst` and `docs/source/api/base_api.rst` before writing strategies
2. **Use correct API signatures**: Check `docs/source/api/base_api.rst` for function parameters and return types
3. **Follow strategy lifecycle**: Implement `init()`, `before_trading()`, `handle_bar()`, `after_trading()` in correct order
4. **Stock code format**: Always use format like "000001.XSHE" (code + exchange)
5. **Date format**: Use 'YYYY-MM-DD' format for dates

### When Debugging/Testing

1. **Write minimal reproducible examples**: Create smallest possible strategy that reproduces the bug
2. **Use logger, not print**: Use `logger.info()` instead of `print()` in strategies
3. **Add assertions**: Verify expected behavior with assertions in test code
4. **Short date ranges**: Use 1-3 month ranges for faster iteration during testing

### Code Modifications

1. **Chinese comments OK**: Domain-specific logic can use Chinese comments
2. **Follow PEP 8**: Standard Python style guide
3. **Test before commit**: Run pytest to ensure tests pass

## Key Architecture Points

- **Environment singleton**: Access via `Environment.get_instance()` - central registry for all components
- **Event-driven**: Mods subscribe to events (BAR, TICK, BEFORE_TRADING, etc.)
- **Mod system**: Extensibility through `AbstractMod` interface
- **Data bundle**: HDF5 format stored in `~/.rqalpha/bundle/`
- **Config hierarchy**: CLI args > strategy `__config__` > config file > defaults

## Detailed Documentation

For detailed information, see:
- **Architecture**: `docs/claude/architecture.md` - Core components and system design
- **Strategy Writing**: `docs/claude/strategy-guide.md` - How to write strategies with API reference
- **Bug Reproduction**: `docs/claude/bug-reproduction.md` - Writing backtests to reproduce bugs
- **Development**: `docs/claude/development.md` - Development guidelines and debugging

Official documentation:
- Tutorial: `docs/source/intro/tutorial.rst`
- API Reference: `docs/source/api/base_api.rst`
- Examples: `docs/source/intro/examples.rst`

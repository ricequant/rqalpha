# Development Guide

## Code Style
- Follow PEP 8
- Use type hints where appropriate
- Chinese comments are acceptable for domain-specific logic

## Testing
- Write tests for new features
- Use pytest fixtures in `tests/integration_tests/conftest.py`
- Test both unit and integration levels
- Ensure tests pass before committing

## Adding a New Mod

1. Create mod package: `rqalpha_mod_<name>/`
2. Implement `AbstractMod` interface
3. Define `__config__` dict with mod settings
4. Implement `load_mod()` function returning mod instance
5. Register mod in config file

## Extending Data Sources

1. Implement `AbstractDataSource` interface
2. Override required methods: `get_bar()`, `history_bars()`, etc.
3. Register via `env.set_data_source()` in mod `start_up()`

## Debugging

### Enable Debug Logging
```bash
rqalpha run -f strategy.py --log-level debug
```

### Profiling
```bash
# Requires line_profiler
pip install rqalpha[profiler]
rqalpha run -f strategy.py --enable-profiler
```

### Common Issues

1. **Bundle not found**: Run `rqalpha download-bundle` first
2. **Import errors**: Ensure rqalpha is installed in current environment
3. **Data mismatch**: Check bundle version matches RQAlpha version
4. **Mod conflicts**: Check mod priority and load order

## API Exploration

```bash
# List all instruments
python -c "import rqalpha; from rqalpha.api import *; print(all_instruments('CS'))"

# Get trading dates
python -c "from rqalpha.api import *; print(get_trading_dates('2020-01-01', '2020-12-31'))"
```

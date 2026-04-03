# RQAlpha Architecture

## Core Components

1. **Environment** (`rqalpha/environment.py`)
   - Central registry for all system components
   - Manages global state and provides access to data, broker, event bus, etc.
   - Singleton pattern - accessed via `Environment.get_instance()`

2. **Main Entry** (`rqalpha/main.py`)
   - `run()` function orchestrates the entire backtest/live trading process
   - Initializes environment, loads strategy, sets up mods, and executes

3. **Strategy Execution** (`rqalpha/core/`)
   - `Strategy`: Wraps user strategy code
   - `StrategyContext`: Provides context object passed to strategy functions
   - `StrategyLoader`: Loads strategy from file, source code, or user functions
   - `Executor`: Executes strategy lifecycle (init, before_trading, handle_bar, etc.)

4. **Data Layer** (`rqalpha/data/`)
   - `DataProxy`: Main interface for accessing market data
   - `bundle.py`: Manages local data bundle (HDF5 format)
   - `BaseDataSource`: Abstract interface for data sources
   - Supports both local bundle and RQData remote connection

5. **Event System** (`rqalpha/core/events.py`)
   - Event-driven architecture
   - Key events: `PRE_BEFORE_TRADING`, `BEFORE_TRADING`, `BAR`, `TICK`, `AFTER_TRADING`, `POST_SETTLEMENT`
   - Mods can subscribe to events to extend functionality

6. **Mod System** (`rqalpha/mod/`)
   - Extensibility through `AbstractMod` interface
   - Mods implement `start_up()` and `tear_down()` lifecycle methods
   - System mods (built-in):
     - `sys_accounts`: Account and position management
     - `sys_simulation`: Simulation broker and event source
     - `sys_analyser`: Performance analysis and reporting
     - `sys_risk`: Risk management and order validation
     - `sys_scheduler`: Scheduled task execution
     - `sys_progress`: Progress display
     - `sys_transaction_cost`: Transaction cost calculation

7. **Interface Layer** (`rqalpha/interface.py`)
   - Abstract interfaces for extensibility:
     - `AbstractMod`: Mod extension interface
     - `AbstractBroker`: Broker interface for order execution
     - `AbstractDataSource`: Data source interface
     - `AbstractPosition`: Position interface
     - `AbstractPersistProvider`: Persistence interface

## Key Directories

- `rqalpha/`: Main package
  - `api.py`: Public API functions
  - `apis/`: API implementations
  - `cmds/`: CLI command implementations
  - `core/`: Core execution engine
  - `data/`: Data access layer
  - `mod/`: Built-in mods
  - `model/`: Data models (Order, Trade, Position, etc.)
  - `portfolio/`: Portfolio and account management
  - `utils/`: Utility functions
  - `examples/`: Example strategies

- `tests/`: Test suite
  - `unittest/`: Unit tests
  - `integration_tests/`: Integration tests
  - `api_tests/`: API tests

## Configuration System

- Uses YAML configuration files
- Default config: `rqalpha/config.yml`
- Mod configs: `rqalpha/mod_config.yml`
- Config hierarchy: CLI args > strategy `__config__` > config file > defaults
- Access via `env.config` or passed to mod `start_up()`

## Strategy Lifecycle

1. `init(context)` - Called once at strategy start
2. `before_trading(context)` - Called before market opens each day
3. `handle_bar(context, bar_dict)` - Called on each bar (1d/1m/tick frequency)
4. `after_trading(context)` - Called after market closes each day

## Data Bundle Structure

- Stored in `~/.rqalpha/bundle/` by default
- HDF5 format for efficient storage and access
- Contains:
  - Instrument info
  - Daily bars
  - Dividends and splits
  - Trading calendar
  - Index weights

## Common Patterns

### Accessing Environment
```python
from rqalpha.environment import Environment
env = Environment.get_instance()
```

### Working with Events
```python
# Subscribe to events in mod start_up()
env.event_bus.add_listener(EVENT.POST_BAR, on_bar_callback)

# Publish custom events
env.event_bus.publish_event(Event(EVENT.CUSTOM, data=...))
```

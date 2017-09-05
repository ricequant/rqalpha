.. _development-data-source:

==================
扩展数据源
==================

在程序化交易的过程中，数据的获取是非常重要的一个环节，而数据又包含很多种不同类型的数据，有行情数据、财务数据、指标因子数据以及自定义类型数据。

在实际交易过程中，对接数据源主要分为两种：

*   增加自有数据源

    *   策略中直接读取自有数据
    *   在策略中 `import` 自定义模块
    *   扩展 API 实现自有数据的读取

*   替换已有数据源

    *   基础数据
    *   行情数据

增加自有数据源
====================================

策略中直接读取自有数据
------------------------------------

RQAlpha 不限制本地运行的策略调使用哪些库，因此您可以直接在策略中读取文件、访问数据库等，但需要关注如下两个注意事项:

*   请在 :code:`init`, :code:`before_trading`, :code:`handle_bar`, :code:`handle_tick`, :code:`after_trading` 等函数中读取自有数据，而不要在函数外执行数据获取的代码，否则可能会产生异常。
*   RQAlpha 是读取策略代码并执行的，因此实际当前路径是运行 `rqalpha` 命令的路径，策略使用相对路径容易产生异常。如果您需要根据策略路径来定位相对路径可以通过 :code:`context.config.base.strategy_file` 来获取策略路径，从而获取相对策略文件的其他路径，具体使用方式请看下面的示例代码。

`read_csv_as_df <https://github.com/ricequant/rqalpha/blob/develop/rqalpha/examples/data_source/read_csv_as_df.py>`_

..  code-block:: python3

    from rqalpha.api import *


    def read_csv_as_df(csv_path):
        # 通过 pandas 读取 csv 文件，并生成 DataFrame
        import pandas as pd
        data = pd.read_csv(csv_path)
        return data


    def init(context):
        import os
        # 获取当前运行策略的文件路径
        strategy_file_path = context.config.base.strategy_file
        # 根据当前策略的文件路径寻找到相对路径为 "../IF1706_20161108.csv" 的 csv 文件
        csv_path = os.path.join(os.path.dirname(strategy_file_path), "../IF1706_20161108.csv")
        # 读取 csv 文件并生成 df
        IF1706_df = read_csv_as_df(csv_path)
        # 传入 context 中
        context.IF1706_df = IF1706_df


    def before_trading(context):
        # 通过context 获取在 init 阶段读取的 csv 文件数据
        logger.info(context.IF1706_df)


    def handle_bar(context, bar):
        pass


    __config__ = {
        "base": {
            "start_date": "2015-01-09",
            "end_date": "2015-01-10",
            "frequency": "1d",
            "matching_type": "current_bar",
            "benchmark": None,
            "accounts": {
                "future": 1000000
            }
        },
        "extra": {
            "log_level": "verbose",
        },
    }

在策略中 import 自定义模块
------------------------------------

如果您定义了自定义模块，希望在策略中引用，只需要在初始化的时候将模块对应的路径添加到 :code:`sys.path` 即可，但需要关注如下两个注意事项:

*   如果没有特殊原因，请在 :code:`init` 阶段添加 :code:`sys.path` 路径。
*   如果您的自定义模块是基于策略策略的相对路径，则需要在 :code:`init` 函数中通过 :code:`context.config.base.strategy_file` 获取到策略路径，然后再添加到 :code:`sys.path` 中。
*   RQAlpha 是读取策略代码并执行的，因此实际当前路径是执行 `rqalpha` 命令的路径，避免使用相对路径。

`get_csv_module <https://github.com/ricequant/rqalpha/blob/develop/rqalpha/examples/data_source/get_csv_module.py>`_


..  code-block:: python3

    import os


    def read_csv_as_df(csv_path):
        import pandas as pd
        data = pd.read_csv(csv_path)
        return data


    def get_csv():
        csv_path = os.path.join(os.path.dirname(__file__), "../IF1706_20161108.csv")
        return read_csv_as_df(csv_path)

`import_get_csv_module <https://github.com/ricequant/rqalpha/blob/develop/rqalpha/examples/data_source/import_get_csv_module.py>`_

..  code-block:: python3

    from rqalpha.api import *


    def init(context):
        import os
        import sys
        strategy_file_path = context.config.base.strategy_file
        sys.path.append(os.path.realpath(os.path.dirname(strategy_file_path)))

        from get_csv_module import get_csv

        IF1706_df = get_csv()
        context.IF1706_df = IF1706_df


    def before_trading(context):
        logger.info(context.IF1706_df)


    __config__ = {
        "base": {
            "start_date": "2015-01-09",
            "end_date": "2015-01-10",
            "frequency": "1d",
            "matching_type": "current_bar",
            "benchmark": None,
            "accounts": {
                "future": 1000000
            }
        },
        "extra": {
            "log_level": "verbose",
        },
    }

扩展 API 实现自有数据的读取
------------------------------------

我们通过创建一个 Mod 来实现扩展 API，启动策略时，只需要开启该 Mod, 对应的扩展 API 便可以生效，在策略中直接使用。

`rqalpha_mod_extend_api_demo <https://github.com/ricequant/rqalpha/blob/develop/rqalpha/examples/extend_api/rqalpha_mod_extend_api_demo.py>`_

..  code-block:: python3

    import os
    import pandas as pd
    from rqalpha.interface import AbstractMod


    __config__ = {
        "csv_path": None
    }


    def load_mod():
        return ExtendAPIDemoMod()


    class ExtendAPIDemoMod(AbstractMod):
        def __init__(self):
            # 注入API 一定要在初始化阶段，否则无法成功注入
            self._csv_path = None
            self._inject_api()

        def start_up(self, env, mod_config):
            self._csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), mod_config.csv_path))

        def tear_down(self, code, exception=None):
            pass

        def _inject_api(self):
            from rqalpha import export_as_api
            from rqalpha.execution_context import ExecutionContext
            from rqalpha.const import EXECUTION_PHASE

            @export_as_api
            @ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                            EXECUTION_PHASE.BEFORE_TRADING,
                                            EXECUTION_PHASE.ON_BAR,
                                            EXECUTION_PHASE.AFTER_TRADING,
                                            EXECUTION_PHASE.SCHEDULED)
            def get_csv_as_df():
                data = pd.read_csv(self._csv_path)
                return data


如上代码，我们定义了 :code:`rqalpha_mod_extend_api_demo` Mod，该 Mod 接受一个参数: :code:`csv_path`， 其会转换为基于 Mod 的相对路径来获取对应的 csv 地址。

在该Mod中通过 :code:`_inject_api` 方法，定义了 :code:`get_csv_ad_df` 函数，并通过 :code:`from rqalpha import export_as_api` 装饰器完成了 API 的注入。

如果想限制扩展API所运行使用的范围，可以通过 :code:`ExecutionContext.enforce_phase` 来控制.

接下来我们看一下如何在策略中使用该扩展API:

`test_extend_api <https://github.com/ricequant/rqalpha/blob/develop/rqalpha/examples/extend_api/test_extend_api.py>`_

..  code-block:: python3

    from rqalpha.api import *


    def init(context):
        IF1706_df = get_csv_as_df()
        context.IF1706_df = IF1706_df


    def before_trading(context):
        logger.info(context.IF1706_df)


    __config__ = {
        "base": {
            "start_date": "2015-01-09",
            "end_date": "2015-01-10",
            "frequency": "1d",
            "matching_type": "current_bar",
            "benchmark": None,
            "accounts": {
                "future": 1000000
            }
        },
        "extra": {
            "log_level": "verbose",
        },
        "mod": {
            "extend_api_demo": {
                "enabled": True,
                "lib": "rqalpha.examples.extend_api.rqalpha_mod_extend_api_demo",
                "csv_path": "../IF1706_20161108.csv"
            }
        }
    }

如上述代码，首先配置信息中添加 `extend_api_demo` 对应的配置

*   :code:`enabled`: True 表示开启该 Mod
*   :code:`lib`: 指定该 Mod 对应的加载位置(rqlalpha 会自动去寻找 `rqalpha_mod_xxx` 对应的库，如果该库已经通过 `pip install` 安装，则无需显式指定 lib)
*   :code:`csv_path`： 指定 csv 所在位置

至此，我们就可以直接在策略中使用 `get_csv_as_df` 函数了。

替换已有数据源
====================================

基础数据
------------------------------------

通过 `$ rqalpha update_bundle` 下载的数据有如下文件：

..  code-block:: bash

    $ cd ~/.rqalpha/bundle & tree -A -d -L 1    

    .
    ├── adjusted_dividends.bcolz 
    ├── funds.bcolz
    ├── futures.bcolz
    ├── indexes.bcolz
    ├── original_dividends.bcolz
    ├── st_stock_days.bcolz
    ├── stocks.bcolz
    ├── suspended_days.bcolz
    ├── trading_dates.bcolz
    └── yield_curve.bcolz

目前基础数据，比如 `Instruments`, `st_stocks`, `suspended_days`, `trading_dates` 都是全量数据，并且可以通过 `$ rqalpha update_bundle` 每天更新，因此没有相应的显式接口可以对其进行替换。

您如果想要替换，可以使用如下两种方式:

*   写脚本将自有数据源按照相同的格式生成对应的文件，并进行文件替换。
*   实现 `AbstractDataSource <http://rqalpha.io/zh_CN/latest/development/basic_concept.html#datasource>`_ 对应的接口，您可以继承 `BaseDataSource <https://github.com/ricequant/rqalpha/blob/develop/rqalpha/data/base_data_source.py>`_ 并 override 对应的接口即可完成替换。


行情数据 - 五十行代码接入 tushare 行情数据
------------------------------------------

RQAlpha 支持自定义扩展数据源。得益于 RQAlpha 的 mod 机制，我们可以很方便的替换或者扩展默认的数据接口。

RQAlpha 将提供给用户的数据 API 和回测所需的基础数据抽象成了若干个函数，这些函数被封于 :class:`~DataSource` 类中，并将在需要的时候被调用。简单的说，我们只需要在自己定义的 mod 中扩展或重写默认的 :class:`~DataSource` 类，就可以替换掉默认的数据源，接入自有数据。

:class:`~DataSource` 类的完整文档，请参阅 :ref:`development-basic-concept`。下面将用一个简单的例子，为大家介绍如何用五十行左右的代码将默认的行情数据替换为 `TuShare`_ 的行情数据。

.. _TuShare: http://tushare.org

TushareKDataMod 的作用是使用 tushare 提供的k线数据替换 data_bundle 中的行情数据，由于目前 tushare 仅仅开放了日线、周线和月线的历史数据，所以该 mod 仍然只能提供日回测的功能，若未来 tushare 开放了60分钟或5分钟线的历史数据，只需进行简单修改，便可通过该 mod 使 RQAlpha 实现5分钟回测。

开工前，首先熟悉一下用到的 tushare 的k线接口，接口如下：

.. code-block:: python3

    get_k_data(code, ktype='D', autype='qfq', index=False, start=None, end=None)


如上文所说，我们要做的主要就是扩展或重写默认的 DataSource 类。在此处，我们选择建立一个新的 DataSource 类，该类继承于默认的 :class:`~BaseDataSource` 类。

这样做的好处在于我们不必重写 DataSource 需要实现的所有函数，而可以只实现与我们想替换的数据源相关的函数，其他数据的获取直接甩锅给父类 :class:`~BaseDataSource` 。

与行情数据密切相关的主要有以下三个函数：

*   :code:`current_snapshot(instrument, frequency, dt)`
*   :code:`get_bar(instrument, dt, frequency)`
*   :code:`history_bars(instrument, bar_count, frequency, fields, dt, skip_suspended=True)`
*   :code:`available_data_range(frequency)`

经过查看 :class:`DataProxy` 类的源代码，可以发现，提供日级别数据的 DataSource 类不需要实现 :code:`current_snapshot` 函数，所以我们只关注后三个函数的实现。

:code:`get_bar` 和 :code:`history_bars` 函数实现的主要功能都是传入 instrument 对象，从 tushare 获取指定时间或时间段的 bar 数据。我们把这一过程抽象为一个函数:

.. code-block:: python3

    class TushareKDataSource(BaseDataSource):

    ...

    @staticmethod
    def get_tushare_k_data(instrument, start_dt, end_dt):

        # 首先获取 order_book_id 并将其转换为 tushare 所能识别的 code
        order_book_id = instrument.order_book_id
        code = order_book_id.split(".")[0]

        # tushare 行情数据目前仅支持股票和指数，并通过 index 参数进行区分
        if instrument.type == 'CS':
            index = False
        elif instrument.type == 'INDX':
            index = True
        else:
            return None

        # 调用 tushare 函数，注意 datetime 需要转为指定格式的 str
        return ts.get_k_data(code, index=index, start=start_dt.strftime('%Y-%m-%d'), end=end_dt.strftime('%Y-%m-%d'))


现在实现 :code:`get_bar` 函数：

.. code-block:: python3

    class TushareKDataSource(BaseDataSource):

        ...

        def get_bar(self, instrument, dt, frequency):

            # tushare k线数据暂时只能支持日级别的回测，其他情况甩锅给默认数据源
            if frequency != '1d':
                return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)

            # 调用上边写好的函数获取k线数据
            bar_data = self.get_tushare_k_data(instrument, dt, dt)

            # 遇到获取不到数据的情况，同样甩锅；若有返回值，注意转换格式。
            if bar_data is None or bar_data.empty:
                return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)
            else:
                return bar_data.iloc[0].to_dict()


然后是硬骨头 :code:`history_bars` 函数：

.. code-block:: python3

    class TushareKDataSource(BaseDataSource):

        ...

        def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True):
            # tushare 的k线数据未对停牌日期做补齐，所以遇到不跳过停牌日期的情况我们先甩锅。有兴趣的开发者欢迎提交代码补齐停牌日数据。
            if frequency != '1d' or not skip_suspended:
                return super(TushareKDataSource, self).history_bars(instrument, bar_count, frequency, fields, dt, skip_suspended)

            # 参数只提供了截止日期和天数，我们需要自己找到开始日期
            # 获取交易日列表，并拿到截止日期在列表中的索引，之后再算出开始日期的索引
            start_dt_loc = self.get_trading_calendar().get_loc(dt.replace(hour=0, minute=0, second=0, microsecond=0)) - bar_count + 1
            # 根据索引拿到开始日期
            start_dt = self.get_trading_calendar()[start_dt_loc]

            # 调用上边写好的函数获取k线数据
            bar_data = self.get_tushare_k_data(instrument, start_dt, dt)

            if bar_data is None or bar_data.empty:
                return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)
            else:
                # 注意传入的 fields 参数可能会有不同的数据类型
                if isinstance(fields, six.string_types):
                    fields = [fields]
                fields = [field for field in fields if field in bar_data.columns]

                # 这样转换格式会导致返回值的格式与默认 DataSource 中该方法的返回值格式略有不同。欢迎有兴趣的开发者提交代码进行修改。
                return bar_data[fields].as_matrix()

最后是 :code:`available_data_range` 函数

.. code-block:: python3

    class TushareKDataSource(BaseDataSource):

        ...

        def available_data_range(self, frequency):
            return date(2005, 1, 1), date.today() - relativedelta(days=1)

把以上几个函数组合起来，并加入构造函数，就完成了我们重写的 DataSource 类。完整代码如下：

.. code-block:: python3

    import six
    import tushare as ts
    from datetime import date
    from dateutil.relativedelta import relativedelta
    from rqalpha.data.base_data_source import BaseDataSource


    class TushareKDataSource(BaseDataSource):
        def __init__(self, path):
            super(TushareKDataSource, self).__init__(path)

        @staticmethod
        def get_tushare_k_data(instrument, start_dt, end_dt):
            order_book_id = instrument.order_book_id
            code = order_book_id.split(".")[0]

            if instrument.type == 'CS':
                index = False
            elif instrument.type == 'INDX':
                index = True
            else:
                return None

            return ts.get_k_data(code, index=index, start=start_dt.strftime('%Y-%m-%d'), end=end_dt.strftime('%Y-%m-%d'))

        def get_bar(self, instrument, dt, frequency):
            if frequency != '1d':
                return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)

            bar_data = self.get_tushare_k_data(instrument, dt, dt)

            if bar_data is None or bar_data.empty:
                return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)
            else:
                return bar_data.iloc[0].to_dict()

        def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True):
            if frequency != '1d' or not skip_suspended:
                return super(TushareKDataSource, self).history_bars(instrument, bar_count, frequency, fields, dt, skip_suspended)

            start_dt_loc = self.get_trading_calendar().get_loc(dt.replace(hour=0, minute=0, second=0, microsecond=0)) - bar_count + 1
            start_dt = self.get_trading_calendar()[start_dt_loc]

            bar_data = self.get_tushare_k_data(instrument, start_dt, dt)

            if bar_data is None or bar_data.empty:
                return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)
            else:
                if isinstance(fields, six.string_types):
                    fields = [fields]
                fields = [field for field in fields if field in bar_data.columns]

                return bar_data[fields].as_matrix()

        def available_data_range(self, frequency):
            return date(2005, 1, 1), date.today() - relativedelta(days=1)


到目前为止，我们的主要工作已经完成了。想要将我们刚刚写好的 DataSource 类投入使用，还需要将其放入一个 mod 来被 RQAlpha 加载。

mod 的实现如下：

.. code-block:: python3

    from rqalpha.interface import AbstractMod

    from .data_source import TushareKDataSource


    class TushareKDataMode(AbstractMod):
        def __init__(self):
            pass

        def start_up(self, env, mod_config):
            # 设置 data_source 为 TushareKDataSource 类的对象
            env.set_data_source(TushareKDataSource(env.config.base.data_bundle_path))

        def tear_down(self, code, exception=None):
            pass


最后的最后，添加 :code:`load_mod` 函数，该函数将被 RQAlpha 调用以加载我们刚刚写好的 mod 。

.. code-block:: python3

    from .mod import TushareKDataMode


    def load_mod():
        return TushareKDataMode()


至此，我们已经完成了外部行情数据的接入，剩下要做的就是在 RQAlpha 启动时传入的配置信息中开启以上 mod。

该 mod 只是一个简单的 demo，仍存在一些问题，例如调用 tushare 接口速度较慢，频繁调用会消耗大量时间。如能将多次调用合并，或是将接口的调用改为异步，相信能够大幅提升回测速度。

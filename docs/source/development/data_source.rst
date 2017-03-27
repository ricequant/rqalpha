.. _development-data-source:

==================
扩展数据源
==================

RQAlpha 支持自定义扩展数据源。得益于 RQAlpha 的 mod 机制，我们可以很方便的替换或者扩展默认的数据接口。

RQAlpha 将提供给用户的数据 API 和回测所需的基础数据抽象成了若干个函数，这些函数被封于 :class:`~DataSource` 类中，并将在需要的时候被调用。简单的说，我们只需要在自己定义的 mod 中扩展或重写默认的 :class:`~DataSource` 类，就可以替换掉默认的数据源，接入自有数据。

:class:`~DataSource` 类的完整文档，请参阅 :ref:`development-basic-concept`。下面将用一个简单的例子，为大家介绍如何用五十行左右的代码将默认的行情数据替换为 `TuShare`_ 的行情数据。

.. _TuShare: http://tushare.org


五十行代码接入 tushare 行情数据
====================================

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

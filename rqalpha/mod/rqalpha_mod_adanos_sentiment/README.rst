===============================
adanos_sentiment Mod
===============================

该 Mod 为策略提供可选的 Adanos Market Sentiment API 查询能力，支持 Reddit、X、News 和 Polymarket 的美股市场情绪数据。

模块配置项
===============================

..  code-block:: python

    {
        "api_key": "",  # 也可以设置 ADANOS_API_KEY 环境变量
        "base_url": "https://api.adanos.org",
        "source": "reddit",
        "timeout": 10,
    }

使用方式
===============================

..  code-block:: python

    from rqalpha.api import *


    def handle_bar(context, bar_dict):
        sentiment = adanos_sentiment("TSLA.US", source="reddit", days=7)
        if sentiment["sentiment_score"] > 0:
            logger.info(sentiment)


    __config__ = {
        "mod": {
            "adanos_sentiment": {
                "enabled": True,
                "lib": "rqalpha.mod.rqalpha_mod_adanos_sentiment",
                "api_key": "your-api-key",
                "source": "reddit",
            }
        }
    }

API
===============================

``adanos_sentiment(order_book_id, source=None, days=7)``
    查询单个美股的市场情绪数据。``order_book_id`` 可以是 ``"TSLA"`` 或 ``"TSLA.US"``。

``adanos_sentiment_compare(order_book_ids, source=None, days=7)``
    查询多个美股的市场情绪对比数据。``order_book_ids`` 可以是逗号分隔字符串或可迭代对象。

支持的数据源: ``reddit``, ``x``, ``news``, ``polymarket``。

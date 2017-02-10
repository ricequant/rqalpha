.. _faq:

==================
FAQ
==================

1. 运行回测时，matplotlib 报错怎么办？RuntimeError: Python is not installed as a framework.

    解决方案：创建文件 ~/.matplotlib/matplotlibrc，并加入代码`backend: TkAgg`
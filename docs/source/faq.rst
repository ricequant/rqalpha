.. _faq:

==================
FAQ
==================

1.  运行回测时，matplotlib 报错怎么办？:code:`RuntimeError: Python is not installed as a framework`.

    解决方案：创建文件 :code:`~/.matplotlib/matplotlibrc`，并加入代码 :code:`backend: TkAgg`

2.  在Windows运行报 :code:`Error on import matplotlib.pyplot`

    请访问 `Error on import matplotlib.pyplot (on Anaconda3 for Windows 10 Home 64-bit PC) <http://stackoverflow.com/questions/34004063/error-on-import-matplotlib-pyplot-on-anaconda3-for-windows-10-home-64-bit-pc>`_ 解决。

3.  在Windows出现缺失 :code:`cl.exe`

    请访问 https://wiki.python.org/moin/WindowsCompilers 下载VC并且安装。

4.  Windows 安装时报 :code:`error: Microsoft Visual C++ 14.0 is required.`

    请访问 https://wiki.python.org/moin/WindowsCompilers 下载VC并且安装。

5.  出现安装 :code:`bcolz` 编译失败
    
    在 Windows 环境下编译 :code:`bcolz` 需要 :code:`Cython` 和 :code:`VC`，请参考 FAQ 3 & 4

    或者不进行编译安装，访问 http://www.lfd.uci.edu/~gohlke/pythonlibs/#bcolz 下载 :code:`bcolz` 直接进行安装。

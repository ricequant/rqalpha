=================================
RQAlpha Documentation Instruction
=================================


RQAlpha 使用 Sphinx 进行文档编写。


Requirements
------------

*   pandoc: http://pandoc.org/installing.html
*   Sphinx
*   watchdog
*   sphinx_rtd_theme
*   nbsphinx
*   jupyter_client
*   sphinx-autodoc-typehints

.. code-block:: bash

    pip install Sphinx watchdog sphinx_rtd_theme nbsphinx jupyter_client sphinx-autodoc-typehints

# pandoc 需要下载 http://pandoc.org/installing.html 且重启pycharm（修改了环境变量）

Usage
-----

*   `make html`: 编译文档并在 `{project}/docs/build/` 下生成HTML。
*   `make htmlview`: 本地查看文档。
*   `make clean`: 清空build目录下文件。
*   `make watch`: 使用该命令可以根据源文件的变化自动编译文档。

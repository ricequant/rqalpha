
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

.. code-block:: bash

    pip install Sphinx watchdog sphinx_rtd_theme nbsphinx jupyter_client

Usage
-----

*   `make html`: 编译文档并在 `{project}/docs/build/` 下生成HTML。
*   `make htmlview`: 本地查看文档。
*   `make clean`: 清空build目录下文件。
*   `make watch`: 使用该命令可以根据源文件的变化自动编译文档。

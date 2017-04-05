.. _intro-optimizing-parameters:

==================
批量运行回测参数调优
==================

通过命令行传递参数
====================================

.. code-block:: python

    import os
    import json
    import concurrent.futures
    import multiprocessing


    tasks = []
    for short_period in range(3, 10, 2):
	for long_period in range(30, 90, 5):
	    extra_vars = {
		"SHORTPERIOD": short_period,
		"LONGPERIOD": long_period,
	    }
	    vars_params = json.dumps(extra_vars).encode("utf-8").decode("utf-8")

	    cmd = ("rqalpha run -fq 1d -f rqalpha/examples/golden_cross.py --start-date 2015-01-01 --end-date 2016-01-01 "
		   "-o results/out-{short_period}-{long_period}.pkl -sc 100000 --progress -bm 000001.XSHE --extra-vars '{params}' ").format(
		       short_period=short_period,
		       long_period=long_period,
		       params=vars_params)

	    tasks.append(cmd)


    def run_bt(cmd):
	print(cmd)
	os.system(cmd)


    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
	for task in tasks:
	    executor.submit(run_bt, task)


Python调用传递参数
====================================

TBD


==================
分析批量回测结果
==================

.. _intro-optimizing-parameters:

==================
通过 RQAlpha 进行参数调优
==================


通过函数调用传递参数
====================================

.. code-block:: python

    import concurrent.futures
    import multiprocessing
    from rqalpha import run


    tasks = []
    for short_period in range(3, 10, 2):
	for long_period in range(30, 90, 5):
	    config = {
		"extra": {
		    "context_vars": {
			"SHORTPERIOD": short_period,
			"LONGPERIOD": long_period,
		    },
		    "log_level": "error",
		},
		"base": {
		    "securities": "stock",
		    "matching_type": "current_bar",
		    "start_date": "2015-01-01",
		    "end_date": "2016-01-01",
		    "stock_starting_cash": 100000,
		    "benchmark": "000001.XSHE",
		    "frequency": "1d",
		    "strategy_file": "rqalpha/examples/golden_cross.py",
		},
		"mod": {
		    "sys_progress": {
			"enabled": True,
			"show": True,
		    },
		    "sys_analyser": {
			"enabled": True,
			"output_file": "results/out-{short_period}-{long_period}.pkl".format(
			    short_period=short_period,
			    long_period=long_period,
			)
		    },
		},
	    }

	    tasks.append(config)


    def run_bt(config):
	run(config)


    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
	for task in tasks:
	    executor.submit(run_bt, task)



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



分析批量回测结果
====================================

.. code-block:: python

    import glob
    import pandas as pd


    results = []

    for name in glob.glob("results/*.pkl"):
	result_dict = pd.read_pickle(name)
	summary = result_dict["summary"]
	results.append({
	    "name": name,
	    "annualized_returns": summary["annualized_returns"],
	    "sharpe": summary["sharpe"],
	    "max_drawdown": summary["max_drawdown"],
	})

    results_df = pd.DataFrame(results)

    print("-" * 50)
    print("Sort by sharpe")
    print(results_df.sort_values("sharpe", ascending=False)[:10])

    print("-" * 50)
    print("Sort by annualized_returns")
    print(results_df.sort_values("annualized_returns", ascending=False)[:10])

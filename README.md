# rqalpha

![Architecture](https://raw.githubusercontent.com/ricequant/rqalpha/master/docs/QQ20160713-1.jpeg)

## install
You can install from PyPI:

```
# install
pip install rqalpha

# upgrade
pip install -U rqalpha
```

## Dependencies

### TA-Lib Installation

You can install from PyPI:

```
$ pip install TA-Lib
```

To use [TA-Lib](https://github.com/mrjbq7/ta-lib) for python, you need to have the
[TA-Lib](http://ta-lib.org/hdr_dw.html) already installed:

##### Mac OS X

```
$ brew install ta-lib
```

##### Windows

Download [ta-lib-0.4.0-msvc.zip](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip)
and unzip to ``C:\ta-lib``

##### Linux

Download [ta-lib-0.4.0-src.tar.gz](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz) and:
```
$ untar and cd
$ ./configure --prefix=/usr
$ make
$ sudo make install
```

> If you build ``TA-Lib`` using ``make -jX`` it will fail but that's OK!
> Simply rerun ``make -jX`` followed by ``[sudo] make install``.


## Usage

```
Usage: rqalpha [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose
  --help         Show this message and exit.

Commands:
  generate_examples  generate example strategies to target folder
  run                run strategy from file
  update_bundle      update data bundle, download if not found
```

```
Usage: rqalpha run [OPTIONS]

  run strategy from file

Options:
  -f, --strategy-file PATH        [required]
  -s, --start-date DATE           [required]
  -e, --end-date DATE             [required]
  -o, --output-file PATH
  --draw-result / --no-draw-result
  --help                          Show this message and exit.
```

### Download data bundle
```
rqalpha update_bundle
```

### examples
```
rqalpha generate_examples -d ./
```

### run backtest
```
rqalpha run -f examples/simple_macd.py -s 2014-01-04 -e 2015-01-05 -o /tmp/a.pkl
```


## Develop
```
pyvenv venv
source venv/bin/activate
pip install -e .
```

## run unittest
```
py.test
```

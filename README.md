# Ricequant Opensource Algo Engine

## install
```
pip install --trusted-host mirrors.aliyun.com --index-url http://mirrors.aliyun.com/pypi/simple/ --extra-index-url https://rquser:ricequant99@py.ricequant.com/simple/ -U rqbacktest
```

## Usage

```
Usage: rqbacktest [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose
  --help         Show this message and exit.

Commands:
  generate_examples  generate example strategies to target folder
  run                run strategy from file
  update_bundle      update data bundle, download if not found
```

```
Usage: rqbacktest run [OPTIONS]

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
rqbacktest update_bundle
```

### examples
```
rqbacktest generate_examples -d ./
```

### run backtest
```
rqbacktest run -f examples/simple_macd.py -s 2014-01-04 -e 2015-01-05 -o /tmp/a.pkl
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

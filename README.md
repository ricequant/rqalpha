# rqalpha

![Architecture](https://raw.githubusercontent.com/ricequant/rqalpha/master/docs/QQ20160713-1.jpeg)

## install
```
pip install -U rqalpha
```

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

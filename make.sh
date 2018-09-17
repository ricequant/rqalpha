#!/bin/bash

rm -rf *.egg-info
rm -rf dist
find . -name "__pycache__" | xargs rm -rf
find . -name "*.pyc" | xargs rm -rf

python setup.py "$@"

#!/usr/bin/env sh

rm -rf ./dist
python3 setup.py sdist bdist_wheel
twine check dist/*

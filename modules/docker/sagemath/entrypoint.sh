#!/bin/bash

echo "entrypoint!!"

exec sage -n jupyter --no-browser --ip='0.0.0.0' --port=8888 "$@"

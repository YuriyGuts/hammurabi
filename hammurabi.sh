#!/usr/bin/env bash

export PYTHONPATH="$PYTHONPATH:$PWD"
echo $PYTHONPATH

python ./hammurabi/grader/grader.py

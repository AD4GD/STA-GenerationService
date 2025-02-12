#!/bin/bash

if [[ "$DEBUG" == "True" ]]; then
    exec uvicorn src.main:app --reload --host 0.0.0.0 --port "$PORT"
else
    exec uvicorn src.main:app --host 0.0.0.0 --port "$PORT"
fi

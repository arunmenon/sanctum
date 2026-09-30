#!/bin/sh
set -eu
export LAYA_DEVICE=cpu
export LAYA_HOST=127.0.0.1
export LAYA_PORT=8888
export LAYA_MODELS=english
exec /Users/arunmenon/projects/sanctum/.laya-venv/bin/laya-serve

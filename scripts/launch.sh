#!/bin/sh
# Resolve the checkout independently of the caller's working directory.
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd) || exit 1
cd "$PROJECT_DIR" || exit 1
export PYTHONDONTWRITEBYTECODE=1
exec /usr/bin/python3 -m lucy_diagnose "$@"

#!/bin/sh
set -e

if [ ! -f app/data/clientes.csv ]; then
    python -m db.seed_data
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000

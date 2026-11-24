#!/bin/sh
# Writes ingestion/s3.json (git-ignored) for the landing store from .env: one identity, the landing keys.
set -eu
cd "$(dirname "$0")"
. ../.env
cat > s3.json <<JSON
{"identities": [{"name": "eventzilla", "credentials": [{"accessKey": "$LANDING_ACCESS_KEY", "secretKey": "$LANDING_SECRET_KEY"}],
  "actions": ["Admin", "Read", "List", "Tagging", "Write"]}]}
JSON
echo "wrote $(pwd)/s3.json"

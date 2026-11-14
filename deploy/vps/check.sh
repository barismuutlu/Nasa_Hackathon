#!/usr/bin/env bash
# Health check on the VPS. Exit code 0 = app answers locally.
set -u
BASE=${BASE:-http://127.0.0.1:8501}
systemctl is-active --quiet firecal && echo "service: active" || { echo "service: NOT active → journalctl -u firecal -n 50"; exit 1; }
code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/_stcore/health" || true)
[ "$code" = "200" ] && echo "health:  200 ($BASE/_stcore/health)" || { echo "health:  $code (expected 200)"; exit 1; }
systemctl show firecal -p MemoryCurrent --value | awk '{printf "memory:  %.0f MB (limit 1100 MB)\n", $1/1048576}'
free -h | awk '/^Mem|^Swap/ {print "host:    " $1 " total " $2 ", used " $3}'

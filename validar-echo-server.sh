#!/bin/sh
set -eu

MSG="echo-test-$(date +%s%N)"

RESPONSE=$(docker run --rm --network=container:server alpine sh -c "
  apk add --no-cache netcat-openbsd >/dev/null 2>&1 &&
  echo '$MSG' | nc -w 2 localhost 12345
" 2>/dev/null || true)

if [ -z "$RESPONSE" ]; then
  echo "action: test_echo_server | result: fail"
  exit 0
fi

if echo "$RESPONSE" | grep -q "$MSG"; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi

exit 0
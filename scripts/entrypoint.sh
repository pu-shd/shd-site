#!/bin/sh
# Container entrypoint: `test` runs the suite, `serve` previews the site,
# anything else is executed verbatim.
set -eu

case "${1:-test}" in
  test)
    shift 2>/dev/null || true
    exec pytest "$@"
    ;;
  serve)
    echo "shd-site preview on http://0.0.0.0:8080"
    exec python -m http.server 8080 --bind 0.0.0.0
    ;;
  *)
    exec "$@"
    ;;
esac

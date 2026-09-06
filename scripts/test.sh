#!/usr/bin/env zsh
# Run the site checks. Uses a local virtualenv by default; pass --docker to run
# them in the container instead, and --network to also resolve outbound links.
set -euo pipefail

here=${0:A:h}
root=${here:h}
cd "$root"

use_docker=0
pytest_args=()

for arg in "$@"; do
  case "$arg" in
    --docker)  use_docker=1 ;;
    --network) pytest_args+=(-m network) ;;
    *)         pytest_args+=("$arg") ;;
  esac
done

if (( use_docker )); then
  docker-compose build test
  exec docker-compose run --rm test ${pytest_args[@]:-}
fi

venv="$root/.venv"
if [[ ! -d "$venv" ]]; then
  print "Creating $venv"
  python3 -m venv "$venv"
  "$venv/bin/pip" install --quiet --upgrade pip
  "$venv/bin/pip" install --quiet -r "$root/tests/requirements.txt"
fi

exec "$venv/bin/pytest" ${pytest_args[@]:-}

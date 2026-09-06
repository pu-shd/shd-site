#!/usr/bin/env zsh
# Preview the site locally at http://localhost:8080.
set -euo pipefail
here=${0:A:h}
cd "${here:h}"
print "shd-site preview on http://localhost:8080  (ctrl-c to stop)"
exec python3 -m http.server 8080

#!/usr/bin/env zsh
# Turn on GitHub Pages for this repository, building from the Actions workflow.
# Idempotent: safe to re-run.
set -euo pipefail

repo=${1:-pu-shd/shd-site}

print "Enabling GitHub Pages for $repo (source: GitHub Actions)"

if gh api "repos/$repo/pages" >/dev/null 2>&1; then
  gh api --method PUT "repos/$repo/pages" \
    -f "build_type=workflow" >/dev/null
  print "  updated existing Pages configuration"
else
  gh api --method POST "repos/$repo/pages" \
    -f "build_type=workflow" >/dev/null
  print "  created Pages configuration"
fi

gh api "repos/$repo/pages" --jq '"  url:     \(.html_url)\n  status:  \(.status)\n  source:  \(.build_type)"'

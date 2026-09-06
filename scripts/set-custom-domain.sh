#!/usr/bin/env zsh
# Attach shd.princeton.edu to this repository's GitHub Pages site.
#
# Run this ONLY after the CNAME record exists in DNS:
#
#     shd.princeton.edu.  CNAME  pu-shd.github.io.
#
# Setting the custom domain before DNS resolves makes the site unreachable
# until it does, so the check below refuses to proceed in that case.
set -euo pipefail

repo=${1:-pu-shd/shd-site}
domain=${2:-shd.princeton.edu}
target="pu-shd.github.io"

print "Checking DNS for $domain ..."
resolved=$(dig +short CNAME "$domain" 2>/dev/null | sed 's/\.$//' || true)

if [[ "$resolved" != "$target" ]]; then
  print -u2 "  $domain does not yet point at $target (got: ${resolved:-nothing})."
  print -u2 "  Request the DNS record first, then re-run this script."
  exit 1
fi
print "  ok — resolves to $target"

gh api --method PUT "repos/$repo/pages" -f "cname=$domain" >/dev/null
print "Custom domain set. Waiting for the certificate ..."

gh api --method POST "repos/$repo/pages/https_certificate" >/dev/null 2>&1 || true
gh api --method PUT "repos/$repo/pages" -F "https_enforced=true" >/dev/null 2>&1 \
  || print "  HTTPS enforcement will switch on once the certificate is issued."

print "$domain" > "${0:A:h:h}/CNAME"
print "Wrote CNAME. Commit it so the domain survives future deployments."
gh api "repos/$repo/pages" --jq '"  url: \(.html_url)  status: \(.status)"'

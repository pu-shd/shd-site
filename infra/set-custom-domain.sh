#!/usr/bin/env zsh
# Attach shd.princeton.edu to the Static Web App.
#
# Run this only after OIT has pointed the record at the app:
#
#     shd.princeton.edu.  CNAME  <app>.azurestaticapps.net.
#
# Static Web Apps validates a subdomain by CNAME delegation, so no TXT record is
# involved. The check below refuses to proceed until DNS actually resolves,
# because validation fails otherwise and the domain lands in a stuck state.
set -euo pipefail

here=${0:A:h}
source "$here/config.sh"

domain=${1:-shd.princeton.edu}

az account set --subscription "$SHD_SUBSCRIPTION"

expected=$(az staticwebapp show -n "$SHD_SWA" -g "$SHD_RG" --query defaultHostname -o tsv)
print "Static Web App hostname: $expected"

print "Checking DNS for $domain ..."
resolved=$(dig +short CNAME "$domain" 2>/dev/null | sed 's/\.$//' || true)

if [[ "$resolved" != "$expected" ]]; then
  print -u2 "  $domain does not point at $expected (got: ${resolved:-nothing})."
  print -u2 "  Request this from OIT networking, then re-run:"
  print -u2 "      $domain.  CNAME  $expected."
  exit 1
fi
print "  ok — resolves to $expected"

if az staticwebapp hostname show -n "$SHD_SWA" -g "$SHD_RG" --hostname "$domain" >/dev/null 2>&1; then
  print "$domain is already attached."
else
  print "Attaching $domain ..."
  az staticwebapp hostname set -n "$SHD_SWA" -g "$SHD_RG" \
    --hostname "$domain" --validation-method cname-delegation --no-wait
  print "Requested. Certificate issuance takes a few minutes."
fi

az staticwebapp hostname list -n "$SHD_SWA" -g "$SHD_RG" \
  --query "[].{hostname:name, status:status}" -o table

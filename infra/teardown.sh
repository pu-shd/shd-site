#!/usr/bin/env zsh
# Remove the SHD Azure footprint. Deletes the whole resource group, so it takes
# the Static Web App, the managed identity and the role assignment with it.
#
#   ./infra/teardown.sh            # prompts
#   ./infra/teardown.sh --yes      # no prompt
set -euo pipefail

here=${0:A:h}
source "$here/config.sh"

az account set --subscription "$SHD_SUBSCRIPTION"

if ! az group show -n "$SHD_RG" >/dev/null 2>&1; then
  print "Resource group $SHD_RG does not exist; nothing to do."
  exit 0
fi

print "About to delete resource group $SHD_RG from $(az account show --query name -o tsv):"
az resource list -g "$SHD_RG" --query "[].{name:name, type:type}" -o table

if [[ "${1:-}" != "--yes" ]]; then
  print -n "\nType the resource group name to confirm: "
  read -r reply
  [[ "$reply" == "$SHD_RG" ]] || { print -u2 "Aborted."; exit 1 }
fi

az group delete -n "$SHD_RG" --yes --no-wait
print "Deletion started. Note: shd.princeton.edu will stop resolving to anything"
print "useful until OIT repoints it."

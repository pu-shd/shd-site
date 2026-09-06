#!/usr/bin/env zsh
# Stand up the SHD Azure footprint: resource group, Static Web App, and the
# federated identity GitHub Actions deploys with. Idempotent — safe to re-run.
#
#   ./infra/deploy.sh
#
# Requires: az, authenticated against the pu-shd-azure subscription. If it is
# not listed, refresh the token cache first — `az account list --refresh`.
set -euo pipefail

here=${0:A:h}
source "$here/config.sh"

# Pin the CLI to the SHD subscription for the rest of this script. Setting the
# context once is more reliable than passing --subscription per command, which
# not every az command accepts in the same position.
az account set --subscription "$SHD_SUBSCRIPTION"

print "Subscription: $(az account show --query name -o tsv)"

# --- providers ---------------------------------------------------------------
for ns in Microsoft.Web Microsoft.ManagedIdentity; do
  state=$(az provider show --namespace "$ns" --query registrationState -o tsv 2>/dev/null || echo NotRegistered)
  if [[ "$state" != "Registered" ]]; then
    print "Registering $ns (this can take a minute) ..."
    az provider register --namespace "$ns" --wait
  fi
  print "  $ns: $(az provider show --namespace "$ns" --query registrationState -o tsv)"
done

# --- resource group ----------------------------------------------------------
if ! az group show -n "$SHD_RG" >/dev/null 2>&1; then
  az group create -n "$SHD_RG" -l "$SHD_LOCATION" \
    --tags project=shd managed-by=infra/deploy.sh >/dev/null
  print "Created resource group $SHD_RG in $SHD_LOCATION"
else
  print "Resource group $SHD_RG exists"
fi

# --- static web app ----------------------------------------------------------
# Created without --source so Azure does not write a token-based workflow into
# the repository; deployment is driven by .github/workflows/azure-swa.yml.
if ! az staticwebapp show -n "$SHD_SWA" -g "$SHD_RG" >/dev/null 2>&1; then
  az staticwebapp create -n "$SHD_SWA" -g "$SHD_RG" -l "$SHD_LOCATION" \
    --sku Free --tags project=shd >/dev/null
  print "Created Static Web App $SHD_SWA"
else
  print "Static Web App $SHD_SWA exists"
fi

swa_host=$(az staticwebapp show -n "$SHD_SWA" -g "$SHD_RG" --query defaultHostname -o tsv)
swa_id=$(az staticwebapp show -n "$SHD_SWA" -g "$SHD_RG" --query id -o tsv)

# --- deployment identity -----------------------------------------------------
if ! az identity show -n "$SHD_IDENTITY" -g "$SHD_RG" >/dev/null 2>&1; then
  az identity create -n "$SHD_IDENTITY" -g "$SHD_RG" -l "$SHD_LOCATION" \
    --tags project=shd >/dev/null
  print "Created managed identity $SHD_IDENTITY"
else
  print "Managed identity $SHD_IDENTITY exists"
fi

client_id=$(az identity show -n "$SHD_IDENTITY" -g "$SHD_RG" --query clientId -o tsv)
principal_id=$(az identity show -n "$SHD_IDENTITY" -g "$SHD_RG" --query principalId -o tsv)
tenant_id=$(az account show --query tenantId -o tsv)

# Federated credential, scoped to one repo and one GitHub environment so no
# other workflow — or branch — can assume this identity.
subject="repo:${SHD_GH_ORG}/${SHD_GH_REPO}:environment:${SHD_GH_ENVIRONMENT}"
if ! az identity federated-credential show \
      --identity-name "$SHD_IDENTITY" -g "$SHD_RG" -n gh-actions-production >/dev/null 2>&1; then
  az identity federated-credential create \
    --identity-name "$SHD_IDENTITY" -g "$SHD_RG" -n gh-actions-production \
    --issuer "https://token.actions.githubusercontent.com" \
    --subject "$subject" \
    --audiences "api://AzureADTokenExchange" >/dev/null
  print "Created federated credential for $subject"
else
  print "Federated credential exists for $subject"
fi

# Least privilege: Contributor on the Static Web App resource only — not the
# resource group, not the subscription. This is what permits listing the
# deployment token at deploy time.
if ! az role assignment list --assignee "$principal_id" --scope "$swa_id" \
      --query "[?roleDefinitionName=='Contributor']" -o tsv | grep -q .; then
  az role assignment create --assignee-object-id "$principal_id" \
    --assignee-principal-type ServicePrincipal \
    --role Contributor --scope "$swa_id" >/dev/null
  print "Granted Contributor on the Static Web App"
else
  print "Role assignment already in place"
fi

# --- what to do with this ----------------------------------------------------
cat <<SUMMARY

────────────────────────────────────────────────────────────────────────────
Static Web App hostname   $swa_host
────────────────────────────────────────────────────────────────────────────

1. Set these as GitHub repository *variables* (not secrets — none is sensitive):

     gh variable set AZURE_CLIENT_ID       --repo $SHD_GH_ORG/$SHD_GH_REPO --body $client_id
     gh variable set AZURE_TENANT_ID       --repo $SHD_GH_ORG/$SHD_GH_REPO --body $tenant_id
     gh variable set AZURE_SUBSCRIPTION_ID --repo $SHD_GH_ORG/$SHD_GH_REPO --body $SHD_SUBSCRIPTION
     gh variable set AZURE_SWA_NAME        --repo $SHD_GH_ORG/$SHD_GH_REPO --body $SHD_SWA
     gh variable set AZURE_SWA_RG          --repo $SHD_GH_ORG/$SHD_GH_REPO --body $SHD_RG

2. Create the '$SHD_GH_ENVIRONMENT' environment in the repository — the
   federated credential only trusts that environment.

3. Ask OIT networking for exactly one record change:

     shd.princeton.edu.  CNAME  $swa_host.

   No TXT record: Static Web Apps validates a subdomain by CNAME delegation.

4. Once it resolves, attach the custom domain:

     ./infra/set-custom-domain.sh

SUMMARY

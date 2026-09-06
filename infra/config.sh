#!/usr/bin/env zsh
# Shared configuration for the SHD Azure footprint.
# Sourced by deploy.sh and teardown.sh.

export SHD_SUBSCRIPTION="5099c462-a691-4b67-8c6b-a327a0ba4c85"   # pu-shd-azure
export SHD_LOCATION="eastus2"
export SHD_RG="rg-shd-prod"

# Static Web App serving shd.princeton.edu. Free tier: 100 GB/mo egress,
# 2 custom domains, managed TLS, managed Functions if the site ever needs an API.
export SHD_SWA="swa-shd-site"

# Deployment identity. GitHub Actions authenticates as this via OIDC; no
# credential is ever stored in the repository.
export SHD_IDENTITY="id-shd-site-deploy"
export SHD_GH_ORG="pu-shd"
export SHD_GH_REPO="shd-site"
export SHD_GH_ENVIRONMENT="production"

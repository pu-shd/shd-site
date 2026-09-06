# shd-site

![SHD — at Sherrerd Hall](assets/img/shd-lockup.png)

The landing page for **SHD** — shared ground for groups at Sherrerd Hall,
Princeton University. Sherrerd Hall bridges disciplines; SHD scaffolds
the work. It is a single static page whose job is to explain what SHD is and
point at two places: the [`pu-shd`](https://github.com/pu-shd) GitHub
organization and the
[Facilities record for the building](https://facilities.princeton.edu/projects/sherrerd-hall-2008).

Published with GitHub Pages. Intended to live at **https://shd.princeton.edu**.

> **Currently in holding.** `/` serves a *Coming soon* placeholder. The full
> landing page is staged at `preview.html` and is deliberately **not**
> published — see [Swapping the page in](#swapping-the-page-in).

## Why this exists

Sherrerd Hall was built to connect academics from different fields and capture
the potential of their interactions in the open. SHD captures the systems and
operations that emerge cross-discipline.

From classrooms to conferences, seminars to sites, SHD captures the tooling to
do all of it. Shared systems, hosted in the open, are maintained once and
available to everyone. SHD keeps those systems findable — by the colleague
down the corridor, and by the cohort that comes next.

SHD is *at* Sherrerd Hall. It supports the groups in the building; it does not
speak for them.

## Layout

```
index.html                  the holding page, served at /
preview.html                the full landing page, staged for the swap
assets/css/site.css         one stylesheet, no build step
assets/img/                 web derivatives, committed
_source/                    full-resolution originals — untracked, ~130 MB
scripts/                    build, preview and test helpers
infra/                      Azure footprint as code, with teardown
tests/                      pytest suite (structure, assets, a11y, links, deploy)
Dockerfile                  test and preview container
.github/workflows/          checks on every push; deploy on main
```

There is no site generator and no JavaScript. Both documents share the single
stylesheet, so the holding page inherits the palette, the University signature
and the policy subfooter and adds nothing else.

### Swapping the page in

`scripts/build-site.sh` copies only `index.html`, so `preview.html` never
reaches the published site. To go live:

```sh
git mv index.html holding.html      # keep it, in case you want it back
git mv preview.html index.html
```

Then delete the `<meta name="robots" content="noindex">` line from the new
`index.html` — it exists only to keep "Coming soon" out of search results —
and run `./scripts/test.sh` before pushing. The test suite checks both
documents, so it will tell you if the swap left anything behind.

## Design

The palette and structure come from the building: a black granite base, a
curtain wall of tinted and fritted glass on a mullion grid, one white panel
projecting over the entrance, and cherry wood at the door. The hero is that
projecting panel; the section rules are the mullions; the accent is the door.

The masthead carries the standard University signature — shield, dividing
rule, unit name — with the name set in the site's own typography, reversed out
of the granite. The shield (`assets/img/pu-shield-white.svg`) and the stacked
lockup in the subfooter (`assets/img/pu-logo-stacked-white.svg`) are the
official reversed marks from the Princeton Site Builder theme, used unmodified.

`assets/img/shd-lockup.png` is a rendering of the same signature for use where
HTML is not available — the GitHub organization profile, slides, and so on.

## Working on it

```sh
./scripts/serve.sh            # preview at http://localhost:8080
./scripts/test.sh             # run the offline checks
./scripts/test.sh --network   # also resolve every outbound link
./scripts/test.sh --docker    # run the checks in the container instead
```

With Docker directly:

```sh
docker-compose run --rm test          # offline checks
docker-compose run --rm test-network  # outbound links too
docker-compose up serve               # preview at http://localhost:8080
```

### Rebuilding the imagery

`assets/img/` is committed, so this is only needed when the photograph set
changes. It expects the originals in `_source/` and needs ImageMagick and
`cwebp` (`brew install imagemagick webp`):

```sh
./scripts/build-images.sh
```

### Note on the Princeton bot wall

princeton.edu is behind Cloudflare bot detection. Any automated request to a
princeton.edu URL — including the `network`-marked link check — needs the
header `x-wdsoit-bot-bypass`. Only the header's presence matters; the value is
ignored.

## DNS and hosting

`shd.princeton.edu` is served by an **Azure Static Web App** in the
`pu-shd-azure` subscription. GitHub remains the source of truth and CI; Azure
serves production; GitHub Pages is demoted to a free preview at
`pu-shd.github.io/shd-site`.

The design constraint is that **every DNS record is a per-request ticket to
Princeton OIT networking**, so the architecture is chosen to need as few tickets
as possible, and never a repeat change to the same name.

| | |
|---|---|
| Subscription | `pu-shd-azure` — `5099c462-a691-4b67-8c6b-a327a0ba4c85` |
| Resource group | `rg-shd-prod`, `eastus2` |
| Static Web App | `swa-shd-site`, Free tier |
| Cost | **~$0** — Free tier, no VM, no Front Door |

Static Web Apps was chosen over Pages for the apex specifically because its
managed Functions serve API routes under the *same* `azurestaticapps.net` CNAME
target. If `shd.princeton.edu` ever needs something dynamic, that costs no
second DNS change.

Region only determines where builds and Functions execute — content is served
from a global edge — so there is no reason to match any other resource's region.

### Standing up the infrastructure

Scripted, idempotent, with a teardown:

```sh
./infra/deploy.sh                  # resource group, SWA, federated identity
./infra/set-custom-domain.sh       # after DNS resolves
./infra/teardown.sh                # deletes the resource group
```

If `pu-shd-azure` is not listed by `az account list`, the token cache is stale —
`az account list --refresh` fixes it. It is not a tenant or RBAC problem.

### Attaching shd.princeton.edu

One record, and **no TXT** — Static Web Apps validates a subdomain by CNAME
delegation; TXT is only required by the apex-domain flow, and
`shd.princeton.edu` is a subdomain of `princeton.edu`:

```
shd.princeton.edu.  CNAME  <app>.azurestaticapps.net.
```

`./infra/deploy.sh` prints the exact hostname. Then run
`./infra/set-custom-domain.sh`, which refuses to proceed until the record
actually resolves — validation fails otherwise and leaves the domain stuck.

### Adding a new *.shd.princeton.edu name

1. Stand up the backend first and note its hostname — another SWA (Free) for a
   flat site, Azure Container Apps or GCP Cloud Run for a service. Prefer
   scale-to-zero over always-on.
2. **Batch the request.** Ask OIT for several names at once; a ticket per
   hostname is the tax this architecture is trying to minimise.

   ```
   displays.shd.princeton.edu.  CNAME  <target>
   events.shd.princeton.edu.    CNAME  <target>
   ```
3. Attach the custom domain on the backend and wait for its managed
   certificate.

Two things not to do:

- **Never point a wildcard at `pu-shd.github.io`.** GitHub's domain
  verification covers only *immediate* subdomains, while DNS wildcard synthesis
  answers deeper names — GitHub warns this risks takeover "even if you verify
  the domain." A wildcard onto your own single-tenant endpoint is fine.
- **Do not buy Azure Front Door** (~$35/month before traffic) until something
  genuinely needs WAF or global anycast.

### The longer game: zone delegation

Per-name tickets are the opening move because that is what OIT approves
quickly. The end state is a delegated zone — one request, after which every
record is self-service for ~$0.55/month:

```
; remove — NS and CNAME cannot coexist at the same name
shd.princeton.edu.  CNAME  <app>.azurestaticapps.net.
; add — the nameservers assigned to the Azure DNS zone
shd.princeton.edu.  NS  ns1-NN.azure-dns.com.
...
```

The ask is **only the NS records**. A zone apex cannot be a CNAME, but that is
solved inside your own zone rather than requested: Azure DNS *alias* records can
sit at an apex, and SWA's "Custom Domain on Azure DNS" option provisions the
apex records automatically. Allow up to 72 hours for apex propagation.

## Deployment

`main` deploys itself, twice over:

- `.github/workflows/azure-swa.yml` — **production.** Runs the suite, assembles
  `_site/`, then deploys to the Static Web App.
- `.github/workflows/pages.yml` — preview on `pu-shd.github.io/shd-site`.
  Retire it once SWA's per-PR staging environments prove out.
- `.github/workflows/ci.yml` — the same checks on pull requests, plus a weekly
  link check.

Pages builds from the workflow rather than a branch:

```sh
./scripts/enable-pages.sh          # idempotent
```

There is deliberately **no `CNAME` file**. The custom domain belongs to the
Static Web App, and a `CNAME` here would make Pages claim the same hostname.

### Secretless deploy

The Azure deploy stores no credential. A user-assigned managed identity carries
a federated credential whose subject is
`repo:pu-shd/shd-site:environment:production`, so only a deploy through that
GitHub environment can assume it, and its RBAC is scoped to the Static Web App
resource alone — not the resource group, not the subscription.

`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_SWA_NAME`
and `AZURE_SWA_RG` are repository **variables**, not secrets; none is sensitive.
The one real credential — the SWA deployment token — is fetched just-in-time
under the federated identity, masked, and never persisted.

`tests/test_workflows.py` holds all of that still: it fails if a
`secrets.AZURE_*` reference appears, if the identity stops coming from
variables, if the token stops being fetched at run time or masked, if the
production gate is removed, or if any action loses its SHA pin.

## Credits

Photography: Princeton University Office of Communications. Sherrerd Hall (2008)
was designed by Frederick Fisher and Partners; the stairwell sculpture is by
Jim Isermann.

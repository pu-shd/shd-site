# shd-site

![SHD — at Sherrerd Hall](assets/img/shd-lockup.png)

The landing page for **SHD** — shared ground for groups at Sherrerd Hall,
Princeton University. Sherrerd Hall bridges disciplines; SHD is digital
scaffold. It is a single static page whose job is to explain what SHD is and
point at two places: the [`pu-shd`](https://github.com/pu-shd) GitHub
organization and the
[Facilities record for the building](https://facilities.princeton.edu/projects/sherrerd-hall-2008).

Published with GitHub Pages. Intended to live at **https://shd.princeton.edu**.

## Why this exists

Sherrerd Hall was built to connect academics from different fields and capture
the potential of their interactions in the open. SHD captures the systems and
operations that emerge cross-discipline.

From classrooms to conferences, seminars to sites, SHD captures the tooling to
do all of it. Shared systems, hosted in the open, are maintained once and
available to everyone — somewhere colleagues, be they down the corridor or
across cohorts, can find them again.

SHD is *at* Sherrerd Hall. It supports the groups in the building; it does not
speak for them.

## Layout

```
index.html                  the page
assets/css/site.css         one stylesheet, no build step
assets/img/                 web derivatives, committed
_source/                    full-resolution originals — untracked, ~130 MB
scripts/                    build, preview, test, and deploy helpers
tests/                      pytest suite (structure, assets, a11y, links, deploy)
Dockerfile                  test and preview container
.github/workflows/          checks on every push; deploy on main
```

There is no site generator and no JavaScript. Editing the page means editing
`index.html`.

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

## Deployment

`main` deploys itself. `.github/workflows/pages.yml` runs the test suite,
assembles a clean `_site/` (page, assets, `robots.txt`, `sitemap.xml`,
`.nojekyll`, and `CNAME` if present) and publishes it. `.github/workflows/ci.yml`
runs the same checks on pull requests, plus a weekly link check.

Pages is configured to build from the workflow rather than from a branch:

```sh
./scripts/enable-pages.sh          # idempotent
```

### Attaching shd.princeton.edu

The custom domain is **not** set yet, because setting it before DNS exists takes
the site offline until the record appears. Once OIT has created

```
shd.princeton.edu.  CNAME  pu-shd.github.io.
```

run:

```sh
./scripts/set-custom-domain.sh
```

It refuses to proceed unless the record already resolves, then sets the domain,
requests the certificate, enables HTTPS enforcement, and writes the `CNAME` file
for you to commit.

## Credits

Photography: Princeton University Office of Communications. Sherrerd Hall (2008)
was designed by Frederick Fisher and Partners; the stairwell sculpture is by
Jim Isermann.

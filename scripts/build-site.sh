#!/usr/bin/env zsh
# Assemble the publishable site into _site/. Only the files a visitor needs are
# copied; tests, scripts, Dockerfiles and the photo originals stay behind.
set -euo pipefail

here=${0:A:h}
root=${here:h}
out="${1:-$root/_site}"

rm -rf "$out"
mkdir -p "$out"

# No CNAME: the custom domain lives on the Azure Static Web App, and a CNAME
# file here would make GitHub Pages try to claim the same name.
for item in index.html assets robots.txt sitemap.xml .nojekyll; do
  [[ -e "$root/$item" ]] && cp -R "$root/$item" "$out/"
done

print "Built $out"
du -sh "$out"
find "$out" -type f | sed "s|$out/||" | sort | sed 's/^/  /'

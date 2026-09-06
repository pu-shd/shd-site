#!/usr/bin/env zsh
# Build web-optimized site imagery from the originals in _source/.
# Originals are not committed; run this only when the source set changes.
set -euo pipefail

here=${0:A:h}
root=${here:h}
src="$root/_source"
out="$root/assets/img"

if [[ ! -d "$src" ]]; then
  print -u2 "build-images: no _source/ directory; nothing to do."
  exit 0
fi

mkdir -p "$out"

# name|source file|widths|extra tone adjustment
derivatives=(
  "hero|20181221_campuslife_BO_204.jpg|1800,1200|"
  "screens|20080917_ORFE_13.jpg|1100,640|-brightness-contrast 8x12 -modulate 100,108,100"
  "lantern|20080917_ORFE_54.jpg|1100,640|"
  "townsquare|20181221_campuslife_BO_245.jpg|1100,640|"
  "reflection|20080917_ORFE_40.jpg|1100,640|"
  "terrace|20181221_campuslife_BO_240.jpg|1100,640|"
)

for spec in "${derivatives[@]}"; do
  IFS='|' read -r name file widths tone <<< "$spec"
  in="$src/$file"
  [[ -f "$in" ]] || { print -u2 "build-images: missing $file, skipping $name"; continue }
  # The hero is the largest download on the page; trade a little fidelity for it.
  sharpen="-unsharp 0x0.6+0.5+0.02"
  [[ "$name" == "hero" ]] && sharpen=""
  if [[ "$name" == "hero" ]]; then jpeg_quality=62; webp_quality=54; else jpeg_quality=78; webp_quality=76; fi

  for w in ${(s:,:)widths}; do
    suffix=""
    [[ "$w" != "${${(s:,:)widths}[1]}" ]] && suffix="-${w}w"
    jpg="$out/${name}${suffix}.jpg"
    magick "$in" \
      -auto-orient -strip \
      -colorspace sRGB \
      -resize "${w}x>" \
      ${=tone} \
      ${=sharpen} \
      -quality "$jpeg_quality" -interlace Plane \
      -define jpeg:dct-method=float \
      "$jpg"
    cwebp -quiet -q "$webp_quality" -m 6 -metadata none "$jpg" -o "$out/${name}${suffix}.webp"
    print "  ${name}${suffix}: $(du -h "$jpg" | cut -f1) jpg / $(du -h "$out/${name}${suffix}.webp" | cut -f1) webp"
  done
done

# Social preview card, cropped to the 1.91:1 ratio Open Graph expects.
magick "$src/20181221_campuslife_BO_204.jpg" \
  -auto-orient -strip -colorspace sRGB \
  -resize "1200x630^" -gravity center -extent 1200x630 \
  -quality 82 -interlace Plane "$out/og-card.jpg"
print "  og-card: $(du -h "$out/og-card.jpg" | cut -f1)"

print "\nTotal assets/img: $(du -sh "$out" | cut -f1)"

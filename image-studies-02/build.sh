#!/bin/sh
set -eu
cd "$(dirname "$0")"
if command -v convert >/dev/null; then
  for f in output/0[1-6]-*.svg; do convert -background none "$f" -resize 1200x600 "${f%.svg}.png"; done
    convert output/01-type-monument.png output/02-pop-commons.png +append /tmp/ion-row1.png
  convert output/03-pixel-habitat.png output/04-quiet-signal.png +append /tmp/ion-row2.png
  convert output/05-xerox-broadside.png output/06-chromatic-portal.png +append /tmp/ion-row3.png
  convert /tmp/ion-row1.png /tmp/ion-row2.png /tmp/ion-row3.png -append output/contact-sheet.png
fi
python3 review.py
(cd output && sha256sum 0[1-6]-*.svg 0[1-6]-*.png contact-sheet.png 2>/dev/null > hashes.sha256 || sha256sum 0[1-6]-*.svg > hashes.sha256)

#!/bin/sh
# Minifies assets/style.css (the source to edit) into assets/style.min.css (what the pages load).
# Run after every change to style.css:   scripts/build-css.sh
set -eu
cd "$(dirname "$0")/.."
npx --yes esbuild@0.25 assets/style.css --minify --log-level=warning --outfile=assets/style.min.css

#!/usr/bin/env bash
# Copy worker/core and download English traineddata for offline OCR.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FE="$ROOT/frontend"
mkdir -p "$FE/public/tesseract" "$FE/public/tessdata"
cp "$FE/node_modules/tesseract.js/dist/worker.min.js" "$FE/public/tesseract/"
cp "$FE/node_modules/tesseract.js-core/tesseract-core-simd-lstm.wasm.js" "$FE/public/tesseract/"
cp "$FE/node_modules/tesseract.js-core/tesseract-core-simd-lstm.wasm" "$FE/public/tesseract/"
DEST="$FE/public/tessdata/eng.traineddata.gz"
if [[ ! -f "$DEST" ]]; then
  curl -fsSL -L -o "$DEST" \
    "https://github.com/naptha/tessdata/raw/gh-pages/4.0.0/eng.traineddata.gz"
fi
echo "Bundled tesseract assets under frontend/public/"

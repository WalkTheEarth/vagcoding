#!/bin/sh
# Package the offline site. index.html ends up at the zip root.
set -e
cd "$(dirname "$0")/.."
cd docs
rm -f VAG-Coding-offline.zip
zip -qr9 VAG-Coding-offline.zip . -x 'VAG-Coding-offline.zip' '_test.html'
ls -lh VAG-Coding-offline.zip

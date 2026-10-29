#!/bin/sh
# Package the offline site. index.html ends up at the zip root.
set -e
cd "$(dirname "$0")/.."
rm -f VAG-Coding-offline.zip
cd dist
zip -qr9 ../VAG-Coding-offline.zip . -x '_test.html'
cd ..
ls -lh VAG-Coding-offline.zip

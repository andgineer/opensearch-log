#!/usr/bin/env bash
#
# Create docs in docs/
#

SITE_FOLDER="../site"  # `site_dir` in mkdocs.yml

rm -rf ${SITE_FOLDER}

./scripts/docstrings.sh

for lang in bg de en es fr ru; do
    scripts/docs-render-config.sh $lang
    mkdocs build --dirty --config-file docs/_mkdocs.yml
    rm docs/_mkdocs.yml
done
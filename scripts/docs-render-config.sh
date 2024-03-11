#!/usr/bin/env bash
#
# Substitute language and site in mkdocs.yml in _mkdocs.yml
# language should be passed as an argument
#

lang=$1

sed "s/LANG_PLACEHOLDER/$lang/g" docs/mkdocs.yml > docs/_mkdocs.yml
if [ $lang = "en" ]; then
    # place English to the root of the site
    sed -i "" "s/SITE_PLACEHOLDER//g" docs/_mkdocs.yml
else
    sed -i "" "s/SITE_PLACEHOLDER/$lang/g" docs/_mkdocs.yml
fi

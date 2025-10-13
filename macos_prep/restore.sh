#!/usr/bin/env bash
# Restore using just names, ignoring paths
jq -r '.[] | .full_name // .name' formulas.json | xargs brew install

#!/usr/bin/env bash
# Capture only the essential info, no paths
brew info --json=v2 --installed | jq '[.formulae[] | {
  name: .name,
  full_name: .full_name,
  version: .versions.stable,
  revision: .revision,
  tap: .tap
}]' > formulas.json

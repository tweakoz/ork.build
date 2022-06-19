#!/usr/bin/env sh

mkdir .out
cd .out
export GIT_LFS_SKIP_SMUDGE=1
git clone git@github.com:tweakoz/orkid.git
cd orkid
git submodule init
git submodule update
./ork.build/bin/create_env.py --stagedir ~/.out/.staging-test

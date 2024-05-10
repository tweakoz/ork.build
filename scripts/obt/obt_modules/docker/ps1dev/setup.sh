#!/usr/bin/env sh

export BASEDIR=$PWD
mkdir source build

tar -zxf binutils*gz -C source
tar -zxf gcc*gz -C source

cd build
mkdir psxsdk-binutils
mkdir psxsdk-gcc

cd psxsdk-binutils
$BASEDIR/source/binutils*/configure --disable-nls --prefix=/usr/local/psxsdk --target=mipsel-unknown-elf --with-float=soft
make
make install

cd $BASEDIR/source/gcc*
./contrib/download_prerequisites
cd $BASEDIR/build/psxsdk-gcc
$BASEDIR/source/gcc*/configure --disable-nls --disable-libada --disable-libssp --disable-libquadmath --disable-libstdc++-v3 --target=mipsel-unknown-elf --prefix=/usr/local/psxsdk --with-float=soft --enable-languages=c,c++
make
make install

cd $BASEDIR
tar xvjf psxsdk-20180115.tar.bz2 -C source
cd source/psxsdk-20180115

make  
make install

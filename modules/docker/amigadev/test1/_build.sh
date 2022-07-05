#!/usr/bin/env sh 

cd ~/test1
make

cd ~/test1-build 

xdftool img.adf create 
xdftool img.adf format 'yo'
xdftool img.adf boot install 
xdftool img.adf makedir c
xdftool img.adf makedir s
xdftool img.adf makedir libs
xdftool img.adf write main.exe c
xdftool img.adf write ~/test1/S/* s
xdftool img.adf write ~/test1/libs/mathieeedoubbas.library libs
xdftool img.adf write ~/test1/libs/mathieeedoubtrans.library libs

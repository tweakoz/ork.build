cd ${OBT_BUILDS}
git clone git://github.com/FFmpeg/FFmpeg.git
cd FFmpeg/
./configure --prefix=${OBT_STAGE} --enable-nonfree --enable-shared --enable-debug=1 --disable-stripping --assert-level=1 --enable-memory-poisoning --disable-optimizations
make -j 16
make install

#!/usr/bin/env sh

cd mediapipe
export GLOG_logtostderr=1
bazel run --define MEDIAPIPE_DISABLE_GPU=1 \
    mediapipe/examples/desktop/hello_world:hello_world

bazel build --copt -I/usr/include/opencv4/ --copt -I/usr/include/$(shell gcc -print-multiarch)/opencv4/ --define MEDIAPIPE_DISABLE_GPU=1 mediapipe/examples/desktop/object_detection_3d:objectron_cpu
bazel build --copt -I/usr/include/opencv4/ --copt -I/usr/include/$(shell gcc -print-multiarch)/opencv4/ mediapipe/examples/desktop/pose_tracking:pose_tracking_gpu
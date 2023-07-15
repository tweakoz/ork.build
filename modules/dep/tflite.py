###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path, executors
from obt.command import Command, system

###############################################################################

class tflite(dep.StdProvider):
  name = "tflite"
  def __init__(self):
    super().__init__(tflite.name)
    self.declareDep("bazel")
    PYTHON = self.declareDep("python")
    self._builder = self.createBuilder(dep.CustomBuilder)
    env = {

      "TF_NEED_CUDA":"0",
      "TF_NEED_ROCM":"0",
      "TF_CUDA_CLANG":"0",
      "TF_DOWNLOAD_CLANG":"0",
      "TF_SET_ANDROID_WORKSPACE":"0",
      "TF_CONFIGURE_IOS":"0",
      
      "CC_OPT_FLAGS":"--copt=-mavx --copt=-mavx2 --copt=-mfma --copt=-msse4.2 --copt=-mfpmath=both --config=cuda",
      "PYTHON_BIN_PATH":PYTHON.executable,
      "USE_DEFAULT_PYTHON_LIB_PATH":"1",
      "TF_NEED_JEMALLOC":"1",
      "TF_NEED_GCP":"0",
      "TF_NEED_HDFS":"0",
      "TF_ENABLE_XLA":"0",
      "TF_NEED_OPENCL":"1",


    }


    configure_command = Command([
      "./configure"],
      working_dir=self.source_root,
      environment=env)

    build_cmd = Command(
      [ "bazel", 
        "build",
        "-c","opt",
        "//tensorflow/lite:libtensorflowlite.dylib"],
      working_dir=self.source_root,
      environment=env)

    TENSORFLOW_INST_ROOT = path.stage()/"tensorflow-bin"
    TENSORFLOW_INST_LIB = TENSORFLOW_INST_ROOT/"lib"
    TENSORFLOW_INST_INC = TENSORFLOW_INST_ROOT/"include"/"tensorflow"
    LITE_BUILD_DIR = self.source_root/"bazel-bin"/"tensorflow"/"lite"

    install_commands = []

    def add_cmdlist(cmdlist):
      nonlocal install_commands
      cmd = Command(cmdlist,
                    use_shell=True,      
                    working_dir=self.source_root,
                    environment=env)
      install_commands += [cmd]

    def add_systemcmd(cmdlist):
      nonlocal install_commands
      install_commands += [lambda: system(cmdlist,working_dir=self.source_root)==0]


    install_commands += [executors.rmdir(TENSORFLOW_INST_ROOT,force=True)]
    install_commands += [executors.mkdir(TENSORFLOW_INST_LIB,parents=True,clean=True)]
    install_commands += [executors.mkdir(TENSORFLOW_INST_INC,parents=True,clean=True)]

    #add_systemcmd(["cp","-f","bazel-bin/tensorflow/lite/*.a",TENSORFLOW_INST_LIB])
    #add_systemcmd(["cp","-f","bazel-bin/tensorflow/lite/*.dylib",TENSORFLOW_INST_LIB])

    install_commands += [executors.copy_files( src_dir=LITE_BUILD_DIR,
                                               pattern="*.dylib",
                                               dst_dir=TENSORFLOW_INST_LIB,
                                               modeset="c")]

    install_commands += [executors.copy_files( src_dir=LITE_BUILD_DIR,
                                               pattern="*.a",
                                               dst_dir=TENSORFLOW_INST_LIB,
                                               modeset="c")]

    def rsync(src=None,dst=None,incs=[],excs=[]):
      nonlocal install_commands
      cmd = ["rsync","-avzh"]
      for item in incs:
        cmd += ["--include",item]
      for item in excs:
        cmd += ["--exclude",item]
      cmd += [src,dst]
      add_systemcmd(cmd)


    #rsync( --exclude '_virtual_includes/' --include '*/' --include '*.h' --include '*.inc' --exclude '*' bazel-bin/ $tensorflow_root/include/
    #rsync( src="tensorflow/cc", dst=TENSORFLOW_INST_INC, incs=['*/','*.h','*.inc'], excs=['*'] )
    #rsync( --include '*/' --include '*.h' --include '*.inc' --exclude '*' tensorflow/core $tensorflow_root/include/tensorflow/
    #rsync( --include '*/' --include '*' --exclude '*.cc' third_party/ $tensorflow_root/include/third_party/
    #rsync( --include '*/' --include '*' --exclude '*.txt' bazel-tensorflow/external/eigen_archive/Eigen/ $tensorflow_root/include/Eigen/
    #rsync( --include '*/' --include '*' --exclude '*.txt' bazel-tensorflow/external/eigen_archive/unsupported/ $tensorflow_root/include/unsupported/
    #rsync( --include '*/' --include '*.h' --include '*.inc' --exclude '*' bazel-tensorflow/external/com_google_protobuf/src/google/ $tensorflow_root/include/google/
    #rsync( --include '*/' --include '*.h' --include '*.inc' --exclude '*' bazel-tensorflow/external/com_google_absl/absl/ $tensorflow_root/include/absl/

    self._builder._cleanbuildcommands += [configure_command,build_cmd]
    self._builder._incrbuildcommands += [build_cmd]+install_commands

    #for item in install_commands:
    #  print(item.command_list)

    #cmake ../tensorflow/lite -DTFLITE_KERNEL_TEST=on -DTFLITE_ENABLE_GPU=ON
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=tflite.name,
                             repospec="tweakoz/tensorflow",
                             revision="master",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libtflitemcDynamics.so").exists()


"""
export TF_NCCL_VERSION=1.3

export PYTHONPATH=${TF_ROOT}/lib
export PYTHON_ARG=${TF_ROOT}/lib
export CUDA_TOOLKIT_PATH=${CUDA_HOME}
export CUDNN_INSTALL_PATH=${CUDA_HOME}

export TF_NEED_ROCM=0
export TF_NEED_IGNITE=0
export TF_NEED_GCP=0
export TF_NEED_CUDA=1
export TTENSORRT_INSTALL_PATH = ???
export TF_CUDA_VERSION="$($CUDA_TOOLKIT_PATH/bin/nvcc --version | sed -n 's/^.*release \(.*\),.*/\1/p')"
export TF_CUDA_COMPUTE_CAPABILITIES=6.1,5.2,3.5
export TF_NEED_HDFS=0
export TF_NEED_OPENCL=0
export TF_NEED_JEMALLOC=1
export TF_ENABLE_XLA=0
export TF_NEED_VERBS=0
export TF_CUDA_CLANG=0
export TF_CUDNN_VERSION="$(sed -n 's/^#define CUDNN_MAJOR\s*\(.*\).*/\1/p' $CUDNN_INSTALL_PATH/include/cudnn.h)"
export TF_NEED_MKL=0
export TF_DOWNLOAD_MKL=0
export TF_NEED_AWS=0
export TF_NEED_MPI=0
export TF_NEED_GDR=0
export TF_NEED_S3=0
export TF_NEED_OPENCL_SYCL=0
export TF_SET_ANDROID_WORKSPACE=0
export TF_NEED_COMPUTECPP=0
export GCC_HOST_COMPILER_PATH=$(which gcc)
export CC_OPT_FLAGS="-march=native"

export TF_NEED_KAFKA=0
export TF_NEED_TENSORRT=0"""


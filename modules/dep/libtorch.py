###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path, host

###############################################################################
# libtorch is quarantined for now..
###############################################################################

class libtorch(dep.StdProvider):
  name = "libtorch"
  def __init__(self):
    super().__init__(libtorch.name)
    self.declareDep("cmake")
    self.declareDep("zmq")
    self.declareDep("ffmpeg")
    PYTHON = dep.instance("python")

    self._builder = self.createBuilder(dep.CMakeBuilder,install_prefix=self.prefix)
    self._builder.setCmVar("PYTHON_EXECUTABLE",PYTHON.executable)
    self._builder.setCmVar("USE_NCCL","OFF") # NVIDIA Collective Communication Library (causes errors, atm....)
    self._builder.setCmVar("USE_CUDA","OFF") # (causes errors, atm....)
    self._builder.setCmVar("USE_ZMQ","ON") #
    self._builder.setCmVar("USE_FFMPEG","ON") #

    if host.IsOsx:
      self._builder.setCmVar("USE_METAL", "ON")
      self._builder.setCmVar("CMAKE_CXX_FLAGS", "-Wno-unknown-warning-option")
    else:
      self._builder.setCmVar("BUILD_CAFFE2","ON") #

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=libtorch.name,
                             repospec="pytorch/pytorch",
                             revision="v1.12.0",
                             recursive=True)
  ########################################################################
  @property
  def prefix(self):
    return path.quarantine()/"libtorch"
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (self.prefix/"lib"/"liblibtorchx.so").exists()




"""

Caffe2 is a deep learning framework.that provides an easy and straightforward way for you to experiment
 with deep learning and leverage community contributions of new models and algorithms. You can bring your 
 creations to scale using the power of GPUs in the cloud or to the masses on mobile 
 with Caffe2’s cross-platform libraries.

--   Build type            : Release
--   Compile definitions   : ONNX_ML=1;ONNXIFI_ENABLE_EXT=1;ONNX_NAMESPACE=onnx_torch;HAVE_MMAP=1;_FILE_OFFSET_BITS=64;HAVE_SHM_OPEN=1;HAVE_SHM_UNLINK=1;HAVE_MALLOC_USABLE_SIZE=1;USE_EXTERNAL_MZCRC;MINIZ_DISABLE_ZIP_READER_CRC32_CHECKS
--   CMAKE_PREFIX_PATH     : /usr
--   USE_GOLD_LINKER       : OFF
-- 
--   TORCH_VERSION         : 1.12.0
--   CAFFE2_VERSION        : 1.12.0
--   BUILD_CAFFE2          : OFF
--   BUILD_CAFFE2_OPS      : OFF
--   BUILD_CAFFE2_MOBILE   : OFF
--   BUILD_STATIC_RUNTIME_BENCHMARK: OFF
--   BUILD_TENSOREXPR_BENCHMARK: OFF
--   BUILD_NVFUSER_BENCHMARK: OFF
--   BUILD_BINARY          : OFF
--   BUILD_CUSTOM_PROTOBUF : ON
--     Link local protobuf : ON
--   BUILD_DOCS            : OFF
--   BUILD_PYTHON          : ON
--     Python version      : 3.9.13
--     Python executable   : <staging>/pyvenv/bin/python3
--     Pythonlibs version  : 3.9.13
--     Python library      : <staging>/python-3.9.13/lib/python3.9
--     Python includes     : <staging>/python-3.9.13/include/python3.9
--     Python site-packages: lib/python3.9/site-packages
--   BUILD_SHARED_LIBS     : ON
--   CAFFE2_USE_MSVC_STATIC_RUNTIME     : OFF
--   BUILD_TEST            : OFF
--   BUILD_JNI             : OFF
--   BUILD_MOBILE_AUTOGRAD : OFF
--   BUILD_LITE_INTERPRETER: OFF
--   INTERN_BUILD_MOBILE   : 
--   USE_BLAS              : 1
--     BLAS                : open
--     BLAS_HAS_SBGEMM     : 
--   USE_LAPACK            : 1
--     LAPACK              : open
--   USE_ASAN              : OFF
--   USE_CPP_CODE_COVERAGE : OFF
--   USE_CUDA              : ON
--     Split CUDA          : OFF
--     CUDA static link    : OFF
--     USE_CUDNN           : OFF
--     USE_EXPERIMENTAL_CUDNN_V8_API: ON
--     CUDA version        : 11.5
--     CUDA root directory : /usr
--     CUDA library        : /usr/lib/x86_64-linux-gnu/libcuda.so
--     cudart library      : /usr/lib/x86_64-linux-gnu/libcudart.so
--     cublas library      : /usr/lib/x86_64-linux-gnu/libcublas.so
--     cufft library       : /usr/lib/x86_64-linux-gnu/libcufft.so
--     curand library      : /usr/lib/x86_64-linux-gnu/libcurand.so
--     nvrtc               : /usr/lib/x86_64-linux-gnu/libnvrtc.so
--     CUDA include path   : /usr/include
--     NVCC executable     : /usr/bin/nvcc
--     CUDA compiler       : /usr/bin/nvcc

--     CUDA flags          :  -Xfatbin -compress-all -DONNX_NAMESPACE=onnx_torch -gencode arch=compute_86,code=sm_86 -Xcudafe --diag_suppress=cc_clobber_ignored,--diag_suppress=integer_sign_change,--diag_suppress=useless_using_declaration,--diag_suppress=set_but_not_used,--diag_suppress=field_without_dll_interface,--diag_suppress=base_class_has_different_dll_interface,--diag_suppress=dll_interface_conflict_none_assumed,--diag_suppress=dll_interface_conflict_dllexport_assumed,--diag_suppress=implicit_return_from_non_void_function,--diag_suppress=unsigned_compare_with_zero,--diag_suppress=declared_but_not_referenced,--diag_suppress=bad_friend_decl --expt-relaxed-constexpr --expt-extended-lambda  -Wno-deprecated-gpu-targets --expt-extended-lambda -DCUB_WRAPPED_NAMESPACE=at_cuda_detail -DCUDA_HAS_FP16=1 -D__CUDA_NO_HALF_OPERATORS__ -D__CUDA_NO_HALF_CONVERSIONS__ -D__CUDA_NO_HALF2_OPERATORS__ -D__CUDA_NO_BFLOAT16_CONVERSIONS__
--     CUDA host compiler  : 
--     CUDA --device-c     : OFF
--     USE_TENSORRT        : OFF
--   USE_ROCM              : OFF
--   USE_EIGEN_FOR_BLAS    : ON
--   USE_FBGEMM            : ON
--     USE_FAKELOWP          : OFF
--   USE_KINETO            : ON
--   USE_FFMPEG            : OFF
--   USE_GFLAGS            : OFF
--   USE_GLOG              : OFF
--   USE_LEVELDB           : OFF
--   USE_LITE_PROTO        : OFF
--   USE_LMDB              : OFF
--   USE_METAL             : OFF
--   USE_PYTORCH_METAL     : OFF
--   USE_PYTORCH_METAL_EXPORT     : OFF
--   USE_MPS               : OFF
--   USE_FFTW              : OFF
--   USE_MKL               : OFF
--   USE_MKLDNN            : ON
--   USE_NCCL              : ON
--     USE_SYSTEM_NCCL     : OFF
--     USE_NCCL_WITH_UCC   : OFF
--   USE_NNPACK            : ON
--   USE_NUMPY             : ON
--   USE_OBSERVERS         : ON
--   USE_OPENCL            : OFF
--   USE_OPENCV            : OFF
--   USE_OPENMP            : ON
--   USE_TBB               : OFF
--   USE_VULKAN            : OFF
--   USE_PROF              : OFF
--   USE_QNNPACK           : ON
--   USE_PYTORCH_QNNPACK   : ON
--   USE_XNNPACK           : ON
--   USE_REDIS             : OFF
--   USE_ROCKSDB           : OFF
--   USE_ZMQ               : OFF
--   USE_DISTRIBUTED       : ON
--     USE_MPI               : ON
--     USE_GLOO              : ON
--     USE_GLOO_WITH_OPENSSL : OFF
--     USE_TENSORPIPE        : ON
--   USE_DEPLOY           : OFF
--   Public Dependencies  : caffe2::Threads
--   Private Dependencies : pthreadpool;cpuinfo;qnnpack;pytorch_qnnpack;nnpack;XNNPACK;fbgemm;/usr/lib/x86_64-linux-gnu/libnuma.so;fp16;/usr/lib/x86_64-linux-gnu/libmpi_cxx.so;/usr/lib/x86_64-linux-gnu/libmpi.so;tensorpipe;gloo;foxi_loader;rt;fmt::fmt-header-only;kineto;gcc_s;gcc;dl
--   USE_COREML_DELEGATE     : OFF
--   BUILD_LAZY_TS_BACKEND   : ON

https://github.com/pytorch/pytorch/pull/16242
https://pytorch.org/tutorials/advanced/super_resolution_with_caffe2.html
https://pytorch.org/tutorials/advanced/cpp_export.html

"""

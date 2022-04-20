###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log, path, template

VERSION = "1.77.0"

boost_libs = list()
boost_libs += ["boost_container-mt"]
boost_libs += ["boost_log_setup "]
boost_libs += ["boost_math_tr1l "]
boost_libs += ["boost_graph-mt "]
boost_libs += ["boost_wserialization-mt "]
boost_libs += ["boost_log-mt "]
boost_libs += ["boost_math_c99f "]
boost_libs += ["boost_type_erasure "]
boost_libs += ["boost_signals-mt "]
boost_libs += ["boost_test_exec_monitor "]
boost_libs += ["boost_filesystem "]
boost_libs += ["boost_thread-mt "]
boost_libs += ["boost_math_tr1f-mt "]
boost_libs += ["boost_date_time "]
boost_libs += ["boost_timer "]
boost_libs += ["boost_math_tr1f "]
boost_libs += ["boost_test_exec_monitor-mt "]
boost_libs += ["boost_container "]
boost_libs += ["boost_math_tr1 "]
boost_libs += ["boost_type_erasure-mt "]
boost_libs += ["boost_program_options-mt "]
boost_libs += ["boost_graph "]
boost_libs += ["boost_log_setup-mt "]
boost_libs += ["boost_random "]
boost_libs += ["boost_system "]
boost_libs += ["boost_system-mt "]
boost_libs += ["boost_locale-mt "]
boost_libs += ["boost_wserialization "]
boost_libs += ["boost_regex "]
boost_libs += ["boost_exception "]
boost_libs += ["boost_timer-mt "]
boost_libs += ["boost_signals "]
boost_libs += ["boost_filesystem-mt "]
boost_libs += ["boost_math_c99-mt "]
boost_libs += ["boost_math_tr1-mt "]
boost_libs += ["boost_serialization-mt "]
boost_libs += ["boost_serialization "]
boost_libs += ["boost_prg_exec_monitor "]
boost_libs += ["boost_exception-mt "]
boost_libs += ["boost_coroutine "]
boost_libs += ["boost_math_c99 "]
boost_libs += ["boost_iostreams-mt "]
boost_libs += ["boost_random-mt "]
boost_libs += ["boost_program_options "]
boost_libs += ["boost_atomic-mt "]
boost_libs += ["boost_date_time-mt "]
boost_libs += ["boost_math_c99l "]
boost_libs += ["boost_math_tr1l-mt "]
boost_libs += ["boost_context-mt "]
boost_libs += ["boost_regex-mt "]
boost_libs += ["boost_coroutine-mt "]
boost_libs += ["boost_log "]
boost_libs += ["boost_chrono-mt "]
boost_libs += ["boost_wave-mt "]
boost_libs += ["boost_iostreams "]
boost_libs += ["boost_chrono"]

PKGCONF = """
# Package Information for pkg-config
prefix=$$$STAGING
exec_prefix=${prefix}
libdir=${exec_prefix}/lib
includedir_old=${prefix}/include/boost
includedir_new=${prefix}/include

Name: Boost
Description: Boost (OBT)
Version: $$$VERSION
Libs: -L${exec_prefix}/lib $$$LIBS
Cflags: -I${includedir_old} -I${includedir_new}
"""

###############################################################################
class boost(dep.StdProvider):
  def __init__(self):
    name = "boost"
    super().__init__(name)
    self.declareDep("python")
    self.declareDep("llvm")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="boostorg/boost",
                                      revision="boost-1.77.0",
                                      recursive=True)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "CMAKE_CXX_STANDARD": "17",
      "BOOST_ENABLE_PYTHON": "ON",
      #"CMAKE_CXX_FLAGS": "-fPIC",
      "BUILD_SHARED_LIBS": "ON"
    }

  def onPostBuild(self):
    print("GENERATING PKFCONFIG FILE")
    replacements = dict()
    replacements["STAGING"] = path.stage()
    replacements["VERSION"] = VERSION
    replacements["LIBS"] = " ".join(["-l"+x+" " for x in boost_libs])
    template.template_string(PKGCONF,replacements,path.pkgconfigdir()/"boost.pc")
    return True

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libboost_atomic.a").exists()
###############################################################################



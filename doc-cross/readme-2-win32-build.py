#!/usr/bin/env python
# readme-2-win32-build.py

import sys
import subprocess
import os
from ctypes import cdll

# See if the library is already installed
try:
    lib = cdll.LoadLibrary('build\\output\\cryptoauth.dll')
    # Test to ensure it has the required features to support the
    # python wrapper. It may change later to a version check
    assert 0 != lib.ATCAIfacecfg_size
    _EXTENSIONS = None
except:
    _EXTENSIONS = ['cryptoauthlib']


def get_setup_dir():
    return os.path.dirname(os.path.abspath(__file__)) + os.path.sep


class CryptoAuthCommandBuildExt(object):
    def __init__(self):
        self.setup_dir = get_setup_dir()
        self.build_temp = self.setup_dir + 'build' + os.path.sep + "temp"
        self.build_out  = self.setup_dir + 'build' + os.path.sep + "output"

        self.config_result = ""
        self.build_result = ""

    def build_extension(self):
        # Suppress cmake output
        devnull = open(os.devnull, 'r+b')
        nousb = True

        # Check if CMAKE is installed
        try:
            subprocess.check_call(['cmake', '--version'], stdin=devnull, stdout=devnull, stderr=devnull, shell=False)
        except OSError as e:
            print("CMAKE must be installed on the system for this module to build the required extension e.g. 'apt-get install cmake' or 'yum install cmake'")
            raise e

        ''' the configuration dump and build dump: on the -20200208 version
            ['cmake', 'D:\\win32_ctypes\\cryptoauthlib\\lib',
                '-DATCA_HAL_CUSTOM=ON',
                '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE=D:\\win32_ctypes\\cryptoauthlib\\build\\lib.win-amd64-3.8\\cryptoauthlib',
                '-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE=D:\\win32_ctypes\\cryptoauthlib\\build\\lib.win-amd64-3.8\\cryptoauthlib',
                '-A', 'x64',
                '-DATCACERT_DEF_SRC=D:/win32_ctypes/cryptoauthlib/atca_utils_sizes.c']
            ['cmake', '--build', '.', '--config', 'Release']
        '''
        setupdir = self.setup_dir

        cmakelist_path = os.path.abspath(setupdir + 'lib')

        build_args = ['--config', 'Release']

        cmake_args = ['-DATCA_HAL_CUSTOM=ON']
        cmake_args += ['-DATCA_HAL_I2C=ON']
        cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE=' + self.build_out]
        cmake_args += ['-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE=' + self.build_out]
        cmake_args += ['-A', 'x64']
        #cmake_args += ['-DATCACERT_DEF_SRC={}/lib/atca_utils_sizes.c'.format( setupdir.replace('\\','/') )]
        cmake_args += ["-DCMAKE_VERBOSE_MAKEFILE=1"]

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        # Configure the library
        try:
            print("DUMP cmd: ", ['cmake', cmakelist_path] + cmake_args)
            print("DUMP cwd: ", os.path.abspath(self.build_temp))
            ret_lines = subprocess.check_output(['cmake', cmakelist_path] + cmake_args, cwd=os.path.abspath(self.build_temp), stderr=subprocess.STDOUT)
            self.config_result += ret_lines.decode()
        except subprocess.CalledProcessError as e:
            msg = e.output.decode('utf-8')
            if 'usb' in msg:
                msg += '\n\n   USB libraries or headers were not located. If USB support is\n' \
                       '   not required it can be disabled by setting the environment\n' \
                       '   variable CRYPTOAUTHLIB_NOUSB to true before trying to install\n' \
                       '   this package: \n\n' \
                       '       $ export CRYPTOAUTHLIB_NOUSB=True\n\n' \
                       '   Run setup.py clean before trying install again or use the pip \n' \
                       '   option --no-cache-dir\n'
            raise RuntimeError(msg)

        # Build the library
        try:
            print("DUMP cmd: ", ['cmake', '--build', '.'] + build_args)
            print("DUMP cwd: ", os.path.abspath(self.build_temp))
            ret_lines = subprocess.check_output(['cmake', '--build', '.'] + build_args, cwd=os.path.abspath(self.build_temp), stderr=subprocess.STDOUT)
            self.build_result += ret_lines.decode()
        except subprocess.CalledProcessError as e:
            if sys.version_info[0] <= 2:
                raise RuntimeError(e.output)  # Python 2 doesn't handle unicode exceptions
            else:
                raise RuntimeError(e.output.decode('utf-8'))


if __name__ == '__main__':
    '''must be copied to the top directory and run from there
    assuming the cmake is installed relative to the top directory at ../cmake-bin/cmake_3_20_1_x86_64
    '''

    # insert the cmake path:
    env_var_path = os.environ.get('PATH', '')
    setup_dir = get_setup_dir()
    cmake_bin_dir = os.path.abspath( setup_dir + os.path.sep + ".." + os.path.sep + "cmake-bin")
    cmake_bin_dir += "\\cmake_3_20_1_x86_64\\bin\\"
    env_var_path_new = cmake_bin_dir + ";" + env_var_path
    os.environ['PATH'] = env_var_path_new
    env_vars = os.environ
    #print("os.environ", env_vars)

    bb = CryptoAuthCommandBuildExt()
    bb_except_any = None
    try:
        bb.build_extension()
    except RuntimeError as e:
        print(" RuntimeError: ", e)
        bb_except_any = " RuntimeError " + str(e)
    except:
        print(" Unknown exception: ")
        bb_except_any = " Unknown exception"

    print("")
    print(" config output lines: ", len(bb.config_result) )
    print(" build output lines: ", len(bb.build_result) )
    print("")
    print(" config output lines: \n", bb.config_result )
    print("")
    print(" build output lines: \n", bb.build_result )
    print("")

    if bb_except_any is not None:
        print(" build exception some ", len(str(bb_except_any)))


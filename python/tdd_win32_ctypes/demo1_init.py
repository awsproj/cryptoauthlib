#!/usr/bin/env python
# demo1_init.py

"""
Device Info Retrieval Example
"""
# (c) 2015-2018 Microchip Technology Inc. and its subsidiaries.
#
# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.
#
# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A
# PARTICULAR PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT,
# SPECIAL, PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE
# OF ANY KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF
# MICROCHIP HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE
# FORESEEABLE. TO THE FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL
# LIABILITY ON ALL CLAIMS IN ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED
# THE AMOUNT OF FEES, IF ANY, THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR
# THIS SOFTWARE.

import time
tm00 = time.time()

import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + os.sep + ".."))

from cryptoauthlib import *
from tdd_win32_ctypes.common_win32_ctypes import atca_names_map
from tdd_win32_ctypes.common_win32_ctypes import win32_ctypes_release

import time
import platform


def demo1_init(iface='i2c', device='ecc'):

    # cfg_type: 'cfg_ateccx08a_i2c_default()'
    cfg_type = 'cfg_at{}a_{}_default()'.format(atca_names_map.get(device), atca_names_map.get(iface))

    cfg = eval(cfg_type)        # {ATCAIfaceCfg}
    #print(" cfg repr ", repr(cfg))   # <cryptoauthlib.iface.ATCAIfaceCfg object>

    plat_str = platform.platform()
    if plat_str.startswith("Linux-4.9.37-aarch64"):
        # aarch64: Linux-4.9.37-aarch64-with-glibc2.17
        bus_no = 64
    elif plat_str.startswith("Linux-4.9.107-armv7l"):
        # armhf: Linux-4.9.107-armv7l-with-glibc2.4
        bus_no = 32
    elif plat_str.startswith("Windows-10-"):
        # laptop: Windows-10-10.0.20041-SP2
        bus_no = 10  # win10
    else:
        raise RuntimeError("Unknown platform")

    cfg.cfg.atcai2c.bus = bus_no
    cfg.cfg.atcai2c.slave_address = 0xc0
    cfg.cfg.atcai2c.baud = 400000
    cfg.wake_delay = 1500
    cfg.rx_retries = 20

    # Initialize the stack
    tm1 = time.time()
    rc = atcab_init(cfg)
    if rc == Status.ATCA_SUCCESS:
        rc_ok = True
    else:
        rc_ok = False
    tm2 = time.time()
    print('atcab_init() rc_ok: ', rc_ok)
    print(" time used %.3f" % (tm2 - tm1))

    atcab_release()


if __name__ == '__main__':
    sys_type = sys.platform
    if sys_type == 'ref-win32':
        demo1_init(iface='hid') # for code inspection on windows
    else:
        demo1_init()
    win32_ctypes_release()

    tm99 = time.time()
    print("Total time consumed %.3f" % (tm99 - tm00))
    sys.exit(0)


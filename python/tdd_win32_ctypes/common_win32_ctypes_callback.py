#!/usr/bin/env python
# common_win32_ctypes_callback.py

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

from ctypes import c_uint8, c_uint32, c_int, byref, \
                    create_string_buffer, Structure, c_char, c_uint16
from ctypes import CFUNCTYPE as c_CFUNCTYPE
from cryptoauthlib.status import Status
from cryptoauthlib.library import get_cryptoauthlib, AtcaReference

import copy


class Win32CtypesIfaceData(Structure):
    """Interface structure used by ..."""
    _fields_ = [('req_seqn', c_uint32),
                ('data_len_in', c_uint16),
                ('data_len_out', c_uint16),
                ('buf', c_uint8 * 256),
                ]


_cfg_debug_decode = True
_cfg_debug_vcp_call = True

_g_ser = None # global serial connection


class SerialConnection:
    def __init__(self):
        self._sent_data = None
        self._trans_count = 0
    def hal_send(self, data):
        self._sent_data = copy.deepcopy(data)
        rv = {'a':0, 'n':0}
        self._trans_count += 1
        if self._trans_count >= 4:
            return {'a': 2, 'n': 0}  # 2: fatal failure ATCA_GEN_FAIL
        return rv
    def hal_recv(self, data):
        dlen_in = data.data_len_in
        d_out = [dlen_in]
        if dlen_in == 1:
            d_out[0] = 2
        if dlen_in > 1:
            d_out.extend([x for x in range(1,dlen_in)])
        rv = {'a':0,
              'n':d_out[0],
              'd':bytes(bytearray(d_out))}
        if self._sent_data is None:
            rv = {'a': 1,
                  'n': 0,
                  'd': bytes(bytearray(d_out))}
        self._sent_data = None
        self._trans_count += 1
        if self._trans_count >= 4:
            return {'a':2, 'n':0} # 2: fatal failure ATCA_GEN_FAIL
        return rv
    def finish(self):
        pass # close connection, stop the rx thread

@c_CFUNCTYPE(c_int, c_uint32, c_uint32, c_uint32)
def callback_func(func_sel, seqn, param1):
    if func_sel == 1: # wake
        if _cfg_debug_vcp_call:
            print(" callback_wake seqn %d wake_delay %u" % (seqn, param1))
        data = Win32CtypesIfaceData()
        data.req_seqn = seqn
        data.data_len_in = 0

        rv = None
        if _g_ser is not None:
            rv = _g_ser.hal_wake()
        if rv is None:
            data.data_len_out = 0
        else:
            data.data_len_out = 4
            for i in range(4):
                data.buf[i] = rv['d'][i]

        status = get_cryptoauthlib().hal_win32_ctypes_put_response(seqn, byref(data))
        return status

    elif func_sel == 2: # idle
        if _cfg_debug_vcp_call:
            print(" callback_idle seqn %d param1 %u" % (seqn, param1))
        data = Win32CtypesIfaceData()
        data.req_seqn = seqn
        data.data_len_in = 0

        rv = None
        if _g_ser is not None:
            rv = _g_ser.hal_idle()
        if rv is None:
            status = Status.ATCA_COMM_FAIL
        else:
            if rv.get('a', None) == 0:
                status = Status.ATCA_SUCCESS
            else:
                status = Status.ATCA_COMM_FAIL
        return status

    elif func_sel == 4: # send
        if _cfg_debug_vcp_call:
            print(" callback_send seqn %d txlength %u" % (seqn, param1))
        data = Win32CtypesIfaceData()

        status = Status.ATCA_GEN_FAIL
        while True: # scope
            s1 = get_cryptoauthlib().hal_win32_ctypes_get_request(seqn, byref(data))
            if s1 != Status.ATCA_SUCCESS:
                status = s1
                break

            if seqn != data.req_seqn or param1 != data.data_len_in:
                status = Status.ATCA_BAD_PARAM
                break

            # always 3, 7, op_code
            #print(" send bytes ", "0x- %02x %02x %02x" % (data.buf[0], data.buf[1], data.buf[2]))
            cmd_op_code = 0
            if data.buf[0] == 3 and data.buf[1] == 7:
                cmd_op_code = data.buf[2]

            rv = None
            if _g_ser is not None:
                rv = _g_ser.hal_send(data)
            if cmd_op_code == 0x40: # 0x40 genkey command 80ms
                #import time
                #time.sleep(0.08)
                # ok the lib will retry on a nak. not sleep here.
                pass

            data.req_seqn = seqn
            data.data_len_in = 0
            data.data_len_out = 0

            if rv is None:
                status = Status.ATCA_COMM_FAIL
                break
            if rv.get('a', None) == 0 and rv.get('n', None) == 0:
                status = Status.ATCA_SUCCESS
            elif rv.get('a', None) == 2: # 2: fatal failure
                status = Status.ATCA_GEN_FAIL
            else:
                status = Status.ATCA_COMM_FAIL
            break # scope
        return status

    elif func_sel == 5: # recv
        if _cfg_debug_vcp_call:
            print(" callback_recv seqn %d rxlength %u" % (seqn, param1))
        data = Win32CtypesIfaceData()

        status = Status.ATCA_GEN_FAIL
        while True: # scope
            s1 = get_cryptoauthlib().hal_win32_ctypes_get_request(seqn, byref(data))
            if s1 != Status.ATCA_SUCCESS:
                status = s1
                break

            if seqn != data.req_seqn or param1 != data.data_len_in:
                status = Status.ATCA_BAD_PARAM
                break

            rv = None
            if _g_ser is not None:
                rv = _g_ser.hal_recv(data)

            data.req_seqn = seqn
            data.data_len_in = 0
            data.data_len_out = 0

            if rv is None:
                status = Status.ATCA_COMM_FAIL
                break
            if rv.get('a', None) != 0:
                status = Status.ATCA_COMM_FAIL
                if rv.get('a', None) == 2:  # 2: fatal failure
                    status = Status.ATCA_GEN_FAIL
                break

            dlen = rv.get('n', None)
            pkt = rv.get('d', None)
            if type(dlen) is not int or type(pkt) is not bytes:
                status = Status.ATCA_COMM_FAIL
                break
            plen = len(pkt)
            if dlen != plen:
                status = Status.ATCA_COMM_FAIL
                break

            data.data_len_out = dlen
            for i in range(dlen):
                data.buf[i] = pkt[i]

            status = get_cryptoauthlib().hal_win32_ctypes_put_response(seqn, byref(data))
            break # scope
        return status

    else:
        print("callback_... unknown ", func_sel)
        return Status.ATCA_UNIMPLEMENTED
    return Status.ATCA_SUCCESS

def hal_win32_ctypes_register_callbacks():
    status = get_cryptoauthlib().hal_win32_ctypes_register_cb(callback_func)
    return status


_g_ser = None
_g_ser_status = None

try:
    tmp_ser = SerialConnection()
    tmp_status = hal_win32_ctypes_register_callbacks()
    _g_ser = tmp_ser
    _g_ser_status = tmp_status
except Exception as e:
    print(" hal_win32_ctypes_register_callbacks exception: " + str(e))
except:
    print(" hal_win32_ctypes_register_callbacks exception: unknown")

print(" hal_win32_ctypes_register_callbacks: ", _g_ser_status)


def win32_ctypes_release():
    if _g_ser is not None:
        _g_ser.finish()


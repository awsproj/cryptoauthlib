#!/usr/bin/env python
# common_win32_ctypes.py

from cryptoauthlib import get_device_name
import base64, time, sys, platform

import tdd_win32_ctypes.common_win32_ctypes_callback


def win32_ctypes_release():
    tdd_win32_ctypes.common_win32_ctypes_callback.win32_ctypes_release()

def htk_vcp_gpio_set(chn, val):
    return tdd_win32_ctypes.common_win32_ctypes_callback.htk_gpio_set(chn=chn, pwr=val)


# Maps common name to the specific name used internally
atca_names_map = {'i2c': 'i2c', 'hid': 'kithid', 'sha': 'sha20x', 'ecc': 'eccx08'}

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

def get_device_name_special(revision):
    devname = get_device_name(revision)
    if type(devname) is str and devname == 'ATECC608A':
        # special treatment: the lib still uses 'ATECC608A'
        devname = 'ATECC608'
    return devname

def get_device_rev(revision):
    """
    Returns the device revision model based on the info byte array values returned by atcab_info
    """
    dev_name = get_device_name(revision)
    if dev_name == 'ATECC608A': # the lib still uses 'ATECC608A'
        if revision[3] == 0x02:
            return "A" # ATECC608A
        elif revision[3] == 0x3:
            return "B" # ATECC608B
    return 'UNKNOWN'

def pretty_print_hex(a, l=16, indent=''):
    """
    Format a list/bytes/bytearray object into a formatted ascii hex string
    """
    lines = []
    a = bytearray(a)
    for x in range(0, len(a), l):
        lines.append(indent + ' '.join(['{:02X}'.format(y) for y in a[x:x+l]]))
    return '\n'.join(lines)

def convert_ec_pub_to_pem(raw_pub_key):
    """
    Convert to the key to PEM format. Expects bytes
    """
    public_key_der = bytearray.fromhex('3059301306072A8648CE3D020106082A8648CE3D03010703420004') + raw_pub_key
    public_key_b64 = base64.b64encode(public_key_der).decode('ascii')
    public_key_pem = (
        '-----BEGIN PUBLIC KEY-----\n'
        + '\n'.join(public_key_b64[i:i + 64] for i in range(0, len(public_key_b64), 64)) + '\n'
        + '-----END PUBLIC KEY-----'
    )
    return public_key_pem

def create_chip_cfg(iface, device):
    # cfg_type: 'cfg_ateccx08a_i2c_default()'
    device_mapped = atca_names_map.get(device)
    iface_mapped = atca_names_map.get(iface)
    cfg_type = 'cfg_at{}a_{}_default()'.format(device_mapped, iface_mapped)
    if device_mapped == 'eccx08' and iface_mapped == 'i2c':
        from cryptoauthlib import cfg_ateccx08a_i2c_default
    elif device_mapped == 'eccx08' and iface_mapped == 'hid' and sys.platform == 'win32':
        from cryptoauthlib import cfg_ateccx08a_hid_default
    else:
        raise RuntimeError("Unsupported iface or device")

    cfg = eval(cfg_type)        # {ATCAIfaceCfg}
    #print(" cfg repr ", repr(cfg))   # <cryptoauthlib.iface.ATCAIfaceCfg object>

    plat_str = platform.platform()
    if plat_str.startswith("Linux-4.9.37-aarch64"):
        # h59a: Linux-4.9.37-aarch64-with-glibc2.17
        bus_no = 11
    elif plat_str.startswith("Linux-4.19.111-armv7l"):
        # rv1126: Linux-4.19.111-armv7l-with-glibc2.4
        bus_no = 5  # rv1126
    else:
        raise RuntimeError("Unknown platform")

    cfg.cfg.atcai2c.bus = bus_no
    cfg.cfg.atcai2c.slave_address = 0xc0
    cfg.cfg.atcai2c.baud = 400000
    cfg.wake_delay = 1500
    cfg.rx_retries = 20
    return cfg


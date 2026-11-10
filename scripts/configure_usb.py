#!/usr/bin/env python3
"""Toggle USB 2.0 support for the hardware-modified K2.

Stock K2 has no USB port. This script is for boards that have had a USB
connector soldered on (D+/D- to MT7620A's USB pins, plus 5V).

Two parts must both be in place for USB to work:

  1. Device tree -- patches/mt7620a_phicomm_k2-32m.dts enables &ehci / &ohci.
     mt7620a.dtsi ships them as status = "disabled" because the stock board
     has no port.

  2. Kernel packages -- kmod-usb2 (EHCI), kmod-usb-ohci (OHCI), and
     kmod-usb-storage + block-mount if you want to mount USB drives.

Usage:
    python3 configure_usb.py enable
    python3 configure_usb.py disable
"""
import sys

# 控制器：插 U 盘/键盘等任何 USB 设备都需要
USB_CORE = [
    'kmod-usb2',
    'kmod-usb-ohci',
]

# 存储：只有要挂载 U 盘 / 外置硬盘才需要
USB_STORAGE = [
    'kmod-usb-storage',
    'kmod-fs-ext4',
    'kmod-fs-vfat',
    'kmod-nls-cp437',
    'kmod-nls-iso8859-1',
    'kmod-nls-utf8',
    'block-mount',
]


def set_option(config: str, name: str, value: bool) -> str:
    key = f'CONFIG_{name}'
    out = [
        ln for ln in config.splitlines()
        if not (ln.startswith(key + '=') or ln.startswith(f'# {key} is not set'))
    ]
    out.append(f'{key}=y' if value else f'# {key} is not set')
    return '\n'.join(out) + '\n'


def configure(enable: bool) -> None:
    with open('.config', encoding='utf-8') as fh:
        cfg = fh.read()

    for pkg in USB_CORE + USB_STORAGE:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)

    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    state = 'enabled' if enable else 'disabled'
    print(f'USB 2.0: {state}')
    if enable:
        print('  控制器: kmod-usb2, kmod-usb-ohci')
        print('  存储  : kmod-usb-storage, ext4/vfat, block-mount')
        print('  注意  : DTS 需同时启用 &ehci / &ohci（k2-32m 的 DTS 已包含）')
    else:
        print('  已关闭全部 USB 相关包')


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2
    configure(sys.argv[1] == 'enable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Register the Phicomm K2 flash-mod devices into mt7620.mk if missing.

Handles both the 16MB and 32MB flash variants.

Run from the OpenWrt source root.

Usage:
    python3 register_device.py            # 16M + 32M
    python3 register_device.py 16m        # only 16M
    python3 register_device.py 32m        # only 32M
"""
import sys

MK = 'target/linux/ramips/image/mt7620.mk'

DEVICES = {
    '16m': """define Device/phicomm_k2-16m
  SOC := mt7620a
  IMAGE_SIZE := 16064k
  DEVICE_VENDOR := Phicomm
  DEVICE_MODEL := K2
  DEVICE_VARIANT:= 16M flash mod
  DEVICE_PACKAGES := kmod-mt76x2
  SUPPORTED_DEVICES += psg1218 psg1218a phicomm,psg1218a
endef
TARGET_DEVICES += phicomm_k2-16m

""",
    '32m': """define Device/phicomm_k2-32m
  SOC := mt7620a
  IMAGE_SIZE := 32448k
  DEVICE_VENDOR := Phicomm
  DEVICE_MODEL := K2
  DEVICE_VARIANT:= 32M flash mod
  DEVICE_PACKAGES := kmod-mt76x2
  SUPPORTED_DEVICES += psg1218 psg1218a phicomm,psg1218a
endef
TARGET_DEVICES += phicomm_k2-32m

""",
}

ANCHOR = 'define Device/phicomm_k2-v22.4'


def register(key: str) -> bool:
    with open(MK, encoding='utf-8') as fh:
        src = fh.read()

    name = f'phicomm_k2-{key}'
    if name in src:
        print(f'{name}: already registered, skipping')
        return False

    if ANCHOR not in src:
        print(f'anchor not found: {ANCHOR}', file=sys.stderr)
        raise SystemExit(1)

    src = src.replace(ANCHOR, DEVICES[key] + ANCHOR, 1)
    with open(MK, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print(f'{name}: registered')
    return True


def main() -> int:
    keys = sys.argv[1:] or ['16m', '32m']
    for k in keys:
        if k not in DEVICES:
            print(f'unknown device: {k}', file=sys.stderr)
            return 2
        register(k)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

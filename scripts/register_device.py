#!/usr/bin/env python3
"""Register the Phicomm K2 16M flash mod device into mt7620.mk if missing."""
import sys

MK = 'target/linux/ramips/image/mt7620.mk'

BLOCK = """define Device/phicomm_k2-16m
  SOC := mt7620a
  IMAGE_SIZE := 16064k
  DEVICE_VENDOR := Phicomm
  DEVICE_MODEL := K2
  DEVICE_VARIANT:= 16M flash mod
  DEVICE_PACKAGES := kmod-mt76x2 kmod-usb2 kmod-usb-ohci kmod-usb-storage block-mount
  SUPPORTED_DEVICES += psg1218 psg1218a phicomm,psg1218a
endef
TARGET_DEVICES += phicomm_k2-16m

"""


def main() -> int:
    with open(MK, encoding='utf-8') as fh:
        src = fh.read()

    if 'phicomm_k2-16m' in src:
        print('already registered, skipping')
        return 0

    anchor = 'define Device/phicomm_k2-v22.4'
    if anchor not in src:
        print(f'anchor not found: {anchor}', file=sys.stderr)
        return 1

    with open(MK, 'w', encoding='utf-8') as fh:
        fh.write(src.replace(anchor, BLOCK + anchor, 1))

    print('registered phicomm_k2-16m')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

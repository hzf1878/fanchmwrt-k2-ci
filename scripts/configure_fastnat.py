#!/usr/bin/env python3
"""Toggle the fastnat LuCI panel (HNAT / SFE acceleration UI).

The acceleration stack on this target:

  kmod-shortcut-fe        SFE 快速转发内核模块
  kmod-nf-flow            netfilter flowtable
  kmod-nft-offload        nftables offload
  luci-app-fwx-fastnat    上面的 LuCI 面板

This script only toggles the panel. The kernel modules are left to the
caller, because configure_ssrplus.py turns SFE off when TPROXY is in use --
re-enabling kmod-shortcut-fe here would silently undo that.

MT7620A has no PPE/HWNAT engine, so the "fastnat" panel on this SoC drives
the software fast path only (SFE + flowtable).

Usage:
    python3 configure_fastnat.py enable
    python3 configure_fastnat.py disable
"""
import sys

LUCIS = [
    'luci-app-fwx-fastnat',
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

    for pkg in LUCIS:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)
        cfg = set_option(cfg, f'DEFAULT_{pkg}', enable)

    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    sfe_on = 'kmod-shortcut-fe=y' in cfg
    print(f'fastnat 面板: {"启用" if enable else "关闭"}')
    print(f'  luci-app-fwx-fastnat : {"on" if enable else "off"}')
    print(f'  kmod-shortcut-fe     : {"on" if sfe_on else "off（由 keep_sfe 决定，本脚本不改）"}')
    if enable:
        print('  注意: MT7620A 无 PPE 硬件引擎，面板控制的是 SFE+flowtable 软件路径')


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2
    configure(sys.argv[1] == 'enable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

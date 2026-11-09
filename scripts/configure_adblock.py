#!/usr/bin/env python3
"""Enable/disable adblock-fast (DNS-level ad filtering) plus its LuCI UI.

DNS filtering does not intercept traffic, so it does not conflict with the
TPROXY redirection used by ssr-plus/xray -- unlike Adbyby, which grabs
port 80/443 and fights with the proxy stack.

Usage:
    python3 configure_adblock.py enable
    python3 configure_adblock.py disable
"""
import sys

PKGS = [
    'adblock-fast',
    'luci-app-adblock-fast',
]

# 运行时依赖（官方 feeds 已有，显式打开避免被 defconfig 丢弃）
DEPS = [
    'rpcd-mod-ucode',
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

    for pkg in PKGS + DEPS:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)

    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    state = 'enabled' if enable else 'disabled'
    print(f'adblock-fast: {state}')
    print(f'  service : {"adblock-fast" if enable else "-"}')
    print(f'  luci    : {"luci-app-adblock-fast" if enable else "-"}')
    print(f'  mode    : DNS 层过滤，不截获流量，与 TPROXY 无冲突')


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2
    configure(sys.argv[1] == 'enable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

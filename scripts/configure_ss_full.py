#!/usr/bin/env python3
"""Enable Shadowsocks / ShadowsocksR kernels for luci-app-ssr-plus.

Adds the two extra backends the ssr-plus UI offers beyond Xray:
  - Shadowsocks New Version  -> shadowsocks-rust
  - ShadowsocksR              -> shadowsocksr-libev

Only meaningful on k2-32m; the 16M partition cannot hold them.

Usage:
    python3 configure_ss_full.py enable
    python3 configure_ss_full.py disable
"""
import sys

# ssr-plus 的 INCLUDE 开关
INCLUDE_ON = [
    'INCLUDE_Shadowsocks_Rust_Client',
    'INCLUDE_ShadowsocksR_Libev_Client',
]

# 这些包名由 ssr-plus 的 INCLUDE 通过 DEPENDS 引入，这里显式打开以防被 defconfig 丢弃
PKGS_ON = [
    'shadowsocks-rust-sslocal',
    'shadowsocksr-libev-ssr-redir',
    'shadowsocksr-libev-ssr-local',
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

    for opt in INCLUDE_ON:
        cfg = set_option(cfg, f'PACKAGE_luci-app-ssr-plus_{opt}', enable)

    for pkg in PKGS_ON:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)

    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    state = 'enabled' if enable else 'disabled'
    print(f'ss/ssr backends: {state}')
    print(f'  Shadowsocks New Version : {"on" if enable else "off"} (shadowsocks-rust)')
    print(f'  ShadowsocksR            : {"on" if enable else "off"} (shadowsocksr-libev)')


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2
    configure(sys.argv[1] == 'enable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

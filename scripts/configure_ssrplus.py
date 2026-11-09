#!/usr/bin/env python3
"""Add helloworld feed and configure luci-app-ssr-plus with minimal INCLUDE set.

Run from the OpenWrt source root after feeds have been updated.

Usage:
    python3 configure_ssrplus.py enable
    python3 configure_ssrplus.py disable
"""
import re
import sys

FEEDS_CONF = 'feeds.conf.default'
HELLOWORLD_URL = 'https://github.com/fw876/helloworld.git'

# 只保留 xray 作为代理内核，其余全部关闭以节省空间
INCLUDE_OPTS = [
    'INCLUDE_ChinaDNS_NG',
    'INCLUDE_MosDNS',
    'INCLUDE_Http_Proxy',
    'INCLUDE_Mihomo',
    'INCLUDE_GeoData',
    'INCLUDE_Shadow_TLS',
    'INCLUDE_Kcptun',
    'INCLUDE_NaiveProxy',
    'INCLUDE_Shadowsocks_Simple_Obfs',
    'INCLUDE_Shadowsocks_V2ray_Plugin',
    'INCLUDE_ShadowsocksR_Libev_Client',
    'INCLUDE_ShadowsocksR_Libev_Server',
    'INCLUDE_Shadowsocks_Rust_Client',
    'INCLUDE_Shadowsocks_Rust_Server',
    'INCLUDE_Shadowsocks_NONE_Client',
    'INCLUDE_Shadowsocks_NONE_Server',
]

# 必须关闭的、默认会打开的选项
FORCE_OFF = INCLUDE_OPTS + ['INCLUDE_NONE_V2RAY']

# 必须打开的
FORCE_ON = ['INCLUDE_Xray']


def ensure_feed(enable: bool) -> None:
    with open(FEEDS_CONF, encoding='utf-8') as fh:
        lines = fh.read().splitlines()

    lines = [ln for ln in lines if 'fw876/helloworld' not in ln]

    if enable:
        lines.append(f'src-git helloworld {HELLOWORLD_URL}')
        print(f'feed: added helloworld')
    else:
        print('feed: removed helloworld')

    with open(FEEDS_CONF, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')


def set_option(config: str, name: str, value: bool) -> str:
    """Set CONFIG_<name> to y / not-set, removing any existing definition first."""
    key = f'CONFIG_{name}'
    out = []
    for ln in config.splitlines():
        if ln.startswith(key + '=') or ln.startswith(f'# {key} is not set'):
            continue
        out.append(ln)
    out.append(f'{key}=y' if value else f'# {key} is not set')
    return '\n'.join(out) + '\n'


def configure(enable: bool) -> None:
    with open('.config', encoding='utf-8') as fh:
        cfg = fh.read()

    # 主包
    cfg = set_option(cfg, 'PACKAGE_luci-app-ssr-plus', enable)

    # xray 内核由 openwrt/packages 的 xray-core 包提供，这里只打开 ssr-plus 的 xray 集成
    for opt in FORCE_ON:
        cfg = set_option(cfg, f'PACKAGE_luci-app-ssr-plus_{opt}', enable)

    for opt in FORCE_OFF:
        cfg = set_option(cfg, f'PACKAGE_luci-app-ssr-plus_{opt}', False)

    # 透明代理后端：选 nftables（当前固件用 firewall4）
    cfg = set_option(cfg, 'PACKAGE_luci-app-ssr-plus_Nftables_Transparent_Proxy', enable)
    cfg = set_option(cfg, 'PACKAGE_luci-app-ssr-plus_Iptables_Transparent_Proxy', False)

    # dnsmasq 与 dnsmasq-full 提供相同文件，不能共存。
    # ssr-plus 的 LUCI_DEPENDS 硬依赖 +dnsmasq-full，所以必须把 dnsmasq 换掉。
    # 同理 ip-tiny / ip-full 也冲突，ssr-plus 硬依赖 +ip-full。
    if enable:
        cfg = set_option(cfg, 'PACKAGE_dnsmasq', False)
        cfg = set_option(cfg, 'PACKAGE_dnsmasq-full', True)
        cfg = set_option(cfg, 'PACKAGE_ip-tiny', False)
        cfg = set_option(cfg, 'PACKAGE_ip-full', True)
    else:
        cfg = set_option(cfg, 'PACKAGE_dnsmasq-full', False)
        cfg = set_option(cfg, 'PACKAGE_dnsmasq', True)
        cfg = set_option(cfg, 'PACKAGE_ip-full', False)
        cfg = set_option(cfg, 'PACKAGE_ip-tiny', True)

    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    print(f'ssr-plus: {"enabled" if enable else "disabled"}')
    print(f'  INCLUDE_Xray      = {enable}')
    print(f'  other INCLUDE_*   = False')
    print(f'  dnsmasq           = {"disabled" if enable else "enabled"}')
    print(f'  dnsmasq-full      = {"enabled" if enable else "disabled"}')
    print(f'  ip-tiny           = {"disabled" if enable else "enabled"}')
    print(f'  ip-full           = {"enabled" if enable else "disabled"}')


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2
    enable = sys.argv[1] == 'enable'
    ensure_feed(enable)
    configure(enable)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

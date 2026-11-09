#!/usr/bin/env python3
"""Configure luci-app-ssr-plus with a minimal package set.

Run from the OpenWrt source root, after `./scripts/feeds install -a`.

Rationale: `feeds install -a` materialises every package from helloworld into
package/feeds/helloworld/. OpenWrt then enables a number of them by default
(mihomo, hysteria, naiveproxy, shadowsocks-rust, mosdns, chinadns-ng, ...).
On an 8/16MB flash device that alone blows the image size by several MB.
This script forces every helloworld package off except the ones ssr-plus
actually needs.

Usage:
    python3 configure_ssrplus.py enable
    python3 configure_ssrplus.py disable
"""
import sys

FEEDS_CONF = 'feeds.conf.default'
HELLOWORLD_URL = 'https://github.com/fw876/helloworld.git'

# ssr-plus 的 LUCI_DEPENDS 里写死的运行时依赖，必须打开
REQUIRED = [
    'luci-app-ssr-plus',
    'dns2tcp',
    'microsocks',
    'ipt2socks',
    'lua-neturl',
]

# ssr-plus 内部的可选 INCLUDE 项：只留 xray
INCLUDE_ON = ['INCLUDE_Xray']

INCLUDE_OFF = [
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
    'INCLUDE_NONE_V2RAY',
]

# helloworld 里其余所有包，全部显式关闭（体积杀手）
HELLOWORLD_PKGS_OFF = [
    'chinadns-ng',
    'dns2socks',
    'dns2socks-rust',
    'dnsproxy',
    'gn',
    'hysteria',
    'ipt2socks-rs',
    'mihomo',
    'mosdns',
    'naiveproxy',
    'redsocks2',
    'shadow-tls',
    'shadowsocks-libev',
    'shadowsocks-rust',
    'shadowsocksr-libev',
    'simple-obfs',
    'tcping',
    'tuic-client',
    'upx',
    'v2ray-core',
    'v2ray-plugin',
    'v2raya',
    'xray-plugin',
]

# 文件冲突对：替换者 -> 被替换者
CLASH_PAIRS = [
    ('dnsmasq', 'dnsmasq-full'),
    ('ip-tiny', 'ip-full'),
]

# SFE 会绕过 netfilter，导致 TPROXY 失效、代理不生效。
# 启用 ssr-plus 时关掉 shortcut-fe，改用 nftables flowtable 快速路径。
SFE_PKGS = [
    'kmod-shortcut-fe',
    'luci-app-fwx-fastnat',
]


def ensure_feed(enable: bool) -> None:
    with open(FEEDS_CONF, encoding='utf-8') as fh:
        lines = [ln for ln in fh.read().splitlines() if 'fw876/helloworld' not in ln]
    if enable:
        lines.append(f'src-git helloworld {HELLOWORLD_URL}')
    with open(FEEDS_CONF, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'feed: {"added" if enable else "removed"} helloworld')


def set_option(config: str, name: str, value: bool) -> str:
    key = f'CONFIG_{name}'
    out = [
        ln for ln in config.splitlines()
        if not (ln.startswith(key + '=') or ln.startswith(f'# {key} is not set'))
    ]
    out.append(f'{key}=y' if value else f'# {key} is not set')
    return '\n'.join(out) + '\n'


def configure(enable: bool, keep_sfe: bool = False) -> None:
    with open('.config', encoding='utf-8') as fh:
        cfg = fh.read()

    for pkg in REQUIRED:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)

    for opt in INCLUDE_ON:
        cfg = set_option(cfg, f'PACKAGE_luci-app-ssr-plus_{opt}', enable)

    for opt in INCLUDE_OFF:
        cfg = set_option(cfg, f'PACKAGE_luci-app-ssr-plus_{opt}', False)

    # 透明代理后端：firewall4 -> nftables
    cfg = set_option(cfg, 'PACKAGE_luci-app-ssr-plus_Nftables_Transparent_Proxy', enable)
    cfg = set_option(cfg, 'PACKAGE_luci-app-ssr-plus_Iptables_Transparent_Proxy', False)

    # helloworld 的其余包一律关闭
    for pkg in HELLOWORLD_PKGS_OFF:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', False)

    # 文件冲突：ssr-plus 依赖 full 版，必须换掉 tiny 版
    for base, full in CLASH_PAIRS:
        cfg = set_option(cfg, f'PACKAGE_{base}', not enable)
        cfg = set_option(cfg, f'PACKAGE_{full}', enable)

    # SFE 与 TPROXY 冲突：默认在启用 ssr-plus 时关闭，改用 nft flowtable。
    # 可用 keep_sfe 保留，此时需自行在 fastnat 里排除代理流量。
    # 注意 CONFIG_DEFAULT_<pkg> 是 FanchmWrt 的默认包机制，只关 CONFIG_PACKAGE_ 会被它顶回来。
    sfe_on = (not enable) or keep_sfe
    for pkg in SFE_PKGS:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', sfe_on)
        cfg = set_option(cfg, f'DEFAULT_{pkg}', sfe_on)

    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    state = 'enabled' if enable else 'disabled'
    print(f'ssr-plus: {state}')
    print(f'  required pkgs   : {", ".join(REQUIRED) if enable else "-"}')
    print(f'  INCLUDE_Xray    : {enable}')
    print(f'  other INCLUDE_* : off')
    print(f'  helloworld pkgs : {len(HELLOWORLD_PKGS_OFF)} forced off')
    print(f'  dnsmasq         : {"full" if enable else "tiny"}')
    print(f'  iproute2        : {"full" if enable else "tiny"}')
    if sfe_on:
        print('  SFE             : ON  (需自行在 fastnat 排除代理流量)')
    else:
        print('  SFE             : OFF (TPROXY 需要 netfilter)')


def main() -> int:
    args = [a for a in sys.argv[1:] if a != '--keep-sfe']
    keep_sfe = '--keep-sfe' in sys.argv

    if len(args) != 1 or args[0] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2

    enable = args[0] == 'enable'
    ensure_feed(enable)
    configure(enable, keep_sfe=keep_sfe)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

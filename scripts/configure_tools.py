#!/usr/bin/env python3
"""Toggle two groups of optional utility packages for the K2 build.

Group A -- with_tools（实用小工具）:
    luci-app-ttyd              Web 终端（不装 SSH 也能操作）
    luci-app-wol               网络唤醒
    luci-app-wifischedule      WiFi 定时开关
    luci-app-advanced-reboot   一键重启进 Breed

Group B -- with_extras（按需追加）:
    luci-app-upnp              内网端口自动映射
    luci-app-filebrowser       轻量文件管理

Usage:
    python3 configure_tools.py tools enable
    python3 configure_tools.py extras enable
    python3 configure_tools.py tools disable
"""
import sys

GROUPS = {
    'tools': [
        'luci-app-ttyd',
        'luci-app-wol',
        'luci-app-wifischedule',
        'luci-app-advanced-reboot',
    ],
    'extras': [
        'luci-app-upnp',
        'luci-app-filebrowser',
    ],
}

# 显式打开的后端包（依赖会带，但写死避免被 defconfig 丢弃）
# 注意 miniupnpd 有 iptables / nftables 两个变体，当前固件用 firewall4，
# 必须选 nftables 版，否则会出现和 ssr-plus 类似的文件冲突。
EXTRA_PKGS = {
    'tools': ['ttyd', 'etherwake', 'wifischedule'],
    'extras': ['miniupnpd-nftables', 'rpcd-mod-ucode'],
}

# miniupnpd 变体互斥
EXTRA_OFF = {
    'extras': ['miniupnpd-iptables'],
}


def set_option(config: str, name: str, value: bool) -> str:
    key = f'CONFIG_{name}'
    out = [
        ln for ln in config.splitlines()
        if not (ln.startswith(key + '=') or ln.startswith(f'# {key} is not set'))
    ]
    out.append(f'{key}=y' if value else f'# {key} is not set')
    return '\n'.join(out) + '\n'


def configure(group: str, enable: bool) -> None:
    if group not in GROUPS:
        print(f'unknown group: {group}', file=sys.stderr)
        raise SystemExit(2)

    with open('.config', encoding='utf-8') as fh:
        cfg = fh.read()

    for pkg in GROUPS[group]:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)

    for pkg in EXTRA_PKGS.get(group, []):
        cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)

    for pkg in EXTRA_OFF.get(group, []):
        cfg = set_option(cfg, f'PACKAGE_{pkg}', False)

    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    state = 'enabled' if enable else 'disabled'
    print(f'{group}: {state}')
    for pkg in GROUPS[group]:
        print(f'  {pkg}')


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[2] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2
    configure(sys.argv[1], sys.argv[2] == 'enable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

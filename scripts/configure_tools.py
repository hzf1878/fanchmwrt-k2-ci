#!/usr/bin/env python3
"""按单项开关配置 K2 固件的可选组件。

每一项都可以独立开关，互不影响：

    ttyd      Web 终端            luci-app-ttyd + ttyd
    wol       网络唤醒            luci-app-wol + etherwake
    wifischedule  WiFi 定时开关   luci-app-wifischedule + wifischedule
    advreboot 一键进 Breed        luci-app-advanced-reboot
    upnp      内网端口自动映射    luci-app-upnp + miniupnpd-nftables
    filebrowser 文件管理          luci-app-filebrowser

用法：
    python3 configure_tools.py ttyd enable
    python3 configure_tools.py upnp disable
    python3 configure_tools.py           # 查看全部项目
"""
import sys

# 每项：luci 界面包 + 后端包
ITEMS = {
    'ttyd': {
        'desc': 'Web 终端',
        'luci': ['luci-app-ttyd'],
        'pkgs': ['ttyd'],
        'off': [],
    },
    'wol': {
        'desc': '网络唤醒 WOL',
        'luci': ['luci-app-wol'],
        'pkgs': ['etherwake'],
        'off': [],
    },
    'wifischedule': {
        'desc': 'WiFi 定时开关',
        'luci': ['luci-app-wifischedule'],
        'pkgs': ['wifischedule'],
        'off': [],
    },
    'advreboot': {
        'desc': '一键重启进 Breed',
        'luci': ['luci-app-advanced-reboot'],
        'pkgs': [],
        'off': [],
    },
    'upnp': {
        'desc': 'UPnP 端口映射',
        'luci': ['luci-app-upnp'],
        # miniupnpd 有 iptables / nftables 两个变体，固件用 firewall4，
        # 必须选 nftables 版，否则会和 ssr-plus 一样出现文件冲突。
        'pkgs': ['miniupnpd-nftables', 'rpcd-mod-ucode'],
        'off': ['miniupnpd-iptables'],
    },
    'filebrowser': {
        'desc': 'FileBrowser 文件管理',
        'luci': ['luci-app-filebrowser'],
        'pkgs': [],
        'off': [],
    },
}

# 兼容旧参数名
ALIASES = {
    'tools': None,    # 展开成 4 个
    'extras': None,   # 展开成 2 个
}
LEGACY = {
    'tools': ['ttyd', 'wol', 'wifischedule', 'advreboot'],
    'extras': ['upnp', 'filebrowser'],
}


def set_option(config: str, name: str, value: bool) -> str:
    key = f'CONFIG_{name}'
    out = [
        ln for ln in config.splitlines()
        if not (ln.startswith(key + '=') or ln.startswith(f'# {key} is not set'))
    ]
    out.append(f'{key}=y' if value else f'# {key} is not set')
    return '\n'.join(out) + '\n'


def expand(name: str):
    if name in LEGACY:
        result = []
        for item in LEGACY[name]:
            result.extend(expand(item))
        return result
    if name not in ITEMS:
        return []
    return [name]


def configure(names, enable: bool) -> None:
    with open('.config', encoding='utf-8') as fh:
        cfg = fh.read()

    done = []
    for name in names:
        spec = ITEMS[name]
        for pkg in spec['luci'] + spec['pkgs']:
            cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)
        for pkg in spec['off']:
            cfg = set_option(cfg, f'PACKAGE_{pkg}', False)
        done.append(name)

    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    state = 'enabled' if enable else 'disabled'
    for name in done:
        spec = ITEMS[name]
        print(f"{name}: {state}  ({spec['desc']})")
        for pkg in spec['luci'] + spec['pkgs']:
            print(f'    {pkg}')


def main() -> int:
    if len(sys.argv) == 1:
        print('可配置项：')
        for k, v in ITEMS.items():
            print(f'  {k:12s} {v["desc"]}')
        return 0

    if len(sys.argv) != 3 or sys.argv[2] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2

    names = expand(sys.argv[1])
    if not names:
        print(f'unknown item: {sys.argv[1]}', file=sys.stderr)
        return 2

    configure(names, sys.argv[2] == 'enable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

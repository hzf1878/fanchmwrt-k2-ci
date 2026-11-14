#!/usr/bin/env python3
"""Toggle exFAT / NTFS support for the K2 firmware.

这两个文件系统只在挂了 U 盘 / 移动硬盘时才有意义，所以它们都依赖
USB 功能（with_usb）。build.yml 里会在 with_usb=false 时强制关闭，
本脚本只负责按开关值改 .config。

exFAT（约 152KB 未压缩）
    kmod-fs-exfat   内核驱动
    exfat-mkfs      mkfs.exfat
    exfat-fsck      fsck.exfat

NTFS（约 1.18MB 未压缩）
    kmod-fs-ntfs3   内核驱动，读写，比 ntfs-3g 走 FUSE 快
    ntfs-3g         提供 libntfs-3g.so.89，是下面那套工具的运行时依赖
    ntfs-3g-utils   mkntfs / ntfsfix / ntfsresize 等

用法：
    python3 configure_fs.py exfat enable
    python3 configure_fs.py ntfs disable
    python3 configure_fs.py               # 查看全部项目
"""
import sys

ITEMS = {
    'exfat': {
        'desc': 'exFAT 支持',
        'pkgs': ['kmod-fs-exfat', 'exfat-mkfs', 'exfat-fsck'],
        'size': '约 152KB',
    },
    'ntfs': {
        'desc': 'NTFS 支持',
        'pkgs': ['kmod-fs-ntfs3', 'ntfs-3g', 'ntfs-3g-utils'],
        'size': '约 1.18MB',
    },
}


def set_option(config: str, name: str, value: bool) -> str:
    key = f'CONFIG_{name}'
    out = [
        ln for ln in config.splitlines()
        if not (ln.startswith(key + '=') or ln.startswith(f'# {key} is not set'))
    ]
    out.append(f'{key}=y' if value else f'# {key} is not set')
    return '\n'.join(out) + '\n'


def configure(item: str, enable: bool) -> None:
    info = ITEMS[item]
    with open('.config', encoding='utf-8') as fh:
        cfg = fh.read()

    for pkg in info['pkgs']:
        cfg = set_option(cfg, f'PACKAGE_{pkg}', enable)

    # ntfs-3g-utils 依赖 ntfs-3g 提供的 libntfs-3g.so.89。
    # 关 NTFS 时两者一起关，开的时候也一起开（pkgs 里已包含）。
    with open('.config', 'w', encoding='utf-8') as fh:
        fh.write(cfg)

    state = 'enabled' if enable else 'disabled'
    print(f"{info['desc']}: {state}  ({info['size']})")
    print(f"  包: {', '.join(info['pkgs'])}")


def main() -> int:
    if len(sys.argv) == 1:
        print(__doc__)
        for k, v in ITEMS.items():
            print(f"  {k:<8} {v['desc']:<16} {v['size']:<10} {' + '.join(v['pkgs'])}")
        return 0

    if len(sys.argv) != 3 or sys.argv[1] not in ITEMS \
            or sys.argv[2] not in ('enable', 'disable'):
        print(__doc__, file=sys.stderr)
        return 2

    configure(sys.argv[1], sys.argv[2] == 'enable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

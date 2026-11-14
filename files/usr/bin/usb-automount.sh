#!/bin/sh
# U 盘自动挂载兜底脚本
#
# /etc/config/fstab 里已配置 uuid=6BFC-6CB2 → /mnt/sda1，
# 但 fstab 服务在开机早期运行，此时 USB 存储枚举可能尚未完成，
# 或者 exfat 模块还没加载，导致自动挂载失败。
# 这里在 rc.local 阶段再尝试一次，失败则重试。
#
# 只在 /mnt/sda1 未挂载时才动手，不干扰 block-mount 的正常流程。

set -u

DEV=/dev/sda1
MP=/mnt/sda1
TRIES=5
WAIT=4

# 已经挂上就不管
if mountpoint -q "$MP" 2>/dev/null || grep -q " $MP " /proc/mounts 2>/dev/null; then
    exit 0
fi

# 等设备枚举
i=0
while [ ! -b "$DEV" ] && [ "$i" -lt "$TRIES" ]; do
    sleep "$WAIT"
    i=$((i + 1))
done

[ -b "$DEV" ] || { logger -t usb-mount "设备 $DEV 未出现，跳过"; exit 0; }

mkdir -p "$MP"

# 按 exfat → ntfs3 → vfat 顺序尝试
for FS in exfat ntfs3 vfat; do
    modprobe "$FS" 2>/dev/null
    if mount -t "$FS" "$DEV" "$MP" 2>/dev/null; then
        logger -t usb-mount "已挂载 $DEV ($FS) → $MP"
        exit 0
    fi
done

logger -t usb-mount "挂载 $DEV 失败（已尝试 exfat/ntfs3/vfat）"
exit 0

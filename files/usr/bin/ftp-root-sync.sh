#!/bin/sh
# FTP 根目录动态跟随 U 盘
#
# 问题：vsftpd 的 local_root 是静态配置，写死 /mnt/sda1。
# 插了不同的 U 盘（匿名挂载到 /mnt/<卷标>）后，FTP 仍然指向空的 /mnt/sda1。
#
# 做法：在 vsftpd 启动前探测当前挂载的 U 盘，把 local_root 指向它。
# 通过 uci-defaults 机制写入 vsftpd 的 UCI 配置，vsftpd 的 init 脚本
# 会据此生成 /var/etc/vsftpd.conf。
#
# 用法：
#   ftp-root-sync.sh            检测并更新 local_root（有变化才写）
#   ftp-root-sync.sh -s         只显示检测结果，不写入
#
# 挂载点优先级：
#   1. /mnt/sda1（fstab 里配了 UUID 的固定盘）
#   2. 其它 /mnt/<非空目录> 里最像 U 盘的（有文件、非空）
#   3. 都不符合则保留原值不动

set -u

DRY=0
[ "${1:-}" = "-s" ] && DRY=1

log() { echo "$*"; logger -t ftp-root-sync "$*" 2>/dev/null; }

# 收集所有挂载在 /mnt/* 下的块设备
find_mounts() {
    awk '$2 ~ /^\/mnt\// { print $2 }' /proc/mounts 2>/dev/null | sort -u
}

# 判断是否是「像样的」存储（可写、非空、不是 overlay/root）
is_usable() {
    mp="$1"
    [ -d "$mp" ] || return 1
    # 排除系统挂载
    case "$mp" in
        /mnt/sda1|/mnt/mmcblk*|/mnt/usb*|/mnt/[A-Za-z0-9_-]*) : ;;
        *) return 1 ;;
    esac
    # 必须是真实块设备的挂载
    grep -q " $mp " /proc/mounts 2>/dev/null || return 1
    dev=$(awk -v m="$mp" '$2 == m { print $1 }' /proc/mounts 2>/dev/null | head -1)
    case "$dev" in
        /dev/sd*|/dev/mmcblk*|/dev/ubi*) : ;;
        *) return 1 ;;
    esac
    # 可写
    [ -w "$mp" ] || return 1
    return 0
}

MOUNTS=$(find_mounts)

if [ -z "$MOUNTS" ]; then
    log "没有挂载任何 /mnt 下的设备，保留原配置"
    exit 0
fi

# 优先 /mnt/sda1
PICK=""
for m in $MOUNTS; do
    if [ "$m" = "/mnt/sda1" ] && is_usable "$m"; then
        PICK="$m"
        break
    fi
done

# 其次挑第一个可用的
if [ -z "$PICK" ]; then
    for m in $MOUNTS; do
        if is_usable "$m"; then
            PICK="$m"
            break
        fi
    done
fi

if [ -z "$PICK" ]; then
    log "所有 /mnt 挂载都不可用，保留原配置"
    exit 0
fi

CUR=$(uci get vsftpd.global.local_root 2>/dev/null || echo "")

if [ "$PICK" = "$CUR" ]; then
    log "local_root 已是 $PICK，无需改动"
    exit 0
fi

log "FTP 根目录: ${CUR:-未设置} → $PICK"

if [ "$DRY" -eq 1 ]; then
    exit 0
fi

uci set vsftpd.global.local_root="$PICK"
uci commit vsftpd

# 同步更新 FTP 用户的 home（vsftpd 用它做 chroot 参考）
USER_NAME=$(head -1 /etc/vsftpd.users 2>/dev/null | tr -d ' \r\n')
if [ -n "$USER_NAME" ] && id "$USER_NAME" >/dev/null 2>&1; then
    sed -i "s|^\(${USER_NAME}:[^:]*:[^:]*:[^:]*:[^:]*:\)[^:]*:|\1${PICK}:|" /etc/passwd
    log "已更新 $USER_NAME 的 home 为 $PICK"
fi

if /etc/init.d/vsftpd running 2>/dev/null; then
    /etc/init.d/vsftpd restart >/dev/null 2>&1 && log "vsftpd 已重启"
fi

exit 0

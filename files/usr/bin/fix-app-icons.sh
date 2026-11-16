#!/bin/sh
# 恢复特征库应用图标（app_icons）
#
# 背景：
#   特征库的应用图标不是固件自带的，而是随特征库包一起从
#   api.openappfilter.com 下载的。包是 tar.gz，内含 feature.bin
#   和 app_icons/*.png。fwxd 更新时会把 app_icons 拷到
#   /www/luci-static/resources/app_icons/。
#
#   如果该目录被清空（例如清理 overlay 空间时误删），
#   特征库页面就只剩首字母方块，没有图标。
#
# 用法：
#   fix-app-icons.sh              从网络下载当前在用的特征库并安装图标
#   fix-app-icons.sh -f FILE      从本地 tar.gz 包安装（离线）
#   fix-app-icons.sh -l           只列出，不安装
#
# 依赖：curl、tar、ubus

set -u

API="https://api.openappfilter.com/api"
DST="/www/luci-static/resources/app_icons"
WORK="/tmp/fix_app_icons"
METHOD="online"
LOCAL_PKG=""

while [ $# -gt 0 ]; do
    case "$1" in
        -f) LOCAL_PKG="${2:-}"; METHOD="local"; shift 2 ;;
        -l) METHOD="list"; shift ;;
        -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "未知参数: $1" >&2; exit 2 ;;
    esac
done

log() { echo "[$(date +%H:%M:%S)] $*"; }

# 读 device_id 和版本
CONF=$(ubus call fwx common '{"CopyRight":"www.fanchmwrt.com","api":"get_feature_online_config","data":{}}' 2>/dev/null)
DEVICE_ID=$(echo "$CONF" | sed -n 's/.*"device_id": *"\([a-f0-9]*\)".*/\1/p')
VERSION=$(echo "$CONF" | sed -n 's/.*"version": *"\(v[0-9.]*\)".*/\1/p')
[ -n "$VERSION" ] || VERSION="v4.0"

if [ -z "$DEVICE_ID" ]; then
    log "错误：取不到 device_id，fwxd 没在跑？"
    exit 1
fi
log "device_id=$DEVICE_ID  version=$VERSION"

# 拉在线列表
LIST=$(curl -s -m 30 "$API/get_feature_list?device_id=$DEVICE_ID&lang=cn&version=$VERSION" 2>/dev/null)
if ! echo "$LIST" | grep -q '"code": *20000'; then
    log "错误：拉取特征库列表失败"
    echo "$LIST" | head -c 200
    exit 1
fi

if [ "$METHOD" = "list" ]; then
    log "可用特征库："
    echo "$LIST" | tr ',' '\n' | grep -E '"(id|version|count|free)"' | paste - - - - 2>/dev/null || echo "$LIST"
    exit 0
fi

# 找当前在用的特征库 id 和 md5：优先用本地已装的 feature.bin 大小匹配
# 简单起见，取列表里第一个 free=1 的（免费版），否则取第一个
PICK=$(echo "$LIST" | sed 's/},{/}\n{/g' | grep '"free": *1' | head -1)
[ -n "$PICK" ] || PICK=$(echo "$LIST" | sed 's/},{/}\n{/g' | head -1)

ID=$(echo "$PICK" | sed -n 's/.*"id": *\([0-9]*\).*/\1/p')
MD5=$(echo "$PICK" | sed -n 's/.*"md5": *"\([a-f0-9]*\)".*/\1/p')
VER=$(echo "$PICK" | sed -n 's/.*"version": *"\([^"]*\)".*/\1/p')
CNT=$(echo "$PICK" | sed -n 's/.*"count": *\([0-9]*\).*/\1/p')
log "选中特征库: id=$ID version=$VER count=$CNT"

rm -rf "$WORK"
mkdir -p "$WORK"
PKG="$WORK/feature.pkg"

if [ "$METHOD" = "local" ]; then
    [ -f "$LOCAL_PKG" ] || { log "错误：本地包不存在: $LOCAL_PKG"; exit 1; }
    log "使用本地包: $LOCAL_PKG"
    cp "$LOCAL_PKG" "$PKG"
else
    URL="$API/download_feature?id=$ID&device_id=$DEVICE_ID&lang=cn&version=$VERSION"
    [ -n "$MD5" ] && URL="$URL&md5=$MD5"
    log "下载中..."
    curl -s -m 300 -o "$PKG" "$URL" 2>/dev/null
    SZ=$(wc -c < "$PKG" 2>/dev/null || echo 0)
    log "下载完成: $SZ 字节"
    if [ "$SZ" -lt 100000 ]; then
        log "错误：包太小（$SZ 字节），可能下载失败"
        head -c 200 "$PKG"
        exit 1
    fi
fi

# 解压
log "解压..."
cd "$WORK" || exit 1
if ! tar -xzf "$PKG" 2>/dev/null; then
    log "错误：解压失败，不是有效的 tar.gz"
    exit 1
fi

N=$(ls app_icons/*.png 2>/dev/null | wc -l)
log "包内图标数: $N"
if [ "$N" -eq 0 ]; then
    log "错误：包里没有图标"
    exit 1
fi

# 安装
log "安装到 $DST ..."
mkdir -p "$DST"
rm -rf "$DST"/*
cp -r app_icons/. "$DST"/

FINAL=$(ls "$DST" 2>/dev/null | wc -l)
log "完成：$DST 现有 $FINAL 个文件"
du -sh "$DST" 2>/dev/null

# 备份包到 U 盘（如果 U 盘挂着）
if mountpoint -q /mnt/sda1 2>/dev/null || grep -q " /mnt/sda1 " /proc/mounts 2>/dev/null; then
    cp "$PKG" "/mnt/sda1/feature_${ID}.pkg" 2>/dev/null && \
        log "已备份到 /mnt/sda1/feature_${ID}.pkg"
fi

rm -rf "$WORK"
log "全部完成。刷新浏览器（Ctrl+F5）查看图标。"

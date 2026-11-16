#!/bin/sh
# fwxd 特征库下载不完整时的兜底修复
#
# 问题：
#   fwxd 用 libcurl 下载特征库包（约 2.2MB），在 K2 这种慢速设备上
#   偶发下载不完整（实测停在 2.01MB / 2.22MB）。此时 tar -zxf 解压失败，
#   fwxd 把 icons_skipped 置 1 但整体仍返回 success，
#   结果 /www/luci-static/resources/app_icons 被清空且没有新图标。
#
#   这个脚本用 curl 重试下载并做完整性校验（tar -tzf + 文件数），
#   校验通过才安装，失败则保留原图标不动。
#
# 用法：
#   ensure-app-icons.sh            # 后缀没有图标时才修复
#   ensure-app-icons.sh -f         # 强制重装
#
# 建议放 rc.local 或 cron 里，开机/定时自愈。

set -u

API="https://api.openappfilter.com/api"
DST="/www/luci-static/resources/app_icons"
WORK="/tmp/ensure_icons"
MIN_ICONS=100          # 少于这个数认为异常
FORCE=0
[ "${1:-}" = "-f" ] && FORCE=1

log() { logger -t ensure-app-icons "$*"; echo "$*"; }

CUR=$(ls "$DST" 2>/dev/null | wc -l)
if [ "$FORCE" -eq 0 ] && [ "$CUR" -ge "$MIN_ICONS" ]; then
    exit 0
fi

log "图标数 $CUR < $MIN_ICONS，开始修复"

CONF=$(ubus call fwx common '{"CopyRight":"www.fanchmwrt.com","api":"get_feature_online_config","data":{}}' 2>/dev/null)
DEVICE_ID=$(echo "$CONF" | sed -n 's/.*"device_id": *"\([a-f0-9]*\)".*/\1/p')
VERSION=$(echo "$CONF" | sed -n 's/.*"version": *"\(v[0-9.]*\)".*/\1/p')
[ -n "$VERSION" ] || VERSION="v4.0"
[ -n "$DEVICE_ID" ] || { log "取不到 device_id，放弃"; exit 1; }

LIST=$(curl -s -m 30 "$API/get_feature_list?device_id=$DEVICE_ID&lang=cn&version=$VERSION" 2>/dev/null)
echo "$LIST" | grep -q '"code": *20000' || { log "拉列表失败，放弃"; exit 1; }

PICK=$(echo "$LIST" | sed 's/},{/}\n{/g' | grep '"free": *1' | head -1)
[ -n "$PICK" ] || PICK=$(echo "$LIST" | sed 's/},{/}\n{/g' | head -1)
ID=$(echo "$PICK" | sed -n 's/.*"id": *\([0-9]*\).*/\1/p')
MD5=$(echo "$PICK" | sed -n 's/.*"md5": *"\([a-f0-9]*\)".*/\1/p')

rm -rf "$WORK"; mkdir -p "$WORK"
PKG="$WORK/pkg.bin"
URL="$API/download_feature?id=$ID&device_id=$DEVICE_ID&lang=cn&version=$VERSION"
[ -n "$MD5" ] && URL="$URL&md5=$MD5"

# 重试下载，最多 3 次，每次校验是否能完整列出 tar
OK=0
for try in 1 2 3; do
    log "下载尝试 $try/3 (id=$ID)"
    rm -f "$PKG"
    curl -s -m 300 --retry 2 --retry-delay 3 -o "$PKG" "$URL" 2>/dev/null
    SZ=$(wc -c < "$PKG" 2>/dev/null || echo 0)
    log "  下载 $SZ 字节"
    if [ "$SZ" -lt 100000 ]; then
        log "  太小，重试"
        continue
    fi
    # 完整性校验：能完整列出且含 app_icons
    N=$(tar -ztf "$PKG" 2>/dev/null | grep -c 'app_icons/.*\.png$')
    if [ "$N" -ge "$MIN_ICONS" ]; then
        log "  校验通过：$N 个图标"
        OK=1
        break
    fi
    log "  校验失败：只列出 $N 个图标，包不完整，重试"
done

[ "$OK" -eq 1 ] || { log "3 次都失败，保留原图标不动"; rm -rf "$WORK"; exit 1; }

# 解压并原子替换
cd "$WORK" || exit 1
tar -xzf "$PKG" 2>/dev/null || { log "解压失败"; rm -rf "$WORK"; exit 1; }
NEW=$(ls app_icons/*.png 2>/dev/null | wc -l)
[ "$NEW" -ge "$MIN_ICONS" ] || { log "解压后只有 $NEW 个，放弃"; rm -rf "$WORK"; exit 1; }

TMPDST="$DST.new"
rm -rf "$TMPDST"; mkdir -p "$TMPDST"
cp -r app_icons/. "$TMPDST"/
rm -rf "$DST"
mv "$TMPDST" "$DST"
log "已安装 $NEW 个图标到 $DST"

# 备份到 U 盘
if grep -q " /mnt/sda1 " /proc/mounts 2>/dev/null; then
    cp "$PKG" "/mnt/sda1/feature_${ID}.pkg" 2>/dev/null && log "已备份到 U 盘"
fi

rm -rf "$WORK"
exit 0

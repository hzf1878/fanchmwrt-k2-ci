#!/bin/sh
# 重建 ssr-plus 依赖检查所需的占位文件
#
# 背景：/etc/init.d/shadowsocksr 用文件存在性判断透明代理依赖是否就绪：
#     file_path="/usr/lib/opkg/info";  file_ext=".control"
#     [ -d "/lib/apk/packages" ] && { file_path="/lib/apk/packages"; file_ext=".list"; }
#     for pkg in kmod-nft-socket kmod-nft-tproxy kmod-nft-nat; do
#         [ -s "${file_path}/${pkg}${file_ext}" ] || echo "警告：缺失依赖 $pkg"
#     done
#
# 但 25.12 用 apk 做包管理器，既没有 /lib/apk/packages 目录，
# /lib/apk/db 也是空的，于是脚本退回 opkg 路径，而 opkg 的 info
# 目录里同样没有这几个文件 —— 明明内核模块已加载，却一直报缺失。
#
# 这个脚本按实际内核模块是否存在来生成占位文件，模块真不存在就
# 不生成（保持警告），避免掩盖真实问题。

set -u

INFO_DIR=/usr/lib/opkg/info
APK_PKGS=/lib/apk/packages
MODDIR=/lib/modules/$(uname -r)

# 与 init 脚本里的 nftables 分支保持一致
PKGS="kmod-nft-socket kmod-nft-tproxy kmod-nft-nat"

# 模块文件名映射（下划线形式）
mod_name() {
    echo "$1" | sed 's/^kmod-//; s/-/_/g'
}

created=0

for pkg in $PKGS; do
    mod="$(mod_name "$pkg")"

    # 模块文件不在就直接跳过，让 ssr-plus 继续报警——说明是真缺
    if [ ! -f "$MODDIR/$mod.ko" ] && [ ! -f "$MODDIR/$mod.ko.gz" ] \
       && [ ! -f "$MODDIR/$mod.ko.xz" ]; then
        continue
    fi

    # opkg 路径（当前固件用的是这个）
    mkdir -p "$INFO_DIR"
    f="$INFO_DIR/$pkg.control"
    if [ ! -s "$f" ]; then
        printf 'Package: %s\nVersion: local\nDepends: kernel\nStatus: install user installed\nArchitecture: all\nDescription: placeholder for ssr-plus dependency check\n' \
            "$pkg" > "$f"
        created=$((created + 1))
    fi

    # apk 路径（未来若出现 /lib/apk/packages 就一并覆盖）
    if [ -d "$APK_PKGS" ]; then
        l="$APK_PKGS/$pkg.list"
        if [ ! -s "$l" ]; then
            printf '/lib/modules/%s/%s.ko\n' "$(uname -r)" "$mod" > "$l"
            created=$((created + 1))
        fi
    fi
done

[ "$created" -gt 0 ] && logger -t ssr-dep-fix "重建 $created 个占位依赖文件"

exit 0

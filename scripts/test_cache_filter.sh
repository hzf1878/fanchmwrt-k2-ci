#!/bin/sh
# 模拟 clear-cache.yml 的 key 匹配逻辑，验证不会误删/漏删
set -eu

# 模拟缓存 key 列表（真实格式：<type>-<device>-<confighash>）
KEYS="dl-k2-16m-a1b2c3d4e5f60718
dl-k2-8m-1122334455667788
ccache-k2-16m-a1b2c3d4e5f60718
ccache-k2-8m-1122334455667788
dl-k2-16m-9999999999999999
some-other-cache-key"

run_case() {
    DEVICE="$1"
    CTYPE="$2"

    case "$CTYPE" in
        dl)     PREFIXES="dl-" ;;
        ccache) PREFIXES="ccache-" ;;
        all)    PREFIXES="dl- ccache-" ;;
    esac

    echo "--- 设备=$DEVICE  类型=$CTYPE ---"
    for PREFIX in $PREFIXES; do
        if [ "$DEVICE" = "all" ]; then
            EXPECT_PREFIX="$PREFIX"
        else
            EXPECT_PREFIX="${PREFIX}${DEVICE}-"
        fi
        printf '%s\n' "$KEYS" | while IFS= read -r KEY; do
            case "$KEY" in
                "$EXPECT_PREFIX"*) echo "  删除  $KEY" ;;
            esac
        done
    done
    printf '%s\n' "$KEYS" | while IFS= read -r KEY; do
        MATCH=0
        for PREFIX in $PREFIXES; do
            if [ "$DEVICE" = "all" ]; then EP="$PREFIX"; else EP="${PREFIX}${DEVICE}-"; fi
            case "$KEY" in "$EP"*) MATCH=1 ;; esac
        done
        [ "$MATCH" = "0" ] && echo "  保留  $KEY"
    done
    echo
}

run_case all all
run_case k2-16m all
run_case k2-16m dl
run_case k2-8m ccache

#!/bin/sh
# 复现 build.yml 中 Resolve build parameters 的开关解析逻辑
set -eu

resolve() {
    INPUT_USE_CACHE="$1"   # 空串代表未提供
    INPUT_USE_CCACHE="$2"

    USE_CACHE="$INPUT_USE_CACHE"
    [ -z "$USE_CACHE" ] && USE_CACHE="true"

    USE_CCACHE="$INPUT_USE_CCACHE"
    [ -z "$USE_CCACHE" ] && USE_CCACHE="$USE_CACHE"

    [ "$USE_CACHE" != "true" ] && USE_CCACHE="false"

    if [ "$USE_CACHE" = "true" ]; then USE_DL="true"; else USE_DL="false"; fi

    printf 'use_cache=%-6s use_dl=%-6s use_ccache=%-6s\n' \
        "$USE_CACHE" "$USE_DL" "$USE_CCACHE"
}

echo "输入(use_cache, use_ccache)          -> 解析结果"
echo "--------------------------------------------------------------"
printf '   未提供,    未提供     -> '; resolve "" ""
printf '   true,      true       -> '; resolve "true" "true"
printf '   true,      false      -> '; resolve "true" "false"
printf '   false,     true       -> '; resolve "false" "true"
printf '   false,     false      -> '; resolve "false" "false"

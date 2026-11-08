#!/bin/sh
# 复现 build.yml 中 with_xray 的解析逻辑
set -eu

resolve() {
    DEVICE="$1"
    INPUT="$2"   # 空串代表未提供

    WITH_XRAY="$INPUT"
    [ -z "$WITH_XRAY" ] && WITH_XRAY="false"

    WARN=""
    if [ "$WITH_XRAY" = "true" ] && [ "$DEVICE" = "k2-8m" ]; then
        WARN=" [已强制关闭: 8M 空间不足]"
        WITH_XRAY="false"
    fi

    printf '%-10s %-10s -> with_xray=%-6s%s\n' "$DEVICE" "${INPUT:-未提供}" "$WITH_XRAY" "$WARN"
}

echo "device     with_xray  -> 结果"
echo "--------------------------------------------------------------"
resolve k2-16m ""
resolve k2-16m "true"
resolve k2-16m "false"
resolve k2-8m  ""
resolve k2-8m  "true"
resolve k2-8m  "false"

echo
echo "=== 产物命名 ==="
for pair in "k2-16m true" "k2-16m false" "k2-8m true" "k2-8m false"; do
    set -- $pair
    if [ "$2" = "true" ]; then SUF="-xray"; else SUF=""; fi
    echo "  FanchmWrt-K2-$1$SUF"
done

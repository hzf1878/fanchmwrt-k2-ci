#!/bin/sh
# K2 WAN 口修复脚本
# 用法：ssh 或 ttyd 里执行  sh /tmp/fix_wan.sh
# 或者在 LuCI 的系统→终端 里粘贴

echo "=== 1. 查看当前网络配置 ==="
uci show network | grep -E "interface|switch" | head -30

echo ""
echo "=== 2. 查看交换机状态 ==="
swconfig dev switch0 show 2>/dev/null | head -20

echo ""
echo "=== 3. 重建 WAN 接口 ==="
# 删除已有 wan（如果存在但配置错误）
uci -q delete network.wan
uci -q delete network.wan6

# 创建 wan（DHCP 客户端，对应 switch 端口 4）
uci set network.wan=interface
uci set network.wan.proto='dhcp'
uci set network.wan.device='eth0.2'
uci set network.wan.ifname='eth0.2'

# 确认 lan 包含 switch0
uci set network.lan.device='br-lan'

# 创建 wan6（可选，IPv6）
uci set network.wan6=interface
uci set network.wan6.proto='dhcpv6'
uci set network.wan6.device='eth0.2'
uci set network.wan6.ifname='eth0.2'

# VLAN 配置：eth0.1=lan, eth0.2=wan
uci -q delete network.@switch_vlan[0]
uci -q delete network.@switch_vlan[1]

uci add network switch_vlan
uci set network.@switch_vlan[-1].device='switch0'
uci set network.@switch_vlan[-1].vlan='1'
uci set network.@switch_vlan[-1].ports='0 1 2 3 6t'

uci add network switch_vlan
uci set network.@switch_vlan[-1].device='switch0'
uci set network.@switch_vlan[-1].vlan='2'
uci set network.@switch_vlan[-1].ports='4 6t'

uci commit network

echo ""
echo "=== 4. 重启网络 ==="
/etc/init.d/network restart

echo ""
echo "=== 5. 验证 ==="
sleep 3
ip addr show | grep -E "^[0-9]+:|inet "
echo ""
echo "--- WAN 状态 ---"
ubus call network.interface.wan status 2>/dev/null | head -20

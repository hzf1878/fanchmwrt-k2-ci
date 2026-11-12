# FanchmWrt K2 云编译

斐讯 K2（MT7620A + MT7612E）的 FanchmWrt 固件云端编译配置，基于上游
[fanchmwrt/fanchmwrt](https://github.com/fanchmwrt/fanchmwrt) 源码
（分支 `fanchmwrt-25.12.6`）。

本仓库只存放**编译配置、补丁和 workflow**，不含源码。每次编译从上游拉取，
本地 12GB 的源码树不进仓库。

## Fork 使用

1. 点右上角 **Fork** → **Create fork**
2. 进入你自己的 fork → **Settings → Actions → General**
3. 选择 **Allow all actions and reusable workflows**，点 **Save**
   （fork 出来的仓库 Actions 默认关闭，不开启的话看不到 Run workflow 按钮）
4. 进入 **Actions** → **编译斐讯 K2 固件** → **Run workflow**

注意：fork 后缓存为空，第一次编译是冷启动（约 85 分钟），第二次起才会快。

## 支持的设备

| 配置 | 设备 | Flash | 芯片 | 可写区 |
|---|---|---|---|---|
| `k2-8m` | Phicomm K2 v22.4 or older | 8MB | 原装 W25Q64 | 约 320KB |
| `k2-16m` | Phicomm K2 (16M flash mod) | 16MB | W25Q128 | 约 4.7MB |
| `k2-32m` | Phicomm K2 (32M flash mod) | 32MB | W25Q256 | 约 20.7MB |

16M / 32M 是换芯片后的自定义变体，需要改分区表，对应 DTS 见 `patches/`。
前提是使用 **Breed** 作为 bootloader —— 原厂 U-Boot 对大容量芯片支持不可靠。

## 编译参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `device` | `k2-8m` | 目标设备：`k2-8m` / `k2-16m` / `k2-32m` |
| `use_cache` | 开 | dl 源码包 + ccache 总开关，省约 55 分钟 |
| `use_ccache` | 开 | 单独控制 ccache（依赖 use_cache） |
| `with_xray` | 关 | 加入 xray-core（trojan/VMess/VLESS/SS，约 3.5MB） |
| `with_ssrplus` | 关 | 加入 luci-app-ssr-plus 图形界面（约 9MB） |
| `with_ss_full` | 关 | 额外加入 SS/SSR 内核（约 7MB，仅 32M） |
| `keep_sfe` | 关 | 保留 SFE 加速。与 TPROXY 冲突且无法排除，跑代理必须关闭 |
| `with_hnat` | 关 | 加入 fastnat 加速面板（软件快速路径） |
| `with_ttyd` | 关 | Web 终端 ttyd（约 470KB） |
| `with_wol` | 关 | 网络唤醒 WOL（约 18KB） |
| `with_wifischedule` | 关 | WiFi 定时开关（约 6KB） |
| `with_advreboot` | 关 | 一键重启进 Breed（免按复位键，约 13KB） |
| `with_upnp` | 关 | UPnP 端口自动映射（约 160KB） |
| `with_filebrowser` | 关 | FileBrowser 文件管理（仅界面，约 1KB，无二进制） |
| `with_usb` | 关 | 启用 USB 2.0（仅限焊接了 USB 口的改装机，约 1MB） |

### 自动联动规则

这些规则在参数解析阶段自动执行，无需手动处理：

```
with_ssrplus=true, with_xray=false   → 自动开启 with_xray（ssr-plus 需要内核）
with_ss_full=true, with_ssrplus=false → 自动关闭 with_ss_full（内核脱离界面无意义）
with_ss_full=true, device≠k2-32m      → 强制关闭（7MB 放不下）
with_ssrplus=true, device=k2-16m      → 强制关闭 with_ssrplus 和 with_xray（见空间限制）
with_ttyd/wol/wifischedule/advreboot/upnp/filebrowser=true, device=k2-8m
                                       → 强制关闭（可写区仅 320KB）
with_usb=true, device≠k2-32m         → 强制关闭（仅 k2-32m 的 DTS 启用 ehci/ohci）
```

### 各设备功能可用性

| 参数 | `k2-8m` | `k2-16m` | `k2-32m` |
|---|---|---|---|
| `use_cache` | ✅ | ✅ | ✅ |
| `use_ccache` | ✅ | ✅ | ✅ |
| `with_hnat` | ✅ | ✅ | ✅ |
| `keep_sfe` | ✅ | ✅ | ✅ |
| `with_xray` | ❌ 强制关闭 | ⚠️ 可用（余约 1.2MB） | ✅ 可用 |
| `with_ttyd` | ❌ 强制关闭 | ✅ 可用（470KB） | ✅ 可用 |
| `with_wol` | ❌ 强制关闭 | ✅ 可用（18KB） | ✅ 可用 |
| `with_wifischedule` | ❌ 强制关闭 | ✅ 可用（6KB） | ✅ 可用 |
| `with_advreboot` | ❌ 强制关闭 | ✅ 可用（13KB） | ✅ 可用 |
| `with_upnp` | ❌ 强制关闭 | ⚠️ 可用（160KB） | ✅ 可用 |
| `with_filebrowser` | ❌ 强制关闭 | ✅ 可用（1KB） | ✅ 可用 |
| `with_usb` | ❌ 强制关闭 | ❌ 强制关闭 | ✅ 可用（需改装硬件） |
| `with_ssrplus` | ❌ 强制关闭 | ❌ 强制关闭（超 4.8MB） | ✅ 可用 |
| `with_ss_full` | ❌ 强制关闭 | ❌ 强制关闭 | ✅ 可用 |

图例：✅ 可用　⚠️ 可用但余量紧张　❌ 会被自动关闭

**`k2-16m` 上的降级顺序**（超限时按体积从大到小依次放弃）：

```
① 关 with_xray（3.5MB）
② 关 with_ttyd（470KB）
③ 关 with_upnp（160KB）
```

每次降级都会在日志里输出 `::warning`，说明关了哪项、原本会超多少。
勾了 `with_ssrplus` 则直接关闭 xray 和 ssr-plus 两项（见上文）。

### 各设备推荐配置

| 用途 | `k2-8m` | `k2-16m` | `k2-32m` |
|---|---|---|---|
| 纯路由（最快） | 默认即可 | 默认即可 | 默认即可 |
| 加 Web 终端 | — | + `with_ttyd` | + `with_ttyd` |
| 加常用工具 | — | + `with_ttyd` + `with_wol` + `with_advreboot` | 同左 |
| 跑 trojan | — | + `with_xray`（keep_sfe 保持默认关闭） | + `with_xray` + `with_ssrplus` |
| 全功能 | — | 放不下 | 全部勾选约 27.9MB（分区 31.7MB，余 3.75MB） |

## 空间限制（实测数据）

| 设备 | firmware 分区 | 空固件镜像 | 剩余可写区 |
|---|---|---|---|
| `k2-8m` | 7.87 MB | 7.34 MB | **约 0.32 MB** |
| `k2-16m` | 15.69 MB | 10.94 MB | **约 4.75 MB** |
| `k2-32m` | 31.69 MB | 10.94 MB | **约 20.75 MB** |

### 各功能的空间开销（实测）

| 组合 | 镜像增量 | 总镜像 | 16M 可行 |
|---|---|---|---|
| 基础固件 | — | 10.94 MB | ✅ 余 4.75MB |
| + `with_xray` | 约 3.5 MB | 约 14.4 MB | ✅ 余约 1.2MB |
| + `with_ssrplus` | 再 +5.9 MB | **20.3 MB** | ❌ **超 4.8MB** |
| + `with_ss_full` | 再 +7 MB | 约 27 MB | ❌ 仅 32M |

**关键结论**：

- `with_ssrplus` **只能在 `k2-32m` 上使用**。16M 上编出来的镜像超限，
  `make` 会丢弃 `squashfs-sysupgrade.bin`，产物里只剩 `initramfs-kernel.bin`
  —— 那个不能刷进 flash。
- 在 `k2-16m` 上勾选 `with_ssrplus` 会**自动关闭 xray 和 ssr-plus 两项**，
  编出的是基础固件，不会给你不可刷的残包。
- 想用图形代理界面，只能换 32MB 芯片。

## 加速功能说明

固件里有两套 offload 机制，都容易和代理冲突：

| 模块 | 名称 | 机制 | 与代理冲突 |
|---|---|---|---|
| `kmod-shortcut-fe` | **SFE** | 独立快捷通道，绕过 netfilter | **会冲突** |
| `kmod-nf-flow` + `kmod-nft-offload` | flowtable | nftables 原生 flow 表 | **同样会冲突** |

**这两条路径都会绕过 netfilter 的转发链**，TPROXY 建立的重定向收不到后续数据包，
表现为"能连上但卡住"或"部分站点打不开"。区别只是 SFE 更激进。

因此 `keep_sfe` 的取舍：

| 场景 | keep_sfe | flowtable |
|---|---|---|
| 跑代理（默认） | **false** | **必须关闭** |
| 纯路由，要满速 | true（需接受代理不工作） | 可开 |

**关于 fastnat 面板的"排除代理流量"**

面板上没有这个功能，也没有办法实现：SFE 模块（`shortcut-fe-cm.ko`）的排除条件
全部是内核内部状态判定（广播/组播、无 conntrack、ALG、TCP 未建立、LOCAL_OUT、
FWX_APPID 等），没有暴露任何按端口、mark 或接口筛选的用户可配开关。
sysfs 只提供 `/sys/sfe_cm/enabled` 一个总开关。

所以"两者都要"做不到。要跑代理就必须关掉 offload，没有折中方案。

关闭方法：

```sh
# SFE
uci set fastnat.global.enabled='0'
uci commit fastnat
/etc/init.d/fastnat stop

# flowtable（若曾开启）
uci set firewall.@defaults[0].flow_offloading='0'
uci commit firewall
/etc/init.d/firewall restart
```

**性能影响对 K2 可忽略**：MT7620A 关掉 offload 后 CPU 转发仍有 300–400Mbps，
高于百兆网口上限，也高于这台机器无线中继的实际带宽。

### 关于 MT7620A 的"HWNAT"

**这颗 SoC 没有 PPE 硬件加速单元**。fastnat 面板里那些"硬件加速"选项在 K2
上不会产生硬件效果，实际起作用的是软件实现的 SFE 和 flowtable。

真正的 HWNAT 出现在 MT7621 / MT7622 / MT7981 等芯片上。

## 目录结构

```
.github/workflows/build.yml          编译工作流
.github/workflows/clear-cache.yml    清理编译缓存（按设备/类型筛选）
.github/workflows/cleanup.yml        综合清理（缓存/产物/运行记录，含定时任务）

config/k2-8m.config                  8MB flash 编译配置
config/k2-16m.config                 16MB flash 编译配置
config/k2-32m.config                 32MB flash 编译配置

patches/mt7620a_phicomm_k2-16m.dts   16M 分区表设备树
patches/mt7620a_phicomm_k2-32m.dts   32M 分区表设备树

scripts/register_device.py           注册 16M/32M 设备到 mt7620.mk（幂等）
scripts/configure_ssrplus.py         ssr-plus 开关、helloworld feed、SFE 取舍
scripts/configure_ss_full.py         SS/SSR 内核（必须在 ssrplus 之后执行）
scripts/configure_fastnat.py         fastnat 面板（只控界面，不碰内核模块）
scripts/configure_tools.py           可选组件逐项开关（ttyd/wol/wifischedule/
                                     advreboot/upnp/filebrowser）
scripts/configure_usb.py             USB 2.0 支持（仅改装机）

scripts/test_cache_filter.sh         缓存清理过滤逻辑自测
scripts/test_cache_switches.sh       缓存开关逻辑自测
scripts/test_xray_switch.sh          xray 开关逻辑自测
```

## 自定义内容说明

上游源码不含 K2 的大容量变体，本仓库通过以下改动实现：

1. **DTS**：firmware 分区扩展
   - 16M：`0x50000 0x7b0000` → `0x50000 0xfb0000`
   - 32M：`0x50000 0x7b0000` → `0x50000 0x1fb0000`
2. **设备定义**：`register_device.py` 在 `mt7620.mk` 插入
   `Device/phicomm_k2-16m`（IMAGE_SIZE 16064k）和
   `Device/phicomm_k2-32m`（IMAGE_SIZE 32448k）
3. **第三方 feed**：启用 ssr-plus 时追加 `fw876/helloworld`，
   并强制关闭其中 23 个不需要的包（mihomo、hysteria、naiveproxy、
   shadowsocks-rust、mosdns、chinadns-ng 等），否则镜像会超限数 MB

脚本全部带幂等保护，重复执行不会产生重复条目。

## 缓存机制

两类缓存，通过 `actions/cache` 持久化：

| 缓存 | 路径 | 内容 | 收益 |
|---|---|---|---|
| `dl-*` | `openwrt/dl` | 软件包源码压缩包（约 550MB） | 省约 20 分钟 |
| `ccache-*` | `openwrt/.ccache` | 编译中间产物（约 400MB） | 省约 35 分钟 |

**ccache 需要 `CONFIG_DEVEL=y`**。OpenWrt 的 `config CCACHE` 声明是
`bool "Use ccache" if DEVEL`，不开 DEVEL 时该符号不存在，`make defconfig`
会静默丢弃 `CONFIG_CCACHE=y`，导致 ccache 完全不生效、目录始终为空。
workflow 已自动处理这一点。

缓存 key 格式为 `<type>-<device>-<配置哈希>`，配置变更会重建，但
`restore-keys` 会回退匹配同设备的旧缓存。GitHub 缓存 7 天不访问会自动清除。

### 清理

| 工作流 | 用途 |
|---|---|
| **清理编译缓存** | 按设备/类型精细筛选，`仅预览` 默认开启 |
| **清理（缓存/产物/运行记录）** | 综合清理，支持 `keep_days`，每月 1 号自动跑一次 |

## 编译耗时参考

| 场景 | 耗时 |
|---|---|
| 冷启动（无缓存） | 约 85 分钟 |
| 有 dl + ccache 缓存 | 约 50 分钟 |
| 仅基础固件（含缓存） | 约 45 分钟 |
| 首次编 SS/SSR（构建 Rust 工具链） | 额外 +50 分钟 |

## 硬件改装说明

### 更换 Flash（8MB → 32MB）

**必须改源码**，否则内核认不到新容量：

| 改动 | 位置 |
|---|---|
| 分区表 | `patches/mt7620a_phicomm_k2-32m.dts`，firmware 分区扩到 `0x1fb0000` |
| 镜像上限 | `register_device.py`，`IMAGE_SIZE := 32448k` |

**推荐芯片**：`MX25L25645GM2I-10G`（Macronix，32MB，200mil 8-SOP）
—— 和原装 GD25Q64C 同为 8-SOP 208mil，可直接焊。
官方参数表确认该型号同时提供 200mil 8-SOP 和 300mil 16-SOP 两种封装，
买 M2I 后缀的是 8 脚。

### 更换内存（64MB → 256MB）

**不需要改源码**。内存容量由 U-Boot 上电探测后传给内核，内核不硬编码。

MT7620A 支持上限 256MB DDR2（16 位位宽）。

注意事项：

- 内存是 **84-ball FBGA** 封装，焊盘在芯片底部，需热风枪 + 助焊膏，
  焊接难度远高于 Flash 的 SOP-8
- 原厂 U-Boot 可能写死 64MB 参数，换 Breed 更稳妥
- 换完进系统用 `free -m` 确认，应显示约 24xxxx KB

### USB 2.0

**需要改源码 + 硬件焊接**：

| 部分 | 处理 |
|---|---|
| 硬件 | 焊 USB 母座，D+/D- 接 MT7620A 的 USB 引脚，接 5V |
| 设备树 | `mt7620a.dtsi` 里 `&ehci` / `&ohci` 默认 `status = "disabled"`，k2-32m 的 DTS 已加 `status = "okay"` |
| 内核包 | `with_usb` 开关，带入 kmod-usb2/ohci/storage + ext4/vfat |

**只有 k2-32m 的 DTS 启用了 USB**，其他设备选 `with_usb` 会被强制关闭。

## 刷机注意

- **换芯片前必须先备份原 8MB 芯片全文**，`factory` 分区含 WiFi
  射频校准数据和 MAC 地址，丢失后无线不可用
- 8MB 原机建议先用 `k2-8m` 版验证，确认配置能持久化
- 刷写前在 Breed 里备份当前固件，出问题可回退
- 16M/32M 版刷入前确认分区表已正确（`cat /proc/mtd` 看 firmware 大小）

## 已知限制

- K2 只有 64MB 内存，跑满 LuCI 后余量紧张（实测启动后用掉约 63%）
- 8MB 版 JFFS2 需要至少 5 个 64KB 块（约 320KB）才能挂载，低于此值
  overlay 会退化到 `/tmp/root` 导致配置不保存
- 16MB 装不了 ssr-plus（超 4.8MB），已自动降级
- 换大容量芯片后如果仍用原厂 U-Boot，可能无法识别新容量，建议刷 Breed
- MT7620A 是**单核** 580MHz，RPS / SMP affinity 之类的多核调优无效
- MT7620A **无 PPE 硬件加速**，所谓 HNAT 在此平台是软件实现
- Kcptun / xkcptun 类 UDP 加速在单核 580MHz 上会严重拖慢路由，不建议使用

## 许可证

[MIT](LICENSE)

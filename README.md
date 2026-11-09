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
| `keep_sfe` | **开** | 保留 SFE 加速。与 TPROXY 冲突，见下文 |
| `with_hnat` | **开** | 加入 fastnat 加速面板（软件快速路径） |
| `with_adblock` | 关 | 加入 adblock-fast DNS 广告过滤 |

### 自动联动规则

这些规则在参数解析阶段自动执行，无需手动处理：

```
with_ssrplus=true, with_xray=false   → 自动开启 with_xray（ssr-plus 需要内核）
with_ss_full=true, with_ssrplus=false → 自动关闭 with_ss_full（内核脱离界面无意义）
with_ss_full=true, device≠k2-32m      → 强制关闭（7MB 放不下）
with_ssrplus=true, device=k2-16m      → 强制关闭 with_ssrplus 和 with_xray（见空间限制）
with_adblock=true, device=k2-8m       → 强制关闭（规则文件需数 MB）
```

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
| + `with_adblock` | 约 0.3 MB | +0.3 MB | ✅ |

**关键结论**：

- `with_ssrplus` **只能在 `k2-32m` 上使用**。16M 上编出来的镜像超限，
  `make` 会丢弃 `squashfs-sysupgrade.bin`，产物里只剩 `initramfs-kernel.bin`
  —— 那个不能刷进 flash。
- 在 `k2-16m` 上勾选 `with_ssrplus` 会**自动关闭 xray 和 ssr-plus 两项**，
  编出的是基础固件，不会给你不可刷的残包。
- 想用图形代理界面，只能换 32MB 芯片。

## 加速功能说明

固件里有三条加速路径，容易混淆：

| 模块 | 名称 | 机制 | 与代理冲突 |
|---|---|---|---|
| `kmod-shortcut-fe` | **SFE** | 独立快捷通道，绕过 netfilter | **会冲突** |
| `kmod-nf-flow` | flowtable | netfilter 内部 flow 表 | 较小，可按规则排除 |
| `kmod-nft-offload` | nft offload | nftables offload | 较小，可按规则排除 |

**SFE 会跳过 netfilter，导致 TPROXY 重定向失效** —— 表现为直连正常但代理不通。

因此 `keep_sfe` 的取舍：

| 场景 | keep_sfe |
|---|---|
| 纯路由，要满速 | **true**（默认） |
| 跑代理 | **false**（关 SFE，保留 flowtable） |
| 两者都要 | true，但需在 fastnat 面板把代理流量加入排除 |

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
scripts/configure_adblock.py         DNS 层广告过滤

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

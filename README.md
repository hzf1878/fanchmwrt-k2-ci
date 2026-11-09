# FanchmWrt K2 云编译

斐讯 K2（MT7620A + MT7612E）的 FanchmWrt 固件云端编译配置，基于上游
[fanchmwrt/fanchmwrt](https://github.com/fanchmwrt/fanchmwrt) 源码。

本仓库只存放**编译配置、补丁和 workflow**，不含源码。每次编译时从上游拉取。

## Fork 使用

1. 点右上角 **Fork** → **Create fork**
2. 进入你自己的 fork → **Settings → Actions → General**
3. 选择 **Allow all actions and reusable workflows**，点 **Save**
   （fork 出来的仓库 Actions 默认关闭，不开启的话看不到 Run workflow 按钮）
4. 进入 **Actions** → **Build FanchmWrt for Phicomm K2** → **Run workflow**

注意：fork 后缓存是空的，第一次编译会冷启动（约 85 分钟），从第二次起才会快。

## 编译参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `device` | `k2-16m` | 目标设备：`k2-8m` / `k2-16m` / `k2-32m` |
| `use_cache` | 开 | dl 源码包 + ccache 总开关，省约 55 分钟 |
| `use_ccache` | 开 | 单独控制 ccache（依赖 use_cache） |
| `with_xray` | 关 | 加入 xray-core（trojan/VMess/VLESS/SS） |
| `with_ssrplus` | 关 | 加入 luci-app-ssr-plus 图形界面 |

`with_ssrplus` 会自动开启 `with_xray`，因为 ssr-plus 需要一个代理内核。

## 各设备的空间限制（实测，非估算）

| 设备 | firmware 分区 | 空固件镜像 | 剩余可写区 |
|---|---|---|---|
| `k2-8m` | 7.87 MB | 7.34 MB | **约 0.32 MB** |
| `k2-16m` | 15.69 MB | 10.94 MB | **约 4.75 MB** |
| `k2-32m` | 31.69 MB | 10.94 MB | **约 20.75 MB** |

### 代理功能需要多少空间（实测）

| 组合 | 镜像增量 | 总镜像 | 能否装进 16M |
|---|---|---|---|
| 仅 `with_xray` | 约 3.5 MB | 约 14.4 MB | 勉强，可写区剩约 1.2MB |
| `with_xray` + `with_ssrplus` | **约 9.4 MB** | **约 20.3 MB** | ❌ **超出 4.8MB** |

**关键结论**：

- `with_ssrplus` **只能在 `k2-32m` 上使用**。在 `k2-16m` 上编出来的镜像会超限，
  `make` 会丢弃 `squashfs-sysupgrade.bin`，产物里只剩 `initramfs-kernel.bin`——
  那个不能刷进 flash。
- `k2-8m` 上这两个选项会被自动强制关闭。
- 在 `k2-16m` 上勾选 `with_ssrplus` 只会得到一条 warning，编译仍会继续，但结果不可用。


## 支持的设备

| 配置 | 设备 | Flash | 芯片 | 可写区 |
|---|---|---|---|---|
| `k2-8m` | Phicomm K2 v22.4 or older | 8MB | 原装 W25Q64 | 约 320KB |
| `k2-16m` | Phicomm K2 (16M flash mod) | 16MB | W25Q128 | 约 4.7MB |
| `k2-32m` | Phicomm K2 (32M flash mod) | 32MB | W25Q256 | 约 20.7MB |

16M / 32M 是换芯片后的自定义变体，需要改分区表，对应 DTS 见 `patches/`。
前提是使用 Breed 作为 bootloader，原厂 U-Boot 对大容量芯片支持不可靠。

## 目录结构

```
.github/workflows/build.yml         编译工作流
.github/workflows/clear-cache.yml   手动清理缓存
config/k2-16m.config                16MB flash 编译配置
config/k2-8m.config                 8MB flash 编译配置
patches/mt7620a_phicomm_k2-16m.dts  16M 分区表设备树
patches/0001-add-k2-16m-device.patch 设备定义补丁（参考用）
scripts/register_device.py          把 16M 设备注册进 mt7620.mk
scripts/configure_ssrplus.py        ssr-plus 开关与 helloworld feed 管理
scripts/test_cache_filter.sh        缓存清理逻辑自测
scripts/test_cache_switches.sh      缓存开关逻辑自测
scripts/test_xray_switch.sh         xray 开关逻辑自测
```

## 自定义内容说明

上游源码不含 K2 的 16MB 变体，本仓库通过两处改动实现：

1. **DTS**：`mt7620a_phicomm_k2-16m.dts`，firmware 分区从
   `0x50000 0x7b0000`（8MB）扩展到 `0x50000 0xfb0000`（16MB）
2. **设备定义**：`register_device.py` 在 `mt7620.mk` 中插入
   `Device/phicomm_k2-16m`（IMAGE_SIZE 16064k）

脚本带幂等保护，已存在则跳过。

## 缓存机制

编译使用两类缓存，都通过 `actions/cache` 持久化：

| 缓存 | 路径 | 内容 | 收益 |
|---|---|---|---|
| `dl-*` | `openwrt/dl` | 软件包源码压缩包（约 550MB） | 省约 20 分钟 |
| `ccache-*` | `openwrt/.ccache` | 编译中间产物 | 省约 35 分钟 |

**ccache 需要 `CONFIG_DEVEL=y`**。OpenWrt 的 `config CCACHE` 声明是
`bool "Use ccache" if DEVEL`，不开 DEVEL 时该符号不存在，`make defconfig`
会静默丢弃 `CONFIG_CCACHE=y`，导致 ccache 完全不生效、目录始终为空。
workflow 已自动处理这一点。

缓存 key 格式为 `<type>-<device>-<配置哈希>`，配置变更会重建，但
`restore-keys` 会回退匹配同设备的旧缓存。

清理缓存：**Actions → Clear build caches → Run workflow**，支持按设备
和类型筛选，`dry_run` 可先预览。

## 刷机注意

- **换 16MB 芯片前必须先备份原 8MB 芯片全文**，`factory` 分区含 WiFi
  射频校准数据和 MAC 地址，丢失后无线不可用
- 8MB 原机建议先用 `k2-8m` 版验证，确认配置能持久化
- 刷写前在 Breed 里备份当前固件，出问题可回退

## 已知限制

- K2 只有 64MB 内存，跑满 LuCI 后余量紧张
- 8MB 版 JFFS2 需要至少 5 个 64KB 块（约 320KB）才能挂载，低于此值
  overlay 会退化到 `/tmp/root` 导致配置不保存
- **16MB 装不了 ssr-plus**：实测镜像 20.3MB，超出 15.69MB 分区上界 4.8MB。
  `make` 会丢弃超限的 sysupgrade 镜像，产物里只剩 initramfs（不可刷）
- 换大容量芯片后如果仍用原厂 U-Boot，可能无法识别新容量，建议刷 Breed
- `kmod-shortcut-fe` 硬件加速与透明代理冲突：代理流量需从 flowtable 排除，
  否则 TPROXY 规则不生效（表现为直连正常、走代理不通）

## 许可证

[MIT](LICENSE)

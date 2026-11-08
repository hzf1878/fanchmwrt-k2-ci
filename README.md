# FanchmWrt K2 云编译

斐讯 K2（MT7620A + MT7612E）的 FanchmWrt 固件云端编译配置，基于上游
[fanchmwrt/fanchmwrt](https://github.com/fanchmwrt/fanchmwrt) 源码。

## 支持的设备

| 配置 | 设备 | Flash | 说明 |
|---|---|---|---|
| `k2-16m` | Phicomm K2 (16M flash mod) | 16MB | 需换 W25Q128 芯片，可写区约 6MB |
| `k2-8m` | Phicomm K2 v22.4 or older | 8MB | 原机直接刷，可写区约 320KB |

## 用法

1. Fork 本仓库到自己的账号
2. 进入 **Actions** → **Build FanchmWrt for Phicomm K2** → **Run workflow**
3. 选择 `device`（`k2-16m` 或 `k2-8m`）
4. 等待约 80–120 分钟，从 Artifacts 下载固件

也可以推送 `v*` 标签自动触发（默认编 16M 版）：

```bash
git tag v1.0
git push origin v1.0
```

## 目录结构

```
.github/workflows/build.yml       GitHub Actions 工作流
config/k2-16m.config              16MB flash 编译配置
config/k2-8m.config               8MB flash 编译配置
patches/mt7620a_phicomm_k2-16m.dts  16M 分区表设备树
scripts/register_device.py        把 16M 设备注册进 mt7620.mk
```

## 自定义内容说明

上游源码本身不含 K2 的 16MB 变体，本仓库通过两处改动实现：

1. **DTS**：`mt7620a_phicomm_k2-16m.dts`，firmware 分区从
   `0x50000 0x7b0000`（8MB）扩展到 `0x50000 0xfb0000`（16MB）
2. **设备定义**：`register_device.py` 在 `mt7620.mk` 中插入
   `Device/phicomm_k2-16m`（IMAGE_SIZE 16064k）

脚本带幂等保护，已存在则跳过。

## 刷机注意

- **换 16MB 芯片前必须先备份原 8MB 芯片全文**，`factory` 分区含 WiFi
  射频校准数据和 MAC 地址，丢失后无线不可用
- 8MB 原机建议先用 `k2-8m` 版验证，确认配置能持久化
- 刷写前在 Breed 里备份当前固件，出问题可回退

## 已知限制

- K2 只有 64MB 内存，跑满 LuCI 后余量紧张
- 8MB 版 JFFS2 需要至少 5 个 64KB 块（约 320KB）才能挂载，低于此值
  overlay 会退化到 `/tmp/root` 导致配置不保存

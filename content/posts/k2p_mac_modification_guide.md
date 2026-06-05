---
title: "斐讯 K2P 硬件级修改无线 MAC 地址全历程复盘与逆向思维实录"
date: 2026-06-05T08:40:00+08:00
draft: false
tags:
  - "斐讯K2P"
  - "Padavan"
  - "MAC修改"
  - "硬改"
  - "嵌入式Linux"
categories:
  - "网络技术"
  - "极客折腾"
toc: true
---

## 🏛️ 一、核心破局思路：基因改造法

### 初始诉求

将斐讯 K2P 路由器魔改固件中的 Wi-Fi 6 无线接口（`rax0`）的 MAC 地址，彻底且永久地修改为：

```

XX:XX:XX:XX:XX:XX

````

---

### 传统道路的死胡同

最开始，通过 SSH 执行 Linux 标准命令：

```bash
ifconfig rax0 hw ether XX:XX:XX:XX:XX:XX
````

系统直接返回：

```text
ifconfig: SIOCSIFHWADDR: Not supported
```

#### 底层原因

这套 K2P 魔改固件集成了芯片厂商提供的闭源无线驱动。

驱动初始化时，会绕过 Linux 网络层，直接读取闪存中的 Factory（EEPROM）分区，将出厂 MAC 地址写入无线芯片寄存器。

一旦驱动完成初始化：

* ifconfig 修改无效；
* NVRAM 参数无效；
* 系统运行期间无法动态改变 MAC。

换句话说，驱动根本不理会 Linux 标准网络接口。

---

### 思路转变：基因改造法

既然系统启动后不允许修改，

那就直接修改驱动读取的数据源。

在驱动初始化之前，将 Factory 分区中的原始 MAC 地址修改掉，让驱动开机时读取到新的 MAC。

本质上：

> 修改硬件基因，而不是修改运行状态。

---

# 🛠️ 二、底层侦察：寻找目标基因

## 揪出 Factory 分区

查看 MTD 分区表：

```bash
cat /proc/mtd
```

输出：

```text
dev:    size   erasesize  name
mtd0: 00040000 00010000 "Bootloader"
mtd1: 00010000 00010000 "Config"
mtd2: 00010000 00010000 "Factory"
```

可以确定：

Factory 分区对应：

```text
mtd2
```

---

## 提取 Factory 镜像

使用 dd 克隆：

```bash
dd if=/dev/mtd2 of=/tmp/factory.bin
```

得到：

```text
/tmp/factory.bin
```

大小：

```text
65536 Bytes
```

---

# 💥 三、跨平台博弈：突破文件传输封锁

拿到 factory.bin 后，需要传输到电脑进行修改。

过程中遇到了两个经典障碍。

---

## 僵局一：SCP 连接被拒绝

执行：

```bash
scp admin@192.168.2.1:/tmp/factory.bin ./
```

报错：

```text
sh: /opt/libexec/sftp-server: not found
scp: Connection closed
```

### 原因

现代 OpenSSH 的 scp 默认使用 SFTP。

而 Padavan 的 Dropbear 没有编译 sftp-server。

协议不兼容。

---

## 解决方案：强制使用旧版 SCP

加入：

```bash
-O
```

即可：

```bash
scp -O admin@192.168.2.1:/tmp/factory.bin ./
```

成功传输。

---

## 僵局二：网页目录无法写入

尝试：

```bash
cp /tmp/factory.bin /www/syslog.bin
```

系统提示：

```text
Read-only file system
```

### 原因

Padavan 的 `/www`

位于 SquashFS 只读文件系统。

运行时无法写入。

---

## 备用方案：Base64 屏幕流还原

如果 SCP 完全失效，

仍然可以：

### 路由器端

```bash
cat /tmp/factory.bin | base64
```

输出大量文本。

复制保存为：

```text
factory.txt
```

Windows 下：

```powershell
certutil -decode factory.txt factory.bin
```

即可恢复原始二进制文件。

这种思路实际上是：

> 将二进制降维为文本流。

属于嵌入式开发中非常实用的一种技巧。

---

# 🔍 四、十六进制定位与格子对齐修改

## 路由器自己当向导

直接搜索 MAC 地址不一定能找到。

于是使用：

```bash
hexdump -C /tmp/factory.bin | grep -i "f2:19"
```

得到：

```text
00000000  15 76 a0 00 fc 7c 02 d7  f2 19 15 76 c3 14 00 80
```

其中：

原始 MAC：

```text
fc 7c 02 d7 f2 19
```

位于：

```text
Offset 0x04 ~ 0x09
```

---

## 精确覆盖修改

目标：

```text
XX XX XX XX XX XX
```

修改对应关系：

| Offset | 原值                | 新值 | 含义     |
| ------ | ----------------- | -- | ------ |
| 00~03  | 15 76 a0 00       | 不变 | 引导头    |
| 04     | fc                | XX | MAC1   |
| 05     | 7c                | XX | MAC2   |
| 06     | 02                | XX | MAC3   |
| 07     | d7                | XX | MAC4   |
| 08     | f2                | XX | MAC5   |
| 09     | 19                | XX | MAC6   |
| 0A~0F  | 15 76 c3 14 00 80 | 不变 | 射频校准参数 |

---

### 铁律

只能覆盖。

绝不能：

* Delete
* Backspace

否则文件长度变化：

```
65536 Bytes
```

一旦长度改变，

极有可能直接变砖。

修改完成保存：

```text
factory_new.bin
```

---

# 🚀 五、重新烧录 Factory 分区

## 上传回路由器

```bash
scp -O factory_new.bin admin@192.168.2.1:/tmp/
```

---

## 刷写闪存

进入：

```bash
cd /tmp
```

执行：

```bash
mtd_write write factory_new.bin Factory
```

底层实际上完成：

1. 擦除 mtd2；
2. 写入新的二进制镜像；
3. 更新 Factory 数据。

---

## 重启

```bash
reboot
```

---

# 🏁 六、最终成果

系统重新启动后，

无线驱动再次读取 Factory 分区。

由于最源头的数据已经改变，

因此：

```text
ra0
rax0
```

全部获得新的硬件地址：

```text
XX:XX:XX:XX:XX:XX
```

并且：

* 恢复出厂不会丢失；
* 清空 NVRAM 不会丢失；
* 更换固件不会丢失；

因为修改的是：

> Factory 分区中的硬件基因。

属于真正意义上的永久修改。

---

# 📝 工程师手记

这次折腾最大的收获，不是改掉了一个 MAC 地址，而是再次验证了一条嵌入式世界的规律：

> 当应用层解决不了问题，就向下一层寻找答案。

整个过程实际上是一场不断下潜的过程：

* Linux 网络接口失效；
* 转向驱动初始化；
* 驱动不可控；
* 转向 EEPROM；
* 文件无法传输；
* 降级协议；
* 协议失效；
* 文本流编码；
* 无法定位；
* 借助 hexdump 反向导航；
* 最终直接修改闪存。

很多问题并不是没有答案，

只是答案不在当前这一层。

对于嵌入式开发而言，

真正重要的能力，从来不是记住多少命令，

而是能够不断向下追问：

> 它真正的数据源在哪里？

最后，

一定要保留一份原始的：

```text
factory.bin
```

这是整个过程中最重要的保险。

因为对于一台设备来说，

Factory 分区，

就是它的基因。

```
```

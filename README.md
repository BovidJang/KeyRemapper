<div align="center">

# KeyRemapper

**一款轻量级 Windows 游戏按键重映射工具**

KeyRemapper是一款轻量级的 Windows 按键重映射工具，专为游戏设计。通过WH_KEYBOARD_LL在操作系统层面拦截并替换按键，可以对游戏厂商不允许修改的特定操作按键进行修改。

[![Python](https://img.shields.io/badge/Python-3.6+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v2.0-orange)]()

---

[功能特性](#-功能特性) · [快速开始](#-快速开始) · [使用指南](#-使用指南) · [配置说明](#-配置说明) · [常见问题](#-常见问题) · [技术栈](#-技术栈)

---

</div>

## 功能特性

<table>
<tr>
<td width="50%">

**精准映射**
- 键盘按键 → 键盘按键
- 鼠标按键 → 键盘按键
- 支持所有标准键、功能键、小键盘键

</td>
<td width="50%">

**按键宏**
- 单键触发多键连招
- 键盘 + 鼠标操作混合编排

</td>
</tr>
<tr>
<td>

**鼠标支持**
- 左键 / 右键 / 中键
- 上滚轮 / 下滚轮
- 上侧键 / 下侧键

</td>
<td>

**多配置管理**
- 多游戏独立配置
- 每游戏多预设方案
- 一键导入 / 导出分享

</td>
</tr>
</table>

> **安全可靠** — 基于 `WH_KEYBOARD_LL` 低级键盘钩子，在 OS 层拦截按键，不修改游戏内存，不注入 DLL，不影响系统其他应用。

## 快速开始

### 方式一：直接运行 EXE（推荐）

从 [Releases](https://github.com/BovidJang/KeyRemapper/) 下载最新版本，双击运行即可。
该方法已弃用，项目仓库将不再提供exe程序
可以通过百度网盘进行下载[百度网盘](https://pan.baidu.com/s/1B79VTxpZ7Mkjq55YTDMKlQ?pwd=evwr)

> **需要以管理员身份运行**（右键 → 以管理员身份运行）

### 方式二：从源码构建

```bash
# 1. 克隆仓库
git clone https://github.com/BovidJang/KeyRemapper.git
cd KeyRemapper

# 2. 一键构建 EXE
build.bat

# 3. 构建完成后 EXE 位于
dist/KeyRemapper.exe
```

### 方式三：直接运行 Python

```bash
python main.py
```

> 需要 Python 3.6+ 环境

## 使用指南

> **Step 1** → 选择目标游戏窗口
> **Step 2** → 点击键盘按键进行绑定
> **Step 3** → 同意用户协议
> **Step 4** → 点击「启动」，游戏内即刻生效

### 键盘映射

1. 在可视化键盘上点击要映射的按键（变为蓝色）
2. 直接按下键盘上的目标按键完成绑定
3. 绑定后的按键变为绿色，显示映射目标

### 鼠标映射

1. 在右侧鼠标列表中点击要映射的鼠标按键
2. 按下键盘上的目标按键完成绑定

### 按键宏

1. 点击键盘按键 → 选择「设为宏」
2. 在宏编辑器中添加键盘按键或鼠标操作
3. 支持上移 / 下移调整顺序

### 导入 / 导出

- **导出**：点击「导出预设」→ 复制字符串 → 发给朋友
- **导入**：点击「导入预设」→ 粘贴字符串 → 自动还原配置

## 配置说明

配置文件 `profiles.json` 自动保存在程序同目录：

```json
{
  "current_profile": "冒险岛怀旧服",
  "current_preset_index": 0,
  "profiles": [
    {
      "name": "冒险岛怀旧服",
      "presets": [
        {
          "name": "预设1",
          "remappings": { "87": 38, "65": 37 },
          "macros": { "67": [17, 67] },
          "mouse_bindings": {},
          "mouse_button_macro": {}
        }
      ]
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| `remappings` | 按键映射 `{原键VK码: 目标键VK码}` |
| `macros` | 按键宏 `{触发键: [按键序列]}` |
| `mouse_bindings` | 鼠标→键盘映射 `{鼠标VK码: 键盘VK码}` |
| `mouse_button_macro` | 鼠标宏 `{鼠标VK码: [操作序列]}` |

## 常见问题

<details>
<summary><b>启动后按什么都没反应？</b></summary>

1. 确保以 **管理员身份** 运行
2. 确保已选择目标游戏窗口
3. 确保已点击「启动」按钮
4. 检查是否同意了用户协议
</details>

<details>
<summary><b>绑定的按键在游戏中没生效？</b></summary>

1. 确认目标窗口选择正确
2. 确认钩子已启动（状态栏显示「运行中」）
3. 部分游戏使用直接输入（Direct Input），可能需要额外适配
</details>

<details>
<summary><b>杀毒软件报毒怎么办？</b></summary>

这是 PyInstaller 打包的未签名 exe 的常见误报。添加信任即可：
- Windows Defender：设置 → 更新和安全 → Windows 安全中心 → 病毒和威胁防护 → 排除项
</details>

<details>
<summary><b>构建 EXE 失败？</b></summary>

1. 确保安装了 Python 3.6+ 并添加到 PATH
2. 确保已安装 PyInstaller：`pip install pyinstaller`
3. 关闭正在运行的旧版 exe
</details>

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3 |
| GUI | tkinter |
| 键盘钩子 | `WH_KEYBOARD_LL` (SetWindowsHookExW) |
| 按键注入 | `SendInput` |
| 按键检测 | `GetAsyncKeyState` |
| 打包 | PyInstaller |
| 平台 | Windows 10/11 |

### 架构说明

```
用户按键 → WH_KEYBOARD_LL 钩子拦截 → SendInput 发送映射键 → 游戏接收
                 ↓
           原键被拦截（返回 -1）
```

## 项目结构

```
KeyRemapper/
├── main.py              # 程序入口
├── app.py               # 主窗口 UI（游戏列表/预设/编辑面板）
├── key_hook.py          # 键盘钩子核心（WH_KEYBOARD_LL + SendInput）
├── keyboard_widget.py   # 可视化键盘组件
├── mouse_widget.py      # 鼠标按键列表组件
├── profile_manager.py   # 配置管理（JSON 读写/导入导出）
├── requirements.txt     # 依赖（仅 Python 标准库）
├── build.bat            # 一键打包脚本
├── KeyRemapper.spec     # PyInstaller 打包配置
└── README.md            # 说明文档
```

## License

[MIT License](LICENSE) - 自由使用、修改和分发。

## Author

**BovidJang**

- BiliBili: [@BovidJang](https://space.bilibili.com/551892641/dynamic)
- GitHub: [@BovidJang](https://github.com/BovidJang)
- Email: bovidjang@foxmail.com

---

<div align="center">

**如果这个项目对你有帮助，欢迎 Star ⭐ 支持一下！**

</div>

<p align="right">
  <a href="#中文">中文</a> ·
  <a href="#english">English</a>
</p>

# Remote Keyboard

Use your phone as a wireless keyboard for your Linux computer — no app installation needed.

通过手机无线控制 Linux 电脑输入 — 无需安装任何 App。

---

## English

### What Is This?

A web-based virtual keyboard that lets you control your Linux machine's keyboard input from any phone browser over your local network. Open a webpage on your phone, type on the virtual keyboard, and keystrokes appear on your computer.

### Features

- **Virtual keyboard** with text input area, shortcut buttons (Backspace, Enter, Send), and arrow keys
- **Long-press repeat** — hold Backspace or arrow keys to repeat
- **Language toggle** — switch between English and Chinese UI
- **Connection indicator** — shows whether the server is reachable
- **No client app needed** — works from any mobile browser (iOS & Android)

### Quick Start

```bash
# 1. Install system dependency
sudo apt install xdotool        # Debian/Ubuntu
sudo dnf install xdotool        # Fedora

# 2. Install Python dependency
pip install flask

# 3. Start the server
cd src/server && python server.py

# 4. Open the URL shown in terminal on your phone (same network)
```

### Limitations

1. **X11 only** — requires an X11 desktop session; pure Wayland is not supported
2. **Same network required** — phone and computer must be on the same LAN; no remote access over the internet
3. **No authentication** — anyone on the same network can connect and control your keyboard
4. **Keyboard only** — no mouse or trackpad support
5. **Chinese/CJK input** — non-ASCII text is sent via clipboard paste (`Ctrl+Shift+V`); the target app must support this shortcut. IME composition (e.g. pinyin selection) is not supported
6. **Focused window receives input** — keystrokes go to whichever window currently has focus on the Linux machine

### Claude Code Workflow

This tool enables a nearly hands-free Claude Code experience. With your phone as the keyboard, you can dictate commands via voice input, use Enter to execute prompts, and the arrow keys to navigate Claude Code's interactive menus — all without ever touching your computer's keyboard or mouse.

---

## 中文

### 这是什么？

一个基于网页的虚拟键盘，让你在手机浏览器上控制同一局域网内 Linux 电脑的键盘输入。打开手机网页，在虚拟键盘上打字，输入内容就会出现在电脑当前焦点窗口。

### 功能

- **虚拟键盘**：包含文本输入区、快捷按钮（退格、回车、发送）和方向键
- **长按连发**：长按退格键或方向键可重复触发
- **语言切换**：一键切换英文/中文界面
- **连接指示灯**：实时显示服务器是否可达
- **无需客户端**：手机浏览器直接访问，iOS/Android 通用

### 快速开始

```bash
# 1. 安装系统依赖
sudo apt install xdotool        # Debian/Ubuntu
sudo dnf install xdotool        # Fedora

# 2. 安装 Python 依赖
pip install flask

# 3. 启动服务器
cd src/server && python server.py

# 4. 用手机打开终端显示的网址（需在同一局域网）
```

### 限制

1. **仅支持 X11** — 需要 X11 桌面环境，纯 Wayland 不可用
2. **必须同一局域网** — 手机和电脑需连接同一网络，不支持远程访问
3. **无身份验证** — 同一网络中的任何设备都可连接并控制键盘输入
4. **仅支持键盘** — 没有鼠标/触控板功能
5. **中文输入** — 非 ASCII 文本通过剪贴板粘贴（`Ctrl+Shift+V`）注入，需要目标应用支持该快捷键；不支持拼音选字等 IME 输入
6. **输入发送到焦点窗口** — 按键会注入 Linux 电脑当前获得焦点的窗口

### Claude Code 工作流

搭配这个工具，你可以实现几乎完全脱离键盘的 Claude Code 使用体验。在手机上使用语音输入来发送指令，用 Enter 执行提示，用方向键在 Claude Code 的交互菜单中导航选项 — 全程无需触碰电脑的键盘或鼠标。

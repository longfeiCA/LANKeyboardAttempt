# Remote Keyboard

<details open>
<summary><b>🌐 Language / 语言</b></summary>

- **[English](#english)** — this document
- **[中文](#中文文档)** — [Click to jump to Chinese version](#中文文档)
</details>

<br>

---

## English

### Overview

A tool that lets you control Linux keyboard input over a local network using your phone. Each key press or text input from the virtual keyboard on the phone is sent via HTTP requests to a Flask server, which injects it into the currently focused Linux window using `xdotool`.

### Architecture

```
┌─────────────┐         WiFi          ┌─────────────┐
│  Phone       │ ◀──── HTTP Req ─────▶ │  Flask      │
│  Browser     │                       │  (Python)   │
└─────────────┘                       └──────┬──────┘
                                             │ xdotool
                                             ▼
                                      ┌─────────────┐
                                      │ Linux X11   │
                                      │ (Simulated  │
                                      │  keypress)  │
                                      └─────────────┘
```

### Components

#### 1. Flask Web Server (`server/server.py`)

- **Port**: 5000
- **API Endpoints**:
  - `GET /` — Serves the web page (all HTML/CSS/JS embedded inline)
  - `GET /api/status` — Checks xdotool keyboard injector status
  - `POST /api/key` — Sends a single keypress `{"key": "a", "modifiers": ["ctrl"]}`
  - `POST /api/text` — Sends text `{"content": "hello"}`

#### 2. Keyboard Injector (`server/input_xdotool.py`)

Wraps `xdotool` to simulate keyboard input via X11:

```bash
# Single key
xdotool key a

# Combo (Ctrl+C)
xdotool keydown ctrl key c keyup ctrl

# Send text (pure ASCII)
xdotool type "hello"

# Send CJK text (via clipboard Ctrl+Shift+V)
wl-copy / xclip / xsel → xdotool key ctrl+shift+v
```

Supported keys: a-z, 0-9, function keys (Enter, Tab, Esc, BackSpace, Delete), arrow keys (Up, Down, Left, Right), modifiers (Ctrl, Shift, Alt, Super), symbol keys, and Home/End/PageUp/PageDown/Insert.

#### 3. Web Frontend (embedded in `server.py` `HTML_TEMPLATE`)

- **Text input area**: Multi-line textarea, sent via SEND button or Enter key
- **Shortcut button row**: BackSpace (DEL), Enter, SEND
- **Arrow row**: ↑ (UP), ↓ (DOWN)
- **Status bar**: Connection indicator light + language toggle (EN/中文)

**Frontend features**:

| Feature | Description |
|---------|-------------|
| Long-press repeat | Holding BackSpace, ↑, or ↓ delays 300ms then repeats every 80ms |
| Language toggle | EN/中文 button switches UI language; saved in `localStorage` |
| Connection check | Polls `/api/status` every 5 seconds to update indicator |
| Mobile optimized | `user-scalable=no` disables zoom, `user-select: none` prevents long-press text selection on buttons |

#### 4. Dependencies

**Python packages**:

```
flask>=3.0.0
```

**System packages**:

```
xdotool               # Core: simulate keypresses
wl-copy / xclip / xsel  # At least one: CJK text injection (via clipboard)
```

### Usage

```bash
# 1. Install system dependencies
sudo dnf install xdotool        # Fedora
sudo apt install xdotool        # Debian/Ubuntu

# 2. Install Python dependencies
pip install flask

# 3. Start the server
cd server && python server.py

# 4. Open on phone (same network)
# http://<your_ip>:5000
```

### API Protocol

#### Send Single Key

```http
POST /api/key
Content-Type: application/json

{"key": "backspace", "modifiers": []}
{"key": "a", "modifiers": ["ctrl"]}
```

#### Send Text

```http
POST /api/text
Content-Type: application/json

{"content": "Hello World"}
```

#### Health Check

```http
GET /api/status

# Response
{"status": "ok", "message": "Keyboard injector ready"}
```

### Design Decisions

#### Why xdotool?

| Approach | Pros | Cons |
|----------|------|------|
| xdotool | No root needed, simple setup | Requires X11 session |
| python-uinput | Doesn't depend on X11 | Requires root, complex build |
| evdev | Low-level, reliable | Requires root, complex build |

xdotool simulates keypresses via X11's XTEST extension — the simplest and most reliable approach.

#### Why Flask + Embedded HTML?

- Zero frontend framework dependencies — runs from a single file
- Mature Python ecosystem, direct `subprocess` calls to xdotool
- Accessible from any phone browser — no app installation needed (iOS & Android)

### File Structure

```
remote-keyboard/
├── server/
│   ├── server.py           # Flask server + embedded web frontend
│   ├── input_xdotool.py    # xdotool keyboard injection wrapper
│   ├── input_injector.py   # python-uinput fallback (not currently used)
│   └── requirements.txt    # Python dependencies
├── README.md               # This document
└── .gitignore
```

### Limitations & Notes

1. **X11 required**: xdotool needs an X11 display server; pure Wayland is unsupported (auto-detected with warning)
2. **Same network**: Phone and computer must be on the same LAN
3. **Focused window**: Keypresses go to whichever window currently has focus on the Linux machine
4. **CJK input**: Non-ASCII text is injected via clipboard + `Ctrl+Shift+V`, requiring the target application to support this shortcut

---

## 中文文档

<details open>
<summary><b>👆 点击上方展开中文版</b></summary>
</details>

<br>

### 概述

这是一个通过局域网用手机控制 Linux 电脑输入的工具。手机访问网页后，通过虚拟键盘按下的每个按键或输入的文本都会经由 HTTP 请求发送到 Flask 服务器，再由服务器通过 `xdotool` 注入到 Linux 当前焦点窗口。

### 架构

```
┌─────────────┐         WiFi          ┌─────────────┐
│   手机浏览器  │ ◀──── HTTP 请求 ────▶  │  Flask 服务  │
│  (网页界面)   │                       │   (Python)  │
└─────────────┘                       └──────┬──────┘
                                             │ xdotool
                                             ▼
                                      ┌─────────────┐
                                      │ Linux X11   │
                                      │ (模拟按键)   │
                                      └─────────────┘
```

### 组件

#### 1. Flask Web 服务器 (`server/server.py`)

- **端口**: 5000
- **API 路由**:
  - `GET /` — 返回网页界面（HTML/CSS/JS 全部内嵌）
  - `GET /api/status` — 检查 xdotool 键盘注入器状态
  - `POST /api/key` — 发送单个按键 `{"key": "a", "modifiers": ["ctrl"]}`
  - `POST /api/text` — 发送文本 `{"content": "hello"}`

#### 2. 键盘注入器 (`server/input_xdotool.py`)

封装 `xdotool` 命令，通过 X11 模拟键盘输入：

```bash
# 单个按键
xdotool key a

# 组合键 (Ctrl+C)
xdotool keydown ctrl key c keyup ctrl

# 发送文本（纯 ASCII）
xdotool type "hello"

# 发送中文（走剪贴板 Ctrl+Shift+V）
wl-copy / xclip / xsel → xdotool key ctrl+shift+v
```

支持的按键包括：字母 a-z、数字 0-9、功能键（Enter、Tab、Esc、BackSpace、Delete）、方向键（Up、Down、Left、Right）、修饰键（Ctrl、Shift、Alt、Super）、符号键以及 Home/End/PageUp/PageDown/Insert。

#### 3. 网页前端（全部内嵌在 `server.py` 的 `HTML_TEMPLATE`）

- **文本输入区**：可输入多行文本，点击 SEND 或 Enter 键发送
- **快捷按钮行**：BackSpace（DEL）、Enter、SEND
- **箭头行**：↑（UP）、↓（DOWN）
- **状态栏**：连接状态指示灯 + 语言切换按钮（EN/中文）

**前端功能**：

| 功能 | 说明 |
|------|------|
| 长按连发 | 长按 BackSpace、↑、↓ 会先延迟 300ms 后以 80ms 间隔重复发送 |
| 语言切换 | 点击 EN/中文 按钮切换界面语言，设置存储在 `localStorage` |
| 连接检测 | 每 5 秒轮询 `/api/status` 更新状态指示灯 |
| 移动端优化 | `user-scalable=no` 禁止缩放，`user-select: none` 禁止长按选中文字 |

#### 4. 依赖

**Python 包**:

```
flask>=3.0.0
```

**系统包**:

```
xdotool               # 核心：模拟按键
wl-copy / xclip / xsel  # 至少一个：中文文本注入（剪贴板方式）
```

### 使用方法

```bash
# 1. 安装系统依赖
sudo dnf install xdotool        # Fedora
sudo apt install xdotool        # Debian/Ubuntu

# 2. 安装 Python 依赖
pip install flask

# 3. 启动服务器
cd server && python server.py

# 4. 手机访问（同一局域网）
# http://<本机IP>:5000
```

### 通信协议

#### 发送单个按键

```http
POST /api/key
Content-Type: application/json

{"key": "backspace", "modifiers": []}
{"key": "a", "modifiers": ["ctrl"]}
```

#### 发送文本

```http
POST /api/text
Content-Type: application/json

{"content": "你好世界"}
```

#### 状态检查

```http
GET /api/status

# 响应
{"status": "ok", "message": "键盘注入器已就绪"}
```

### 技术选择

#### 为什么用 xdotool？

| 方案 | 优点 | 缺点 |
|------|------|------|
| xdotool | 不需要 root，安装简单 | 需要 X11 会话 |
| python-uinput | 不依赖 X11 | 需要 root 权限，编译复杂 |
| evdev | 底层可靠 | 需要 root，编译困难 |

xdotool 通过 X11 的 XTEST 扩展模拟按键，是最简单可靠的方案。

#### 为什么用 Flask + 内嵌 HTML？

- 零前端框架依赖，单个文件即可运行
- Python 生态成熟，`subprocess` 调用 xdotool 直接
- 手机浏览器即可访问，无需安装 App（iOS/Android 通用）

### 文件结构

```
remote-keyboard/
├── server/
│   ├── server.py           # Flask 服务器 + 内嵌网页前端
│   ├── input_xdotool.py    # xdotool 键盘注入封装
│   ├── input_injector.py   # python-uinput 方案（备用，当前未使用）
│   └── requirements.txt    # Python 依赖
├── README.md               # 本文档
└── .gitignore
```

### 限制与注意

1. **X11 必需**：xdotool 需要 X11 显示服务器，纯 Wayland 环境不可用（自动检测并提示）
2. **同一局域网**：手机和电脑需连接同一网络
3. **焦点窗口**：Linux 上当前获得焦点的窗口会接收按键
4. **中文输入**：中文等非 ASCII 文本通过剪贴板 + `Ctrl+Shift+V` 注入，需要目标应用支持该快捷键

# 远程键盘 - 技术文档

## 概述

这是一个通过局域网用手机控制 Linux 电脑输入的工具。手机访问网页，点击虚拟键盘或使用语音输入，内容会实时发送到 Linux 并模拟键盘输入到当前焦点窗口。

## 架构

```
┌─────────────┐         WiFi          ┌─────────────┐
│   手机浏览器  │ ──────────────────▶  │  Flask 服务  │
│  (网页界面)   │    HTTP 请求         │   (Python)  │
└─────────────┘                       └──────┬──────┘
                                             │
                                             │ xdotool
                                             ▼
                                      ┌─────────────┐
                                      │ Linux X11   │
                                      │ (模拟按键)   │
                                      └─────────────┘
```

## 组件

### 1. Flask Web 服务器 (`server.py`)

- **端口**: 5000
- **路由**:
  - `GET /` - 返回网页界面
  - `GET /api/status` - 检查服务状态
  - `POST /api/key` - 发送单个按键
  - `POST /api/text` - 发送文本

### 2. 键盘注入器 (`input_xdotool.py`)

封装 xdotool 命令，通过 X11 模拟键盘输入：

```python
# 发送单个按键
xdotool key a

# 发送文本
xdotool type "hello world"

# 组合键 (Ctrl+C)
xdotool keydown ctrl key c keyup ctrl
```

### 3. 网页前端 (内嵌在 server.py)

- 虚拟键盘 UI (CSS Grid/Flexbox)
- Web Speech API 语音输入
- 原生 JavaScript，无框架依赖

## 通信协议

### 发送按键

```http
POST /api/key
Content-Type: application/json

{"key": "a", "modifiers": ["ctrl"]}
```

### 发送文本

```http
POST /api/text
Content-Type: application/json

{"content": "hello world"}
```

## 技术选择

### 为什么用 xdotool？

| 方案 | 优点 | 缺点 |
|------|------|------|
| xdotool | 无需 root，安装简单 | 需要 X11 会话 |
| python-uinput | 底层可靠 | 需要 root，编译困难 |
| evdev | 底层可靠 | 需要 root，编译困难 |

xdotool 通过 X11 的 XTEST 扩展模拟按键，是最简单可靠的方案。

### 为什么用 Flask？

- 轻量，内嵌 HTML/CSS/JS
- Python 生态成熟
- 易于部署和维护

### 为什么用网页而不是 App？

- 无需安装，即用即走
- 跨平台兼容（iOS/Android）
- 开发成本低

## 依赖

```
flask>=3.0.0
xdotool (系统包)
```

## 使用方法

```bash
# 1. 安装依赖
pip install flask

# 2. 启动服务器
python server.py

# 3. 手机访问
# http://<Linux_IP>:5000
```

## 限制

1. Linux 必须运行 X11 会话（Wayland 不支持 xdotool）
2. 手机和电脑必须在同一局域网
3. Linux 电脑的焦点窗口会接收按键

## 文件结构

```
remote-keyboard/
├── server/
│   ├── server.py           # Flask 服务器 + 网页
│   ├── input_xdotool.py    # xdotool 封装
│   └── requirements.txt    # Python 依赖
└── README.md               # 本文档
```

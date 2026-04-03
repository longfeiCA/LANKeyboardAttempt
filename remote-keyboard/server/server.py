#!/usr/bin/env python3
"""
远程键盘服务器 - Flask + xdotool
手机访问: http://<Linux_IP>:5000
"""

import logging
import os
import sys

from flask import Flask, request, jsonify, render_template_string

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 延迟导入
injector = None


def get_injector():
    """延迟初始化 injector"""
    global injector
    if injector is None:
        try:
            from input_xdotool import KeyboardInjector
            injector = KeyboardInjector()
            if not injector.initialize():
                logger.error("无法初始化键盘注入器")
                return None
        except Exception as e:
            logger.error(f"无法加载 input_xdotool: {e}")
            return None
    return injector


# ============================================================================
# API 路由
# ============================================================================

@app.route('/api/status', methods=['GET'])
def status():
    """检查服务状态"""
    inj = get_injector()
    return jsonify({
        'status': 'ok' if inj and inj._initialized else 'error',
        'message': '键盘注入器已就绪' if inj and inj._initialized else '键盘注入器未就绪'
    })


@app.route('/api/key', methods=['POST'])
def send_key():
    """发送单个按键"""
    inj = get_injector()
    if not inj:
        return jsonify({'error': '键盘注入器未初始化'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': '未提供数据'}), 400

    key = data.get('key')
    modifiers = data.get('modifiers', [])

    if not key:
        return jsonify({'error': '未提供 key'}), 400

    try:
        inj.send_key(key, modifiers)
        logger.info(f"发送按键: key={key}, modifiers={modifiers}")
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"发送按键失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/text', methods=['POST'])
def send_text():
    """发送文本"""
    inj = get_injector()
    if not inj:
        return jsonify({'error': '键盘注入器未初始化'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': '未提供数据'}), 400

    content = data.get('content', '')
    if not content:
        return jsonify({'error': '未提供 content'}), 400

    try:
        inj.send_text(content)
        logger.info(f"发送文本: {content[:50]}...")
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"发送文本失败: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 网页界面
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>远程键盘</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: #16213e;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #0f3460;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #e94560;
        }

        .status-dot.connected {
            background: #4ade80;
        }

        .text-input-area {
            padding: 12px;
            background: #16213e;
        }

        .text-input-row {
            display: flex;
            gap: 8px;
        }

        #textInput {
            flex: 1;
            padding: 12px;
            border: 1px solid #0f3460;
            border-radius: 8px;
            background: #1a1a2e;
            color: #eee;
            font-size: 16px;
            resize: none;
        }

        .send-btn {
            padding: 12px 24px;
            background: #e94560;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }

        .send-btn:active {
            background: #c73e54;
        }

        .keyboard {
            flex: 1;
            padding: 8px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            overflow-y: auto;
        }

        .row {
            display: flex;
            gap: 4px;
            justify-content: center;
        }

        .key {
            min-width: 32px;
            height: 48px;
            border: none;
            border-radius: 6px;
            background: #16213e;
            color: #eee;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.1s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .key:active {
            background: #e94560;
            transform: scale(0.95);
        }

        .key.wide {
            min-width: 64px;
        }

        .key.space {
            min-width: 180px;
        }

        .key.modifier {
            background: #0f3460;
            font-size: 12px;
        }

        .key.modifier.active {
            background: #e94560;
        }

        .row.func-row {
            gap: 8px;
        }

        .key.func {
            min-width: 48px;
            height: 36px;
            font-size: 12px;
            background: #0f3460;
        }

        .footer {
            padding: 12px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <span style="font-weight: bold;">远程键盘</span>
        <div class="status">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">连接中...</span>
        </div>
    </div>

    <div class="text-input-area">
        <div class="text-input-row">
            <input type="text" id="textInput" placeholder="输入文字...">
            <button class="send-btn" id="sendBtn">发送</button>
        </div>
    </div>

    <div class="keyboard">
        <!-- 功能键行 -->
        <div class="row func-row">
            <button class="key func" data-key="escape">Esc</button>
            <button class="key func" data-key="f1">F1</button>
            <button class="key func" data-key="f2">F2</button>
            <button class="key func" data-key="f3">F3</button>
            <button class="key func" data-key="f4">F4</button>
            <button class="key func" data-key="f5">F5</button>
            <button class="key func" data-key="f6">F6</button>
            <button class="key func" data-key="f7">F7</button>
            <button class="key func" data-key="f8">F8</button>
            <button class="key func" data-key="f9">F9</button>
            <button class="key func" data-key="f10">F10</button>
            <button class="key func" data-key="f11">F11</button>
            <button class="key func" data-key="f12">F12</button>
        </div>

        <!-- 第一行: 数字 -->
        <div class="row">
            <button class="key" data-key="1">1</button>
            <button class="key" data-key="2">2</button>
            <button class="key" data-key="3">3</button>
            <button class="key" data-key="4">4</button>
            <button class="key" data-key="5">5</button>
            <button class="key" data-key="6">6</button>
            <button class="key" data-key="7">7</button>
            <button class="key" data-key="8">8</button>
            <button class="key" data-key="9">9</button>
            <button class="key" data-key="0">0</button>
            <button class="key wide" data-key="backspace">⌫</button>
        </div>

        <!-- 第二行: QWERTY -->
        <div class="row">
            <button class="key" data-key="q">Q</button>
            <button class="key" data-key="w">W</button>
            <button class="key" data-key="e">E</button>
            <button class="key" data-key="r">R</button>
            <button class="key" data-key="t">T</button>
            <button class="key" data-key="y">Y</button>
            <button class="key" data-key="u">U</button>
            <button class="key" data-key="i">I</button>
            <button class="key" data-key="o">O</button>
            <button class="key" data-key="p">P</button>
            <button class="key" data-key="bracket_left">[</button>
            <button class="key" data-key="bracket_right">]</button>
        </div>

        <!-- 第三行: ASDF -->
        <div class="row">
            <button class="key" data-key="a">A</button>
            <button class="key" data-key="s">S</button>
            <button class="key" data-key="d">D</button>
            <button class="key" data-key="f">F</button>
            <button class="key" data-key="g">G</button>
            <button class="key" data-key="h">H</button>
            <button class="key" data-key="j">J</button>
            <button class="key" data-key="k">K</button>
            <button class="key" data-key="l">L</button>
            <button class="key" data-key="semicolon">;</button>
            <button class="key" data-key="quote">'</button>
            <button class="key wide" data-key="enter">Enter</button>
        </div>

        <!-- 第四行: ZXCV -->
        <div class="row">
            <button class="key modifier" data-key="shift" data-modifier="shift">⇧</button>
            <button class="key" data-key="z">Z</button>
            <button class="key" data-key="x">X</button>
            <button class="key" data-key="c">C</button>
            <button class="key" data-key="v">V</button>
            <button class="key" data-key="b">B</button>
            <button class="key" data-key="n">N</button>
            <button class="key" data-key="m">M</button>
            <button class="key" data-key="comma">,</button>
            <button class="key" data-key="period">.</button>
            <button class="key" data-key="slash">/</button>
            <button class="key modifier" data-key="ctrl" data-modifier="ctrl">Ctrl</button>
        </div>

        <!-- 第五行: 控制键 -->
        <div class="row">
            <button class="key modifier" data-key="alt" data-modifier="alt">Alt</button>
            <button class="key modifier" data-key="super" data-modifier="super">⊞</button>
            <button class="key space" data-key="space">空格</button>
            <button class="key modifier" data-key="tab" data-modifier="tab">Tab</button>
        </div>

        <!-- 方向键 -->
        <div class="row">
            <button class="key" data-key="up">↑</button>
        </div>
        <div class="row">
            <button class="key" data-key="left">←</button>
            <button class="key" data-key="down">↓</button>
            <button class="key" data-key="right">→</button>
        </div>
    </div>

    <div class="footer">
        在 Linux 电脑上打开此页面，当前焦点的窗口将接收按键
    </div>

    <script>
        // 当前修饰键状态
        let activeModifiers = new Set();

        // 检查连接状态
        async function checkStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                const dot = document.getElementById('statusDot');
                const text = document.getElementById('statusText');

                if (data.status === 'ok') {
                    dot.classList.add('connected');
                    text.textContent = '已连接';
                } else {
                    dot.classList.remove('connected');
                    text.textContent = data.message || '未连接';
                }
            } catch (e) {
                document.getElementById('statusDot').classList.remove('connected');
                document.getElementById('statusText').textContent = '未连接';
            }
        }

        // 发送按键
        async function sendKey(key, modifiers = []) {
            try {
                await fetch('/api/key', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key, modifiers: modifiers.length ? modifiers : undefined})
                });
            } catch (e) {
                console.error('发送按键失败:', e);
            }
        }

        // 发送文本
        async function sendText(text) {
            try {
                await fetch('/api/text', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({content: text})
                });
            } catch (e) {
                console.error('发送文本失败:', e);
            }
        }

        // 键盘按钮点击
        document.querySelectorAll('.key').forEach(btn => {
            btn.addEventListener('click', () => {
                const key = btn.dataset.key;
                const modifier = btn.dataset.modifier;

                if (modifier) {
                    // 修饰键切换
                    if (activeModifiers.has(modifier)) {
                        activeModifiers.delete(modifier);
                        btn.classList.remove('active');
                    } else {
                        activeModifiers.add(modifier);
                        btn.classList.add('active');
                    }
                } else {
                    // 普通按键
                    const modifiers = Array.from(activeModifiers);
                    sendKey(key, modifiers);

                    // 清空修饰键状态
                    activeModifiers.clear();
                    document.querySelectorAll('.key.modifier.active').forEach(b => {
                        b.classList.remove('active');
                    });
                }
            });
        });

        // 文本发送
        document.getElementById('sendBtn').addEventListener('click', () => {
            const input = document.getElementById('textInput');
            const text = input.value.trim();
            if (text) {
                sendText(text);
                input.value = '';
            }
        });

        // 回车发送
        document.getElementById('textInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('sendBtn').click();
            }
        });

        // 定期检查状态
        checkStatus();
        setInterval(checkStatus, 5000);
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)


# ============================================================================
# 启动
# ============================================================================

def main():
    port = 5000
    host = '0.0.0.0'

    # 检查 xdotool 是否可用
    import subprocess
    try:
        subprocess.run(['xdotool', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("错误: xdotool 未安装")
        logger.error("请运行: sudo apt install xdotool  (Debian/Ubuntu)")
        logger.error("或:   sudo dnf install xdotool  (Fedora)")
        sys.exit(1)

    logger.info(f"启动服务器: http://{host}:{port}")
    logger.info("手机访问: http://<本机IP>:5000")
    logger.info("按 Ctrl+C 停止服务器")

    # 预初始化 injector
    get_injector()

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()

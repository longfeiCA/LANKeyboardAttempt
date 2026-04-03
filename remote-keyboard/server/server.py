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
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex: 1;
            min-height: 120px;
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
            min-height: 40px;
        }

        .button-row {
            display: flex;
            gap: 8px;
        }

        .send-btn {
            flex: 1;
            padding: 14px;
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
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: #16213e;
            border-top: 1px solid #0f3460;
        }

        .row {
            display: flex;
            gap: 8px;
            justify-content: center;
        }

        .key {
            flex: 1;
            height: 52px;
            border: none;
            border-radius: 8px;
            background: #0f3460;
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
            transform: scale(0.98);
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
        <textarea id="textInput" placeholder="输入文字..."></textarea>
        <div class="button-row">
            <button class="key" data-key="backspace">⌫ 删除</button>
            <button class="key" data-key="enter">↵ 回车</button>
            <button class="send-btn" id="sendBtn">发送</button>
        </div>
    </div>

    <div class="footer">
        在 Linux 电脑上打开此页面，当前焦点的窗口将接收按键
    </div>

    <script>
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
        async function sendKey(key) {
            try {
                await fetch('/api/key', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key})
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

        // 按钮点击 - 只处理 backspace 和 enter
        document.querySelectorAll('.key').forEach(btn => {
            btn.addEventListener('click', () => {
                const key = btn.dataset.key;
                sendKey(key);
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

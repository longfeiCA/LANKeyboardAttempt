"""
键盘注入模块 - 使用 xdotool 模拟键盘输入
xdotool 通过 X11 模拟按键，不需要 root 权限
"""

import logging
import subprocess
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# 检测 Wayland
IS_WAYLAND = bool(os.environ.get('WAYLAND_DISPLAY'))

# xdotool key 名称映射
KEY_MAP = {
    # 字母 (小写)
    **{chr(c): f"key {chr(c)}" for c in range(ord('a'), ord('z') + 1)},
    # 数字
    **{str(i): f"key {i}" for i in range(10)},
    # 功能键
    'enter': 'key Return',
    'tab': 'key Tab',
    'space': 'key space',
    'backspace': 'key BackSpace',
    'delete': 'key Delete',
    'escape': 'key Escape',
    'esc': 'key Escape',
    # 方向键
    'up': 'key Up',
    'down': 'key Down',
    'left': 'key Left',
    'right': 'key Right',
    # 控制键
    'ctrl': 'key Ctrl',
    'shift': 'key Shift',
    'alt': 'key Alt',
    'super': 'key Super',
    'meta': 'key Super',
    # 符号
    'comma': 'key comma',
    'period': 'key period',
    'slash': 'key slash',
    'semicolon': 'key semicolon',
    'quote': 'key apostrophe',
    'backslash': 'key backslash',
    'bracket_left': 'key bracketleft',
    'bracket_right': 'key bracketright',
    'minus': 'key minus',
    'equal': 'key equal',
    'backquote': 'key grave',
    'grave': 'key grave',
    # 其他
    'home': 'key Home',
    'end': 'key End',
    'pageup': 'key Prior',
    'pagedown': 'key Next',
    'insert': 'key Insert',
}

# 修饰键
MODIFIERS = ['ctrl', 'shift', 'alt', 'super']


class KeyboardInjector:
    def __init__(self):
        self._initialized = True
        self._wayland = IS_WAYLAND

    def initialize(self) -> bool:
        """xdotool 不需要初始化"""
        logger.info(f"xdotool 键盘注入器就绪 (Wayland={self._wayland})")
        return True

    def _run(self, cmd: list[str], input_text: str = None) -> bool:
        """运行命令"""
        try:
            kwargs = {'capture_output': True, 'text': True, 'timeout': 2}
            if input_text:
                kwargs['input'] = input_text
            result = subprocess.run(cmd, **kwargs)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            return False

    def send_key(self, key: str, modifiers: list[str] = None):
        """
        发送单个按键

        Args:
            key: 按键名称 (如 'a', 'enter', 'ctrl')
            modifiers: 修饰键列表 (如 ['ctrl', 'shift'])
        """
        modifiers = modifiers or []

        args = []

        # 先添加修饰键 (keydown)
        for mod in modifiers:
            mod_lower = mod.lower()
            if mod_lower in MODIFIERS:
                args.extend(['keydown', mod_lower])

        # 添加主键
        key_lower = key.lower()
        if key_lower in KEY_MAP:
            _, keyname = KEY_MAP[key_lower].split()
            args.extend(['key', keyname])
        else:
            args.extend(['key', key_lower])

        # 添加修饰键 keyup
        for mod in reversed(modifiers):
            mod_lower = mod.lower()
            if mod_lower in MODIFIERS:
                args.extend(['keyup', mod_lower])

        self._run(['xdotool'] + args)
        logger.info(f"发送按键: key={key}, modifiers={modifiers}")

    def send_text(self, text: str):
        """
        发送文本
        - 纯ASCII: xdotool type
        - 含中文: 剪贴板 + Ctrl+V
        """
        has_cjk = any(ord(c) > 127 for c in text)

        if has_cjk:
            # 中文: 复制到剪贴板，然后粘贴
            self._copy_to_clipboard(text)
            import time; time.sleep(0.2)  # 等待剪贴板同步
            # 尝试 Ctrl+Shift+V (终端/命令行)，不行再用 Ctrl+V
            if not self._run(['xdotool', 'key', 'ctrl+shift+v']):
                self._run(['xdotool', 'key', 'ctrl+v'])
            logger.info(f"发送中文(剪贴板): {text[:30]}...")
        else:
            self._run(['xdotool', 'type', '--', text])
            logger.info(f"发送文本: {text[:30]}...")

    def _copy_to_clipboard(self, text: str):
        """复制到剪贴板"""
        # 尝试 Wayland
        if self._run(['wl-copy'], input_text=text):
            return

        # 尝试 xclip
        try:
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-i'],
                input=text.encode('utf-8'),
                capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return
        except FileNotFoundError:
            pass

        # 尝试 xsel
        try:
            result = subprocess.run(
                ['xsel', '--clipboard', '--input'],
                input=text.encode('utf-8'),
                capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return
        except FileNotFoundError:
            pass

        logger.warning("未找到剪贴板工具 wl-copy/xclip/xsel")

    def cleanup(self):
        pass


# 全局实例
_injector: Optional[KeyboardInjector] = None


def get_injector() -> KeyboardInjector:
    """获取全局键盘注入器实例"""
    global _injector
    if _injector is None:
        _injector = KeyboardInjector()
        _injector.initialize()
    return _injector

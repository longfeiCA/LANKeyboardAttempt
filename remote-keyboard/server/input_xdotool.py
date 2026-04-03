"""
键盘注入模块 - 使用 xdotool 模拟键盘输入
xdotool 通过 X11 模拟按键，不需要 root 权限
"""

import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

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
    # 符号 - xdotool 使用单字符
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

    def initialize(self) -> bool:
        """xdotool 不需要初始化"""
        logger.info("xdotool 键盘注入器就绪")
        return True

    def _run_xdotool(self, args: list[str]) -> bool:
        """运行 xdotool 命令"""
        try:
            result = subprocess.run(
                ['xdotool'] + args,
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode != 0:
                logger.warning(f"xdotool 警告: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"xdotool 执行失败: {e}")
            return False

    def send_key(self, key: str, modifiers: list[str] = None):
        """
        发送单个按键

        Args:
            key: 按键名称 (如 'a', 'enter', 'ctrl')
            modifiers: 修饰键列表 (如 ['ctrl', 'shift'])
        """
        modifiers = modifiers or []

        # 构建命令
        args = []

        # 先添加修饰键 (keydown)
        for mod in modifiers:
            mod_lower = mod.lower()
            if mod_lower in MODIFIERS:
                args.append('keydown')
                args.append(mod_lower)

        # 添加主键
        key_lower = key.lower()
        if key_lower in KEY_MAP:
            # 提取 key 后面的部分
            cmd = KEY_MAP[key_lower]
            _, keyname = cmd.split()
            args.append('key')
            args.append(keyname)
        else:
            # 尝试直接发送
            args.append('key')
            args.append(key_lower)

        # 添加修饰键 keyup
        for mod in reversed(modifiers):
            mod_lower = mod.lower()
            if mod_lower in MODIFIERS:
                args.append('keyup')
                args.append(mod_lower)

        self._run_xdotool(args)
        logger.info(f"发送按键: key={key}, modifiers={modifiers}")

    def send_text(self, text: str):
        """
        发送一串文本

        Args:
            text: 要发送的文本
        """
        # xdotool type 直接输入文本
        self._run_xdotool(['type', '--', text])
        logger.info(f"发送文本: {text[:50]}...")

    def cleanup(self):
        """清理（xdotool 不需要）"""
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

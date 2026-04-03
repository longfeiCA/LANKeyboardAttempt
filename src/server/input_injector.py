"""
键盘注入模块 - 使用 python-uinput 模拟物理键盘输入
需要在 Linux 上有 uinput 权限（通常需要 root 或加入 input 组）
"""

import logging
import time
from typing import Optional

try:
    import uinput
except ImportError:
    uinput = None

logger = logging.getLogger(__name__)

# 按键码映射表 (Linux input event keycode)
KEY_MAP = {
    # 字母 A-Z
    **{chr(c): 30 + i for i, c in enumerate(range(ord('a'), ord('z') + 1))},
    # 数字 0-9
    **{str(i): 1 + i for i in range(10)},
    # 功能键
    'enter': 28,
    'tab': 15,
    'space': 57,
    'backspace': 14,
    'delete': 111,
    'escape': 1,
    'esc': 1,
    # 方向键
    'up': 103,
    'down': 108,
    'left': 105,
    'right': 106,
    # 控制键
    'ctrl': 29,
    'shift': 42,
    'alt': 56,
    'super': 127,  # Windows/Meta key
    'meta': 127,
    # 符号
    'comma': 51,
    'period': 52,
    'slash': 53,
    'semicolon': 39,
    'quote': 40,
    'backslash': 43,
    'bracket_left': 26,
    'bracket_right': 27,
    'minus': 12,
    'equal': 13,
    'backquote': 41,
    'grave': 41,
    # 其他
    'home': 102,
    'end': 107,
    'pageup': 104,
    'pagedown': 109,
    'insert': 110,
}

# 修饰键的 keycode
MODIFIER_KEYCODES = {
    'ctrl': 29,
    'shift': 42,
    'alt': 56,
    'super': 127,
}


class KeyboardInjector:
    def __init__(self):
        self.device: Optional['uinput.Device'] = None
        self._initialized = False

    def initialize(self) -> bool:
        """初始化 uinput 虚拟键盘设备"""
        if uinput is None:
            logger.error("python-uinput 未安装")
            return False

        try:
            # 创建所有可能的按键事件
            events = (
                uinput.EV_KEY,
                uinput.EV_REL,
                uinput.EV_ABS,
            )

            # 收集所有需要的键码
            key_codes = set(KEY_MAP.values())
            key_codes.update(MODIFIER_KEYCODES.values())
            key_codes.add(0)  # RELEASE 事件需要

            # 创建虚拟设备
            self.device = uinput.Device(key_codes)
            self._initialized = True
            logger.info("uinput 虚拟键盘设备创建成功")
            return True

        except Exception as e:
            logger.error(f"创建 uinput 设备失败: {e}")
            logger.error("请确保有 root 权限或 uinput 模块已加载")
            return False

    def _press_key(self, keycode: int):
        """按下按键"""
        if self.device:
            self.device.emit(uinput.EV_KEY, keycode, 1)  # 1 = pressed

    def _release_key(self, keycode: int):
        """释放按键"""
        if self.device:
            self.device.emit(uinput.EV_KEY, keycode, 0)  # 0 = released

    def _sync(self):
        """同步事件（必须调用以使事件生效）"""
        if self.device:
            self.device.emit(uinput.EV_SYN, uinput.SYN_REPORT, 0)

    def send_key(self, key: str, modifiers: list[str] = None):
        """
        发送单个按键

        Args:
            key: 按键名称 (如 'a', 'enter', 'ctrl')
            modifiers: 修饰键列表 (如 ['ctrl', 'shift'])
        """
        if not self._initialized:
            logger.error("设备未初始化")
            return

        modifiers = modifiers or []

        # 获取修饰键码
        modifier_keycodes = []
        for mod in modifiers:
            mod_lower = mod.lower()
            if mod_lower in MODIFIER_KEYCODES:
                modifier_keycodes.append(MODIFIER_KEYCODES[mod_lower])
            elif mod_lower in KEY_MAP:
                modifier_keycodes.append(KEY_MAP[mod_lower])

        # 按下修饰键
        for code in modifier_keycodes:
            self._press_key(code)

        # 按下主键
        key_lower = key.lower()
        if key_lower in KEY_MAP:
            self._press_key(KEY_MAP[key_lower])
            self._release_key(KEY_MAP[key_lower])
        else:
            logger.warning(f"未知按键: {key}")
            return

        # 释放修饰键
        for code in reversed(modifier_keycodes):
            self._release_key(code)

        # 同步
        self._sync()

    def send_text(self, text: str, delay: float = 0.01):
        """
        发送一串文本（逐字输入）

        Args:
            text: 要发送的文本
            delay: 每个字符之间的延迟（秒）
        """
        if not self._initialized:
            logger.error("设备未初始化")
            return

        for char in text:
            keycode = self._get_keycode_for_char(char)
            if keycode is None:
                logger.warning(f"无法输入字符: {char}")
                continue

            # 如果是大写字母，需要 Shift
            modifiers = []
            if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?':
                modifiers.append('shift')

            self.send_key(keycode if keycode else char, modifiers)
            time.sleep(delay)

    def _get_keycode_for_char(self, char: str) -> Optional[int]:
        """获取字符对应的按键码"""
        c = char.lower()

        # 检查字母
        if c.isalpha():
            return KEY_MAP.get(c)

        # 检查数字
        if c.isdigit():
            return KEY_MAP.get(c)

        # 检查空格
        if char == ' ':
            return KEY_MAP.get('space')

        # 检查常见符号
        symbol_map = {
            '!': ('1', ['shift']),
            '@': ('2', ['shift']),
            '#': ('3', ['shift']),
            '$': ('4', ['shift']),
            '%': ('5', ['shift']),
            '^': ('6', ['shift']),
            '&': ('7', ['shift']),
            '*': ('8', ['shift']),
            '(': ('9', ['shift']),
            ')': ('0', ['shift']),
            '_': ('minus', ['shift']),
            '+': ('equal', ['shift']),
            '{': ('bracket_left', ['shift']),
            '}': ('bracket_right', ['shift']),
            '|': ('backslash', ['shift']),
            ':': ('semicolon', ['shift']),
            '"': ('quote', ['shift']),
            '<': ('comma', ['shift']),
            '>': ('period', ['shift']),
            '?': ('slash', ['shift']),
            '~': ('grave', ['shift']),
        }

        if char in symbol_map:
            key, mods = symbol_map[char]
            return KEY_MAP.get(key)

        # 其他符号直接用自身
        return KEY_MAP.get(c)

    def cleanup(self):
        """清理设备"""
        if self.device:
            # 销毁设备
            self.device = None
            self._initialized = False
            logger.info("uinput 设备已清理")


# 全局实例
_injector: Optional[KeyboardInjector] = None


def get_injector() -> KeyboardInjector:
    """获取全局键盘注入器实例"""
    global _injector
    if _injector is None:
        _injector = KeyboardInjector()
    return _injector
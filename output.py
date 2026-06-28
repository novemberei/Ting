"""Ting 语音输入工具 - 输出模块（三级输出策略）"""

import time
from enum import Enum, auto

import win32clipboard
import win32gui
from pynput.keyboard import Controller, Key


class OutputResult(Enum):
    """输出结果枚举"""
    APP_WIDGET = auto()   # 焦点在本应用，通过回调写入
    PASTED = auto()       # 通过剪贴板+Ctrl+V 粘贴成功
    CLIPBOARD = auto()    # 仅复制到剪贴板（回退）
    FAILED = auto()       # 全部失败


class OutputManager:
    """封装三级输出策略"""

    def __init__(self, config, app_hwnd: int):
        """
        Args:
            config: Config 实例
            app_hwnd: 本应用的窗口句柄
        """
        self.config = config
        self.app_hwnd = app_hwnd
        self._kb = Controller()

    # ── 公开方法 ──────────────────────────────────────────

    def output(self, text: str, text_widget_callback) -> OutputResult:
        """核心输出方法，按优先级尝试三级输出。

        Args:
            text: 要输出的文本
            text_widget_callback: 签名 callback(text: str) 用于写入本应用控件

        Returns:
            OutputResult 枚举值
        """
        try:
            focused_hwnd = self.get_focused_window()

            # 第一级：焦点是本应用窗口 → 回调写入
            if self._is_self_window(focused_hwnd):
                text_widget_callback(text)
                return OutputResult.APP_WIDGET

            # clipboard_only 模式：跳过模拟粘贴，直接复制到剪贴板
            if self.config.output_method == "clipboard_only":
                self._clipboard_copy(text)
                return OutputResult.CLIPBOARD

            # 第二级：焦点是其他窗口 → 剪贴板粘贴
            return self._paste_via_clipboard(text)

        except Exception:
            # 第三级回退：尝试仅复制到剪贴板
            try:
                self._clipboard_copy(text)
                return OutputResult.CLIPBOARD
            except Exception:
                return OutputResult.FAILED

    def get_focused_window(self) -> int:
        """获取当前前台窗口句柄"""
        return win32gui.GetForegroundWindow()

    # ── 内部方法 ──────────────────────────────────────────

    def _is_self_window(self, hwnd: int) -> bool:
        """判断给定句柄是否属于本应用窗口"""
        return hwnd == self.app_hwnd

    def _paste_via_clipboard(self, text: str) -> OutputResult:
        """保存剪贴板 → 设置新文本 → 模拟 Ctrl+V → 恢复剪贴板"""
        saved = self._save_clipboard()
        try:
            self._clipboard_copy(text)
            # 模拟 Ctrl+V
            self._kb.press(Key.ctrl_l)
            self._kb.press('v')
            self._kb.release('v')
            self._kb.release(Key.ctrl_l)
            # 等待粘贴完成
            time.sleep(0.05)
            return OutputResult.PASTED
        finally:
            self._restore_clipboard(saved)

    def _clipboard_copy(self, text: str) -> None:
        """将文本写入剪贴板"""
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()

    @staticmethod
    def _save_clipboard() -> str:
        """保存当前剪贴板内容"""
        try:
            win32clipboard.OpenClipboard()
            try:
                text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            except TypeError:
                text = ""
            win32clipboard.CloseClipboard()
            return text
        except Exception:
            return ""

    @staticmethod
    def _restore_clipboard(saved_text: str) -> None:
        """恢复剪贴板内容"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(saved_text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except Exception:
            pass

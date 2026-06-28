"""Ting 语音输入工具 - UI 界面模块"""

import tkinter as tk
from typing import Callable, Optional

import win32gui


class AppUI:
    """Ting 语音输入工具主界面（无边框圆形按钮）"""

    BG_COLOR = "#010101"  # 透明色
    BTN_SIZE = 70
    WIN_W = 120
    WIN_H = 110

    def __init__(self, config):
        self.config = config
        self._on_toggle: Optional[Callable[[], None]] = None
        self._is_recording = False
        self._drag_x = 0
        self._drag_y = 0

        # 主窗口
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes('-topmost', True)
        self.root.configure(bg=self.BG_COLOR)
        self.root.attributes('-transparentcolor', self.BG_COLOR)

        # 窗口位置：屏幕右下角
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - self.WIN_W - 50
        y = screen_h - self.WIN_H - 100
        self.root.geometry(f"{self.WIN_W}x{self.WIN_H}+{x}+{y}")

        # Canvas 绘制圆形按钮
        self.canvas = tk.Canvas(
            self.root, width=self.WIN_W, height=82,
            bg=self.BG_COLOR, highlightthickness=0
        )
        self.canvas.pack(pady=(3, 0))

        self._cx = self.WIN_W // 2  # 圆心 x
        self._cy = 41  # 圆心 y
        self._draw_button()

        # 按钮事件
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", lambda e: self._draw_button(hover=True))
        self.canvas.bind("<Leave>", lambda e: self._draw_button(hover=False))
        self.canvas.bind("<Button-3>", self._on_right_click)  # 右键退出

        # 拖拽（中键按住拖拽）
        self.root.bind("<ButtonPress-2>", self._drag_start)
        self.root.bind("<B2-Motion>", self._drag_motion)

        # 状态栏
        self.status_label = tk.Label(
            self.root, text="F8",
            font=("Microsoft YaHei", 8),
            fg="#888888", bg=self.BG_COLOR
        )
        self.status_label.pack()

    def _draw_button(self, hover=False):
        """绘制圆形按钮"""
        self.canvas.delete("btn")
        r = self.BTN_SIZE // 2
        x, y = self._cx, self._cy

        if self._is_recording:
            color = "#ff6659" if hover else "#f44336"
            icon = "⏹"
        else:
            color = "#66BB6A" if hover else "#4CAF50"
            icon = "🎤"

        # 圆形
        self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill=color, outline="", tags="btn"
        )
        # 图标
        self.canvas.create_text(
            x, y, text=icon,
            font=("Segoe UI Emoji", 22), fill="white", tags="btn"
        )

    def _is_in_button(self, event):
        """检查坐标是否在圆形按钮范围内"""
        dx = event.x - self._cx
        dy = event.y - self._cy
        return (dx * dx + dy * dy) <= (self.BTN_SIZE // 2) ** 2

    def _on_click(self, event):
        """左键点击"""
        if self._is_in_button(event) and self._on_toggle:
            self._on_toggle()

    def _on_right_click(self, event):
        """右键点击：若在按钮区域内则退出"""
        if self._is_in_button(event):
            self._on_close()

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_motion(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def get_root(self) -> tk.Tk:
        """返回 root 窗口"""
        return self.root

    def get_hwnd(self) -> int:
        """返回本应用的顶层窗口句柄"""
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        while True:
            parent = win32gui.GetParent(hwnd)
            if parent == 0 or parent == hwnd:
                break
            hwnd = parent
        return hwnd

    def set_status(self, status: str):
        """更新状态栏（线程安全）"""
        self.root.after(0, self._do_set_status, status)

    def _do_set_status(self, status: str):
        self.status_label.config(text=status)

    def set_recording_state(self, is_recording: bool):
        """更新录音按钮状态（线程安全）"""
        self.root.after(0, self._do_set_recording_state, is_recording)

    def _do_set_recording_state(self, is_recording: bool):
        self._is_recording = is_recording
        self._draw_button()

    def set_on_toggle(self, callback: Callable[[], None]):
        """设置录音按钮的回调"""
        self._on_toggle = callback

    def _on_close(self):
        """窗口关闭处理"""
        self.root.destroy()

    def start_mainloop(self):
        """启动 tkinter 主循环"""
        self.root.mainloop()

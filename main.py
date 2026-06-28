"""Ting 语音输入工具 - 入口"""

import asyncio
import threading
import time

import numpy as np
from pynput import keyboard as pynput_keyboard

from config import load as load_config
from asr_engine import ASREngine
from vad import VADDetector
from recorder import Recorder
from output import OutputManager, OutputResult
from ui import AppUI


class TingApp:
    """Ting 语音输入工具主应用"""

    def __init__(self):
        # 加载配置
        self.config = load_config()

        # 初始化 ASR 引擎（不加载模型）
        self.engine = ASREngine(self.config)

        # 初始化 VAD（不加载模型）
        self.vad = VADDetector(self.config)

        # 初始化 UI
        self.ui = AppUI(self.config)

        # 初始化输出管理器
        self.output_mgr = OutputManager(self.config, self.ui.get_hwnd())

        # 初始化录音器
        self.recorder = Recorder(self.config, self._on_audio_chunk)

        # 状态
        self.recording_event = threading.Event()
        self._audio_buffer: list[np.ndarray] = []
        self._focused_hwnd = 0  # 录音开始时的焦点窗口
        self._stopping_lock = threading.Lock()  # 防止 _stop_recording 被并发调用

        # 连接 UI 回调
        self.ui.set_on_toggle(self.toggle_recording)

    def _on_audio_chunk(self, chunk):
        """录音回调：缓存音频 + VAD 检测（在 sounddevice C 线程中）"""
        self._audio_buffer.append(chunk.copy())

        # VAD 检测（在录音回调线程中）
        if self.config.vad_enabled and self.vad.model is not None:
            try:
                if self.vad.detect(chunk):
                    # 语音段结束，触发自动停止（调度到主线程）
                    self.ui.get_root().after(0, self._stop_recording)
            except Exception:
                pass

    def toggle_recording(self):
        """切换录音状态（热键和按钮共用）"""
        if self.recorder.is_recording():
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """开始录音"""
        # 记录当前焦点窗口
        self._focused_hwnd = self.output_mgr.get_focused_window()

        # 重置音频缓冲
        self._audio_buffer = []

        # 重置 VAD
        if self.config.vad_enabled:
            self.vad.reset()

        # 启动录音
        self.recorder.start()

        # 更新 UI
        self.ui.set_recording_state(True)
        self.ui.set_status("录音中 | F8")

    def _stop_recording(self):
        """停止录音并一次性识别"""
        # 原子 guard：防止 VAD 自动停止与热键手动停止并发进入
        if not self._stopping_lock.acquire(blocking=False):
            return  # 另一个 _stop_recording 正在执行
        try:
            if not self.recorder.is_recording():
                return

            # 短暂延迟确保最后一帧音频已被回调捕获
            time.sleep(0.05)

            # 停止录音
            self.recorder.stop()
            self.recording_event.clear()
            self.ui.set_recording_state(False)
            self.ui.set_status("识别中...")

            # 拼接音频并一次性识别
            if self._audio_buffer:
                # 追加尾部静音（800ms），防止末字被截断
                tail_silence = np.zeros(
                    int(self.config.sample_rate * 0.8), dtype=np.float32
                )
                self._audio_buffer.append(tail_silence)

                full_audio = np.concatenate(self._audio_buffer)
                self._audio_buffer = []

                # 在后台线程中识别（避免阻塞 UI）
                threading.Thread(
                    target=self._transcribe_and_output,
                    args=(full_audio,),
                    daemon=True,
                ).start()
            else:
                self.ui.set_status("空闲 | F8")
        finally:
            self._stopping_lock.release()

    def _transcribe_and_output(self, audio):
        """后台识别并输出（在独立线程中运行 asyncio 事件循环）"""
        try:
            text = asyncio.run(self.engine.transcribe(audio))
            if text.strip():
                result = self.output_mgr.output(text, lambda t: None)
                # 更新状态栏
                status_map = {
                    OutputResult.APP_WIDGET: "已写入",
                    OutputResult.PASTED: "已粘贴",
                    OutputResult.CLIPBOARD: "已复制",
                    OutputResult.FAILED: "失败",
                }
                self.ui.set_status(f"{status_map.get(result, '')} | F8")
            else:
                self.ui.set_status("未识别 | F8")
        except Exception as e:
            print(f"[main] 识别失败: {e}")
            self.ui.set_status("识别失败 | F8")

    def _on_hotkey_press(self, key):
        """pynput 全局热键回调"""
        try:
            if key == pynput_keyboard.Key.f8:
                # 使用 after 调度到主线程
                self.ui.get_root().after(0, self.toggle_recording)
        except Exception:
            pass

    def run(self):
        """启动应用"""
        print("[ting] Ting 语音输入工具启动")
        print(f"[ting] 热键: {self.config.hotkey.upper()}")
        print(f"[ting] VAD: {'启用' if self.config.vad_enabled else '禁用'}")

        # 加载模型（在 UI 启动前，避免阻塞 UI 线程）
        print("[ting] 正在加载模型...")
        self.engine.load()
        if self.config.vad_enabled:
            self.vad.load()
        print("[ting] 模型加载完成")

        # 启动 pynput 热键监听
        listener = pynput_keyboard.Listener(on_press=self._on_hotkey_press)
        listener.daemon = True
        listener.start()

        # 更新状态栏
        self.ui.set_status("F8")

        # 启动 UI 主循环
        self.ui.start_mainloop()

        # 退出清理
        listener.stop()
        print("[ting] 应用退出")


if __name__ == "__main__":
    app = TingApp()
    app.run()


"""Ting 语音输入工具 - 录音模块"""

import threading
from typing import Callable, Optional

import numpy as np
import sounddevice as sd


class Recorder:
    """基于 sounddevice 的流式录音模块"""

    def __init__(self, config, on_chunk: Callable[[np.ndarray], None]):
        """
        config: Config 对象，提供 sample_rate, chunk_size_ms 等参数
        on_chunk: 音频回调函数，每个 chunk 调用一次
        """
        self.config = config
        self.on_chunk = on_chunk
        self._stream: Optional[sd.InputStream] = None
        self._recording = threading.Event()

        # 计算 chunk 大小（samples per block）
        self._chunk_samples = int(config.sample_rate * config.chunk_size_ms / 1000)

    def start(self):
        """开始录音"""
        if self._recording.is_set():
            return

        self._recording.set()

        try:
            self._stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self._chunk_samples,
                callback=self._audio_callback,
            )
            self._stream.start()
            print(f"[recorder] 录音开始 (采样率={self.config.sample_rate}, chunk={self.config.chunk_size_ms}ms)")
        except Exception as e:
            self._recording.clear()
            raise RuntimeError(f"无法启动录音: {e}")

    def stop(self):
        """停止录音"""
        self._recording.clear()

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        print("[recorder] 录音停止")

    def is_recording(self) -> bool:
        """返回当前录音状态"""
        return self._recording.is_set()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """sounddevice 回调，在独立 C 线程中执行"""
        if status:
            print(f"[recorder] 音频状态: {status}")

        if self._recording.is_set():
            # 将音频数据通过回调传出（仅做 put 操作，避免 GIL 竞争）
            # indata shape: (frames, 1), 转为 1D float32 array
            chunk = indata[:, 0].copy()
            try:
                self.on_chunk(chunk)
            except Exception as e:
                print(f"[recorder] 回调异常: {e}")

    @staticmethod
    def list_devices() -> list[str]:
        """列出可用的音频输入设备"""
        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                input_devices.append(f"[{i}] {dev['name']} (输入通道: {dev['max_input_channels']})")
        return input_devices

"""Ting 语音输入工具 - VAD (语音活动检测) 模块"""

import os

import numpy as np
from funasr import AutoModel


class VADDetector:
    """基于 FunASR fsmn-vad 的语音活动检测器

    流式模式下，fsmn-vad 在检测到语音段结束（尾部静音超过阈值）时
    返回非空 segments，直接作为"语音段结束"信号使用。
    """

    def __init__(self, config):
        """保存配置，不加载模型"""
        self.config = config
        self.model = None
        self._cache = {}
        self._segment_ended = False  # 最近一次 detect 是否检测到段结束

    def load(self):
        """加载 VAD 模型"""
        if self.config.model_cache_dir:
            os.environ["MODELSCOPE_CACHE"] = self.config.model_cache_dir
            os.environ["HF_HOME"] = self.config.model_cache_dir
            print(f"[vad] 模型缓存路径: {self.config.model_cache_dir}")

        print(f"[vad] 正在加载 VAD 模型 {self.config.vad_model}...")
        self.model = AutoModel(
            model=self.config.vad_model,
            device=self.config.device,
            hub=self.config.model_hub,
            max_end_silence_time=self.config.vad_silence_ms,
            model_cache_dir=self.config.model_cache_dir or None,
        )
        print("[vad] VAD 模型加载完成")

    def reset(self):
        """重置检测状态（新录音开始时调用）"""
        self._cache = {}
        self._segment_ended = False

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        送入音频 chunk，返回是否检测到语音段结束。

        fsmn-vad 流式模式下，当尾部静音超过 max_end_silence_time 时
        返回非空 segments [[start_ms, end_ms], ...]，表示一个语音段已结束。
        """
        if self.model is None:
            return False  # 模型未加载时不触发自动停止

        try:
            result = self.model.generate(
                input=audio_chunk,
                cache=self._cache,
                is_final=False,
            )

            # res[0]["value"] 非空 → 检测到语音段结束
            self._segment_ended = bool(
                result
                and len(result) > 0
                and isinstance(result[0], dict)
                and result[0].get("value")
            )
            return self._segment_ended

        except Exception as e:
            print(f"[vad] 检测异常: {e}")
            self._segment_ended = False
            return False

    def should_auto_stop(self) -> bool:
        """判断是否应该自动停止（最近一次 detect 检测到语音段结束）"""
        if not self.config.vad_enabled:
            return False
        return self._segment_ended

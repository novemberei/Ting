"""Ting 语音输入工具 - ASR 引擎模块"""

import asyncio
import os
import re

import numpy as np
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess


class ASREngine:
    """FunASR 语音识别引擎（非流式，一次性识别）"""

    def __init__(self, config):
        """保存配置，不加载模型"""
        self.config = config
        self.model = None

    def load(self):
        """加载 ASR 模型"""
        # 离线模式：跳过模型在线更新检查
        if self.config.model_offline:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            os.environ.setdefault("MODELSCOPE_OFFLINE", "1")
            print("[asr] 离线模式：跳过在线更新检查")

        if self.config.model_cache_dir:
            os.environ["MODELSCOPE_CACHE"] = self.config.model_cache_dir
            os.environ["HF_HOME"] = self.config.model_cache_dir
            print(f"[asr] 模型缓存路径: {self.config.model_cache_dir}")

        # 加载 ASR 模型
        print(f"[asr] 正在加载 ASR 模型 {self.config.model_name}...")
        try:
            self.model = AutoModel(
                model=self.config.model_name,
                hub=self.config.model_hub,
                device=self.config.device,
            )
        except Exception as e:
            self.model = None
            raise RuntimeError(
                f"ASR 模型加载失败 ({self.config.model_name}): {e}"
            ) from e
        print("[asr] ASR 模型加载完成")

    async def transcribe(self, audio: np.ndarray) -> str:
        """一次性识别完整音频，返回带标点的识别文本（异步，不阻塞事件循环）"""
        if self.model is None:
            raise RuntimeError("模型未加载")

        try:
            result = await asyncio.to_thread(
                self.model.generate,
                input=audio,
                cache={},
                language="auto",
                use_itn=self.config.use_itn,
                ban_emo_unk=self.config.ban_emo_unk,
                batch_size_s=60,
            )
            if result and len(result) > 0:
                text = rich_transcription_postprocess(result[0]["text"])
                # ban_emo_unk 兜底清理
                if self.config.ban_emo_unk:
                    text = re.sub(r"<\|emo_unk\|>\s*", "", text)
                    text = re.sub(r"emo_unk\s*", "", text)
                    text = text.strip()
                return text
        except Exception as e:
            print(f"[asr] 识别异常: {e}")
        return ""

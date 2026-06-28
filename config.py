"""Ting 语音输入工具 - 配置管理模块"""

import json
import os
from dataclasses import dataclass, fields


@dataclass
class Config:
    """应用配置，所有可调参数集中管理"""

    # 热键
    hotkey: str = "f8"

    # 音频参数
    sample_rate: int = 16000
    chunk_size_ms: int = 600

    # ASR 模型
    model_name: str = "FunAudioLLM/SenseVoiceSmall"
    model_hub: str = "hf"  # "hf" (HuggingFace) 或 "ms" (ModelScope)
    model_cache_dir: str = ""  # 空字符串表示使用默认缓存路径
    device: str = "cpu"
    model_offline: bool = True  # 离线模式，跳过模型在线更新检查
    use_itn: bool = True  # SenseVoice 标点+逆文本规范化开关
    ban_emo_unk: bool = True  # 禁止输出 emo_unk 标记

    # 输出策略
    output_method: str = "auto"  # "auto" | "clipboard_only"

    # VAD 参数
    vad_enabled: bool = False
    vad_silence_ms: int = 800
    vad_model: str = "funasr/fsmn-vad"

def load() -> Config:
    """加载配置：先读默认值，再用 config.json（如存在）覆盖"""
    config = Config()

    # 查找配置文件：优先当前目录，其次 ~/.ting/config.json
    config_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
        os.path.join(os.path.expanduser("~"), ".ting", "config.json"),
    ]

    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    overrides = json.load(f)
                # 仅覆盖 Config 中存在的字段
                valid_fields = {f.name for f in fields(config)}
                for key, value in overrides.items():
                    if key in valid_fields:
                        setattr(config, key, value)
                print(f"[config] 已加载配置: {path}")
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"[config] 配置文件 {path} 读取失败: {e}，使用默认配置")

    print("[config] 使用默认配置")
    return config

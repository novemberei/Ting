"""Ting 语音输入工具 - 模型更新检查脚本

用法：
    python update_models.py            # 检查并更新所有模型
    python update_models.py --dry-run  # 仅检查，不下载
"""

import os
import sys

# 强制在线模式，允许检查更新
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ.pop("TRANSFORMERS_OFFLINE", None)
os.environ.pop("MODELSCOPE_OFFLINE", None)

from config import load as load_config
from funasr import AutoModel


def update_models(dry_run=False):
    config = load_config()

    models = [
        ("ASR 模型", config.model_name),
    ]
    if config.vad_enabled:
        models.append(("VAD 模型", config.vad_model))

    print("=" * 50)
    print("Ting 语音输入 - 模型更新检查")
    print(f"来源: {'HuggingFace' if config.model_hub == 'hf' else 'ModelScope'}")
    print("=" * 50)

    for label, model_name in models:
        print(f"\n[{label}] {model_name}")
        if dry_run:
            print("  (dry-run 模式，跳过下载)")
            continue

        try:
            AutoModel(
                model=model_name,
                hub=config.model_hub,
                device=config.device,
            )
            print("  OK 已就绪")
        except Exception as e:
            print(f"  FAIL 失败: {e}")

    print("\n" + "=" * 50)
    print("完成！")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("(dry-run 模式)")
    update_models(dry_run=dry_run)

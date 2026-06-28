# FunASR 语音输入工具

## 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 环境管理 | pixi | 用户指定 |
| ASR 模型 | FunASR paraformer-zh (流式) | 中文流式识别，用户指定 |
| 音频采集 | pyaudio | 成熟的跨平台录音方案 |
| UI 框架 | tkinter | Python 内置，零额外依赖，轻量 |
| 全局热键 | keyboard | 支持全局快捷键监听，也可模拟键盘输入 |
| 窗口焦点检测 | pywin32 (win32gui) | Windows 下检测当前焦点窗口 |
| 剪贴板回退 | pyperclip | 无光标时复制到剪贴板 |

## 功能设计

- 点击「开始录音」按钮或按全局热键 (默认 F8) 触发录音
- 录音过程中实时流式识别，文字逐步显示在 UI 文本框中（仅预览）
- 点击「停止录音」或再次按热键结束录音
- **停止后的输出逻辑（优先级从高到低）：**
  1. 焦点在本应用文本框内 → 直接追加到文本框
  2. 焦点在其他窗口（有光标） → `keyboard.write()` 模拟输入，插入光标位置
  3. 模拟输入失败（无有效光标窗口） → 回退 `pyperclip.copy()` 到剪贴板
- 底部状态栏显示当前状态（空闲/录音中/识别中）及输出方式提示

## 项目结构

```
c:\Project\Ting\
├── pixi.toml           # pixi 项目配置，声明依赖和 Python 版本
├── main.py             # 入口，绑定热键，启动主循环
├── ui.py               # tkinter 界面：录音按钮、文本预览区、状态栏
├── recorder.py         # 音频采集模块：pyaudio 流式录音，线程安全
├── asr_engine.py       # ASR 引擎：加载 FunASR 模型，流式识别接口
└── output.py           # 输出模块：检测焦点窗口，模拟输入或剪贴板回退
```

## 实施任务

### Task 1: 初始化 pixi 项目
- 在 `c:\Project\Ting\` 下执行 `pixi init` 创建项目
- 在 `pixi.toml` 中添加依赖：funasr, pyaudio, keyboard, pyperclip, pywin32, torch (CPU 版本)
- 添加 modelscope 相关依赖 (modelscope, torchaudio)

### Task 2: 实现 ASR 引擎 (asr_engine.py)
- 封装 FunASR 流式 paraformer 模型加载
- 提供 `start_session()` / `feed_chunk(audio_chunk)` / `end_session()` 接口
- `feed_chunk` 返回增量识别文本
- 首次运行时自动下载模型到本地缓存

### Task 3: 实现录音模块 (recorder.py)
- 基于 pyaudio 实现流式录音（16kHz, 16bit, 单声道）
- 在独立线程中运行，通过回调将音频 chunk 推送给 ASR 引擎
- 提供 `start()` / `stop()` 控制接口

### Task 4: 实现 UI 界面 (ui.py)
- tkinter 主窗口，包含：
  - 大号「录音」按钮（点击切换录音/停止状态）
  - 多行文本框实时预览识别结果
  - 底部状态栏显示提示信息和快捷键说明
- 录音过程中文本框实时更新（仅预览，非最终输出）

### Task 5: 实现输出模块 (output.py)
- `get_foreground_window()`: 用 pywin32 获取当前焦点窗口句柄
- `insert_text(text, app_window_hwnd)`: 核心输出逻辑
  - 判断焦点是否为本应用窗口 → 直接写入 UI 文本框
  - 否则调用 `keyboard.write(text)` 模拟键盘输入（支持中文，keyboard 内部通过剪贴板+Ctrl+V 实现）
  - 捕获异常，失败时回退 `pyperclip.copy()` 并提示用户

### Task 6: 实现入口 (main.py)
- 初始化各模块，绑定全局热键 F8
- 热键触发时记录焦点窗口（用于后续输出定位）
- 确保全局热键与 UI 按钮行为一致

### Task 7: 测试验证
- 启动应用，验证模型加载正常
- 测试按钮触发录音和流式识别
- 测试热键在其他应用中触发，验证文字插入光标位置
- 测试无焦点窗口时回退剪贴板

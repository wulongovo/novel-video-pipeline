# 📺 Novel Video Pipeline - AI小说视频自动化管道

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Edge--TTS-Latest-0078D4?style=flat-square&logo=microsoft&logoColor=white" />
  <img src="https://img.shields.io/badge/Playwright-1.60+-2EAD33?style=flat-square&logo=playwright&logoColor=white" />
  <img src="https://img.shields.io/badge/FFmpeg-8.x-007805?style=flat-square&logo=ffmpeg&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

**AI自动生成末世/爽文小说 → 语音配音 → 视频合成 → 自动发布到抖音/B站**

一条命令，从0到1，每天自动发布AI生成的小说视频。

---

## ✨ 功能特性

- 🤖 **AI写小说** — 调用本地Ollama模型生成末世/爽文小说，支持多种模板
- 🎙️ **智能配音** — Edge TTS中文配音，低沉男声适合末世/哄睡风格
- 📹 **视频合成** — 自动合成竖屏视频（1080x1920），带字幕+氛围背景
- 📤 **自动发布** — Playwright自动发布到抖音/B站网页版
- ⏸️ **随时暂停** — 双击pause.bat暂停，双击resume.bat恢复
- 🔄 **全自动循环** — 设置间隔时间，持续生成+发布

## 📁 项目结构

```
novel-video-pipeline/
├── main.py                    # 主控调度器
├── src/
│   ├── novel/
│   │   └── generator.py       # AI小说生成器
│   ├── tts/
│   │   └── engine.py          # TTS语音合成
│   ├── video/
│   │   └── composer.py        # FFmpeg视频合成
│   └── publisher/
│       └── douyin.py          # 抖音/B站自动发布
├── configs/
│   └── config.yaml            # 配置文件
├── scripts/
│   ├── start_auto.bat         # 启动全自动模式
│   ├── generate_one.bat       # 生成一集
│   ├── login_douyin.bat       # 登录抖音
│   ├── login_bilibili.bat     # 登录B站
│   ├── pause.bat              # 暂停
│   └── resume.bat             # 恢复
└── data/
    ├── stories/               # 生成的小说
    ├── audio/                 # 生成的音频+字幕
    ├── images/                # 背景图片
    └── videos/                # 输出视频
```

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/wulongovo/novel-video-pipeline.git
cd novel-video-pipeline
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置

编辑 `configs/config.yaml`，配置AI模型和TTS参数。

默认使用Ollama本地模型（qwen35-heristic），确保Ollama已运行。

### 3. 登录平台

```bash
# 双击 scripts/login_douyin.bat
python main.py --login douyin

# 双击 scripts/login_bilibili.bat
python main.py --login bilibili
```

浏览器会弹出，手动登录后按回车保存Cookie。

### 4. 生成视频

```bash
# 生成一集
python main.py

# 指定模板
python main.py --template 末世系统流

# 生成并发布
python main.py --publish
```

### 5. 全自动模式

```bash
# 双击 scripts/start_auto.bat
python main.py --mode auto
```

暂停：双击 `scripts/pause.bat` 或创建 `data/PAUSE` 文件
恢复：双击 `scripts/resume.bat` 或删除 `data/PAUSE` 文件

## 📖 小说模板

| 模板 | 风格 | 适合标签 |
|------|------|----------|
| 末世重生 | 丧尸+重生+复仇 | 末世、爽文、重生 |
| 末世系统流 | 系统+升级+打怪 | 系统流、升级、爽文 |
| 末世基建 | 建基地+科技+管理 | 基建、种田、生存 |
| 都市异能爽文 | 透视+逆袭+打脸 | 都市、异能、逆袭 |

## ⚙️ 配置说明

### TTS声音选择

| 声音 | 特点 | 适合场景 |
|------|------|----------|
| zh-CN-YunxiNeural | 男声 沉稳 | 末世小说（推荐） |
| zh-CN-YunjianNeural | 男声 磁性 | 都市爽文 |
| zh-CN-XiaoxiaoNeural | 女声 温柔 | 言情小说 |

### 视频参数

- 分辨率: 1080x1920（竖屏，抖音标准）
- 字幕: 微软雅黑 42号 白色黑边
- 背景: 暗色系氛围图（雨夜/废墟/星空）
- 编码: H.264 + AAC

## 🔄 完整流程

```
Ollama本地模型
    ↓
AI生成末世小说 (3000字/章)
    ↓
Edge TTS语音合成 (低沉男声 + SRT字幕)
    ↓
FFmpeg视频合成 (暗色背景 + 字幕 + 音频)
    ↓
Playwright自动发布 (抖音/B站)
    ↓
等待N小时 → 下一集
```

## 📄 License

MIT License

---

⭐ 如果这个项目对你有帮助，请点个 Star！

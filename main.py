#!/usr/bin/env python3
"""
Novel Video Pipeline - AI小说视频自动化管道

用法:
  python main.py                     # 生成一集完整视频
  python main.py --mode auto         # 全自动循环（持续生成+发布）
  python main.py --mode manual       # 手动模式（只生成，不发布）
  python main.py --login douyin      # 登录抖音
  python main.py --login bilibili    # 登录B站
  python main.py --chapter 3         # 生成第3章
  python main.py --template 末世系统流  # 指定小说模板
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime

import yaml

from src.novel.generator import NovelGenerator, STORY_TEMPLATES
from src.tts.engine import TTSEngine
from src.video.composer import VideoComposer
from src.publisher.douyin import DouyinPublisher, BilibiliPublisher


def load_config(config_path: str = "configs/config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state(state_file: str = "data/state.json") -> dict:
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {"episode": 0, "last_publish": None, "paused": False}


def save_state(state: dict, state_file: str = "data/state.json"):
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def generate_one_episode(config: dict, state: dict, template: str = None, chapter_num: int = None) -> dict:
    """生成一集完整视频（小说→语音→视频）"""
    ep = state.get("episode", 0) + 1
    if chapter_num:
        ep = chapter_num

    template = template or "末世重生"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    episode_name = f"ep{ep:03d}_{timestamp}"

    print(f"\n{'='*60}")
    print(f"  第{ep}集 | {template} | {episode_name}")
    print(f"{'='*60}\n")

    # Step 1: 生成小说
    print("[1/4] 生成小说...")
    novel_cfg = config["novel"]
    generator = NovelGenerator(
        api_base=novel_cfg["api_base"],
        model=novel_cfg["model"],
        temperature=novel_cfg.get("temperature", 0.85),
    )

    story_file = f"data/stories/{episode_name}.txt"

    # 检查是否有之前的故事上下文
    prev_stories = sorted([f for f in os.listdir("data/stories") if f.endswith(".txt")]) if os.path.exists("data/stories") else []
    if prev_stories:
        with open(f"data/stories/{prev_stories[-1]}", "r", encoding="utf-8") as f:
            story_so_far = f.read()
        chapter = generator.generate_next_chapter(story_so_far, ep, template)
    else:
        chapter = generator.generate_first_chapter(template, name="林默")

    generator.save_chapter(chapter, "data/stories")
    story_file = f"data/stories/chapter_{ep:03d}.txt"
    print(f"  小说: {chapter['title']} ({chapter['word_count']}字)")

    # Step 2: 语音合成
    print("\n[2/4] 语音合成...")
    tts_cfg = config["tts"]
    tts = TTSEngine(
        voice=tts_cfg.get("voice", "zh-CN-YunxiNeural"),
        rate=tts_cfg.get("rate", "-10%"),
        pitch=tts_cfg.get("pitch", "-5Hz"),
    )

    audio_file = f"data/audio/{episode_name}.mp3"
    srt_file = f"data/audio/{episode_name}.srt"
    tts.generate(chapter["content"], audio_file, srt_file)
    duration = tts.get_audio_duration(audio_file)
    print(f"  音频: {duration:.0f}秒 ({duration/60:.1f}分钟)")

    # Step 3: 生成背景图
    print("\n[3/4] 生成背景...")
    video_cfg = config["video"]
    composer = VideoComposer(ffmpeg_path=video_cfg.get("ffmpeg_path", "E:/ffmpeg/ffmpeg.exe"))

    bg_file = f"data/images/bg_{episode_name}.png"
    composer.create_ambient_background(style="night", output_path=bg_file)

    # Step 4: 合成视频
    print("\n[4/4] 合成视频...")
    video_file = f"data/videos/{episode_name}.mp4"
    w, h = video_cfg.get("resolution", "1080x1920").split("x")

    composer.compose_video(
        audio_path=audio_file,
        srt_path=srt_file,
        background_path=bg_file,
        output_path=video_file,
        resolution=video_cfg.get("resolution", "1080x1920"),
        font_size=video_cfg.get("subtitle", {}).get("font_size", 42),
        margin_bottom=video_cfg.get("subtitle", {}).get("margin_bottom", 200),
    )

    # 更新状态
    state["episode"] = ep
    state["last_generated"] = {
        "name": episode_name,
        "title": chapter["title"],
        "video": video_file,
        "duration": duration,
        "timestamp": timestamp,
    }
    save_state(state)

    print(f"\n{'='*60}")
    print(f"  ✅ 第{ep}集生成完成！")
    print(f"  标题: {chapter['title']}")
    print(f"  时长: {duration/60:.1f}分钟")
    print(f"  视频: {video_file}")
    print(f"{'='*60}\n")

    return {
        "episode": ep,
        "video": video_file,
        "title": chapter["title"],
        "duration": duration,
    }


async def publish_episode(config: dict, state: dict, platforms: list = None):
    """发布最新视频"""
    publish_cfg = config.get("publish", {})
    if not publish_cfg.get("auto", False):
        print("自动发布已关闭 (publish.auto=false)")
        return

    last = state.get("last_generated")
    if not last:
        print("没有待发布的视频")
        return

    platforms = platforms or ["douyin", "bilibili"]
    video_path = last["video"]
    title = f"{last['title']} | AI末世小说连更"
    tags = ["末世", "爽文", "小说", "哄睡", "助眠", "夜间", "有声书", "AI"]

    for platform in platforms:
        if platform == "douyin" and "douyin" in str(publish_cfg.get("platforms", [])):
            publisher = DouyinPublisher(cookie_dir=publish_cfg.get("cookie_dir", "./cookies"))
            print(f"\n发布到抖音: {title}")
            await publisher.publish(video_path, title, tags)

        elif platform == "bilibili" and "bilibili" in str(publish_cfg.get("platforms", [])):
            publisher = BilibiliPublisher(cookie_dir=publish_cfg.get("cookie_dir", "./cookies"))
            desc = f"{title} - AI自动生成的末世连更小说，适合睡前收听"
            print(f"\n发布到B站: {title}")
            await publisher.publish(video_path, title, desc, tags)


def auto_mode(config: dict):
    """全自动模式 - 持续生成+发布"""
    state = load_state()
    interval = config.get("publish", {}).get("interval_hours", 24)

    print(f"\n🤖 全自动模式启动")
    print(f"   发布间隔: {interval}小时")
    print(f"   暂停方式: 创建 data/PAUSE 文件或 Ctrl+C\n")

    while True:
        # 检查暂停
        if os.path.exists("data/PAUSE") or state.get("paused"):
            print("⏸️  已暂停 (删除 data/PAUSE 文件恢复)")
            time.sleep(60)
            continue

        # 生成
        result = generate_one_episode(config, state)

        # 发布
        if config.get("publish", {}).get("auto", False):
            asyncio.run(publish_episode(config, state))

        # 等待
        print(f"\n⏰ 等待 {interval} 小时后生成下一集...")
        time.sleep(interval * 3600)


def main():
    parser = argparse.ArgumentParser(description="Novel Video Pipeline")
    parser.add_argument("--mode", choices=["auto", "manual", "single"], default="single")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--login", choices=["douyin", "bilibili"])
    parser.add_argument("--template", choices=list(STORY_TEMPLATES.keys()), default="末世重生")
    parser.add_argument("--chapter", type=int)
    parser.add_argument("--publish", action="store_true", help="生成后自动发布")
    parser.add_argument("--pause", action="store_true", help="暂停自动模式")
    parser.add_argument("--resume", action="store_true", help="恢复自动模式")
    args = parser.parse_args()

    config = load_config(args.config)
    state = load_state()

    # 登录
    if args.login:
        if args.login == "douyin":
            asyncio.run(DouyinPublisher().login_manual())
        elif args.login == "bilibili":
            asyncio.run(BilibiliPublisher().login_manual())
        return

    # 暂停/恢复
    if args.pause:
        open("data/PAUSE", "w").close()
        print("⏸️  已暂停自动模式")
        return
    if args.resume:
        if os.path.exists("data/PAUSE"):
            os.remove("data/PAUSE")
        state["paused"] = False
        save_state(state)
        print("▶️  已恢复自动模式")
        return

    # 全自动模式
    if args.mode == "auto":
        auto_mode(config)
        return

    # 单次生成
    result = generate_one_episode(config, state, template=args.template, chapter_num=args.chapter)

    # 发布
    if args.publish and config.get("publish", {}).get("auto", False):
        asyncio.run(publish_episode(config, state))


if __name__ == "__main__":
    main()

"""
视频合成器 - 使用FFmpeg将音频+字幕+背景合成为视频
"""

import os
import subprocess
import json
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont


class VideoComposer:
    """视频合成器"""

    def __init__(self, ffmpeg_path: str = "E:/ffmpeg/ffmpeg.exe"):
        self.ffmpeg = ffmpeg_path
        self.ffprobe = ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")

    def get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        r = subprocess.run(
            [self.ffprobe, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, timeout=15
        )
        return float(r.stdout.strip())

    def create_dark_background(self, width: int = 1080, height: int = 1920, output_path: str = "./data/images/bg_black.png"):
        """创建纯黑背景图"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img = Image.new("RGB", (width, height), (10, 10, 10))
        img.save(output_path)
        return output_path

    def create_ambient_background(
        self,
        width: int = 1080,
        height: int = 1920,
        style: str = "rain",
        output_path: str = "./data/images/bg_ambient.png",
    ):
        """创建氛围背景图（带文字提示的纯色背景）"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        colors = {
            "rain": (15, 20, 35),        # 深蓝灰 - 雨夜
            "ruins": (25, 15, 10),       # 暗棕 - 废墟
            "blood": (30, 10, 10),       # 暗红 - 末世
            "night": (5, 5, 15),         # 深蓝黑 - 夜空
            "fire": (35, 15, 5),         # 暗橙 - 火光
        }
        bg_color = colors.get(style, (10, 10, 10))

        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # 添加一些装饰文字（营造氛围）
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 24)
        except:
            font = ImageFont.load_default()

        # 底部渐变效果（用多条半透明线模拟）
        for i in range(200):
            alpha = int(255 * (1 - i / 200) * 0.3)
            y = height - i
            draw.line([(0, y), (width, y)], fill=(bg_color[0] + 10, bg_color[1] + 10, bg_color[2] + 15))

        img.save(output_path)
        return output_path

    def compose_video(
        self,
        audio_path: str,
        srt_path: str,
        background_path: str,
        output_path: str,
        resolution: str = "1080x1920",
        font_size: int = 42,
        font_color: str = "white",
        margin_bottom: int = 200,
    ) -> str:
        """
        合成最终视频

        Args:
            audio_path: 音频文件路径
            srt_path: SRT字幕文件路径
            background_path: 背景图片路径
            output_path: 输出视频路径
            resolution: 分辨率 (宽x高)
            font_size: 字幕字号
            font_color: 字幕颜色
            margin_bottom: 字幕距底部距离
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        w, h = resolution.split("x")
        duration = self.get_audio_duration(audio_path)

        # 字幕样式 - 适配中文
        subtitle_style = (
            f"FontName=Microsoft YaHei,"
            f"FontSize={font_size},"
            f"PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00000000,"
            f"BorderStyle=1,"
            f"Outline=2,"
            f"Shadow=1,"
            f"Alignment=2,"  # 底部居中
            f"MarginV={margin_bottom}"
        )

        # FFmpeg命令：图片循环 + 音频 + 字幕
        # 需要转义字幕路径中的反斜杠和冒号
        srt_escaped = srt_path.replace("\", "/").replace(":", "\\:")

        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1",
            "-i", background_path,
            "-i", audio_path,
            "-vf", f"subtitles='{srt_escaped}':force_style='{subtitle_style}',format=yuv420p",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-t", str(duration),
            "-s", resolution,
            output_path,
        ]

        print(f"合成视频中... (时长: {duration:.0f}秒)")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            # 如果字幕方式失败，用简单方式（无字幕）
            print(f"字幕合成失败，尝试简单模式...")
            cmd_simple = [
                self.ffmpeg, "-y",
                "-loop", "1", "-i", background_path,
                "-i", audio_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-t", str(duration),
                "-s", resolution,
                "-pix_fmt", "yuv420p",
                output_path,
            ]
            result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            size_mb = os.path.getsize(output_path) / 1024 / 1024
            print(f"✅ 视频生成完成: {output_path} ({size_mb:.1f}MB)")
        else:
            print(f"❌ 视频生成失败: {result.stderr[-500:]}")

        return output_path

    def compose_with_subtitles_via_drawtext(
        self,
        audio_path: str,
        srt_path: str,
        background_path: str,
        output_path: str,
        resolution: str = "1080x1920",
    ) -> str:
        """备用方案：用drawtext绘制字幕（不需要字幕字体支持）"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 读取SRT文件
        srt_entries = self._parse_srt(srt_path)
        if not srt_entries:
            print("字幕为空，使用无字幕模式")
            return output_path

        duration = self.get_audio_duration(audio_path)

        # 构建drawtext滤镜链（取前50条避免命令过长）
        drawtext_parts = []
        for entry in srt_entries[:100]:
            text = entry["text"].replace("'", "\'").replace(":", "\:")
            start = entry["start"]
            end = entry["end"]
            drawtext_parts.append(
                f"drawtext=text='{text}':fontfile=C\\:/Windows/Fonts/msyh.ttc:"
                f"fontsize=38:fontcolor=white:borderw=2:bordercolor=black:"
                f"x=(w-text_w)/2:y=h-300:"
                f"enable='between(t,{start},{end})'"
            )

        vf = ",".join(drawtext_parts) if drawtext_parts else "null"

        w, h = resolution.split("x")
        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1", "-i", background_path,
            "-i", audio_path,
            "-vf", f"{vf},format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-t", str(duration),
            "-s", resolution,
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print(f"✅ 视频生成完成: {output_path}")
        else:
            print(f"❌ drawtext失败: {result.stderr[-300:]}")

        return output_path

    @staticmethod
    def _parse_srt(srt_path: str) -> list:
        """解析SRT字幕文件"""
        entries = []
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                time_line = lines[1]
                text = " ".join(lines[2:])
                parts = time_line.split(" --> ")
                if len(parts) == 2:
                    start = VideoComposer._srt_time_to_seconds(parts[0].strip())
                    end = VideoComposer._srt_time_to_seconds(parts[1].strip())
                    entries.append({"start": start, "end": end, "text": text})

        return entries

    @staticmethod
    def _srt_time_to_seconds(time_str: str) -> float:
        """SRT时间格式转秒数"""
        time_str = time_str.replace(",", ".")
        parts = time_str.split(":")
        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s

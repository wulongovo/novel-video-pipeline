"""
语音合成引擎 - 使用Edge TTS生成中文配音
支持生成音频和字幕文件
"""

import asyncio
import os
import re
from typing import Optional, List, Tuple

import edge_tts


class TTSEngine:
    """Edge TTS语音合成引擎"""

    # 可用的中文声音列表
    VOICES = {
        "yunxi": "zh-CN-YunxiNeural",       # 男声 沉稳 (推荐末世)
        "yunjian": "zh-CN-YunjianNeural",     # 男声 磁性
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",   # 女声 温柔
        "xiaoyi": "zh-CN-XiaoyiNeural",       # 女声 活泼
        "yunfeng": "zh-CN-YunfengNeural",     # 男声 成熟
        "yunhao": "zh-CN-YunhaoNeural",       # 男声 新闻风
    }

    def __init__(
        self,
        voice: str = "zh-CN-YunxiNeural",
        rate: str = "-10%",
        volume: str = "+0%",
        pitch: str = "-5Hz",
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch

    async def _generate_audio(
        self,
        text: str,
        output_path: str,
        subtitle_path: Optional[str] = None,
    ) -> str:
        """生成音频和字幕"""
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch,
        )

        subs = []
        with open(output_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    subs.append({
                        "offset": chunk["offset"],        # 纳秒
                        "duration": chunk["duration"],    # 纳秒
                        "text": chunk["text"],
                    })

        # 生成SRT字幕
        if subtitle_path and subs:
            self._generate_srt(subs, subtitle_path)

        return output_path

    def _generate_srt(self, word_boundaries: list, output_path: str):
        """从词边界生成SRT字幕（按句子分组）"""
        srt_lines = []
        index = 1
        current_text = ""
        current_start = 0
        current_end = 0

        for wb in word_boundaries:
            text = wb["text"]
            start_ms = wb["offset"] / 10000  # 纳秒转毫秒
            end_ms = start_ms + wb["duration"] / 10000

            if not current_text:
                current_start = start_ms

            current_text += text
            current_end = end_ms

            # 遇到句号/问号/感叹号/逗号且文本够长时断句
            if any(current_text.endswith(c) for c in ["。", "！", "？", "……", "；"])                and len(current_text) > 5:
                srt_lines.append({
                    "index": index,
                    "start": current_start,
                    "end": current_end,
                    "text": current_text.strip(),
                })
                index += 1
                current_text = ""

        # 处理最后一段
        if current_text.strip():
            srt_lines.append({
                "index": index,
                "start": current_start,
                "end": current_end,
                "text": current_text.strip(),
            })

        # 写入SRT文件
        with open(output_path, "w", encoding="utf-8") as f:
            for line in srt_lines:
                f.write(f"{line['index']}\n")
                f.write(f"{self._ms_to_srt_time(line['start'])} --> {self._ms_to_srt_time(line['end'])}\n")
                f.write(f"{line['text']}\n\n")

    @staticmethod
    def _ms_to_srt_time(ms: float) -> str:
        """毫秒转SRT时间格式"""
        ms = int(ms)
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        millis = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

    def generate(self, text: str, output_path: str, subtitle_path: Optional[str] = None) -> Tuple[str, str]:
        """同步接口：生成音频和字幕"""
        return asyncio.run(self._generate_audio(text, output_path, subtitle_path))

    def generate_from_file(self, text_file: str, output_dir: str = "./data/audio") -> Tuple[str, str]:
        """从文本文件生成音频"""
        os.makedirs(output_dir, exist_ok=True)

        with open(text_file, "r", encoding="utf-8") as f:
            text = f.read()

        # 提取文件名
        basename = os.path.splitext(os.path.basename(text_file))[0]
        audio_path = os.path.join(output_dir, f"{basename}.mp3")
        srt_path = os.path.join(output_dir, f"{basename}.srt")

        self.generate(text, audio_path, srt_path)
        return audio_path, srt_path

    def get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长(秒)"""
        import subprocess
        ffmpeg = "E:/ffmpeg/ffmpeg.exe"
        ffprobe = ffmpeg.replace("ffmpeg.exe", "ffprobe.exe")
        result = subprocess.run(
            [ffprobe, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, timeout=15
        )
        return float(result.stdout.strip())

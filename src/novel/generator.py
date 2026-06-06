"""
AI小说生成器 - 调用本地Ollama或OpenAI兼容API生成末世/爽文小说
"""

import json
import os
import requests
from datetime import datetime
from typing import Optional


# 末世小说常用设定和模板
STORY_TEMPLATES = {
    "末世重生": {
        "opening": "2024年，末日降临。丧尸病毒席卷全球，百分之九十的人类在三天内变成了行尸走肉。{name}上一世在末世中苟活了三年，最终被最信任的人背叛，死在了丧尸潮中。然而当他再次睁开眼睛，发现自己回到了末日降临的前一天。",
        "settings": ["丧尸末世", "病毒爆发", "重生复仇", "囤物资", "建基地"],
        "conflicts": ["背叛者的威胁", "丧尸围城", "物资争夺", "人性考验", "异能觉醒"],
    },
    "末世系统流": {
        "opening": "叮！末世生存系统已绑定宿主{name}。当整个世界陷入混乱，{name}发现自己脑海中出现了一个神秘系统，击杀丧尸可以获得进化点数，开启各种超凡能力。在这个人吃人的末世，他将用系统之力，一步步登上巅峰。",
        "settings": ["系统面板", "进化升级", "异能觉醒", "等级划分", "BOSS战"],
        "conflicts": ["系统任务失败惩罚", "其他系统拥有者", "高级变异体", "人类内斗"],
    },
    "末世基建": {
        "opening": "末日第三年，{name}站在自己一手建立的避难所城墙上，望着远处密密麻麻的丧尸潮。三年前他只是一个普通的工程师，如今却是这座十万人城市的领袖。末世最缺的不是武器，而是秩序。",
        "settings": ["基地建设", "科技发展", "人口管理", "军事防御", "资源采集"],
        "conflicts": ["丧尸围城", "其他势力入侵", "内部叛乱", "能源危机", "新型变异"],
    },
    "都市异能爽文": {
        "opening": "{name}是一个被所有人看不起的上门女婿，每天忍受着岳母的辱骂和妻子的冷漠。直到有一天，他意外获得了一双透视眼，从此命运彻底改写。商界大佬对他点头哈腰，地下世界奉他为王，曾经看不起他的人，一个个跪着求他原谅。",
        "settings": ["透视异能", "商战", "打脸", "逆袭", "隐藏身份"],
        "conflicts": ["商业对手", "家族阴谋", "异能反噬", "感情纠葛"],
    },
}

# 章节续写提示词
CHAPTER_PROMPTS = {
    "next_chapter": """你是一个专业的网络小说作者，擅长写{genre}类型的小说。

当前故事背景：
{story_so_far}

请续写下一章内容，要求：
1. 字数：2500-3500字
2. 风格：节奏紧凑，每500字至少一个爽点或悬念
3. 必须有：至少一个打脸/逆袭/升级/危机解除的爽点
4. 结尾：必须留悬念，让读者想看下一章
5. 语言：口语化，适合朗读，多用短句
6. 章节标题：取一个吸引人的标题

输出格式：
第X章 标题名
（正文内容）""",

    "first_chapter": """你是一个专业的网络小说作者，擅长写{genre}类型的小说。

请根据以下设定，写一个吸引人的第一章：

故事设定：{setting}
主角名字：{name}

要求：
1. 字数：2500-3500字
2. 开头50字内必须抓住读者（危机/悬念/反转）
3. 风格：节奏快，爽点密集，适合朗读
4. 语言：口语化，多用短句，适合配音
5. 结尾：必须留悬念

输出格式：
第一章 标题名
（正文内容）""",
}


class NovelGenerator:
    """AI小说生成器"""

    def __init__(self, api_base: str, model: str, temperature: float = 0.85):
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.temperature = temperature

    def _call_llm(self, prompt: str, max_tokens: int = 4000) -> str:
        """调用LLM API (OpenAI兼容格式)"""
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的网络小说作者，擅长写末世、爽文类型的小说。你的文笔流畅，节奏紧凑，非常适合朗读配音。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return ""

    def generate_first_chapter(self, template_key: str = "末世重生", name: str = "林默") -> dict:
        """生成第一章"""
        template = STORY_TEMPLATES.get(template_key, STORY_TEMPLATES["末世重生"])
        opening = template["opening"].format(name=name)
        settings = "、".join(template["settings"])

        prompt = CHAPTER_PROMPTS["first_chapter"].format(
            genre=template_key,
            setting=f"{opening}\n核心元素：{settings}",
            name=name,
        )

        print(f"正在生成第一章 ({template_key})...")
        content = self._call_llm(prompt)

        title = content.split("\n")[0].strip() if content else f"第一章 {template_key}"
        return {
            "chapter": 1,
            "title": title,
            "content": content,
            "template": template_key,
            "protagonist": name,
            "word_count": len(content),
        }

    def generate_next_chapter(self, story_so_far: str, chapter_num: int, genre: str = "末世重生") -> dict:
        """续写下一章"""
        prompt = CHAPTER_PROMPTS["next_chapter"].format(
            genre=genre,
            story_so_far=story_so_far[-2000:],  # 最多传2000字上下文
        )

        print(f"正在生成第{chapter_num}章...")
        content = self._call_llm(prompt)

        title = content.split("\n")[0].strip() if content else f"第{chapter_num}章"
        return {
            "chapter": chapter_num,
            "title": title,
            "content": content,
            "word_count": len(content),
        }

    def generate_series(self, template_key: str = "末世重生", name: str = "林默", chapters: int = 5) -> list:
        """生成系列小说"""
        results = []

        # 第一章
        ch1 = self.generate_first_chapter(template_key, name)
        results.append(ch1)

        # 后续章节
        story_so_far = ch1["content"]
        for i in range(2, chapters + 1):
            ch = self.generate_next_chapter(story_so_far, i, template_key)
            results.append(ch)
            story_so_far += "\n\n" + ch["content"]

        return results

    def save_chapter(self, chapter: dict, output_dir: str = "./data/stories"):
        """保存章节到文件"""
        os.makedirs(output_dir, exist_ok=True)
        filename = f"chapter_{chapter['chapter']:03d}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{chapter['title']}\n\n{chapter['content']}")

        print(f"✅ 保存: {filepath} ({chapter['word_count']}字)")
        return filepath

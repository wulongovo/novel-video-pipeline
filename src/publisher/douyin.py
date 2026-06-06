"""
抖音自动发布 - 使用Playwright模拟浏览器操作
"""

import os
import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright


class DouyinPublisher:
    """抖音网页版自动发布"""

    PUBLISH_URL = "https://creator.douyin.com/creator-micro/content/upload"

    def __init__(self, cookie_dir: str = "./cookies"):
        self.cookie_dir = cookie_dir
        os.makedirs(cookie_dir, exist_ok=True)
        self.cookie_file = os.path.join(cookie_dir, "douyin.json")

    async def login_manual(self):
        """手动登录并保存Cookie"""
        print("\n=== 抖音登录 ===")
        print("1. 浏览器将打开抖音创作者中心")
        print("2. 请手动扫码登录")
        print("3. 登录成功后按回车继续...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://creator.douyin.com/")

            input("登录完成后按回车...")

            # 保存cookies
            cookies = await context.cookies()
            import json
            with open(self.cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)

            print(f"✅ Cookie已保存: {self.cookie_file}")
            await browser.close()

    async def publish(
        self,
        video_path: str,
        title: str,
        tags: List[str] = None,
        cover_path: Optional[str] = None,
    ) -> bool:
        """发布视频到抖音"""
        if not os.path.exists(self.cookie_file):
            print("❌ 未找到Cookie，请先运行 login_manual()")
            return False

        import json
        with open(self.cookie_file, "r") as f:
            cookies = json.load(f)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # 有头模式便于观察
            context = await browser.new_context()
            await context.add_cookies(cookies)
            page = await context.new_page()

            try:
                # 打开发布页面
                await page.goto(self.PUBLISH_URL, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # 上传视频
                upload_input = page.locator('input[type="file"]').first
                await upload_input.set_input_files(video_path)
                print("视频上传中...")

                # 等待上传完成
                await page.wait_for_timeout(10000)

                # 填写标题
                title_input = page.locator('[class*="title"] input, [class*="caption"] [contenteditable], .ql-editor').first
                if await title_input.count() > 0:
                    await title_input.click()
                    await title_input.fill(title)
                    print(f"标题: {title}")

                # 添加标签
                if tags:
                    for tag in tags[:5]:
                        await page.keyboard.type(f"#{tag} ")
                        await page.wait_for_timeout(500)

                await page.wait_for_timeout(3000)

                # 点击发布按钮
                publish_btn = page.locator('button:has-text("发布"), [class*="publish"] button').first
                if await publish_btn.count() > 0:
                    await publish_btn.click()
                    print("✅ 已点击发布")
                    await page.wait_for_timeout(5000)

                # 保存cookies（可能刷新了）
                new_cookies = await context.cookies()
                with open(self.cookie_file, "w") as f:
                    json.dump(new_cookies, f, indent=2)

                return True

            except Exception as e:
                print(f"❌ 发布失败: {e}")
                # 截图保存错误现场
                await page.screenshot(path="./data/publish_error.png")
                return False
            finally:
                await browser.close()


class BilibiliPublisher:
    """B站自动发布"""

    PUBLISH_URL = "https://member.bilibili.com/platform/upload/video/frame"

    def __init__(self, cookie_dir: str = "./cookies"):
        self.cookie_dir = cookie_dir
        os.makedirs(cookie_dir, exist_ok=True)
        self.cookie_file = os.path.join(cookie_dir, "bilibili.json")

    async def login_manual(self):
        """手动登录B站"""
        print("\n=== B站登录 ===")
        print("1. 浏览器将打开B站创作中心")
        print("2. 请手动登录")
        print("3. 登录成功后按回车继续...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://member.bilibili.com/")

            input("登录完成后按回车...")

            cookies = await context.cookies()
            import json
            with open(self.cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)

            print(f"✅ Cookie已保存: {self.cookie_file}")
            await browser.close()

    async def publish(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: List[str] = None,
    ) -> bool:
        """发布视频到B站"""
        if not os.path.exists(self.cookie_file):
            print("❌ 未找到Cookie，请先运行 login_manual()")
            return False

        import json
        with open(self.cookie_file, "r") as f:
            cookies = json.load(f)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            await context.add_cookies(cookies)
            page = await context.new_page()

            try:
                await page.goto(self.PUBLISH_URL, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # 上传视频
                upload_input = page.locator('input[type="file"]').first
                await upload_input.set_input_files(video_path)
                print("视频上传中...")
                await page.wait_for_timeout(15000)

                # 填写标题
                title_input = page.locator('[class*="title"] input, input[maxlength]').first
                if await title_input.count() > 0:
                    await title_input.fill(title)

                # 填写简介
                desc_input = page.locator('textarea, [class*="desc"] input').first
                if await desc_input.count() > 0:
                    await desc_input.fill(description[:250])

                await page.wait_for_timeout(3000)

                # 点击投稿
                submit_btn = page.locator('button:has-text("投稿"), [class*="submit"] button').first
                if await submit_btn.count() > 0:
                    await submit_btn.click()
                    print("✅ 已点击投稿")
                    await page.wait_for_timeout(5000)

                new_cookies = await context.cookies()
                with open(self.cookie_file, "w") as f:
                    json.dump(new_cookies, f, indent=2)

                return True

            except Exception as e:
                print(f"❌ 发布失败: {e}")
                await page.screenshot(path="./data/bilibili_error.png")
                return False
            finally:
                await browser.close()

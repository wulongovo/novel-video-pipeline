@echo off
echo B站登录 - 请在弹出的浏览器中手动登录
cd /d E:\novel-video-pipeline
venv\Scripts\python.exe main.py --login bilibili
pause

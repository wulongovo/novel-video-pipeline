@echo off
cd /d E:\novel-video-pipeline
if exist data\PAUSE (
    del data\PAUSE
    echo 已恢复自动模式
) else (
    echo 已经在运行中
)
pause

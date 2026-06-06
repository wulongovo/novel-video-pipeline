@echo off
cd /d E:\novel-video-pipeline
if not exist data mkdir data
if not exist data\PAUSE (
    echo. > data\PAUSE
    echo 已暂停自动模式
) else (
    echo 已经是暂停状态
)
pause

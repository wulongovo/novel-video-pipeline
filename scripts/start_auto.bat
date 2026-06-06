@echo off
echo ========================================
echo  Novel Video Pipeline - 全自动模式
echo ========================================
echo.
echo 暂停: 双击 pause.bat
echo 恢复: 双击 resume.bat
echo 停止: Ctrl+C
echo.
cd /d E:\novel-video-pipeline
venv\Scripts\python.exe main.py --mode auto
pause

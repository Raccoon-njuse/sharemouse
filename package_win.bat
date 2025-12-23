@echo off

REM Windows 打包脚本

echo 开始打包 ShareMouse for Windows...

echo 安装依赖...
pip install -r requirements.txt
pip install pyinstaller

REM 清理之前的打包结果
echo 清理之前的打包结果...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /f /q "*.spec"

REM 打包应用
echo 执行打包...
pyinstaller --name="ShareMouse" --onefile main.py

echo 打包完成！
echo 应用程序位于: dist\ShareMouse.exe
echo 使用方法:
echo   服务器模式: "dist\ShareMouse.exe" --mode server
echo   客户端模式: "dist\ShareMouse.exe" --mode client --host <服务器IP>
echo.
echo 注意: 首次运行可能需要以管理员身份运行，以便应用程序能够捕获输入设备！
pause
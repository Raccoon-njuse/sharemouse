# ShareMouse 打包指南

本指南将帮助您将 ShareMouse 打包为可执行的应用程序，支持 macOS 和 Windows 平台。

## 前提条件

- Python 3.7 或更高版本
- pip 包管理器
- 项目依赖已安装：`pip install -r requirements.txt`

## 选择打包工具

我们推荐使用 **PyInstaller** 进行打包，它支持跨平台且配置相对简单。

```bash
pip install pyinstaller
```

## macOS 打包步骤

### 1. 基本打包命令

```bash
# 创建单个可执行文件
pyinstaller --onefile --name="ShareMouse" --windowed main.py

# 创建包含所有文件的应用包
pyinstaller --name="ShareMouse" --windowed main.py
```

### 2. 处理权限需求

macOS 需要特定权限才能捕获鼠标和键盘事件：

1. 打包完成后，右键点击 `dist/ShareMouse.app` → 选择 "显示包内容"
2. 进入 `Contents/Info.plist`，添加以下权限：

```xml
<key>NSAppleEventsUsageDescription</key>
<string>This app needs access to your keyboard and mouse to share them across devices.</string>
<key>NSInputMonitoringUsageDescription</key>
<string>This app needs to monitor keyboard input to detect hotkeys.</string>
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
</dict>
```

### 3. 签名应用（可选）

如果您有 Apple 开发者证书，可以签名应用：

```bash
codesign --deep --force --verbose --sign "Your Developer ID" dist/ShareMouse.app
```

## Windows 打包步骤

### 1. 基本打包命令

```cmd
:: 创建单个可执行文件
pyinstaller --onefile --name="ShareMouse.exe" main.py

:: 创建包含所有文件的应用目录
pyinstaller --name="ShareMouse" main.py
```

### 2. 处理权限需求

Windows 可能需要管理员权限才能捕获鼠标和键盘事件：

1. 打包完成后，右键点击 `dist/ShareMouse.exe` → 选择 "属性"
2. 进入 "兼容性" 标签页
3. 勾选 "以管理员身份运行此程序"

### 3. 配置高级选项（可选）

创建一个 `sharemouse.spec` 文件来自定义打包配置：

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)
pyz = PYZ(a.pure)

# 对于 Windows
if sys.platform == 'win32':
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              name='ShareMouse',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              upx_exclude=[],
              runtime_tmpdir=None,
              console=False,  # 设置为 True 以显示控制台窗口
              disable_windowed_traceback=False,
              target_arch=None,
              codesign_identity=None,
              entitlements_file=None)

# 对于 macOS
elif sys.platform == 'darwin':
    exe = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name='ShareMouse',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              console=False)
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   upx_exclude=[],
                   name='ShareMouse')
    app = BUNDLE(coll,
                 name='ShareMouse.app',
                 icon=None,
                 bundle_identifier=None)
```

然后使用此配置文件打包：

```bash
pyinstaller sharemouse.spec
```

## 使用打包后的应用

### macOS

```bash
# 服务器模式
./dist/ShareMouse.app/Contents/MacOS/ShareMouse --mode server

# 客户端模式
./dist/ShareMouse.app/Contents/MacOS/ShareMouse --mode client --host <服务器IP>
```

### Windows

```cmd
:: 服务器模式
"dist\ShareMouse.exe" --mode server

:: 客户端模式
"dist\ShareMouse.exe" --mode client --host <服务器IP>
```

## 常见问题

### 1. 输入捕获权限问题

- **macOS**: 前往 "系统偏好设置" → "安全性与隐私" → "隐私" → 确保应用程序被允许 "监控输入" 和 "辅助功能"
- **Windows**: 确保以管理员身份运行应用程序

### 2. 网络连接问题

- 确保防火墙允许应用程序访问网络
- 检查是否有其他应用程序占用相同端口（默认 5001）

### 3. 应用程序崩溃

- 尝试使用 `--console` 选项打包，查看控制台输出的错误信息
- 检查是否缺少依赖项

## 高级选项

### 添加图标

- macOS: 创建一个 `.icns` 图标文件，使用 `--icon="sharemouse.icns"` 参数
- Windows: 创建一个 `.ico` 图标文件，使用 `--icon="sharemouse.ico"` 参数

### 包含额外文件

使用 `--add-data` 参数包含额外文件：

```bash
pyinstaller --onefile --name="ShareMouse" --add-data="README.md:." main.py
```

## 注意事项

- 打包后的应用程序可能会被杀毒软件误报，请确保用户了解这一点
- macOS 应用可能需要经过 Gatekeeper 批准才能运行
- 定期更新依赖项并重新打包以修复安全问题

## 自动化打包脚本

创建一个 `package.sh` 脚本（macOS/Linux）：

```bash
#!/bin/bash

# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 打包
pyinstaller --onefile --name="ShareMouse" --windowed main.py

echo "打包完成！应用程序位于 dist/ShareMouse.app"
```

创建一个 `package.bat` 脚本（Windows）：

```batch
@echo off

:: 安装依赖
pip install -r requirements.txt
pip install pyinstaller

:: 打包
pyinstaller --onefile --name="ShareMouse.exe" main.py

echo 打包完成！应用程序位于 dist\ShareMouse.exe
pause
```
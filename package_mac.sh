#!/bin/bash

# macOS 打包脚本

echo "开始打包 ShareMouse for macOS..."

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt
pip install pyinstaller

# 清理之前的打包结果
echo "清理之前的打包结果..."
rm -rf build dist *.spec

# 打包应用
echo "执行打包..."
pyinstaller --name="ShareMouse" --windowed --onefile main.py

# 创建应用包结构
echo "创建应用包结构..."

# 添加 Info.plist 权限配置
echo "添加权限配置..."
cat > "dist/ShareMouse.app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleExecutable</key>
    <string>ShareMouse</string>
    <key>CFBundleIdentifier</key>
    <string>com.sharemouse.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>ShareMouse</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.1.0</string>
    <key>CFBundleVersion</key>
    <string>1.1.0</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>This app needs access to your keyboard and mouse to share them across devices.</string>
    <key>NSInputMonitoringUsageDescription</key>
    <string>This app needs to monitor keyboard input to detect hotkeys.</string>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsLocalNetworking</key>
        <true/>
    </dict>
    <key>NSAppleScriptEnabled</key>
    <true/>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

echo "打包完成！"
echo "应用程序位于: dist/ShareMouse.app"
echo "使用方法:"
echo "  服务器模式: ./dist/ShareMouse.app/Contents/MacOS/ShareMouse --mode server"
echo "  客户端模式: ./dist/ShareMouse.app/Contents/MacOS/ShareMouse --mode client --host <服务器IP>"
echo ""
echo "注意: 首次运行需要在 系统偏好设置 > 安全性与隐私 > 隐私 中授权应用程序访问输入设备！"
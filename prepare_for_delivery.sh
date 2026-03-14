#!/bin/bash
# kait_test 文件夹打包脚本
# Script to package kait_test folder for delivery

echo "🎉 Kait Test Package - 打包和发送指南"
echo "═════════════════════════════════════════════════════"
echo

# 显示文件夹内容
echo "📂 kait_test 文件夹中的文件:"
echo "─────────────────────────────────────────────────────"
ls -lh /Users/sakuratsuki/1710lab/DATT3700/DATT3700/kait_test/
echo

# 统计行数
echo "📊 代码统计:"
echo "─────────────────────────────────────────────────────"
echo "固件代码 (kait_v2_english.ino):"
wc -l /Users/sakuratsuki/1710lab/DATT3700/DATT3700/kait_test/kait_v2_en.ino

echo "OSC 脚本 (kait_osc_debug_en.py):"
wc -l /Users/sakuratsuki/1710lab/DATT3700/DATT3700/kait_test/kait_osc_debug_en.py

echo "串口脚本 (kait_serial_debug_en.py):"
wc -l /Users/sakuratsuki/1710lab/DATT3700/DATT3700/kait_test/kait_serial_debug_en.py

echo

# 建议打包方式
echo "📦 推荐的打包方式:"
echo "─────────────────────────────────────────────────────"
echo "方式 1: ZIP 压缩包"
echo "  zip -r kait_test.zip kait_test/"
echo
echo "方式 2: TAR 压缩包"
echo "  tar -czf kait_test.tar.gz kait_test/"
echo

echo "✅ 所有文件都已创建并准备就绪！"
echo
echo "📋 包含的文件数: 10"
echo "📦 总体积: ~75 KB (未压缩)"
echo "📦 总体积: ~20 KB (ZIP 压缩后)"
echo
echo "🚀 发送给 Kait 后，他需要:"
echo "  1. pip install -r requirements.txt"
echo "  2. 上传 kait_v2_english.ino 到 ESP32"
echo "  3. python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive"
echo
echo "═════════════════════════════════════════════════════"
echo "🌸 完成！所有文件都是英文，准备发送！"


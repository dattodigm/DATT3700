#!/bin/bash
# F7OWER Kait Node v2 - 快速安装脚本
# 自动安装依赖和配置环境

set -e

echo "╔════════════════════════════════════════════╗"
echo "║   F7OWER Kait Node v2 - 快速安装脚本      ║"
echo "╚════════════════════════════════════════════╝"
echo

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装 Python 3.6 或更高版本"
    exit 1
fi

python_version=$(python3 --version | awk '{print $2}')
echo "✅ Python 版本: $python_version"
echo

# 检查 pip
echo "🔍 检查 pip..."
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ 未找到 pip，请先安装"
    exit 1
fi
echo "✅ pip 已安装"
echo

# 安装依赖
echo "📦 安装 Python 依赖..."
echo "  → python-osc (OSC 协议)"
python3 -m pip install python-osc -q
echo "  ✓ python-osc 安装完成"

echo "  → pyserial (串口通信)"
python3 -m pip install pyserial -q
echo "  ✓ pyserial 安装完成"

echo "  → matplotlib (可视化)"
python3 -m pip install matplotlib -q
echo "  ✓ matplotlib 安装完成"

echo "  → numpy (数值计算)"
python3 -m pip install numpy -q
echo "  ✓ numpy 安装完成"
echo

# 设置脚本执行权限
echo "🔐 设置脚本权限..."
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$script_dir/kait_osc_debug.py" 2>/dev/null && echo "  ✓ kait_osc_debug.py" || true
chmod +x "$script_dir/kait_serial_debug.py" 2>/dev/null && echo "  ✓ kait_serial_debug.py" || true
chmod +x "$script_dir/kait_motion_visualization.py" 2>/dev/null && echo "  ✓ kait_motion_visualization.py" || true
echo

# 验证安装
echo "✅ 验证安装..."
if python3 -c "from pythonosc import udp_client; print('OK')" 2>/dev/null; then
    echo "  ✓ pythonosc 导入成功"
fi

if python3 -c "import serial; print('OK')" 2>/dev/null; then
    echo "  ✓ serial 导入成功"
fi

if python3 -c "import matplotlib.pyplot; print('OK')" 2>/dev/null; then
    echo "  ✓ matplotlib 导入成功"
fi

if python3 -c "import numpy; print('OK')" 2>/dev/null; then
    echo "  ✓ numpy 导入成功"
fi
echo

# 显示快速开始
echo "╔════════════════════════════════════════════╗"
echo "║        🎉 安装完成！快速开始指南          ║"
echo "╚════════════════════════════════════════════╝"
echo

echo "📡 OSC 远程控制（WiFi）:"
echo "   python3 kait_osc_debug.py -i F7OWER_kait.local --interactive"
echo

echo "🔌 串口调试控制（USB）:"
echo "   python3 kait_serial_debug.py --list-ports"
echo "   python3 kait_serial_debug.py -p /dev/ttyUSB0 --interactive"
echo

echo "📊 运动模式可视化:"
echo "   python3 kait_motion_visualization.py --all"
echo

echo "📖 更多帮助:"
echo "   cat KAIT_V2_GUIDE.md"
echo "   cat QUICK_REFERENCE.md"
echo

echo "✨ 祝你使用愉快！"


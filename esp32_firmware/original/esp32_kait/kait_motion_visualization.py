#!/usr/bin/env python3
"""
F7OWER Kait Node - 运动模式可视化演示脚本
用于理解每个运动模式的具体效果
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.patches import FancyBboxPatch
import argparse

# ============================================================
# 运动模式数据生成
# ============================================================

def generate_sway_pattern(duration=3.0, amplitude=100):
    """缓慢摇晃模式"""
    t = np.linspace(0, duration, int(duration * 100))
    # 正反交替：先正，后反
    pattern = []
    for ti in t:
        phase = (ti % 2.0)
        if phase < 1.0:
            pattern.append(amplitude)
        else:
            pattern.append(-amplitude)
    return np.array(pattern)

def generate_fast_spin_pattern(duration=2.0, speed=220):
    """快速旋转模式"""
    t = np.linspace(0, duration, int(duration * 100))
    return np.full_like(t, speed)

def generate_vibrate_pattern(duration=1.0, intensity=120):
    """脉冲抖动模式"""
    t = np.linspace(0, duration, int(duration * 100))
    pattern = []
    for ti in t:
        phase = (ti * 10) % 1.0  # 10 Hz 频率
        if phase < 0.5:
            pattern.append(intensity)
        else:
            pattern.append(-intensity)
    return np.array(pattern)

def generate_accelerate_pattern(duration=3.0, max_speed=220):
    """加速螺旋模式"""
    t = np.linspace(0, duration, int(duration * 100))
    return (max_speed / duration) * t

def generate_brake_pattern(duration=1.5, initial_speed=200):
    """平滑制动模式"""
    t = np.linspace(0, duration, int(duration * 100))
    return initial_speed * (1 - t / duration)

def generate_pulse_start_pattern(duration=2.0, target_speed=150):
    """脉冲启动模式"""
    t = np.linspace(0, duration, int(duration * 100))
    pattern = []

    # 前 0.3 秒：脉冲 3 次
    pulse_end = 0.3
    # 后 1.7 秒：稳定运行

    for ti in t:
        if ti < pulse_end:
            # 脉冲阶段
            phase = (ti * 30) % 1.0  # 30 个脉冲/秒
            if phase < 0.5:
                pattern.append(200)
            else:
                pattern.append(0)
        else:
            # 稳定阶段
            pattern.append(target_speed)

    return np.array(pattern)

# ============================================================
# 绘图函数
# ============================================================

def plot_single_pattern(pattern_func, title, filename=None):
    """绘制单个运动模式"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # 生成模式数据
    if title == "缓慢摇晃":
        pattern = pattern_func(duration=4.0, amplitude=80)
        duration = 4.0
    elif title == "快速旋转":
        pattern = pattern_func(duration=2.0, speed=220)
        duration = 2.0
    elif title == "脉冲抖动":
        pattern = pattern_func(duration=1.0, intensity=120)
        duration = 1.0
    elif title == "加速螺旋":
        pattern = pattern_func(duration=3.0, max_speed=220)
        duration = 3.0
    elif title == "平滑制动":
        pattern = pattern_func(duration=1.5, initial_speed=200)
        duration = 1.5
    elif title == "脉冲启动":
        pattern = pattern_func(duration=2.0, target_speed=150)
        duration = 2.0
    else:
        pattern = pattern_func()
        duration = 3.0

    t = np.linspace(0, duration, len(pattern))

    # 绘制数据
    ax.plot(t, pattern, linewidth=2, color='#2E86AB', label='电机速度')
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.fill_between(t, 0, pattern, where=(pattern >= 0), alpha=0.3, color='green', label='正向')
    ax.fill_between(t, 0, pattern, where=(pattern < 0), alpha=0.3, color='red', label='反向')

    # 样式
    ax.set_xlabel('时间 (秒)', fontsize=12, fontweight='bold')
    ax.set_ylabel('速度 (-255 ~ 255)', fontsize=12, fontweight='bold')
    ax.set_title(f'运动模式: {title}', fontsize=14, fontweight='bold')
    ax.set_ylim(-260, 260)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=10)

    # 添加注释
    if "摇晃" in title:
        ax.text(0.98, 0.95, '🌿 温柔摇晃\n来回摆动5次',
                transform=ax.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    elif "旋转" in title and "加速" not in title:
        ax.text(0.98, 0.95, '⚡ 快速旋转\n持续高速',
                transform=ax.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    elif "抖动" in title:
        ax.text(0.98, 0.95, '🚨 告急信号\n快速颤动',
                transform=ax.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
    elif "加速" in title:
        ax.text(0.98, 0.95, '🌪️ 加速螺旋\n逐渐加速',
                transform=ax.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    elif "制动" in title:
        ax.text(0.98, 0.95, '⏱️ 平滑制动\n缓慢减速',
                transform=ax.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    elif "启动" in title:
        ax.text(0.98, 0.95, '⚙️ 脉冲启动\n冲击后稳定',
                transform=ax.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))

    plt.tight_layout()

    if filename:
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"✅ 已保存: {filename}")

    return fig

def plot_all_patterns():
    """绘制所有运动模式对比"""
    patterns = [
        (generate_sway_pattern, "缓慢摇晃", (4.0, 80)),
        (generate_fast_spin_pattern, "快速旋转", (2.0, 220)),
        (generate_vibrate_pattern, "脉冲抖动", (1.0, 120)),
        (generate_accelerate_pattern, "加速螺旋", (3.0, 220)),
        (generate_brake_pattern, "平滑制动", (1.5, 200)),
        (generate_pulse_start_pattern, "脉冲启动", (2.0, 150)),
    ]

    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    axes = axes.flatten()

    for idx, (func, title, args) in enumerate(patterns):
        ax = axes[idx]

        if title == "缓慢摇晃":
            pattern = func(duration=args[0], amplitude=args[1])
            duration = args[0]
        elif title == "快速旋转":
            pattern = func(duration=args[0], speed=args[1])
            duration = args[0]
        elif title == "脉冲抖动":
            pattern = func(duration=args[0], intensity=args[1])
            duration = args[0]
        elif title == "加速螺旋":
            pattern = func(duration=args[0], max_speed=args[1])
            duration = args[0]
        elif title == "平滑制动":
            pattern = func(duration=args[0], initial_speed=args[1])
            duration = args[0]
        elif title == "脉冲启动":
            pattern = func(duration=args[0], target_speed=args[1])
            duration = args[0]

        t = np.linspace(0, duration, len(pattern))

        ax.plot(t, pattern, linewidth=2, color='#2E86AB')
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        ax.fill_between(t, 0, pattern, where=(pattern >= 0), alpha=0.2, color='green')
        ax.fill_between(t, 0, pattern, where=(pattern < 0), alpha=0.2, color='red')

        ax.set_ylim(-260, 260)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('时间 (秒)', fontsize=10)
        ax.set_ylabel('速度', fontsize=10)
        ax.grid(True, alpha=0.3)

    plt.suptitle('F7OWER Kait - 所有运动模式对比', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()

    return fig

def plot_comparison_timeline():
    """绘制时间轴对比"""
    fig, ax = plt.subplots(figsize=(14, 8))

    modes = [
        ("缓慢摇晃", 4.0, '#90EE90'),
        ("快速旋转", 2.0, '#87CEEB'),
        ("脉冲抖动", 1.0, '#FFB6C6'),
        ("加速螺旋", 3.0, '#FFD700'),
        ("平滑制动", 1.5, '#DDA0DD'),
        ("脉冲启动", 2.0, '#F0E68C'),
    ]

    y_pos = len(modes) - 1
    colors = ['#90EE90', '#87CEEB', '#FFB6C6', '#FFD700', '#DDA0DD', '#F0E68C']

    for (mode, duration, color) in modes:
        rect = FancyBboxPatch((0, y_pos - 0.4), duration, 0.8,
                              boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(rect)

        # 添加标签
        ax.text(-0.5, y_pos, mode, fontsize=11, fontweight='bold',
                verticalalignment='center', horizontalalignment='right')
        ax.text(duration / 2, y_pos, f'{duration}s', fontsize=10, fontweight='bold',
                verticalalignment='center', horizontalalignment='center')

        y_pos -= 1

    ax.set_xlim(-3, 5)
    ax.set_ylim(-1, len(modes))
    ax.set_xlabel('持续时间 (秒)', fontsize=12, fontweight='bold')
    ax.set_title('运动模式执行时间对比', fontsize=14, fontweight='bold')
    ax.set_yticks([])
    ax.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    return fig

def create_info_sheet():
    """创建信息表"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('tight')
    ax.axis('off')

    # 运动模式信息
    modes_data = [
        ['模式', '名称', '持续时间', '速度范围', '效果', '用途'],
        ['1', '缓慢摇晃', '4秒', '±80', '来回摆动', '安抚/展示'],
        ['2', '快速旋转', '2秒', '+220', '持续旋转', '高兴/兴奋'],
        ['3', '脉冲抖动', '1秒', '±120', '快速颤动', '告急/提醒'],
        ['4', '加速螺旋', '3秒', '50→220', '逐步加速', '启动/唤醒'],
        ['5', '平滑制动', '1.5秒', '200→0', '缓速减速', '停止/休眠'],
        ['6', '脉冲启动', '2秒', '200→150', '冲击启动', '启动/复苏'],
    ]

    table = ax.table(cellText=modes_data, loc='upper center',
                     cellLoc='center', colWidths=[0.08, 0.12, 0.12, 0.12, 0.12, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)

    # 表头样式
    for i in range(6):
        table[(0, i)].set_facecolor('#2E86AB')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # 行样式
    colors = ['#E8F4F8', '#F4E8F8', '#F8E8E8', '#F8F4E8', '#E8F8F4', '#F4F8E8']
    for i in range(1, 7):
        for j in range(6):
            table[(i, j)].set_facecolor(colors[i - 1])

    plt.title('F7OWER Kait 运动模式详细参数', fontsize=16, fontweight='bold', pad=20)

    # 添加说明文字
    info_text = """
    参数说明:
    • 模式: 调用方式 /motion <模式号>
    • 持续时间: 执行完整周期所需时间
    • 速度范围: 电机PWM值 (-255～255)，负数表示反向
    • 效果: 视觉表现和物理感受
    • 用途: 建议的应用场景
    
    速度级别对应:
    • 0: 停止状态
    • ±50: 很低速（安静态）
    • ±100: 低速（展示态）
    • ±150: 中速（交互态）
    • ±200: 高速（活跃态）
    • ±255: 极速（告急态）
    """

    ax.text(0.5, -0.15, info_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top', horizontalalignment='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    return fig

# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Kait 运动模式可视化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 kait_motion_visualization.py --all
  python3 kait_motion_visualization.py --mode 1
  python3 kait_motion_visualization.py --timeline
  python3 kait_motion_visualization.py --info
        """
    )

    parser.add_argument("--all", action="store_true",
                        help="绘制所有模式对比图")
    parser.add_argument("--mode", type=int, choices=[1, 2, 3, 4, 5, 6],
                        help="绘制指定模式")
    parser.add_argument("--timeline", action="store_true",
                        help="绘制时间轴对比")
    parser.add_argument("--info", action="store_true",
                        help="绘制信息表")
    parser.add_argument("--output", "-o", type=str,
                        help="保存输出文件（PNG）")
    parser.add_argument("--show", "-s", action="store_true", default=True,
                        help="显示图表（默认）")
    parser.add_argument("--no-show", action="store_false", dest="show",
                        help="不显示图表，仅保存")

    args = parser.parse_args()

    # 默认选项
    if not any([args.all, args.mode, args.timeline, args.info]):
        args.all = True

    # 生成图表
    figs = []

    if args.mode:
        mode_funcs = {
            1: generate_sway_pattern,
            2: generate_fast_spin_pattern,
            3: generate_vibrate_pattern,
            4: generate_accelerate_pattern,
            5: generate_brake_pattern,
            6: generate_pulse_start_pattern,
        }
        mode_names = {
            1: "缓慢摇晃",
            2: "快速旋转",
            3: "脉冲抖动",
            4: "加速螺旋",
            5: "平滑制动",
            6: "脉冲启动",
        }

        filename = args.output or f"kait_mode_{args.mode}.png"
        fig = plot_single_pattern(mode_funcs[args.mode], mode_names[args.mode], filename)
        figs.append(fig)
        print(f"✅ 模式 {args.mode}: {mode_names[args.mode]}")

    if args.all:
        filename = args.output or "kait_all_patterns.png"
        fig = plot_all_patterns()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"✅ 已保存: {filename}")
        figs.append(fig)

    if args.timeline:
        filename = args.output or "kait_timeline.png"
        fig = plot_comparison_timeline()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"✅ 已保存: {filename}")
        figs.append(fig)

    if args.info:
        filename = args.output or "kait_info_sheet.png"
        fig = create_info_sheet()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"✅ 已保存: {filename}")
        figs.append(fig)

    if args.show and figs:
        plt.show()
    elif not args.output:
        print("💡 提示: 使用 --output 保存为 PNG 文件")

if __name__ == "__main__":
    main()


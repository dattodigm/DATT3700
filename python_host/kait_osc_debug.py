#!/usr/bin/env python3
"""
F7OWER Kait Node - OSC 调试脚本
支持 OSC 协议控制 Kait 节点的电机运动
"""

import argparse
import time
from pythonosc import udp_client
import socket
import sys

# ============================================================
# OSC 客户端配置
# ============================================================
class KaitOSCController:
    def __init__(self, ip="127.0.0.1", port=8888):
        self.ip = ip
        self.port = port
        try:
            self.client = udp_client.SimpleUDPClient(ip, port)
            print(f"✅ OSC 客户端已连接: {ip}:{port}")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            sys.exit(1)

    # ============================================================
    # 基础控制接口
    # ============================================================

    def set_motor_speed(self, speed):
        """
        设置电机速度
        :param speed: -255 ~ 255 (负数=反向，正数=正向，0=停止)
        """
        speed = max(-255, min(255, speed))
        self.client.send_message("/motor", speed)
        direction = "反向" if speed < 0 else ("正向" if speed > 0 else "停止")
        print(f"🎚️ 电机设置: {direction} (速度: {abs(speed)})")

    def execute_motion(self, mode):
        """
        执行预设运动模式
        :param mode: 1-6
                1: 缓慢摇晃
                2: 快速旋转
                3: 脉冲抖动
                4: 加速螺旋
                5: 平滑制动
                6: 脉冲启动
        """
        if 1 <= mode <= 6:
            self.client.send_message("/motion", mode)
            modes = {
                1: "缓慢摇晃",
                2: "快速旋转",
                3: "脉冲抖动",
                4: "加速螺旋",
                5: "平滑制动",
                6: "脉冲启动"
            }
            print(f"📍 执行运动模式 {mode}: {modes[mode]}")
        else:
            print(f"❌ 无效的模式号: {mode} (应该是 1-6)")

    def stop(self):
        """停止电机"""
        self.client.send_message("/stop", 0)
        print("⏹️ 电机已停止")

    # ============================================================
    # 运动序列
    # ============================================================

    def sequence_gentle_sway(self):
        """序列: 温柔摇晃"""
        print("\n🌿 执行序列: 温柔摇晃 (5次)")
        for i in range(5):
            print(f"  [{i+1}/5] 正向摇晃...")
            self.set_motor_speed(80)
            time.sleep(1.0)
            print(f"  [{i+1}/5] 反向摇晃...")
            self.set_motor_speed(-80)
            time.sleep(1.0)
        self.stop()
        print("✓ 序列完成\n")

    def sequence_excited_spin(self):
        """序列: 兴奋旋转（快速，间隔停顿）"""
        print("\n⚡ 执行序列: 兴奋旋转")
        for i in range(3):
            print(f"  [{i+1}/3] 旋转...")
            self.set_motor_speed(220)
            time.sleep(2.0)
            print(f"  [{i+1}/3] 停顿...")
            self.stop()
            time.sleep(0.5)
        print("✓ 序列完成\n")

    def sequence_alert_vibrate(self):
        """序列: 告急信号（快速颤动）"""
        print("\n🚨 执行序列: 告急信号")
        for cycle in range(2):
            print(f"  [周期 {cycle+1}/2] 快速颤动...")
            for _ in range(10):
                self.set_motor_speed(150)
                time.sleep(0.05)
                self.set_motor_speed(-150)
                time.sleep(0.05)
            time.sleep(0.5)
        self.stop()
        print("✓ 序列完成\n")

    def sequence_smooth_wake(self):
        """序列: 平滑唤醒（从慢到快）"""
        print("\n🌅 执行序列: 平滑唤醒")
        speeds = [50, 80, 120, 160, 200]
        for i, speed in enumerate(speeds):
            print(f"  [{i+1}/5] 速度 {speed}...")
            self.set_motor_speed(speed)
            time.sleep(0.8)
        print("  稳定运行...")
        time.sleep(1.0)
        print("  平滑制动...")
        for speed in reversed(speeds):
            self.set_motor_speed(speed)
            time.sleep(0.3)
        self.stop()
        print("✓ 序列完成\n")

    def sequence_dance(self):
        """序列: 舞蹈节奏（复杂的组合）"""
        print("\n💃 执行序列: 舞蹈节奏")
        patterns = [
            (120, 0.3, "快速摇晃"),
            (0, 0.2, "停顿"),
            (200, 0.5, "快速旋转"),
            (-120, 0.3, "反向快摇"),
            (0, 0.2, "停顿"),
            (180, 0.4, "中速旋转"),
        ]

        for repeat in range(2):
            print(f"  [周期 {repeat+1}/2]")
            for speed, duration, desc in patterns:
                self.set_motor_speed(speed)
                print(f"    {desc}...")
                time.sleep(duration)
        self.stop()
        print("✓ 序列完成\n")

    def sequence_test_all_modes(self):
        """序列: 测试所有运动模式"""
        print("\n🧪 执行序列: 测试所有模式")
        modes_info = [
            (1, "缓慢摇晃"),
            (2, "快速旋转"),
            (3, "脉冲抖动"),
            (4, "加速螺旋"),
            (5, "平滑制动"),
            (6, "脉冲启动"),
        ]

        for mode, name in modes_info:
            print(f"  测试模式 {mode}: {name}...")
            self.execute_motion(mode)
            time.sleep(3.5)  # 等待模式完成
        print("✓ 序列完成\n")

    # ============================================================
    # 实时交互控制
    # ============================================================

    def interactive_mode(self):
        """进入交互模式"""
        print("\n" + "="*50)
        print("进入交互模式 (输入 'help' 查看命令)")
        print("="*50 + "\n")

        while True:
            try:
                cmd = input("kait> ").strip()

                if not cmd:
                    continue

                elif cmd == "quit" or cmd == "exit":
                    print("👋 再见!")
                    break

                elif cmd == "help":
                    self._print_help()

                elif cmd.startswith("motor "):
                    try:
                        speed = int(cmd.split()[1])
                        self.set_motor_speed(speed)
                    except (ValueError, IndexError):
                        print("❌ 用法: motor <speed> (-255 ~ 255)")

                elif cmd.startswith("motion "):
                    try:
                        mode = int(cmd.split()[1])
                        self.execute_motion(mode)
                    except (ValueError, IndexError):
                        print("❌ 用法: motion <mode> (1-6)")

                elif cmd == "stop":
                    self.stop()

                elif cmd.startswith("seq "):
                    seq_name = cmd.split()[1] if len(cmd.split()) > 1 else ""
                    self._run_sequence(seq_name)

                elif cmd == "seqs":
                    self._list_sequences()

                else:
                    print(f"❌ 未知命令: {cmd} (输入 'help' 查看帮助)")

            except KeyboardInterrupt:
                print("\n\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

    def _print_help(self):
        print("\n" + "="*50)
        print("命令列表:")
        print("="*50)
        print("  motor <speed>     - 设置电机速度 (-255 ~ 255)")
        print("  motion <mode>     - 执行运动模式 (1-6)")
        print("  stop              - 停止电机")
        print("  seq <name>        - 执行预设序列")
        print("  seqs              - 列出所有预设序列")
        print("  help              - 显示此帮助")
        print("  quit/exit         - 退出程序")
        print("="*50 + "\n")

    def _list_sequences(self):
        sequences = [
            ("gentle_sway", "温柔摇晃 - 缓慢来回摆动"),
            ("excited_spin", "兴奋旋转 - 快速旋转，间隔停顿"),
            ("alert_vibrate", "告急信号 - 快速颤动"),
            ("smooth_wake", "平滑唤醒 - 从慢到快的加速"),
            ("dance", "舞蹈节奏 - 复杂的组合运动"),
            ("test_all", "测试所有模式 - 依次测试模式 1-6"),
        ]

        print("\n预设序列列表:")
        print("-" * 50)
        for name, desc in sequences:
            print(f"  {name:<20} - {desc}")
        print("-" * 50 + "\n")

    def _run_sequence(self, seq_name):
        sequences = {
            "gentle_sway": self.sequence_gentle_sway,
            "excited_spin": self.sequence_excited_spin,
            "alert_vibrate": self.sequence_alert_vibrate,
            "smooth_wake": self.sequence_smooth_wake,
            "dance": self.sequence_dance,
            "test_all": self.sequence_test_all_modes,
        }

        if seq_name in sequences:
            sequences[seq_name]()
        else:
            print(f"❌ 未知的序列: {seq_name}")
            print("输入 'seqs' 查看所有可用序列")


# ============================================================
# 命令行接口
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="F7OWER Kait Node - OSC 调试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 kait_osc_debug.py -i 192.168.1.100        # 连接到指定IP
  python3 kait_osc_debug.py --speed 100             # 设置电机速度
  python3 kait_osc_debug.py --motion 1              # 执行运动模式1
  python3 kait_osc_debug.py --seq gentle_sway      # 执行温柔摇晃序列
  python3 kait_osc_debug.py --interactive           # 进入交互模式
        """
    )

    parser.add_argument("-i", "--ip", default="127.0.0.1",
                        help="Kait 节点的 IP 地址 (默认: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int, default=8888,
                        help="OSC 端口 (默认: 8888)")
    parser.add_argument("--speed", type=int,
                        help="设置电机速度 (-255 ~ 255)")
    parser.add_argument("--motion", type=int,
                        help="执行运动模式 (1-6)")
    parser.add_argument("--stop", action="store_true",
                        help="停止电机")
    parser.add_argument("--seq", type=str,
                        help="执行预设序列")
    parser.add_argument("--interactive", "-it", action="store_true",
                        help="进入交互模式")

    args = parser.parse_args()

    # 创建控制器
    controller = KaitOSCController(args.ip, args.port)

    # 执行命令
    if args.speed is not None:
        controller.set_motor_speed(args.speed)

    elif args.motion is not None:
        controller.execute_motion(args.motion)

    elif args.stop:
        controller.stop()

    elif args.seq:
        sequences = {
            "gentle_sway": controller.sequence_gentle_sway,
            "excited_spin": controller.sequence_excited_spin,
            "alert_vibrate": controller.sequence_alert_vibrate,
            "smooth_wake": controller.sequence_smooth_wake,
            "dance": controller.sequence_dance,
            "test_all": controller.sequence_test_all_modes,
        }
        if args.seq in sequences:
            sequences[args.seq]()
        else:
            print(f"❌ 未知的序列: {args.seq}")
            controller._list_sequences()

    elif args.interactive:
        controller.interactive_mode()

    else:
        # 默认进入交互模式
        controller.interactive_mode()


if __name__ == "__main__":
    main()


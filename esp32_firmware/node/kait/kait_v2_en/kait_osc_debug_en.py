#!/usr/bin/env python3
"""
F7OWER Kait Node - OSC Debug Script (English Version)
Control Kait node's motor movement via OSC protocol
"""

import argparse
import time
from pythonosc import udp_client
import socket
import sys

# ============================================================
# OSC Client Configuration
# ============================================================
class KaitOSCController:
    def __init__(self, ip="127.0.0.1", port=8888):
        self.ip = ip
        self.port = port
        try:
            self.client = udp_client.SimpleUDPClient(ip, port)
            print(f"✅ OSC Client Connected: {ip}:{port}")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            sys.exit(1)

    # ============================================================
    # Basic Control Interface
    # ============================================================

    def set_motor_speed(self, speed):
        """
        Set motor speed
        :param speed: -255 ~ 255 (negative=reverse, positive=forward, 0=stop)
        """
        speed = max(-255, min(255, speed))
        self.client.send_message("/motor", speed)
        direction = "Reverse" if speed < 0 else ("Forward" if speed > 0 else "Stop")
        print(f"🎚️ Motor Set: {direction} (Speed: {abs(speed)})")

    def execute_motion(self, mode):
        """
        Execute preset motion mode
        :param mode: 1-6
                1: Gentle Sway
                2: Fast Spin
                3: Pulse Vibrate
                4: Accelerate Spin
                5: Smooth Brake
                6: Pulse Start
        """
        if 1 <= mode <= 6:
            self.client.send_message("/motion", mode)
            modes = {
                1: "Gentle Sway",
                2: "Fast Spin",
                3: "Pulse Vibrate",
                4: "Accelerate Spin",
                5: "Smooth Brake",
                6: "Pulse Start"
            }
            print(f"📍 Motion Mode {mode}: {modes[mode]}")
        else:
            print(f"❌ Invalid Mode: {mode} (Should be 1-6)")

    def stop(self):
        """Stop motor"""
        self.client.send_message("/stop", 0)
        print("⏹️ Motor Stopped")

    # ============================================================
    # Motion Sequences
    # ============================================================

    def sequence_gentle_sway(self):
        """Sequence: Gentle Sway (5 times)"""
        print("\n🌿 Sequence: Gentle Sway (5 cycles)")
        for i in range(5):
            print(f"  [{i+1}/5] Swaying forward...")
            self.set_motor_speed(80)
            time.sleep(1.0)
            print(f"  [{i+1}/5] Swaying backward...")
            self.set_motor_speed(-80)
            time.sleep(1.0)
        self.stop()
        print("✓ Sequence Complete\n")

    def sequence_excited_spin(self):
        """Sequence: Excited Spin (fast rotation with pauses)"""
        print("\n⚡ Sequence: Excited Spin")
        for i in range(3):
            print(f"  [{i+1}/3] Spinning...")
            self.set_motor_speed(220)
            time.sleep(2.0)
            print(f"  [{i+1}/3] Pausing...")
            self.stop()
            time.sleep(0.5)
        print("✓ Sequence Complete\n")

    def sequence_alert_vibrate(self):
        """Sequence: Alert Signal (rapid trembling)"""
        print("\n🚨 Sequence: Alert Signal")
        for cycle in range(2):
            print(f"  [Cycle {cycle+1}/2] Rapid trembling...")
            for _ in range(10):
                self.set_motor_speed(150)
                time.sleep(0.05)
                self.set_motor_speed(-150)
                time.sleep(0.05)
            time.sleep(0.5)
        self.stop()
        print("✓ Sequence Complete\n")

    def sequence_smooth_wake(self):
        """Sequence: Smooth Wake (accelerate from slow to fast)"""
        print("\n🌅 Sequence: Smooth Wake")
        speeds = [50, 80, 120, 160, 200]
        for i, speed in enumerate(speeds):
            print(f"  [{i+1}/5] Speed {speed}...")
            self.set_motor_speed(speed)
            time.sleep(0.8)
        print("  Stable operation...")
        time.sleep(1.0)
        print("  Smooth braking...")
        for speed in reversed(speeds):
            self.set_motor_speed(speed)
            time.sleep(0.3)
        self.stop()
        print("✓ Sequence Complete\n")

    def sequence_dance(self):
        """Sequence: Dance Rhythm (complex combination)"""
        print("\n💃 Sequence: Dance Rhythm")
        patterns = [
            (120, 0.3, "Fast sway"),
            (0, 0.2, "Pause"),
            (200, 0.5, "Fast spin"),
            (-120, 0.3, "Reverse sway"),
            (0, 0.2, "Pause"),
            (180, 0.4, "Medium spin"),
        ]

        for repeat in range(2):
            print(f"  [Cycle {repeat+1}/2]")
            for speed, duration, desc in patterns:
                self.set_motor_speed(speed)
                print(f"    {desc}...")
                time.sleep(duration)
        self.stop()
        print("✓ Sequence Complete\n")

    def sequence_test_all_modes(self):
        """Sequence: Test all motion modes"""
        print("\n🧪 Sequence: Test All Modes")
        modes_info = [
            (1, "Gentle Sway"),
            (2, "Fast Spin"),
            (3, "Pulse Vibrate"),
            (4, "Accelerate Spin"),
            (5, "Smooth Brake"),
            (6, "Pulse Start"),
        ]

        for mode, name in modes_info:
            print(f"  Testing Mode {mode}: {name}...")
            self.execute_motion(mode)
            time.sleep(3.5)  # Wait for mode to complete
        print("✓ Sequence Complete\n")

    # ============================================================
    # Interactive Mode
    # ============================================================

    def interactive_mode(self):
        """Enter interactive mode"""
        print("\n" + "="*50)
        print("Entering Interactive Mode (type 'help' for commands)")
        print("="*50 + "\n")

        while True:
            try:
                cmd = input("kait> ").strip()

                if not cmd:
                    continue

                elif cmd == "quit" or cmd == "exit":
                    print("👋 Goodbye!")
                    break

                elif cmd == "help":
                    self._print_help()

                elif cmd.startswith("motor "):
                    try:
                        speed = int(cmd.split()[1])
                        self.set_motor_speed(speed)
                    except (ValueError, IndexError):
                        print("❌ Usage: motor <speed> (-255 ~ 255)")

                elif cmd.startswith("motion "):
                    try:
                        mode = int(cmd.split()[1])
                        self.execute_motion(mode)
                    except (ValueError, IndexError):
                        print("❌ Usage: motion <mode> (1-6)")

                elif cmd == "stop":
                    self.stop()

                elif cmd.startswith("seq "):
                    seq_name = cmd.split()[1] if len(cmd.split()) > 1 else ""
                    self._run_sequence(seq_name)

                elif cmd == "seqs":
                    self._list_sequences()

                else:
                    print(f"❌ Unknown Command: {cmd} (type 'help' for help)")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def _print_help(self):
        print("\n" + "="*50)
        print("Command List:")
        print("="*50)
        print("  motor <speed>     - Set motor speed (-255 ~ 255)")
        print("  motion <mode>     - Execute motion mode (1-6)")
        print("  stop              - Stop motor")
        print("  seq <name>        - Execute preset sequence")
        print("  seqs              - List all preset sequences")
        print("  help              - Show this help")
        print("  quit/exit         - Exit program")
        print("="*50 + "\n")

    def _list_sequences(self):
        sequences = [
            ("gentle_sway", "Gentle Sway - Slow back and forth movement"),
            ("excited_spin", "Excited Spin - Fast rotation with pauses"),
            ("alert_vibrate", "Alert Signal - Rapid trembling"),
            ("smooth_wake", "Smooth Wake - Accelerate from slow to fast"),
            ("dance", "Dance Rhythm - Complex movement combination"),
            ("test_all", "Test All Modes - Test modes 1-6 sequentially"),
        ]

        print("\nPreset Sequences:")
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
            print(f"❌ Unknown Sequence: {seq_name}")
            print("Type 'seqs' to see all available sequences")


# ============================================================
# Command Line Interface
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="F7OWER Kait Node - OSC Debug Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 kait_osc_debug_en.py -i 192.168.1.100        # Connect to IP
  python3 kait_osc_debug_en.py --speed 100             # Set motor speed
  python3 kait_osc_debug_en.py --motion 1              # Execute motion mode 1
  python3 kait_osc_debug_en.py --seq dance             # Execute dance sequence
  python3 kait_osc_debug_en.py --interactive           # Enter interactive mode
        """
    )

    parser.add_argument("-i", "--ip", default="127.0.0.1",
                        help="Kait node IP address (default: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int, default=8888,
                        help="OSC port (default: 8888)")
    parser.add_argument("--speed", type=int,
                        help="Set motor speed (-255 ~ 255)")
    parser.add_argument("--motion", type=int,
                        help="Execute motion mode (1-6)")
    parser.add_argument("--stop", action="store_true",
                        help="Stop motor")
    parser.add_argument("--seq", type=str,
                        help="Execute preset sequence")
    parser.add_argument("--interactive", "-it", action="store_true",
                        help="Enter interactive mode")

    args = parser.parse_args()

    # Create controller
    controller = KaitOSCController(args.ip, args.port)

    # Execute commands
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
            print(f"❌ Unknown Sequence: {args.seq}")
            controller._list_sequences()

    elif args.interactive:
        controller.interactive_mode()

    else:
        # Default to interactive mode
        controller.interactive_mode()


if __name__ == "__main__":
    main()


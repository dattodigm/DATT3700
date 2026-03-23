#!/usr/bin/env python3
"""
F7OWER Kait Node - Serial Debug Script (English Version)
Control Kait node's motor movement via Serial port
"""

import serial
import argparse
import time
import sys
from typing import Optional

# ============================================================
# Serial Client Configuration
# ============================================================
class KaitSerialController:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(0.5)  # Wait for ESP32 initialization
            print(f"✅ Serial Port Connected: {port} @ {baudrate} baud")
        except serial.SerialException as e:
            print(f"❌ Serial Connection Failed: {e}")
            print(f"Please check:")
            print(f"  1. Device connected to {port}")
            print(f"  2. Sufficient permissions (sudo chmod 666 {port})")
            sys.exit(1)

    def _send_command(self, cmd: str) -> str:
        """
        Send serial command and get response
        :param cmd: Command to send
        :return: Device response
        """
        if not self.ser or not self.ser.is_open:
            print("❌ Serial Port Not Connected")
            return ""

        try:
            self.ser.write((cmd + "\n").encode('utf-8'))
            self.ser.flush()
            time.sleep(0.1)

            # Read response
            response = ""
            while self.ser.in_waiting:
                response += self.ser.read(1).decode('utf-8', errors='ignore')

            return response
        except Exception as e:
            print(f"❌ Serial Communication Error: {e}")
            return ""

    # ============================================================
    # Basic Control Interface
    # ============================================================

    def set_motor_speed(self, speed: int):
        """
        Set motor speed
        :param speed: -255 ~ 255
        """
        speed = max(-255, min(255, speed))
        cmd = f"motor {speed}"
        print(f"📤 Sending: {cmd}")
        response = self._send_command(cmd)
        if response:
            print(f"📥 Response: {response.strip()}")
        direction = "Reverse" if speed < 0 else ("Forward" if speed > 0 else "Stop")
        print(f"🎚️ Motor Set: {direction} (Speed: {abs(speed)})\n")

    def execute_motion(self, mode: int):
        """
        Execute preset motion mode
        :param mode: 1-6
        """
        if 1 <= mode <= 6:
            cmd = f"motion {mode}"
            print(f"📤 Sending: {cmd}")
            response = self._send_command(cmd)
            if response:
                print(f"📥 Response: {response.strip()}")
            modes = {
                1: "Gentle Sway",
                2: "Fast Spin",
                3: "Pulse Vibrate",
                4: "Accelerate Spin",
                5: "Smooth Brake",
                6: "Pulse Start"
            }
            print(f"📍 Motion Mode {mode}: {modes[mode]}\n")
        else:
            print(f"❌ Invalid Mode: {mode} (Should be 1-6)\n")

    def stop(self):
        """Stop motor"""
        cmd = "stop"
        print(f"📤 Sending: {cmd}")
        response = self._send_command(cmd)
        if response:
            print(f"📥 Response: {response.strip()}")
        print("⏹️ Motor Stopped\n")

    def get_info(self):
        """Get device info"""
        cmd = "info"
        print(f"📤 Sending: {cmd}")
        response = self._send_command(cmd)
        if response:
            print("📥 Device Info:")
            print(response)
        print()

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
                        print("❌ Usage: motor <speed> (-255 ~ 255)\n")

                elif cmd.startswith("motion "):
                    try:
                        mode = int(cmd.split()[1])
                        self.execute_motion(mode)
                    except (ValueError, IndexError):
                        print("❌ Usage: motion <mode> (1-6)\n")

                elif cmd == "stop":
                    self.stop()

                elif cmd == "info":
                    self.get_info()

                elif cmd.startswith("seq "):
                    seq_name = cmd.split()[1] if len(cmd.split()) > 1 else ""
                    self._run_sequence(seq_name)

                elif cmd == "seqs":
                    self._list_sequences()

                else:
                    print(f"❌ Unknown Command: {cmd} (type 'help' for help)\n")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")

    def _print_help(self):
        print("\n" + "="*50)
        print("Command List:")
        print("="*50)
        print("  motor <speed>     - Set motor speed (-255 ~ 255)")
        print("  motion <mode>     - Execute motion mode (1-6)")
        print("  stop              - Stop motor")
        print("  info              - Get device information")
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
            print("Type 'seqs' to see all available sequences\n")

    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()
            print("✅ Serial Port Closed")


# ============================================================
# Command Line Interface
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="F7OWER Kait Node - Serial Debug Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 kait_serial_debug_en.py                      # Default device
  python3 kait_serial_debug_en.py -p /dev/ttyUSB1     # Specify port
  python3 kait_serial_debug_en.py --speed 100         # Set motor speed
  python3 kait_serial_debug_en.py --motion 1          # Execute motion mode 1
  python3 kait_serial_debug_en.py --seq dance         # Execute dance sequence
  python3 kait_serial_debug_en.py --interactive       # Enter interactive mode
        """
    )

    parser.add_argument("-p", "--port", default="/dev/ttyUSB0",
                        help="Serial port path (default: /dev/ttyUSB0)")
    parser.add_argument("-b", "--baud", type=int, default=115200,
                        help="Baud rate (default: 115200)")
    parser.add_argument("--speed", type=int,
                        help="Set motor speed (-255 ~ 255)")
    parser.add_argument("--motion", type=int,
                        help="Execute motion mode (1-6)")
    parser.add_argument("--stop", action="store_true",
                        help="Stop motor")
    parser.add_argument("--info", action="store_true",
                        help="Get device information")
    parser.add_argument("--seq", type=str,
                        help="Execute preset sequence")
    parser.add_argument("--interactive", "-it", action="store_true",
                        help="Enter interactive mode")
    parser.add_argument("--list-ports", action="store_true",
                        help="List all available serial ports")

    args = parser.parse_args()

    # List available ports
    if args.list_ports:
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            if ports:
                print("Available Serial Ports:")
                for port in ports:
                    print(f"  {port.device:<20} - {port.description}")
            else:
                print("⚠️ No Serial Ports Found")
        except ImportError:
            print("⚠️ serial.tools.list_ports not available")
        return

    # Create controller
    controller = KaitSerialController(args.port, args.baud)

    try:
        # Execute commands
        if args.speed is not None:
            controller.set_motor_speed(args.speed)

        elif args.motion is not None:
            controller.execute_motion(args.motion)

        elif args.stop:
            controller.stop()

        elif args.info:
            controller.get_info()

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

    finally:
        controller.close()


if __name__ == "__main__":
    main()


"""
OSC Client — Multi-device flower control.
Matches the actual esp32_sylvie.ino OSC protocol.
"""

from pythonosc import udp_client
import configparser
import logging

logger = logging.getLogger(__name__)


class FlowerDevice:
    """Represents a single ESP32 flower device."""

    def __init__(self, name: str, ip: str, port: int, device_type: str = 'dc_motor'):
        self.name = name
        self.ip = ip
        self.port = port
        self.device_type = device_type  # 'dc_motor' or 'servo'
        try:
            self.client = udp_client.SimpleUDPClient(ip, port)
            self.connected = True
        except Exception as e:
            logger.warning(f"[OSC] Could not create client for {name} ({ip}:{port}): {e}")
            self.client = None
            self.connected = False

    def send(self, address: str, value):
        if self.client is None:
            return
        try:
            self.client.send_message(address, value)
        except Exception as e:
            logger.debug(f"[OSC] Send error to {self.name}: {e}")

    # --- High-level helpers for dc_motor type (esp32_sylvie protocol) ---
    def set_auto(self, enabled: bool):
        self.send('/auto', 1 if enabled else 0)

    def set_motor(self, motor_num: int, direction: int):
        """direction: 1=forward, -1=reverse, 0=stop"""
        self.send(f'/motor{motor_num}', direction)

    def set_led(self, led_num: int, r: int, g: int, b: int):
        self.send(f'/led{led_num}', [r, g, b])

    def set_preset(self, preset: int):
        self.send('/preset', preset)

    def stop_all(self):
        self.set_auto(False)
        self.set_preset(3)  # preset 3 = stop all in esp32_sylvie

    # --- Convenience: set flower openness (0.0-1.0) mapped to motor direction ---
    def set_openness(self, openness: float):
        """openness 0.0=closed, 1.0=fully open. Drives motor1 to open/close."""
        direction = 1 if openness > 0.5 else (-1 if openness < 0.3 else 0)
        self.set_motor(1, direction)

    # --- Convenience: set LED color from HSV-like params ---
    def set_led_hsv(self, led_num: int, hue: float, saturation: float, brightness: float):
        """hue 0-360, saturation 0-1, brightness 0-1"""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue / 360.0, saturation, brightness)
        self.set_led(led_num, int(r * 255), int(g * 255), int(b * 255))


class FlowerNetwork:
    """Manages all flower devices loaded from config."""

    def __init__(self, config: configparser.ConfigParser):
        self.devices: dict[str, FlowerDevice] = {}
        device_list = [d.strip() for d in config.get('Devices', 'device_list', fallback='').split(',') if d.strip()]
        for name in device_list:
            section = f'Device_{name}'
            if config.has_section(section):
                ip = config.get(section, 'ip')
                port = config.getint(section, 'port')
                dev_type = config.get(section, 'type', fallback='dc_motor')
                self.devices[name] = FlowerDevice(name, ip, port, dev_type)
                logger.info(f"[Network] Registered device '{name}' at {ip}:{port} (type={dev_type})")
            else:
                logger.warning(f"[Network] No config section for device '{name}'")

    def get(self, name: str) -> FlowerDevice:
        return self.devices.get(name)

    def all_devices(self) -> list:
        return list(self.devices.values())

    def broadcast_stop(self):
        for dev in self.devices.values():
            dev.stop_all()

    def device_names(self) -> list:
        return list(self.devices.keys())

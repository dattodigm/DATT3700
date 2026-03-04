"""Device discovery helpers for ESP32 flower nodes."""

from __future__ import annotations

import json
import os
import time as time_module

try:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
except ImportError:  # pragma: no cover - optional dependency in tests
    Zeroconf = None
    ServiceBrowser = None
    ServiceListener = object


REGISTRY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "ui", "device_registry.json"
)


class _MDNSListener(ServiceListener):
    """Collect mDNS services while the browser runs."""

    def __init__(self, zeroconf, service_type):
        self._zeroconf = zeroconf
        self._service_type = service_type
        self.records = []

    def remove_service(self, zeroconf, service_type, name):
        pass

    def update_service(self, zeroconf, service_type, name):
        pass

    def add_service(self, zeroconf, service_type, name):
        info = self._zeroconf.get_service_info(self._service_type, name, timeout=300)
        if info is None:
            return

        try:
            addresses = info.parsed_addresses()
        except Exception:
            addresses = []
        if not addresses:
            return

        txt = {}
        for key, value in info.properties.items():
            k = key.decode("utf-8", errors="ignore")
            if isinstance(value, bytes):
                txt[k] = value.decode("utf-8", errors="ignore")
            else:
                txt[k] = str(value)

        self.records.append(
            {
                "service_name": name,
                "hostname": info.server.rstrip(".") if info.server else "",
                "ip": addresses[0],
                "port": int(info.port),
                "txt": txt,
            }
        )


def load_registry(registry_path: str = REGISTRY_PATH) -> dict:
    if not os.path.exists(registry_path):
        return {
            "default_osc_port": 8888,
            "known_devices": {},
            "name_rules": [],
            "node_types": {},
        }
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def infer_node_type(name: str, txt_node_type: str | None = None, registry: dict | None = None) -> str:
    if txt_node_type:
        return txt_node_type

    registry = registry or load_registry()
    known = registry.get("known_devices", {})
    if name in known and known[name].get("node_type"):
        return known[name]["node_type"]

    lowered = (name or "").lower()
    for rule in registry.get("name_rules", []):
        token = (rule.get("contains") or "").lower()
        if token and token in lowered:
            return rule.get("node_type", "unknown")

    return "unknown"


def discover_mdns_nodes(timeout_sec: float = 1.2, registry: dict | None = None) -> list[dict]:
    """Discover devices from mDNS service advertisements."""
    if Zeroconf is None or ServiceBrowser is None:
        return []

    browser_cls = ServiceBrowser
    zeroconf_cls = Zeroconf
    if browser_cls is None or zeroconf_cls is None:
        return []

    registry = registry or load_registry()
    services = ["_datt_flower._tcp.local.", "_osc._udp.local."]
    seen = {}

    zc = zeroconf_cls()
    try:
        listeners = []
        browsers = []
        for service in services:
            listener = _MDNSListener(zc, service)
            listeners.append(listener)
            browsers.append(browser_cls(zc, service, listener))

        # Let the browser collect announcements for a short window.
        end_at = time_module.time() + timeout_sec
        while time_module.time() < end_at:
            time_module.sleep(0.05)

        for listener in listeners:
            for item in listener.records:
                name = item["hostname"].split(".")[0] if item["hostname"] else item["service_name"]
                txt_node_type = item["txt"].get("node_type")
                node_type = infer_node_type(name, txt_node_type=txt_node_type, registry=registry)
                key = f"{name}@{item['ip']}"
                seen[key] = {
                    "name": name,
                    "ip": item["ip"],
                    "port": item["port"] or registry.get("default_osc_port", 8888),
                    "node_type": node_type,
                    "source": "mdns",
                    "metadata": {
                        "service_name": item["service_name"],
                        "txt": item["txt"],
                    },
                }
    finally:
        zc.close()

    return list(seen.values())


def discover_nodes_via_gateway(
    osc_sender,
    gateway_ip: str,
    gateway_port: int = 8888,
    timeout_sec: float = 0.8,
    registry: dict | None = None,
) -> list[dict]:
    """Query a gateway ESP32 for AP client list and probe each client via /info/self."""
    registry = registry or load_registry()

    results = []
    seen = set()

    gateway_self = osc_sender.query_info_self_ip(gateway_ip, gateway_port, timeout=timeout_sec)
    gateway_name = gateway_self.get("name") if gateway_self else "gateway"
    gateway_type = infer_node_type(gateway_name, registry=registry)
    results.append(
        {
            "name": gateway_name,
            "ip": gateway_ip,
            "port": gateway_port,
            "node_type": gateway_type,
            "source": "gateway_self",
            "metadata": gateway_self or {},
        }
    )
    seen.add(gateway_ip)

    payload = osc_sender.query_info_clients_ip(gateway_ip, gateway_port, timeout=timeout_sec)
    if not payload:
        return results

    clients = payload.get("clients", [])
    for idx, client in enumerate(clients, start=1):
        ip = client.get("ip")
        if not ip or ip in seen:
            continue
        seen.add(ip)

        info = osc_sender.query_info_self_ip(ip, gateway_port, timeout=timeout_sec) or {}
        name = info.get("name") or f"client_{idx}"
        node_type = infer_node_type(name, registry=registry)

        results.append(
            {
                "name": name,
                "ip": ip,
                "port": gateway_port,
                "node_type": node_type,
                "source": "gateway_clients",
                "metadata": {
                    "mac": client.get("mac", ""),
                    "self": info,
                },
            }
        )

    return results


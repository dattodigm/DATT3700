"""
flower_client.py - OSC花朵客户端

管理与多个ESP32花朵的OSC通信
支持同时控制多个花朵，实现群体行为

作者: Digital Bloom Team
版本: 1.0.0
"""

from pythonosc import udp_client
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio
import time
from typing import Dict, List, Optional


class FlowerClient:
    """
    单个花朵的OSC客户端
    """
    
    def __init__(self, flower_id: str, name: str, ip: str, port: int = 8888):
        """
        初始化花朵客户端
        
        Args:
            flower_id: 唯一标识符
            name: 花朵名称
            ip: ESP32的IP地址
            port: OSC端口号
        """
        self.flower_id = flower_id
        self.name = name
        self.ip = ip
        self.port = port
        
        # 创建OSC客户端
        self.client = udp_client.SimpleUDPClient(ip, port)
        
        # 状态跟踪
        self.current_state = {
            'bloom': 0.0,
            'jitter': 0.0,
            'speed': 0.0,
            'r': 0,
            'g': 0,
            'b': 0,
            'label': 'BOREDOM'
        }
        
        self.last_update = 0
        self.is_connected = True
        
        print(f"🌸 花朵客户端已创建: {name} ({flower_id}) @ {ip}:{port}")
    
    def send_state(self, bloom: float, jitter: float, speed: float, 
                   r: int, g: int, b: int, lcd_message: str = ""):
        """
        发送完整状态到花朵
        
        Args:
            bloom: 开放度 (0.0-1.0)
            jitter: 颤动强度 (0.0-1.0)
            speed: 运动速度 (0.0-1.0)
            r, g, b: LED颜色 (0-255)
            lcd_message: LCD显示文本（可选）
        """
        # 限制范围
        bloom = max(0.0, min(1.0, bloom))
        jitter = max(0.0, min(1.0, jitter))
        speed = max(0.0, min(1.0, speed))
        r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
        
        # 发送OSC消息
        self.client.send_message(f"/flower/state", 
                                [bloom, jitter, speed, r, g, b])
        
        # 发送LCD消息（如果有）
        if lcd_message:
            self.client.send_message(f"/flower/lcd", [lcd_message])
        
        # 更新状态
        self.current_state.update({
            'bloom': bloom,
            'jitter': jitter,
            'speed': speed,
            'r': r,
            'g': g,
            'b': b
        })
        self.last_update = time.time()
    
    def send_preset(self, preset_id: int):
        """
        发送预设场景
        
        Args:
            preset_id: 预设ID (1-5)
        """
        self.client.send_message(f"/flower/preset", [preset_id])
        print(f"[{self.name}] 应用预设: {preset_id}")
    
    def send_label(self, label: str):
        """
        发送性格标签（用于显示）
        """
        self.current_state['label'] = label
    
    def emergency_stop(self):
        """紧急停止"""
        self.client.send_message(f"/system/stop", [])
        print(f"🛑 [{self.name}] 紧急停止")
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            self.client.send_message("/flower/test", [1])
            return True
        except Exception as e:
            self.is_connected = False
            return False


class FlowerOrchestrator:
    """
    花朵编排器
    
    管理多个花朵，实现群体行为和嫉妒网络
    """
    
    def __init__(self):
        """初始化编排器"""
        self.flowers: Dict[str, FlowerClient] = {}
        self.jealousy_enabled = True
        self.jealousy_threshold = 5.0  # 秒
        self.jealousy_cooldown = 3.0   # 嫉妒状态持续时间
        
        # 跟踪每朵花的共情时间
        self.empathy_timers = {}
        self.jealousy_timers = {}
        
    def add_flower(self, flower_id: str, name: str, ip: str, port: int = 8888):
        """
        添加花朵
        
        Args:
            flower_id: 唯一ID
            name: 显示名称
            ip: IP地址
            port: 端口号
        """
        if flower_id in self.flowers:
            print(f"警告: 花朵 {flower_id} 已存在，将覆盖")
        
        self.flowers[flower_id] = FlowerClient(flower_id, name, ip, port)
        self.empathy_timers[flower_id] = 0
        self.jealousy_timers[flower_id] = 0
        
    def remove_flower(self, flower_id: str):
        """移除花朵"""
        if flower_id in self.flowers:
            del self.flowers[flower_id]
            del self.empathy_timers[flower_id]
            del self.jealousy_timers[flower_id]
    
    def update_flower_state(self, flower_id: str, params: dict):
        """
        更新单朵花状态
        
        Args:
            flower_id: 花朵ID
            params: 包含bloom, jitter, speed, r, g, b, lcd的字典
        """
        if flower_id not in self.flowers:
            print(f"错误: 未知花朵 {flower_id}")
            return
        
        flower = self.flowers[flower_id]
        
        # 发送状态
        flower.send_state(
            bloom=params.get('bloom', 0),
            jitter=params.get('jitter', 0),
            speed=params.get('speed', 0),
            r=params.get('r', 0),
            g=params.get('g', 0),
            b=params.get('b', 0),
            lcd_message=params.get('lcd', '')
        )
        
        # 更新共情计时器
        label = params.get('label', '')
        if label == 'EMPATHY':
            self.empathy_timers[flower_id] += 0.1  # 假设每100ms调用一次
        else:
            self.empathy_timers[flower_id] = max(0, self.empathy_timers[flower_id] - 0.1)
        
        # 检查并应用嫉妒网络
        if self.jealousy_enabled:
            self._apply_jealousy_network()
    
    def _apply_jealousy_network(self):
        """
        应用嫉妒网络算法
        
        如果某朵花被持续共情超过阈值，其他花会进入嫉妒状态
        """
        # 找出最受关注的花
        max_empathy = 0
        favored_flower = None
        
        for flower_id, timer in self.empathy_timers.items():
            if timer > max_empathy:
                max_empathy = timer
                favored_flower = flower_id
        
        # 如果超过阈值，触发嫉妒
        if max_empathy > self.jealousy_threshold and favored_flower:
            for flower_id, flower in self.flowers.items():
                if flower_id != favored_flower:
                    # 检查是否在冷却期
                    if self.jealousy_timers[flower_id] <= 0:
                        # 触发嫉妒
                        print(f"💜 嫉妒触发: {flower.name} 嫉妒 {self.flowers[favored_flower].name}")
                        
                        # 覆盖为嫉妒状态
                        flower.send_state(
                            bloom=0.5,
                            jitter=1.0,
                            speed=1.0,
                            r=128, g=0, b=128,
                            lcd_message="Jealous! >:("
                        )
                        flower.send_label('JEALOUS')
                        
                        # 设置冷却时间
                        self.jealousy_timers[flower_id] = self.jealousy_cooldown
        
        # 更新嫉妒计时器
        for flower_id in self.jealousy_timers:
            self.jealousy_timers[flower_id] = max(0, self.jealousy_timers[flower_id] - 0.1)
    
    def broadcast_to_all(self, params: dict):
        """
        广播状态到所有花朵
        
        Args:
            params: 运动参数字典
        """
        for flower in self.flowers.values():
            flower.send_state(
                bloom=params.get('bloom', 0),
                jitter=params.get('jitter', 0),
                speed=params.get('speed', 0),
                r=params.get('r', 0),
                g=params.get('g', 0),
                b=params.get('b', 0),
                lcd_message=params.get('lcd', '')
            )
    
    def emergency_stop_all(self):
        """紧急停止所有花朵"""
        print("🛑 紧急停止所有花朵！")
        for flower in self.flowers.values():
            flower.emergency_stop()
    
    def get_flower_status(self) -> Dict:
        """获取所有花朵状态"""
        status = {}
        for flower_id, flower in self.flowers.items():
            status[flower_id] = {
                'name': flower.name,
                'ip': flower.ip,
                'connected': flower.is_connected,
                'state': flower.current_state,
                'empathy_time': self.empathy_timers[flower_id]
            }
        return status
    
    def list_flowers(self) -> List[str]:
        """列出所有花朵"""
        return [f"{fid}: {f.name}" for fid, f in self.flowers.items()]


# 测试代码
if __name__ == "__main__":
    print("🌸 测试花朵编排器...")
    
    orchestrator = FlowerOrchestrator()
    
    # 添加虚拟花朵（仅用于测试，无实际硬件）
    orchestrator.add_flower("flower1", "Sylvie", "192.168.4.1", 8888)
    orchestrator.add_flower("flower2", "Sue", "192.168.4.2", 8888)
    orchestrator.add_flower("flower3", "Lily", "192.168.4.3", 8888)
    
    print("\n花朵列表:")
    for info in orchestrator.list_flowers():
        print(f"  {info}")
    
    print("\n测试广播...")
    orchestrator.broadcast_to_all({
        'bloom': 0.8,
        'jitter': 0.3,
        'speed': 0.5,
        'r': 255, 'g': 255, 'b': 0,
        'lcd': 'Test!'
    })
    
    print("\n测试嫉妒网络...")
    # 模拟flower1被持续共情
    for i in range(60):  # 6秒
        orchestrator.update_flower_state("flower1", {
            'label': 'EMPATHY',
            'bloom': 0.9, 'jitter': 0.1, 'speed': 0.2,
            'r': 255, 'g': 105, 'b': 180
        })
        time.sleep(0.1)
    
    print("\n测试完成！")

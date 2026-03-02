"""
pid_controller.py - PID控制器

用于平滑的人脸追踪舵机控制

作者: Digital Bloom Team
版本: 1.0.0
"""

import time
from typing import Optional, Tuple


class PIDController:
    """
    PID控制器
    
    实现比例-积分-微分控制算法，用于平滑的舵机控制
    """
    
    def __init__(self, 
                 kp: float = 0.15,
                 ki: float = 0.01, 
                 kd: float = 0.05,
                 setpoint: float = 0.0,
                 output_limits: Optional[Tuple[float, float]] = None,
                 sample_time: float = 0.033):
        """
        初始化PID控制器
        
        Args:
            kp: 比例增益
            ki: 积分增益
            kd: 微分增益
            setpoint: 目标值（误差应为0）
            output_limits: 输出限制 (min, max)
            sample_time: 采样时间（秒）
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits or (-100, 100)
        self.sample_time = sample_time
        
        # 状态变量
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = time.time()
        
        # 输出平滑
        self._last_output = 0.0
        self.output_smoothing = 0.3  # EMA平滑系数
        
    def update(self, error: float) -> float:
        """
        更新PID控制器
        
        Args:
            error: 当前误差值
            
        Returns:
            float: PID输出
        """
        current_time = time.time()
        dt = current_time - self._last_time
        
        # 检查采样时间
        if dt < self.sample_time:
            return self._last_output
        
        # 计算各项
        # 比例项
        proportional = self.kp * error
        
        # 积分项（带抗饱和）
        self._integral += error * dt
        self._integral = max(-100, min(100, self._integral))  # 限制积分累积
        integral = self.ki * self._integral
        
        # 微分项
        if dt > 0:
            derivative = self.kd * (error - self._last_error) / dt
        else:
            derivative = 0.0
        
        # 计算输出
        output = proportional + integral + derivative
        
        # 限制输出范围
        output = max(self.output_limits[0], min(self.output_limits[1], output))
        
        # EMA平滑
        output = (self.output_smoothing * output + 
                 (1 - self.output_smoothing) * self._last_output)
        
        # 更新状态
        self._last_error = error
        self._last_time = current_time
        self._last_output = output
        
        return output
    
    def reset(self):
        """重置控制器"""
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = time.time()
        self._last_output = 0.0
    
    def set_tunings(self, kp: float = None, ki: float = None, kd: float = None):
        """
        调整PID参数
        
        Args:
            kp: 新的比例增益
            ki: 新的积分增益
            kd: 新的微分增益
        """
        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd


class ServoController:
    """
    舵机控制器
    
    整合PID控制和舵机角度计算
    """
    
    def __init__(self, 
                 pan_pid: PIDController = None,
                 tilt_pid: PIDController = None,
                 pan_center: int = 90,
                 tilt_center: int = 90,
                 pan_range: Tuple[int, int] = (0, 180),
                 tilt_range: Tuple[int, int] = (0, 180)):
        """
        初始化舵机控制器
        
        Args:
            pan_pid: 水平方向PID控制器
            tilt_pid: 垂直方向PID控制器
            pan_center: 水平中心角度
            tilt_center: 垂直中心角度
            pan_range: 水平角度范围
            tilt_range: 垂直角度范围
        """
        # 使用默认PID参数如果没有提供
        self.pan_pid = pan_pid or PIDController(
            kp=0.15, ki=0.01, kd=0.05,
            output_limits=(-30, 30)
        )
        
        self.tilt_pid = tilt_pid or PIDController(
            kp=0.15, ki=0.01, kd=0.05,
            output_limits=(-30, 30)
        )
        
        # 角度设置
        self.pan_center = pan_center
        self.tilt_center = tilt_center
        self.pan_range = pan_range
        self.tilt_range = tilt_range
        
        # 当前角度
        self.current_pan = pan_center
        self.current_tilt = tilt_center
        
    def update(self, x_error: float, y_error: float) -> Tuple[int, int]:
        """
        更新舵机角度
        
        Args:
            x_error: X方向误差（像素）
            y_error: Y方向误差（像素）
            
        Returns:
            Tuple[int, int]: (pan_angle, tilt_angle)
        """
        # 计算PID输出
        pan_correction = self.pan_pid.update(x_error)
        tilt_correction = self.tilt_pid.update(y_error)
        
        # 更新角度（注意方向：负误差意味着目标在左边，需要向左转）
        self.current_pan -= pan_correction
        self.current_tilt += tilt_correction
        
        # 限制角度范围
        self.current_pan = max(self.pan_range[0], 
                              min(self.pan_range[1], self.current_pan))
        self.current_tilt = max(self.tilt_range[0], 
                               min(self.tilt_range[1], self.current_tilt))
        
        return int(self.current_pan), int(self.current_tilt)
    
    def reset(self):
        """重置到中心位置"""
        self.pan_pid.reset()
        self.tilt_pid.reset()
        self.current_pan = self.pan_center
        self.current_tilt = self.tilt_center
        
    def set_position(self, pan: int, tilt: int):
        """
        直接设置位置（用于手动控制）
        
        Args:
            pan: 水平角度
            tilt: 垂直角度
        """
        self.current_pan = max(self.pan_range[0], 
                              min(self.pan_range[1], pan))
        self.current_tilt = max(self.tilt_range[0], 
                               min(self.tilt_range[1], tilt))
        
        # 重置PID避免突变
        self.pan_pid.reset()
        self.tilt_pid.reset()


# 测试代码
if __name__ == "__main__":
    print("🎮 测试PID控制器...")
    
    # 创建控制器
    pid = PIDController(kp=0.15, ki=0.01, kd=0.05)
    
    # 模拟追踪
    current_pos = 50
    target_pos = 100
    
    print("模拟从50追踪到100...")
    for i in range(50):
        error = target_pos - current_pos
        output = pid.update(error)
        current_pos += output * 0.1  # 应用输出
        
        if i % 10 == 0:
            print(f"Step {i}: pos={current_pos:.1f}, error={error:.1f}, output={output:.1f}")
    
    print(f"\n最终结果: {current_pos:.1f}")
    
    # 测试舵机控制器
    print("\n测试舵机控制器...")
    servo = ServoController()
    
    # 模拟人脸偏移
    errors = [(50, 30), (30, 20), (10, 5), (0, 0), (-10, -5)]
    
    for x_err, y_err in errors:
        pan, tilt = servo.update(x_err, y_err)
        print(f"Error: ({x_err:3d}, {y_err:3d}) -> Servo: ({pan:3d}, {tilt:3d})")
    
    print("\n测试完成")

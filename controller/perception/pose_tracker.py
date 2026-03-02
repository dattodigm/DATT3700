"""
pose_tracker.py - 姿态识别模块

使用MediaPipe Pose进行人体姿态检测和分析：
- 33个关键点的3D坐标
- 姿态开放度计算（肢体伸展程度）
- 身体朝向和倾斜角度
- 手部活跃度检测

作者: Digital Bloom Team
版本: 1.0.0
"""

import cv2
import numpy as np
import mediapipe as mp
from collections import deque
import math


class PoseTracker:
    """
    MediaPipe姿态跟踪器
    
    分析人体姿态特征，用于花朵行为映射
    """
    
    def __init__(self, smoothing_frames=5):
        """
        初始化姿态跟踪器
        
        Args:
            smoothing_frames: 平滑窗口大小
        """
        self.smoothing_frames = smoothing_frames
        
        # 初始化MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,  # 0=轻量, 1=完整, 2=重型
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 历史记录用于平滑
        self.openness_history = deque(maxlen=smoothing_frames)
        self.energy_history = deque(maxlen=smoothing_frames)
        
        # 关键点索引
        self.KEYPOINTS = {
            'nose': 0,
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_elbow': 13,
            'right_elbow': 14,
            'left_wrist': 15,
            'right_wrist': 16,
            'left_hip': 23,
            'right_hip': 24,
            'left_knee': 25,
            'right_knee': 26,
            'left_ankle': 27,
            'right_ankle': 28,
        }
        
    def analyze(self, frame):
        """
        分析视频帧中的人体姿态
        
        Args:
            frame: OpenCV BGR图像
            
        Returns:
            dict: 姿态分析结果，如果未检测到人体返回None
        """
        # 转换颜色空间（MediaPipe需要RGB）
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 处理图像
        results = self.pose.process(rgb_frame)
        
        if not results.pose_landmarks:
            return None
        
        landmarks = results.pose_landmarks.landmark
        
        # 计算各项指标
        openness = self._calculate_openness(landmarks)
        energy = self._calculate_movement_energy(landmarks)
        posture = self._calculate_posture(landmarks)
        
        # 添加到历史记录
        self.openness_history.append(openness)
        self.energy_history.append(energy)
        
        return {
            'landmarks': landmarks,
            'openness': np.mean(self.openness_history),
            'energy': np.mean(self.energy_history),
            'posture': posture,
            'hand_positions': self._get_hand_positions(landmarks),
            'visibility': self._calculate_visibility(landmarks)
        }
    
    def _calculate_openness(self, landmarks):
        """
        计算姿态开放度（0-1）
        
        基于肩宽和臂展相对于身体高度的比例
        开放度越高 = 肢体越伸展 = 越自信/友好
        """
        try:
            # 获取关键点
            left_shoulder = landmarks[self.KEYPOINTS['left_shoulder']]
            right_shoulder = landmarks[self.KEYPOINTS['right_shoulder']]
            left_wrist = landmarks[self.KEYPOINTS['left_wrist']]
            right_wrist = landmarks[self.KEYPOINTS['right_wrist']]
            left_hip = landmarks[self.KEYPOINTS['left_hip']]
            right_hip = landmarks[self.KEYPOINTS['right_hip']]
            
            # 计算身体高度（肩到髋）
            shoulder_center = self._midpoint(left_shoulder, right_shoulder)
            hip_center = self._midpoint(left_hip, right_hip)
            body_height = self._distance(shoulder_center, hip_center)
            
            if body_height < 0.01:  # 避免除零
                return 0.5
            
            # 计算肩宽
            shoulder_width = self._distance(left_shoulder, right_shoulder)
            
            # 计算臂展（手腕到肩膀的距离之和）
            left_arm_span = self._distance(left_shoulder, left_wrist)
            right_arm_span = self._distance(right_shoulder, right_wrist)
            total_arm_span = left_arm_span + right_arm_span
            
            # 开放度 = (肩宽 + 臂展) / (2 * 身体高度)
            # 理论最大值约1.5（双臂完全伸展）
            openness = (shoulder_width + total_arm_span) / (2 * body_height)
            
            # 归一化到0-1范围
            openness = min(openness / 1.5, 1.0)
            
            return openness
            
        except Exception:
            return 0.5
    
    def _calculate_movement_energy(self, landmarks):
        """
        计算运动能量（手部活跃度）
        
        基于手部相对于身体中心的位置变化
        """
        try:
            left_wrist = landmarks[self.KEYPOINTS['left_wrist']]
            right_wrist = landmarks[self.KEYPOINTS['right_wrist']]
            shoulder_center = self._midpoint(
                landmarks[self.KEYPOINTS['left_shoulder']],
                landmarks[self.KEYPOINTS['right_shoulder']]
            )
            
            # 计算手到身体中心的距离
            left_hand_dist = self._distance(left_wrist, shoulder_center)
            right_hand_dist = self._distance(right_wrist, shoulder_center)
            
            # 归一化
            energy = (left_hand_dist + right_hand_dist) / 2
            return min(energy * 2, 1.0)  # 放大并限制
            
        except Exception:
            return 0.0
    
    def _calculate_posture(self, landmarks):
        """
        计算身体姿态特征
        
        Returns:
            dict: 包含倾斜角度、朝向等
        """
        try:
            # 计算身体倾斜角度
            left_shoulder = landmarks[self.KEYPOINTS['left_shoulder']]
            right_shoulder = landmarks[self.KEYPOINTS['right_shoulder']]
            left_hip = landmarks[self.KEYPOINTS['left_hip']]
            right_hip = landmarks[self.KEYPOINTS['right_hip']]
            
            # 肩线和髋线的角度
            shoulder_angle = math.atan2(
                right_shoulder.y - left_shoulder.y,
                right_shoulder.x - left_shoulder.x
            )
            
            hip_angle = math.atan2(
                right_hip.y - left_hip.y,
                right_hip.x - left_hip.x
            )
            
            # 身体倾斜（前倾/后仰）
            # 基于鼻子到肩膀中心的角度
            nose = landmarks[self.KEYPOINTS['nose']]
            shoulder_center = self._midpoint(left_shoulder, right_shoulder)
            
            lean_angle = math.atan2(
                nose.y - shoulder_center.y,
                nose.x - shoulder_center.x
            )
            
            return {
                'shoulder_angle': math.degrees(shoulder_angle),
                'hip_angle': math.degrees(hip_angle),
                'lean_angle': math.degrees(lean_angle),
                'is_leaning_forward': lean_angle > 0.2,
                'is_leaning_back': lean_angle < -0.2
            }
            
        except Exception:
            return {'lean_angle': 0, 'is_leaning_forward': False, 'is_leaning_back': False}
    
    def _get_hand_positions(self, landmarks):
        """
        获取手部位置信息
        """
        try:
            left_wrist = landmarks[self.KEYPOINTS['left_wrist']]
            right_wrist = landmarks[self.KEYPOINTS['right_wrist']]
            
            return {
                'left': {'x': left_wrist.x, 'y': left_wrist.y, 'visibility': left_wrist.visibility},
                'right': {'x': right_wrist.x, 'y': right_wrist.y, 'visibility': right_wrist.visibility}
            }
        except Exception:
            return {'left': None, 'right': None}
    
    def _calculate_visibility(self, landmarks):
        """
        计算整体可见度（有多少关键点被检测到）
        """
        visibilities = [lm.visibility for lm in landmarks]
        return np.mean(visibilities)
    
    def _midpoint(self, p1, p2):
        """计算两点中点"""
        return type('Point', (), {
            'x': (p1.x + p2.x) / 2,
            'y': (p1.y + p2.y) / 2,
            'z': (p1.z + p2.z) / 2
        })()
    
    def _distance(self, p1, p2):
        """计算两点间距离"""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    
    def draw_results(self, frame, result):
        """
        在图像上绘制姿态骨架
        
        Args:
            frame: OpenCV图像
            result: analyze()的返回结果
            
        Returns:
            绘制后的图像
        """
        if result is None or 'landmarks' not in result:
            return frame
        
        # 转换回RGB用于MediaPipe绘制
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 创建临时results对象用于绘制
        class TempResults:
            def __init__(self, landmarks):
                self.pose_landmarks = type('obj', (object,), {'landmark': landmarks})()
        
        temp_results = TempResults(result['landmarks'])
        
        # 绘制骨架
        self.mp_drawing.draw_landmarks(
            rgb_frame,
            temp_results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        # 转换回BGR
        frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        
        # 绘制开放度指示器
        h, w = frame.shape[:2]
        openness = result['openness']
        bar_width = int(openness * 200)
        
        # 背景条
        cv2.rectangle(frame, (w - 220, 20), (w - 20, 40), (50, 50, 50), -1)
        # 进度条
        color = (0, int(255 * openness), int(255 * (1 - openness)))
        cv2.rectangle(frame, (w - 220, 20), (w - 220 + bar_width, 40), color, -1)
        # 标签
        cv2.putText(frame, f"Openness: {openness:.2f}", (w - 215, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 绘制能量指示器
        energy = result['energy']
        energy_width = int(energy * 200)
        cv2.rectangle(frame, (w - 220, 70), (w - 20, 90), (50, 50, 50), -1)
        cv2.rectangle(frame, (w - 220, 70), (w - 220 + energy_width, 90), 
                     (0, int(255 * energy), 255), -1)
        cv2.putText(frame, f"Energy: {energy:.2f}", (w - 215, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def reset(self):
        """
        重置跟踪器状态
        """
        self.openness_history.clear()
        self.energy_history.clear()


# 测试代码
if __name__ == "__main__":
    print("🕺 测试姿态跟踪器...")
    
    tracker = PoseTracker(smoothing_frames=3)
    cap = cv2.VideoCapture(0)
    
    print("按 'q' 退出")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 翻转图像（镜像效果）
        frame = cv2.flip(frame, 1)
        
        # 分析姿态
        result = tracker.analyze(frame)
        
        # 绘制结果
        frame = tracker.draw_results(frame, result)
        
        # 显示信息
        if result:
            print(f"\r开放度: {result['openness']:.2f} | "
                  f"能量: {result['energy']:.2f} | "
                  f"可见度: {result['visibility']:.2f}", end='')
        
        cv2.imshow('Pose Tracking', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n测试完成")

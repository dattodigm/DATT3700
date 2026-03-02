"""
face_tracker.py - 人脸追踪模块

支持：
- 多目标人脸检测
- 加权选择目标（面积权重 + 中心位置权重）
- 人脸中心坐标计算
- 人脸面积计算（用于距离估计）

作者: Digital Bloom Team
版本: 1.0.0
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class FaceData:
    """人脸数据结构"""
    x: int
    y: int
    width: int
    height: int
    center_x: int
    center_y: int
    area: int
    confidence: float
    
    @property
    def aspect_ratio(self) -> float:
        """宽高比"""
        return self.width / self.height if self.height > 0 else 0


class FaceTracker:
    """
    人脸追踪器
    
    支持多目标检测和智能目标选择
    """
    
    def __init__(self, frame_width: int = 640, frame_height: int = 480,
                 area_weight: float = 0.7, center_weight: float = 0.3):
        """
        初始化人脸追踪器
        
        Args:
            frame_width: 画面宽度
            frame_height: 画面高度
            area_weight: 面积权重（越大表示距离越近权重越高）
            center_weight: 中心位置权重（越居中权重越高）
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        
        # 权重配置
        self.area_weight = area_weight
        self.center_weight = center_weight
        
        # 加载Haar级联分类器
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise RuntimeError("无法加载人脸检测模型")
        
        # 当前追踪目标
        self.current_target: Optional[FaceData] = None
        self.target_face_id = 0  # 用于稳定追踪同一目标
        
    def detect_faces(self, frame: np.ndarray) -> List[FaceData]:
        """
        检测画面中的所有人脸
        
        Args:
            frame: OpenCV BGR图像
            
        Returns:
            List[FaceData]: 检测到的人脸列表
        """
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 检测人脸
        faces_rect = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50),
            maxSize=(frame.shape[1]//2, frame.shape[0]//2)  # 限制最大尺寸
        )
        
        face_list = []
        for i, (x, y, w, h) in enumerate(faces_rect):
            # 计算中心点
            center_x = x + w // 2
            center_y = y + h // 2
            area = w * h
            
            # 简单的置信度（基于检测质量）
            confidence = min(1.0, area / 10000)  # 面积越大越可信
            
            face = FaceData(
                x=int(x), y=int(y),
                width=int(w), height=int(h),
                center_x=int(center_x), center_y=int(center_y),
                area=int(area),
                confidence=float(confidence)
            )
            face_list.append(face)
        
        return face_list
    
    def select_target(self, faces: List[FaceData]) -> Optional[FaceData]:
        """
        根据加权算法选择目标人脸
        
        加权公式：
        score = area_weight * (area / max_area) + 
                center_weight * (1 - distance_to_center / max_distance)
        
        Args:
            faces: 人脸列表
            
        Returns:
            Optional[FaceData]: 选中的目标人脸
        """
        if not faces:
            return None
        
        if len(faces) == 1:
            return faces[0]
        
        # 计算最大面积用于归一化
        max_area = max(f.area for f in faces)
        max_distance = np.sqrt(self.center_x**2 + self.center_y**2)
        
        best_face = None
        best_score = -1
        
        for face in faces:
            # 面积分数（越大越好，表示越近）
            area_score = face.area / max_area if max_area > 0 else 0
            
            # 中心距离分数（越居中越好）
            distance_to_center = np.sqrt(
                (face.center_x - self.center_x)**2 + 
                (face.center_y - self.center_y)**2
            )
            center_score = 1 - (distance_to_center / max_distance) if max_distance > 0 else 0
            
            # 综合加权分数
            total_score = (self.area_weight * area_score + 
                          self.center_weight * center_score)
            
            if total_score > best_score:
                best_score = total_score
                best_face = face
        
        return best_face
    
    def track(self, frame: np.ndarray) -> Tuple[Optional[FaceData], List[FaceData]]:
        """
        追踪人脸
        
        Args:
            frame: OpenCV BGR图像
            
        Returns:
            Tuple[Optional[FaceData], List[FaceData]]: 
                (选中的目标人脸, 所有检测到的人脸列表)
        """
        # 检测所有人脸
        faces = self.detect_faces(frame)
        
        # 选择目标
        target = self.select_target(faces)
        self.current_target = target
        
        return target, faces
    
    def calculate_error(self, target: FaceData) -> Tuple[float, float]:
        """
        计算追踪误差（用于PID控制）
        
        Args:
            target: 目标人脸
            
        Returns:
            Tuple[float, float]: (x方向误差, y方向误差)
        """
        x_error = target.center_x - self.center_x
        y_error = target.center_y - self.center_y
        return x_error, y_error
    
    def get_distance_estimate(self, face: FaceData) -> float:
        """
        根据人脸面积估算距离
        
        假设：标准人脸在1米距离时面积约为10000像素（640x480分辨率）
        
        Args:
            face: 人脸数据
            
        Returns:
            float: 估算距离（米）
        """
        # 简单的反比关系
        reference_area = 10000  # 1米距离时的参考面积
        distance = np.sqrt(reference_area / face.area) if face.area > 0 else 3.0
        return min(distance, 5.0)  # 最大5米
    
    def draw_results(self, frame: np.ndarray, 
                    target: Optional[FaceData],
                    all_faces: List[FaceData],
                    draw_all: bool = True) -> np.ndarray:
        """
        在图像上绘制追踪结果
        
        Args:
            frame: OpenCV图像
            target: 目标人脸
            all_faces: 所有人脸
            draw_all: 是否绘制所有人脸
            
        Returns:
            np.ndarray: 绘制后的图像
        """
        h, w = frame.shape[:2]
        
        # 绘制中心十字准星
        cv2.line(frame, (self.center_x - 20, self.center_y),
                (self.center_x + 20, self.center_y), (255, 255, 255), 1)
        cv2.line(frame, (self.center_x, self.center_y - 20),
                (self.center_x, self.center_y + 20), (255, 255, 255), 1)
        
        # 绘制所有人脸（半透明）
        if draw_all:
            for i, face in enumerate(all_faces):
                if face != target:  # 非目标用灰色
                    cv2.rectangle(frame, (face.x, face.y), 
                                (face.x + face.width, face.y + face.height),
                                (128, 128, 128), 1)
                    cv2.putText(frame, f"Face {i+1}", (face.x, face.y - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)
        
        # 绘制目标人脸（绿色高亮）
        if target:
            cv2.rectangle(frame, (target.x, target.y),
                         (target.x + target.width, target.y + target.height),
                         (0, 255, 0), 3)
            cv2.circle(frame, (target.center_x, target.center_y), 5, (0, 255, 0), -1)
            
            # 绘制信息
            distance = self.get_distance_estimate(target)
            info_text = f"TARGET | Area: {target.area} | Dist: {distance:.2f}m"
            cv2.putText(frame, info_text, (target.x, target.y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 绘制到中心的连线
            cv2.line(frame, (self.center_x, self.center_y),
                    (target.center_x, target.center_y), (0, 255, 0), 1)
        
        # 显示检测到的人脸数量
        count_text = f"Faces: {len(all_faces)}"
        cv2.putText(frame, count_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame


# 测试代码
if __name__ == "__main__":
    print("👤 测试人脸追踪器...")
    
    tracker = FaceTracker(frame_width=640, frame_height=480,
                         area_weight=0.7, center_weight=0.3)
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("按 'q' 退出，按 'w' 切换权重显示")
    show_weights = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 翻转图像（镜像效果）
        frame = cv2.flip(frame, 1)
        
        # 追踪人脸
        target, all_faces = tracker.track(frame)
        
        # 绘制结果
        frame = tracker.draw_results(frame, target, all_faces)
        
        # 显示权重信息
        if show_weights and all_faces:
            y_offset = 60
            cv2.putText(frame, "Weight Scores:", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            max_area = max(f.area for f in all_faces)
            max_distance = np.sqrt(tracker.center_x**2 + tracker.center_y**2)
            
            for i, face in enumerate(all_faces):
                y_offset += 20
                area_score = face.area / max_area if max_area > 0 else 0
                distance_to_center = np.sqrt(
                    (face.center_x - tracker.center_x)**2 + 
                    (face.center_y - tracker.center_y)**2
                )
                center_score = 1 - (distance_to_center / max_distance)
                total_score = (tracker.area_weight * area_score + 
                              tracker.center_weight * center_score)
                
                is_target = "*" if face == target else " "
                text = f"{is_target}Face {i+1}: {total_score:.2f} (area:{area_score:.2f}, center:{center_score:.2f})"
                color = (0, 255, 0) if face == target else (200, 200, 200)
                cv2.putText(frame, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # 显示结果
        cv2.imshow('Face Tracker', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('w'):
            show_weights = not show_weights
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n测试完成")

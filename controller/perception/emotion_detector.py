"""
emotion_detector.py - 情绪识别模块

使用DeepFace进行多维度人脸分析：
- 7类情绪识别（愤怒、厌恶、恐惧、快乐、悲伤、惊讶、中性）
- 年龄估计
- 性别识别
- 种族识别（可选）

作者: Digital Bloom Team
版本: 1.0.0
"""

import cv2
import numpy as np
from deepface import DeepFace
from collections import deque
import time


class EmotionDetector:
    """
    DeepFace情绪检测器
    
    提供平滑的情绪检测结果，避免帧间抖动
    """
    
    def __init__(self, smoothing_frames=5):
        """
        初始化情绪检测器
        
        Args:
            smoothing_frames: 平滑窗口大小（越大越平滑但延迟越高）
        """
        self.smoothing_frames = smoothing_frames
        self.emotion_history = deque(maxlen=smoothing_frames)
        self.age_history = deque(maxlen=smoothing_frames)
        self.gender_history = deque(maxlen=smoothing_frames)
        
        # 情绪到数值的映射（用于排序和可视化）
        self.emotion_order = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        
        # 情绪到颜色的映射（用于可视化）
        self.emotion_colors = {
            'angry': (0, 0, 255),      # 红色
            'disgust': (0, 140, 255),  # 橙色
            'fear': (0, 255, 255),     # 黄色
            'happy': (0, 255, 0),      # 绿色
            'sad': (255, 0, 0),        # 蓝色
            'surprise': (255, 0, 255), # 紫色
            'neutral': (128, 128, 128) # 灰色
        }
        
        self.last_detection_time = 0
        self.detection_interval = 0.2  # 每200ms检测一次（避免过度计算）
        
    def analyze(self, frame):
        """
        分析视频帧中的人脸
        
        Args:
            frame: OpenCV BGR图像
            
        Returns:
            dict: 包含情绪、年龄、性别的分析结果，如果未检测到人脸返回None
        """
        current_time = time.time()
        
        # 限制检测频率
        if current_time - self.last_detection_time < self.detection_interval:
            return self._get_smoothed_result()
        
        try:
            # DeepFace分析
            result = DeepFace.analyze(
                frame,
                actions=['emotion', 'age', 'gender'],
                enforce_detection=False,  # 不强制要求检测到人脸
                silent=True  # 减少控制台输出
            )
            
            self.last_detection_time = current_time
            
            # DeepFace返回的是列表（可能有多个人脸）
            if isinstance(result, list) and len(result) > 0:
                # 取最大的人脸（通常是主要人物）
                result = max(result, key=lambda x: x['face_confidence'])
            elif not isinstance(result, dict):
                return None
            
            # 提取数据
            emotions = result.get('emotion', {})
            age = result.get('age', 0)
            gender = result.get('gender', {})
            region = result.get('region', {})
            
            # 标准化情绪分数（确保总和为1）
            total = sum(emotions.values())
            if total > 0:
                emotions = {k: v/total for k, v in emotions.items()}
            
            # 添加到历史记录
            self.emotion_history.append(emotions)
            self.age_history.append(age)
            
            # 处理性别（DeepFace返回的是字典或字符串）
            if isinstance(gender, dict):
                dominant_gender = max(gender, key=gender.get)
                gender_score = 1 if dominant_gender == 'Man' else 0
            else:
                gender_score = 1 if gender == 'Man' else 0
            self.gender_history.append(gender_score)
            
            return self._get_smoothed_result(region)
            
        except Exception as e:
            # 静默处理错误（避免频繁输出错误信息）
            return None
    
    def _get_smoothed_result(self, region=None):
        """
        获取平滑后的检测结果
        """
        if len(self.emotion_history) == 0:
            return None
        
        # 平均情绪分数
        avg_emotions = {}
        for emotion in self.emotion_order:
            scores = [h.get(emotion, 0) for h in self.emotion_history]
            avg_emotions[emotion] = np.mean(scores)
        
        # 找出主导情绪
        dominant_emotion = max(avg_emotions, key=avg_emotions.get)
        
        # 平均年龄
        avg_age = int(np.mean(self.age_history))
        
        # 性别（多数投票）
        gender_score = np.mean(self.gender_history)
        gender = 'Male' if gender_score > 0.5 else 'Female'
        
        # 计算情绪熵（混乱程度）
        entropy = self._calculate_emotion_entropy(avg_emotions)
        
        return {
            'emotions': avg_emotions,
            'dominant_emotion': dominant_emotion,
            'emotion_vector': [avg_emotions[e] for e in self.emotion_order],
            'age': avg_age,
            'gender': gender,
            'gender_score': gender_score,
            'region': region,
            'entropy': entropy,
            'timestamp': time.time()
        }
    
    def _calculate_emotion_entropy(self, emotions):
        """
        计算情绪分布的熵值（衡量情绪"混乱程度"）
        高熵 = 混合情绪，低熵 = 明确情绪
        """
        import math
        entropy = 0
        for score in emotions.values():
            if score > 0:
                entropy -= score * math.log2(score)
        return entropy
    
    def draw_results(self, frame, result, draw_face_box=True):
        """
        在图像上绘制检测结果
        
        Args:
            frame: OpenCV图像
            result: analyze()的返回结果
            draw_face_box: 是否绘制人脸框
            
        Returns:
            绘制后的图像
        """
        if result is None:
            return frame
        
        h, w = frame.shape[:2]
        
        # 绘制人脸框
        if draw_face_box and result.get('region'):
            region = result['region']
            x, y, w_face, h_face = region.get('x', 0), region.get('y', 0), region.get('w', 0), region.get('h', 0)
            
            color = self.emotion_colors.get(result['dominant_emotion'], (255, 255, 255))
            cv2.rectangle(frame, (x, y), (x + w_face, y + h_face), color, 2)
            
            # 绘制情绪标签
            label = f"{result['dominant_emotion'].upper()}"
            cv2.putText(frame, label, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # 绘制情绪条形图
        emotions = result['emotions']
        bar_x, bar_y = 10, h - 150
        bar_width = 30
        bar_height_max = 100
        
        for i, emotion in enumerate(self.emotion_order):
            score = emotions.get(emotion, 0)
            bar_h = int(score * bar_height_max)
            color = self.emotion_colors[emotion]
            
            # 绘制条形
            cv2.rectangle(frame, 
                         (bar_x + i * (bar_width + 5), bar_y + bar_height_max - bar_h),
                         (bar_x + i * (bar_width + 5) + bar_width, bar_y + bar_height_max),
                         color, -1)
            
            # 绘制标签（首字母）
            cv2.putText(frame, emotion[0].upper(), 
                       (bar_x + i * (bar_width + 5) + 8, bar_y + bar_height_max + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # 绘制年龄和性别
        info_text = f"Age: {result['age']} | Gender: {result['gender']}"
        cv2.putText(frame, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def get_feature_vector(self, result):
        """
        获取11维特征向量用于ML输入
        
        Returns:
            list: [anger, disgust, fear, happy, sad, surprise, neutral, age, gender, 0, 0]
                  最后两个是预留位（姿态开放度和距离）
        """
        if result is None:
            return [0] * 11
        
        vector = []
        # 7类情绪
        for emotion in self.emotion_order:
            vector.append(result['emotions'].get(emotion, 0))
        
        # 年龄（归一化到0-1）
        vector.append(min(result['age'] / 100.0, 1.0))
        
        # 性别（0=Female, 1=Male）
        vector.append(result.get('gender_score', 0.5))
        
        # 预留位（将由姿态和距离填充）
        vector.append(0)  # posture_openness
        vector.append(0)  # distance
        
        return vector
    
    def reset(self):
        """
        重置检测器状态
        """
        self.emotion_history.clear()
        self.age_history.clear()
        self.gender_history.clear()


# 测试代码
if __name__ == "__main__":
    print("🎭 测试情绪检测器...")
    
    detector = EmotionDetector(smoothing_frames=3)
    cap = cv2.VideoCapture(0)
    
    print("按 'q' 退出")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 分析帧
        result = detector.analyze(frame)
        
        # 绘制结果
        frame = detector.draw_results(frame, result)
        
        # 显示特征向量
        if result:
            feature_vector = detector.get_feature_vector(result)
            print(f"\r特征向量: {[f'{v:.2f}' for v in feature_vector[:7]]} | "
                  f"主导情绪: {result['dominant_emotion']} | "
                  f"年龄: {result['age']} | "
                  f"性别: {result['gender']}", end='')
        
        cv2.imshow('Emotion Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n测试完成")

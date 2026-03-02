"""
persona_classifier.py - 性格分类器

使用机器学习将多维感知数据映射到性格标签。
这是三层仿生系统的第一层：ML Brain

性格标签定义：
- DEFENSIVE: 防御性（红色，紧张，闭合）
- PREDATORY: 捕食性（橙色，警觉，半开）
- EMPATHY: 共情（粉色，温柔，完全开放）
- JOYFUL: 快乐（黄色，活泼，摇摆）
- JEALOUS: 嫉妒（紫色，抖动，不安）
- SLEEPY: 困倦（蓝色，静止，闭合）
- STARTLED: 惊吓（白色，快速抖动，瞬间闭合）
- BOREDOM: 无聊（灰色，缓慢，半开）

作者: Digital Bloom Team
版本: 1.0.0
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from collections import deque
import time


class PersonaClassifier:
    """
    性格分类器
    
    将感知特征向量映射到性格标签
    """
    
    # 性格标签定义
    PERSONA_LABELS = [
        'DEFENSIVE',    # 防御
        'PREDATORY',    # 捕食
        'EMPATHY',      # 共情
        'JOYFUL',       # 快乐
        'JEALOUS',      # 嫉妒
        'SLEEPY',       # 困倦
        'STARTLED',     # 惊吓
        'BOREDOM'       # 无聊
    ]
    
    # 性格到运动参数的映射
    PERSONA_PARAMS = {
        'DEFENSIVE': {'bloom': 0.1, 'jitter': 0.8, 'speed': 0.9, 'r': 255, 'g': 0, 'b': 0, 'lcd': 'Defensive!'},
        'PREDATORY': {'bloom': 0.3, 'jitter': 0.5, 'speed': 0.7, 'r': 255, 'g': 140, 'b': 0, 'lcd': 'Predatory...'},
        'EMPATHY': {'bloom': 0.9, 'jitter': 0.1, 'speed': 0.2, 'r': 255, 'g': 105, 'b': 180, 'lcd': 'Empathy~'},
        'JOYFUL': {'bloom': 1.0, 'jitter': 0.6, 'speed': 0.8, 'r': 255, 'g': 255, 'b': 0, 'lcd': 'Joyful! :D'},
        'JEALOUS': {'bloom': 0.5, 'jitter': 1.0, 'speed': 1.0, 'r': 128, 'g': 0, 'b': 128, 'lcd': 'Jealous! >:('},
        'SLEEPY': {'bloom': 0.2, 'jitter': 0.0, 'speed': 0.1, 'r': 0, 'g': 0, 'b': 255, 'lcd': 'zZZ... (-_-)'},
        'STARTLED': {'bloom': 0.0, 'jitter': 1.0, 'speed': 1.0, 'r': 255, 'g': 255, 'b': 255, 'lcd': '!!! O_O'},
        'BOREDOM': {'bloom': 0.4, 'jitter': 0.2, 'speed': 0.3, 'r': 128, 'g': 128, 'b': 128, 'lcd': 'Boring...'}
    }
    
    def __init__(self, model_type='random_forest', model_path=None):
        """
        初始化分类器
        
        Args:
            model_type: 'random_forest' 或 'svm'
            model_path: 预训练模型路径（如果存在）
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = model_path
        
        # 平滑处理
        self.label_history = deque(maxlen=5)
        self.last_switch_time = 0
        self.min_switch_interval = 1.0  # 最小切换间隔（秒）
        
        # 加载或初始化模型
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._init_model()
    
    def _init_model(self):
        """初始化新模型"""
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        elif self.model_type == 'svm':
            self.model = SVC(
                kernel='rbf',
                probability=True,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        print(f"Initialized {self.model_type} model")
    
    def train(self, X, y):
        """
        训练模型
        
        Args:
            X: 特征矩阵 (n_samples, n_features)
            y: 标签列表 (n_samples,)
        """
        # 数据标准化
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练模型
        self.model.fit(X_scaled, y)
        
        # 评估
        if len(X) > 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            self.model.fit(X_train, y_train)
            accuracy = self.model.score(X_test, y_test)
            print(f"Model trained. Test accuracy: {accuracy:.2%}")
        else:
            print(f"Model trained on {len(X)} samples (too few for validation)")
    
    def predict(self, feature_vector, smoothing=True):
        """
        预测性格标签
        
        Args:
            feature_vector: 11维特征向量
            smoothing: 是否启用标签平滑
            
        Returns:
            dict: 包含标签、置信度、运动参数
        """
        if self.model is None:
            return self._default_prediction()
        
        # 标准化
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # 预测
        label = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        confidence = max(probabilities)
        
        # 平滑处理
        if smoothing:
            label = self._smooth_label(label)
        
        # 获取运动参数
        params = self.PERSONA_PARAMS.get(label, self.PERSONA_PARAMS['BOREDOM'])
        
        return {
            'label': label,
            'confidence': confidence,
            'probabilities': dict(zip(self.model.classes_, probabilities)),
            'params': params,
            'timestamp': time.time()
        }
    
    def _smooth_label(self, new_label):
        """
        平滑标签切换，避免快速抖动
        """
        current_time = time.time()
        
        # 添加到历史
        self.label_history.append(new_label)
        
        # 检查是否需要强制切换
        if current_time - self.last_switch_time < self.min_switch_interval:
            # 如果在最小间隔内，返回之前的标签
            if len(self.label_history) > 1:
                return list(self.label_history)[-2]
        
        # 多数投票
        if len(self.label_history) >= 3:
            from collections import Counter
            votes = Counter(self.label_history)
            majority_label, count = votes.most_common(1)[0]
            
            if count >= 3:  # 至少有3帧一致
                if majority_label != new_label:
                    self.last_switch_time = current_time
                return majority_label
        
        return new_label
    
    def _default_prediction(self):
        """默认预测（未训练时）"""
        return {
            'label': 'BOREDOM',
            'confidence': 0.0,
            'probabilities': {},
            'params': self.PERSONA_PARAMS['BOREDOM'],
            'timestamp': time.time()
        }
    
    def save_model(self, path):
        """保存模型"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'labels': self.PERSONA_LABELS
        }
        joblib.dump(model_data, path)
        print(f"Model saved to {path}")
    
    def load_model(self, path):
        """加载模型"""
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.model_type = model_data['model_type']
        print(f"Model loaded from {path}")
    
    def get_label_description(self, label):
        """获取标签描述"""
        descriptions = {
            'DEFENSIVE': '防御状态 - 感到威胁，紧张闭合',
            'PREDATORY': '捕食状态 - 警觉专注，准备行动',
            'EMPATHY': '共情状态 - 温柔开放，积极倾听',
            'JOYFUL': '快乐状态 - 活泼兴奋，愉快互动',
            'JEALOUS': '嫉妒状态 - 不安抖动，渴望关注',
            'SLEEPY': '困倦状态 - 缓慢静止，休息中',
            'STARTLED': '惊吓状态 - 突然反应，瞬间闭合',
            'BOREDOM': '无聊状态 - 缺乏兴趣，缓慢运动'
        }
        return descriptions.get(label, '未知状态')
    
    def generate_training_data_template(self):
        """
        生成训练数据模板
        
        返回DataFrame模板，用于录制训练数据
        """
        columns = [
            'anger', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral',
            'age', 'gender', 'posture_openness', 'distance', 'label'
        ]
        
        # 添加一些启发式规则生成的样本
        data = []
        
        # 快乐情绪 → JOYFUL
        data.append([0.0, 0.0, 0.0, 0.9, 0.0, 0.1, 0.0, 30, 0.5, 0.8, 1.0, 'JOYFUL'])
        data.append([0.1, 0.0, 0.0, 0.8, 0.0, 0.1, 0.0, 25, 0.0, 0.7, 1.2, 'JOYFUL'])
        
        # 悲伤情绪 → EMPATHY
        data.append([0.0, 0.0, 0.1, 0.0, 0.8, 0.0, 0.1, 40, 0.5, 0.5, 0.8, 'EMPATHY'])
        data.append([0.0, 0.0, 0.0, 0.1, 0.7, 0.0, 0.2, 35, 1.0, 0.4, 0.9, 'EMPATHY'])
        
        # 愤怒情绪 → DEFENSIVE
        data.append([0.8, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 35, 0.5, 0.3, 0.5, 'DEFENSIVE'])
        data.append([0.7, 0.2, 0.0, 0.0, 0.1, 0.0, 0.0, 40, 1.0, 0.2, 0.4, 'DEFENSIVE'])
        
        # 恐惧情绪 → STARTLED
        data.append([0.1, 0.0, 0.8, 0.0, 0.0, 0.1, 0.0, 25, 0.0, 0.2, 0.3, 'STARTLED'])
        data.append([0.0, 0.0, 0.9, 0.0, 0.0, 0.1, 0.0, 30, 0.5, 0.1, 0.5, 'STARTLED'])
        
        # 惊讶情绪 → STARTLED
        data.append([0.0, 0.0, 0.1, 0.0, 0.0, 0.9, 0.0, 28, 0.5, 0.9, 1.0, 'STARTLED'])
        
        # 中性情绪 → BOREDOM 或 SLEEPY
        data.append([0.1, 0.0, 0.0, 0.1, 0.1, 0.0, 0.7, 50, 0.5, 0.3, 1.5, 'BOREDOM'])
        data.append([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 60, 0.5, 0.1, 2.0, 'SLEEPY'])
        
        df = pd.DataFrame(data, columns=columns)
        return df


# 测试代码
if __name__ == "__main__":
    print("🧠 测试性格分类器...")
    
    classifier = PersonaClassifier(model_type='random_forest')
    
    # 生成并训练初始模型
    print("\n生成启发式训练数据...")
    training_data = classifier.generate_training_data_template()
    print(training_data)
    
    print("\n训练模型...")
    X = training_data.drop('label', axis=1).values
    y = training_data['label'].values
    classifier.train(X, y)
    
    # 测试预测
    print("\n测试预测...")
    test_cases = [
        # 快乐的人，开放姿态
        [0.0, 0.0, 0.0, 0.9, 0.0, 0.0, 0.1, 30, 0.5, 0.8, 1.0],
        # 悲伤的人，闭合姿态
        [0.0, 0.0, 0.1, 0.0, 0.8, 0.0, 0.1, 40, 0.5, 0.3, 0.8],
        # 愤怒的人，防御姿态
        [0.8, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 35, 0.5, 0.2, 0.5],
    ]
    
    for i, features in enumerate(test_cases):
        result = classifier.predict(features, smoothing=False)
        print(f"\n测试用例 {i+1}:")
        print(f"  预测标签: {result['label']}")
        print(f"  置信度: {result['confidence']:.2%}")
        print(f"  运动参数: bloom={result['params']['bloom']}, "
              f"jitter={result['params']['jitter']}, "
              f"speed={result['params']['speed']}")
    
    # 保存模型
    print("\n保存模型...")
    classifier.save_model('test_model.pkl')
    
    print("\n测试完成！")

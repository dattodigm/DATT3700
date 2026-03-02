"""
control_panel.py - Digital Bloom主控制面板

使用Tkinter构建的非程序员友好界面：
- 实时摄像头预览
- 感知数据可视化
- 手动控制滑块
- 训练数据录制
- 花朵状态监控

作者: Digital Bloom Team
版本: 1.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import cv2
from PIL import Image, ImageTk
import numpy as np
import threading
import time
import json
import os
from datetime import datetime

# 导入自定义模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from perception.emotion_detector import EmotionDetector
from perception.pose_tracker import PoseTracker
from decision.persona_classifier import PersonaClassifier
from communication.flower_client import FlowerOrchestrator


class DigitalBloomControlPanel:
    """
    Digital Bloom主控制面板
    """
    
    def __init__(self, root):
        """初始化控制面板"""
        self.root = root
        self.root.title("🌸 Digital Bloom - 具身AI花朵控制面板")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        # 初始化组件
        self.emotion_detector = None
        self.pose_tracker = None
        self.classifier = None
        self.orchestrator = None
        self.cap = None
        
        # 状态变量
        self.is_running = False
        self.is_recording = False
        self.training_data = []
        self.current_feature_vector = [0] * 11
        self.current_persona = 'BOREDOM'
        
        # 花朵配置
        self.flowers_config = [
            {'id': 'flower1', 'name': 'Sylvie (DC)', 'ip': '192.168.4.1', 'port': 8888},
            {'id': 'flower2', 'name': 'Sue (Servo)', 'ip': '192.168.4.2', 'port': 8888},
        ]
        
        # 创建UI
        self._create_styles()
        self._create_ui()
        
        # 启动后自动初始化
        self.root.after(1000, self._auto_initialize)
    
    def _create_styles(self):
        """创建自定义样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 定义颜色
        self.bg_color = '#2b2b2b'
        self.fg_color = '#ffffff'
        self.accent_color = '#ff6b6b'
        self.success_color = '#51cf66'
        self.warning_color = '#ffd93d'
        
        # 配置样式
        self.style.configure('Dark.TFrame', background=self.bg_color)
        self.style.configure('Dark.TLabel', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('Accent.TButton', background=self.accent_color, foreground='white')
        self.style.configure('Success.TButton', background=self.success_color, foreground='white')
        self.style.configure('Title.TLabel', background=self.bg_color, foreground=self.fg_color, 
                           font=('Helvetica', 16, 'bold'))
        
    def _create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部标题栏
        self._create_header(main_container)
        
        # 主体内容（左右分栏）
        content_frame = ttk.Frame(main_container, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 左侧面板（预览+感知数据）
        left_panel = ttk.Frame(content_frame, style='Dark.TFrame')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._create_left_panel(left_panel)
        
        # 右侧面板（控制+录制）
        right_panel = ttk.Frame(content_frame, style='Dark.TFrame', width=450)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel.pack_propagate(False)
        self._create_right_panel(right_panel)
        
        # 底部状态栏
        self._create_status_bar(main_container)
    
    def _create_header(self, parent):
        """创建顶部标题栏"""
        header = ttk.Frame(parent, style='Dark.TFrame')
        header.pack(fill=tk.X, pady=(0, 10))
        
        title = ttk.Label(header, text="🌸 Digital Bloom 控制面板", 
                         style='Title.TLabel')
        title.pack(side=tk.LEFT)
        
        # 连接按钮
        self.connect_btn = tk.Button(header, text="🔗 连接系统", 
                                    bg=self.success_color, fg='white',
                                    font=('Helvetica', 10, 'bold'),
                                    command=self._toggle_connection,
                                    relief=tk.FLAT, padx=20, pady=5)
        self.connect_btn.pack(side=tk.RIGHT)
        
        # 紧急停止按钮
        self.stop_btn = tk.Button(header, text="🛑 紧急停止", 
                                 bg=self.accent_color, fg='white',
                                 font=('Helvetica', 10, 'bold'),
                                 command=self._emergency_stop,
                                 relief=tk.FLAT, padx=20, pady=5, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=10)
    
    def _create_left_panel(self, parent):
        """创建左侧面板"""
        # 摄像头预览
        preview_frame = tk.LabelFrame(parent, text="📹 实时预览", 
                                     bg=self.bg_color, fg=self.fg_color,
                                     font=('Helvetica', 11, 'bold'))
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_label = tk.Label(preview_frame, bg='black')
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 感知数据显示
        perception_frame = tk.LabelFrame(parent, text="📊 感知数据", 
                                        bg=self.bg_color, fg=self.fg_color,
                                        font=('Helvetica', 11, 'bold'))
        perception_frame.pack(fill=tk.X)
        
        # 情绪条形图
        emotion_frame = ttk.Frame(perception_frame, style='Dark.TFrame')
        emotion_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(emotion_frame, text="情绪分析:", style='Dark.TLabel').pack(anchor=tk.W)
        
        self.emotion_bars = {}
        emotions = ['愤怒', '厌恶', '恐惧', '快乐', '悲伤', '惊讶', '中性']
        emotion_keys = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        
        for emotion, key in zip(emotions, emotion_keys):
            row = ttk.Frame(emotion_frame, style='Dark.TFrame')
            row.pack(fill=tk.X, pady=2)
            
            ttk.Label(row, text=f"{emotion}:", style='Dark.TLabel', width=8).pack(side=tk.LEFT)
            
            bar_container = tk.Frame(row, bg='#404040', width=200, height=15)
            bar_container.pack(side=tk.LEFT, padx=5)
            bar_container.pack_propagate(False)
            
            bar = tk.Frame(bar_container, bg='#666666', width=0, height=15)
            bar.place(x=0, y=0)
            
            value_label = ttk.Label(row, text="0%", style='Dark.TLabel', width=5)
            value_label.pack(side=tk.LEFT)
            
            self.emotion_bars[key] = {'bar': bar, 'label': value_label}
        
        # 其他感知数据
        info_frame = ttk.Frame(perception_frame, style='Dark.TFrame')
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.age_label = ttk.Label(info_frame, text="年龄: --", style='Dark.TLabel')
        self.age_label.pack(side=tk.LEFT, padx=10)
        
        self.gender_label = ttk.Label(info_frame, text="性别: --", style='Dark.TLabel')
        self.gender_label.pack(side=tk.LEFT, padx=10)
        
        self.openness_label = ttk.Label(info_frame, text="开放度: --", style='Dark.TLabel')
        self.openness_label.pack(side=tk.LEFT, padx=10)
        
        self.pose_label = ttk.Label(info_frame, text="姿态: --", style='Dark.TLabel')
        self.pose_label.pack(side=tk.LEFT, padx=10)
    
    def _create_right_panel(self, parent):
        """创建右侧面板"""
        # ML预测结果
        ml_frame = tk.LabelFrame(parent, text="🧠 AI性格识别", 
                                bg=self.bg_color, fg=self.fg_color,
                                font=('Helvetica', 11, 'bold'))
        ml_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.persona_label = tk.Label(ml_frame, text="当前状态: --", 
                                     bg=self.bg_color, fg=self.fg_color,
                                     font=('Helvetica', 14, 'bold'))
        self.persona_label.pack(pady=10)
        
        self.confidence_label = ttk.Label(ml_frame, text="置信度: --", style='Dark.TLabel')
        self.confidence_label.pack()
        
        # 手动控制（滑块）
        control_frame = tk.LabelFrame(parent, text="🎚️ 手动控制 (录制模式)", 
                                     bg=self.bg_color, fg=self.fg_color,
                                     font=('Helvetica', 11, 'bold'))
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 滑块控制
        self.sliders = {}
        
        # 花朵开放度
        self._create_slider(control_frame, "开放度 (Bloom)", "bloom", 0, 100, 50)
        
        # 颤动强度
        self._create_slider(control_frame, "颤动 (Jitter)", "jitter", 0, 100, 0)
        
        # 运动速度
        self._create_slider(control_frame, "速度 (Speed)", "speed", 0, 100, 50)
        
        # 颜色控制
        color_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(color_frame, text="颜色:", style='Dark.TLabel').pack(side=tk.LEFT)
        
        self.color_canvas = tk.Canvas(color_frame, width=50, height=20, bg='#808080')
        self.color_canvas.pack(side=tk.LEFT, padx=5)
        
        self.color_sliders = {}
        for color, default in [('R', 128), ('G', 128), ('B', 128)]:
            slider = tk.Scale(control_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                            label=color, bg=self.bg_color, fg=self.fg_color,
                            highlightthickness=0, command=self._on_color_change)
            slider.set(default)
            slider.pack(fill=tk.X, padx=10, pady=2)
            self.color_sliders[color] = slider
        
        # LCD消息
        lcd_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        lcd_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(lcd_frame, text="LCD显示:", style='Dark.TLabel').pack(side=tk.LEFT)
        
        self.lcd_entry = tk.Entry(lcd_frame, bg='#404040', fg='white', 
                                 insertbackground='white')
        self.lcd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.lcd_entry.insert(0, "Hello!")
        
        # 花朵选择
        flower_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        flower_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(flower_frame, text="目标花朵:", style='Dark.TLabel').pack(side=tk.LEFT)
        
        self.flower_var = tk.StringVar(value="all")
        self.flower_combo = ttk.Combobox(flower_frame, textvariable=self.flower_var,
                                        values=["all", "flower1", "flower2"], 
                                        state="readonly", width=15)
        self.flower_combo.pack(side=tk.LEFT, padx=5)
        
        # 应用按钮
        self.apply_btn = tk.Button(control_frame, text="✓ 应用到花朵", 
                                  bg=self.success_color, fg='white',
                                  command=self._apply_manual_control,
                                  relief=tk.FLAT, padx=20, pady=5)
        self.apply_btn.pack(pady=10)
        
        # 训练数据录制
        record_frame = tk.LabelFrame(parent, text="📝 训练数据录制", 
                                    bg=self.bg_color, fg=self.fg_color,
                                    font=('Helvetica', 11, 'bold'))
        record_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 性格标签选择
        label_frame = ttk.Frame(record_frame, style='Dark.TFrame')
        label_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(label_frame, text="性格标签:", style='Dark.TLabel').pack(side=tk.LEFT)
        
        self.label_var = tk.StringVar(value="JOYFUL")
        self.label_combo = ttk.Combobox(label_frame, textvariable=self.label_var,
                                       values=PersonaClassifier.PERSONA_LABELS,
                                       state="readonly", width=15)
        self.label_combo.pack(side=tk.LEFT, padx=5)
        
        # 录制按钮
        self.record_btn = tk.Button(record_frame, text="🔴 开始录制", 
                                   bg=self.accent_color, fg='white',
                                   command=self._toggle_recording,
                                   relief=tk.FLAT, padx=20, pady=5)
        self.record_btn.pack(pady=10)
        
        # 已录制数量
        self.record_count_label = ttk.Label(record_frame, text="已录制: 0 条数据", 
                                           style='Dark.TLabel')
        self.record_count_label.pack()
        
        # 保存按钮
        self.save_btn = tk.Button(record_frame, text="💾 保存训练数据", 
                                 bg=self.success_color, fg='white',
                                 command=self._save_training_data,
                                 relief=tk.FLAT, padx=20, pady=5)
        self.save_btn.pack(pady=5)
        
        # 花朵状态
        status_frame = tk.LabelFrame(parent, text="🌸 花朵状态", 
                                    bg=self.bg_color, fg=self.fg_color,
                                    font=('Helvetica', 11, 'bold'))
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, bg='#404040', 
                                                    fg='white', height=10)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._update_status_text("系统未连接\n")
    
    def _create_slider(self, parent, label, key, from_, to, default):
        """创建滑块控件"""
        frame = ttk.Frame(parent, style='Dark.TFrame')
        frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(frame, text=label, style='Dark.TLabel', width=12).pack(side=tk.LEFT)
        
        slider = tk.Scale(frame, from_=from_, to=to, orient=tk.HORIZONTAL,
                         bg=self.bg_color, fg=self.fg_color,
                         highlightthickness=0, length=200)
        slider.set(default)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.sliders[key] = slider
    
    def _create_status_bar(self, parent):
        """创建底部状态栏"""
        status_frame = ttk.Frame(parent, style='Dark.TFrame')
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪", style='Dark.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self.fps_label = ttk.Label(status_frame, text="FPS: --", style='Dark.TLabel')
        self.fps_label.pack(side=tk.RIGHT)
    
    def _auto_initialize(self):
        """自动初始化系统"""
        try:
            self._update_status("正在初始化...")
            
            # 初始化感知组件
            self.emotion_detector = EmotionDetector(smoothing_frames=3)
            self.pose_tracker = PoseTracker(smoothing_frames=3)
            
            # 初始化ML分类器
            self.classifier = PersonaClassifier(model_type='random_forest')
            
            # 初始化花朵编排器
            self.orchestrator = FlowerOrchestrator()
            for config in self.flowers_config:
                self.orchestrator.add_flower(**config)
            
            # 初始化摄像头
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("无法打开摄像头")
            
            self._update_status("系统初始化完成！")
            messagebox.showinfo("成功", "系统初始化完成！")
            
        except Exception as e:
            self._update_status(f"初始化失败: {str(e)}")
            messagebox.showerror("错误", f"初始化失败:\n{str(e)}")
    
    def _toggle_connection(self):
        """切换系统连接状态"""
        if not self.is_running:
            self.is_running = True
            self.connect_btn.config(text="⏹ 断开连接", bg=self.accent_color)
            self.stop_btn.config(state=tk.NORMAL)
            self._update_status("系统运行中")
            self._start_video_loop()
        else:
            self.is_running = False
            self.connect_btn.config(text="🔗 连接系统", bg=self.success_color)
            self.stop_btn.config(state=tk.DISABLED)
            self._update_status("系统已停止")
    
    def _start_video_loop(self):
        """启动视频循环"""
        if not self.is_running:
            return
        
        try:
            ret, frame = self.cap.read()
            if ret:
                # 翻转图像（镜像效果）
                frame = cv2.flip(frame, 1)
                
                # 分析情绪
                emotion_result = self.emotion_detector.analyze(frame)
                if emotion_result:
                    frame = self.emotion_detector.draw_results(frame, emotion_result)
                    self._update_emotion_display(emotion_result)
                
                # 分析姿态
                pose_result = self.pose_tracker.analyze(frame)
                if pose_result:
                    frame = self.pose_tracker.draw_results(frame, pose_result)
                    self._update_pose_display(pose_result)
                
                # 组合特征向量
                if emotion_result and pose_result:
                    feature_vector = self.emotion_detector.get_feature_vector(emotion_result)
                    feature_vector[9] = pose_result['openness']  # 姿态开放度
                    feature_vector[10] = 1.0  # 距离（预留）
                    
                    self.current_feature_vector = feature_vector
                    
                    # ML预测
                    persona_result = self.classifier.predict(feature_vector, smoothing=True)
                    self._update_persona_display(persona_result)
                    
                    # 如果不是录制模式，自动发送给花朵
                    if not self.is_recording:
                        self._send_to_flowers(persona_result['params'])
                
                # 显示预览
                self._update_preview(frame)
            
        except Exception as e:
            print(f"视频循环错误: {e}")
        
        # 继续循环
        self.root.after(33, self._start_video_loop)  # ~30 FPS
    
    def _update_preview(self, frame):
        """更新预览画面"""
        # 调整大小
        frame = cv2.resize(frame, (640, 480))
        
        # 转换颜色空间
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 转换为PIL图像
        pil_image = Image.fromarray(rgb_frame)
        
        # 转换为Tkinter图像
        tk_image = ImageTk.PhotoImage(image=pil_image)
        
        # 更新标签
        self.preview_label.config(image=tk_image)
        self.preview_label.image = tk_image  # 保持引用
    
    def _update_emotion_display(self, result):
        """更新情绪显示"""
        emotions = result['emotions']
        
        for key, data in self.emotion_bars.items():
            score = emotions.get(key, 0)
            percentage = int(score * 100)
            
            # 更新条形
            data['bar'].config(width=int(percentage * 2))
            
            # 更新颜色
            if percentage > 50:
                data['bar'].config(bg=self.accent_color)
            else:
                data['bar'].config(bg='#666666')
            
            # 更新标签
            data['label'].config(text=f"{percentage}%")
        
        # 更新年龄和性别
        self.age_label.config(text=f"年龄: {result['age']}")
        self.gender_label.config(text=f"性别: {result['gender']}")
    
    def _update_pose_display(self, result):
        """更新姿态显示"""
        self.openness_label.config(text=f"开放度: {result['openness']:.2f}")
        
        # 姿态描述
        if result['openness'] > 0.7:
            pose_desc = "开放"
        elif result['openness'] > 0.4:
            pose_desc = "中性"
        else:
            pose_desc = "防御"
        
        self.pose_label.config(text=f"姿态: {pose_desc}")
    
    def _update_persona_display(self, result):
        """更新性格显示"""
        label = result['label']
        confidence = result['confidence']
        
        self.persona_label.config(text=f"当前状态: {label}")
        self.confidence_label.config(text=f"置信度: {confidence:.1%}")
        
        # 根据性格改变颜色
        color_map = {
            'DEFENSIVE': '#ff0000',
            'PREDATORY': '#ff8c00',
            'EMPATHY': '#ff69b4',
            'JOYFUL': '#ffff00',
            'JEALOUS': '#800080',
            'SLEEPY': '#0000ff',
            'STARTLED': '#ffffff',
            'BOREDOM': '#808080'
        }
        
        color = color_map.get(label, '#ffffff')
        self.persona_label.config(fg=color)
    
    def _on_color_change(self, event=None):
        """颜色滑块变化回调"""
        r = self.color_sliders['R'].get()
        g = self.color_sliders['G'].get()
        b = self.color_sliders['B'].get()
        
        color_hex = f'#{r:02x}{g:02x}{b:02x}'
        self.color_canvas.config(bg=color_hex)
    
    def _apply_manual_control(self):
        """应用手动控制"""
        params = {
            'bloom': self.sliders['bloom'].get() / 100.0,
            'jitter': self.sliders['jitter'].get() / 100.0,
            'speed': self.sliders['speed'].get() / 100.0,
            'r': self.color_sliders['R'].get(),
            'g': self.color_sliders['G'].get(),
            'b': self.color_sliders['B'].get(),
            'lcd': self.lcd_entry.get()
        }
        
        target = self.flower_var.get()
        
        if target == "all":
            self.orchestrator.broadcast_to_all(params)
            self._update_status_text(f"应用到所有花朵: {params}\n")
        else:
            self.orchestrator.update_flower_state(target, params)
            self._update_status_text(f"应用到 {target}: {params}\n")
    
    def _toggle_recording(self):
        """切换录制状态"""
        if not self.is_recording:
            self.is_recording = True
            self.record_btn.config(text="⏹ 停止录制", bg=self.accent_color)
            self._update_status("正在录制训练数据...")
        else:
            self.is_recording = False
            self.record_btn.config(text="🔴 开始录制", bg=self.accent_color)
            self._update_status(f"录制完成，共 {len(self.training_data)} 条数据")
            self.record_count_label.config(text=f"已录制: {len(self.training_data)} 条数据")
    
    def _save_training_data(self):
        """保存训练数据"""
        if not self.training_data:
            messagebox.showwarning("警告", "没有可保存的训练数据")
            return
        
        try:
            import pandas as pd
            
            # 创建DataFrame
            columns = ['anger', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral',
                      'age', 'gender', 'posture_openness', 'distance', 'label']
            df = pd.DataFrame(self.training_data, columns=columns)
            
            # 保存为CSV
            filename = f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            
            messagebox.showinfo("成功", f"训练数据已保存:\n{filename}\n共 {len(df)} 条记录")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{str(e)}")
    
    def _send_to_flowers(self, params):
        """发送参数到花朵"""
        try:
            self.orchestrator.broadcast_to_all(params)
        except Exception as e:
            print(f"发送失败: {e}")
    
    def _emergency_stop(self):
        """紧急停止"""
        if self.orchestrator:
            self.orchestrator.emergency_stop_all()
        self._update_status_text("🛑 紧急停止已触发！\n")
        self._update_status("紧急停止")
    
    def _update_status(self, text):
        """更新状态栏"""
        self.status_label.config(text=text)
    
    def _update_status_text(self, text):
        """更新状态文本框"""
        self.status_text.insert(tk.END, text)
        self.status_text.see(tk.END)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = DigitalBloomControlPanel(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

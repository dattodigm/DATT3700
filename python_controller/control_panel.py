"""
Digital Bloom Control Panel
Tkinter-based GUI for the Digital Bloom installation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import queue
import logging
import configparser
import os
import sys
from PIL import Image, ImageTk
import cv2

logger = logging.getLogger(__name__)


class ControlPanel:
    """Main Tkinter control panel for Digital Bloom."""

    PERSONAS = ['Empathy', 'Defensive', 'Predatory', 'Boredom', 'Surprise', 'Jealous']
    EMOTION_KEYS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

    def __init__(self, config: configparser.ConfigParser, vision_tracker, flower_network, persona_engine, ml_trainer):
        self.config = config
        self.vision = vision_tracker
        self.network = flower_network
        self.persona_engine = persona_engine
        self.ml_trainer = ml_trainer

        # Camera
        cam_id = config.getint('Vision', 'camera_id', fallback=0)
        self.cap = cv2.VideoCapture(cam_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.getint('Vision', 'frame_width', fallback=640))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.getint('Vision', 'frame_height', fallback=480))

        # State
        self.auto_mode = False
        self.running = True
        self.frame_queue = queue.Queue(maxsize=2)
        self._last_emotion_data = None
        self._selected_device = tk.StringVar()
        device_names = self.network.device_names() if self.network else []
        if device_names:
            self._selected_device.set(device_names[0])

        self._build_ui()
        self._start_vision_thread()

    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title("Digital Bloom Control Panel")
        self.root.configure(bg='#1a1a2e')
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1a1a2e')
        style.configure('TLabel', background='#1a1a2e', foreground='#e0e0e0', font=('Helvetica', 10))
        style.configure('Title.TLabel', background='#1a1a2e', foreground='#00d4ff', font=('Helvetica', 14, 'bold'))
        style.configure('Value.TLabel', background='#1a1a2e', foreground='#00ff88', font=('Helvetica', 10, 'bold'))
        style.configure('TButton', background='#16213e', foreground='#e0e0e0', font=('Helvetica', 9))
        style.configure('TCombobox', background='#16213e', foreground='#e0e0e0')
        style.configure('TScale', background='#1a1a2e', troughcolor='#16213e')
        style.configure('Section.TLabelframe', background='#16213e', foreground='#00d4ff', font=('Helvetica', 10, 'bold'))
        style.configure('Section.TLabelframe.Label', background='#16213e', foreground='#00d4ff')

        # ── Title bar ──
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=8, pady=(8, 0))
        ttk.Label(title_frame, text="🌸 Digital Bloom Control Panel", style='Title.TLabel').pack(side='left')
        self._conn_label = ttk.Label(title_frame, text="● Disconnected", foreground='#ff4444', background='#1a1a2e', font=('Helvetica', 10))
        self._conn_label.pack(side='right', padx=8)

        # ── Top row: preview + perception ──
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill='x', padx=8, pady=4)

        # Webcam preview
        preview_frame = ttk.LabelFrame(top_frame, text="📹 Live Preview", style='Section.TLabelframe')
        preview_frame.pack(side='left', padx=(0, 4))
        self._preview_label = ttk.Label(preview_frame)
        self._preview_label.pack(padx=4, pady=4)

        # Perception data
        perc_frame = ttk.LabelFrame(top_frame, text="📊 Perception Data", style='Section.TLabelframe')
        perc_frame.pack(side='left', fill='both', expand=True, padx=(4, 0))

        self._emotion_labels = {}
        for i, emo in enumerate(self.EMOTION_KEYS):
            row = ttk.Frame(perc_frame)
            row.pack(fill='x', padx=6, pady=1)
            ttk.Label(row, text=f"{emo.capitalize()}:", width=10).pack(side='left')
            val_label = ttk.Label(row, text="0.00", style='Value.TLabel', width=6)
            val_label.pack(side='left')
            bar = ttk.Progressbar(row, length=120, maximum=1.0, mode='determinate')
            bar.pack(side='left', padx=4)
            self._emotion_labels[emo] = (val_label, bar)

        info_frame = ttk.Frame(perc_frame)
        info_frame.pack(fill='x', padx=6, pady=4)
        self._info_labels = {}
        info_fields = [('dominant', 'Emotion'), ('age', 'Age'), ('gender', 'Gender'),
                       ('distance', 'Distance'), ('persons', 'Persons'), ('pose', 'Pose'),('color', 'Color')]
        for key, label_text in info_fields:
            row = ttk.Frame(info_frame)
            row.pack(fill='x', pady=1)
            ttk.Label(row, text=f"{label_text}:", width=10).pack(side='left')
            lbl = ttk.Label(row, text="—", style='Value.TLabel')
            lbl.pack(side='left')
            self._info_labels[key] = lbl

        # ── Middle: manual controls ──
        ctrl_frame = ttk.LabelFrame(self.root, text="🎚️ Manual Control", style='Section.TLabelframe')
        ctrl_frame.pack(fill='x', padx=8, pady=4)

        ctrl_inner = ttk.Frame(ctrl_frame)
        ctrl_inner.pack(fill='x', padx=6, pady=4)

        # Device selector
        dev_row = ttk.Frame(ctrl_inner)
        dev_row.pack(fill='x', pady=2)
        ttk.Label(dev_row, text="Device:").pack(side='left')
        device_names = self.network.device_names() if self.network else []
        dev_combo = ttk.Combobox(dev_row, textvariable=self._selected_device, values=device_names, width=16, state='readonly')
        dev_combo.pack(side='left', padx=6)

        # Sliders
        self._sliders = {}
        slider_defs = [
            ('motor1', 'Motor 1 (DC)', -1.0, 1.0, 0.0),
            ('motor2', 'Motor 2 (DC)', -1.0, 1.0, 0.0),
            ('led_hue', 'LED Hue °', 0, 360, 120),
            ('led_sat', 'LED Saturation', 0.0, 1.0, 0.8),
            ('led_bri', 'LED Brightness', 0.0, 1.0, 0.7),
        ]
        slider_grid = ttk.Frame(ctrl_inner)
        slider_grid.pack(fill='x')
        for col_idx, (key, label, vmin, vmax, default) in enumerate(slider_defs):
            col_frame = ttk.Frame(slider_grid)
            col_frame.grid(row=0, column=col_idx, padx=6, pady=2, sticky='n')
            ttk.Label(col_frame, text=label, font=('Helvetica', 9)).pack()
            var = tk.DoubleVar(value=default)
            slider = ttk.Scale(col_frame, from_=vmin, to=vmax, orient='vertical',
                               variable=var, length=80,
                               command=lambda v, k=key: self._on_slider_change(k))
            slider.pack()
            val_lbl = ttk.Label(col_frame, text=f"{default:.2f}", style='Value.TLabel', font=('Helvetica', 8))
            val_lbl.pack()
            self._sliders[key] = (var, val_lbl)

        send_btn = ttk.Button(ctrl_inner, text="📤 Send Manual", command=self._send_manual)
        send_btn.pack(pady=4)

        # ── Bottom row: Recording + ML ──
        bot_frame = ttk.Frame(self.root)
        bot_frame.pack(fill='x', padx=8, pady=4)

        # Recording
        rec_frame = ttk.LabelFrame(bot_frame, text="💾 Record Mapping", style='Section.TLabelframe')
        rec_frame.pack(side='left', fill='both', expand=True, padx=(0, 4))

        rec_inner = ttk.Frame(rec_frame)
        rec_inner.pack(padx=6, pady=4)
        ttk.Label(rec_inner, text="Persona Label:").pack(side='left')
        self._record_persona = tk.StringVar(value='Empathy')
        persona_combo = ttk.Combobox(rec_inner, textvariable=self._record_persona,
                                     values=self.PERSONAS, width=12, state='readonly')
        persona_combo.pack(side='left', padx=4)
        ttk.Button(rec_inner, text="⏺ Record Sample", command=self._record_sample).pack(side='left', padx=4)
        self._sample_count_label = ttk.Label(rec_inner, text=f"Samples: {self.ml_trainer.sample_count}")
        self._sample_count_label.pack(side='left', padx=4)

        # ML
        ml_frame = ttk.LabelFrame(bot_frame, text="🤖 Machine Learning", style='Section.TLabelframe')
        ml_frame.pack(side='left', fill='both', expand=True, padx=(4, 0))

        ml_inner = ttk.Frame(ml_frame)
        ml_inner.pack(padx=6, pady=4)
        ttk.Button(ml_inner, text="🏋 Train Model", command=self._train_model).pack(side='left', padx=4)
        ttk.Button(ml_inner, text="📂 Load Model", command=self._load_model).pack(side='left', padx=4)
        self._auto_btn = ttk.Button(ml_inner, text="▶ Auto Mode: OFF", command=self._toggle_auto)
        self._auto_btn.pack(side='left', padx=4)
        self._ml_status = ttk.Label(ml_frame, text="No model loaded", foreground='#888')
        self._ml_status.pack(padx=6, pady=2)

    def _on_slider_change(self, key):
        var, lbl = self._sliders[key]
        lbl.config(text=f"{var.get():.2f}")

    def _send_manual(self):
        device_name = self._selected_device.get()
        device = self.network.get(device_name) if self.network else None
        if device is None:
            messagebox.showwarning("No Device", f"Device '{device_name}' not found.")
            return
        m1 = self._sliders['motor1'][0].get()
        m2 = self._sliders['motor2'][0].get()
        hue = self._sliders['led_hue'][0].get()
        sat = self._sliders['led_sat'][0].get()
        bri = self._sliders['led_bri'][0].get()
        
        device.set_motor(1, int(round(m1)))
        device.set_motor(2, int(round(m2)))
        device.set_led_hsv(1, hue, sat, bri)
        device.set_led_hsv(2, (hue + 30) % 360, sat * 0.8, bri * 0.7)

    def _record_sample(self):
        if self._last_emotion_data is None:
            messagebox.showwarning("No Data", "No perception data available yet.")
            return
        label = self._record_persona.get()
        from persona_engine import PersonaEngine
        features = PersonaEngine._extract_features(self._last_emotion_data)
        self.ml_trainer.record_sample(features, label)
        count = self.ml_trainer.sample_count
        self._sample_count_label.config(text=f"Samples: {count}")
        self._ml_status.config(text=f"Recorded '{label}' ({count} total)")

    def _train_model(self):
        self._ml_status.config(text="Training...")
        self.root.update()
        metrics = self.ml_trainer.train()
        if metrics:
            acc = metrics.get('accuracy', 0)
            n = metrics.get('n_samples', 0)
            self._ml_status.config(text=f"Trained: acc={acc:.0%}, n={n}")
            # Push model to persona engine
            self.persona_engine.set_ml_model(self.ml_trainer.model, self.ml_trainer.label_encoder)
        else:
            self._ml_status.config(text="Training failed (need ≥10 samples)")

    def _load_model(self):
        ok = self.ml_trainer.load_model()
        if ok:
            self.persona_engine.set_ml_model(self.ml_trainer.model, self.ml_trainer.label_encoder)
            self._ml_status.config(text="Model loaded ✓")
        else:
            self._ml_status.config(text="No model file found")

    def _toggle_auto(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self._auto_btn.config(text="⏹ Auto Mode: ON")
        else:
            self._auto_btn.config(text="▶ Auto Mode: OFF")
            # Stop all motors
            if self.network:
                self.network.broadcast_stop()

    def _start_vision_thread(self):
        self._vision_thread = threading.Thread(target=self._vision_loop, daemon=True)
        self._vision_thread.start()
        self._update_ui()

    def _vision_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            frame = cv2.flip(frame, 1)
            try:
                annotated, emotion_data = self.vision.process_frame(frame)
            except Exception as e:
                logger.debug(f"Vision error: {e}")
                annotated = frame
                from vision_tracker import EmotionData
                emotion_data = EmotionData()
            
            self._last_emotion_data = emotion_data
            
            # Auto mode: run persona engine
            if self.auto_mode and self.network:
                primary = self._selected_device.get()
                states = self.persona_engine.update(emotion_data, primary_device=primary)
                self.persona_engine.apply_to_network(self.network)
            
            # Put frame in queue (non-blocking)
            try:
                self.frame_queue.put_nowait((annotated, emotion_data))
            except queue.Full:
                pass

    def _update_ui(self):
        if not self.running:
            return
        try:
            annotated, emotion_data = self.frame_queue.get_nowait()
            # Update preview
            rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb).resize((320, 240))
            imgtk = ImageTk.PhotoImage(image=img)
            self._preview_label.imgtk = imgtk
            self._preview_label.config(image=imgtk)
            # Update emotion bars
            for emo_key, (val_lbl, bar) in self._emotion_labels.items():
                val = emotion_data.emotions.get(emo_key, 0.0)
                val_lbl.config(text=f"{val:.2f}")
                bar['value'] = val
            # Update info labels
            self._info_labels['dominant'].config(text=emotion_data.dominant_emotion)
            self._info_labels['age'].config(text=str(emotion_data.age) if emotion_data.age else '—')
            self._info_labels['gender'].config(text=emotion_data.gender)
            self._info_labels['distance'].config(text=f"{emotion_data.distance_estimate:.1f}m")
            self._info_labels['persons'].config(text=str(emotion_data.person_count))
            self._info_labels['pose'].config(text=f"{emotion_data.pose_openness:.2f}")
            color_hex = emotion_data.dominant_color
            self._info_labels['color'].config(text=color_hex, foreground=color_hex if color_hex != '#808080' else '#808080')
            # Connection status
            dev_count = len(self.network.devices) if self.network else 0
            if dev_count > 0:
                self._conn_label.config(text=f"● {dev_count} device(s)", foreground='#00ff88')
            else:
                self._conn_label.config(text="● No devices", foreground='#ffaa00')
        except queue.Empty:
            pass
        except Exception as e:
            logger.debug(f"UI update error: {e}")
        
        self.root.after(33, self._update_ui)  # ~30 fps

    def run(self):
        self.root.mainloop()

    def _on_close(self):
        self.running = False
        if self.network:
            self.network.broadcast_stop()
        self.cap.release()
        self.root.destroy()

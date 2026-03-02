#!/usr/bin/env python3
"""
main.py - Digital Bloom 主程序入口

启动控制面板或命令行模式

用法:
    python main.py                    # 启动GUI模式
    python main.py --cli             # 启动命令行模式
    python main.py --train data.csv  # 训练ML模型
    python main.py --demo            # 演示模式

作者: Digital Bloom Team
版本: 1.0.0
"""

import argparse
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def run_gui():
    """运行GUI模式"""
    print("🌸 启动 Digital Bloom 控制面板...")
    try:
        from ui.control_panel import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"❌ 启动失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)


def run_cli():
    """运行命令行模式"""
    print("🌸 启动 Digital Bloom CLI模式...")
    print("(CLI模式开发中，请使用GUI模式)")


def train_model(data_path):
    """训练ML模型"""
    print(f"🧠 训练ML模型...")
    print(f"训练数据: {data_path}")
    
    try:
        import pandas as pd
        from decision.persona_classifier import PersonaClassifier
        
        # 加载数据
        df = pd.read_csv(data_path)
        print(f"加载了 {len(df)} 条训练数据")
        
        # 准备数据
        X = df.drop('label', axis=1).values
        y = df['label'].values
        
        # 训练模型
        classifier = PersonaClassifier(model_type='random_forest')
        classifier.train(X, y)
        
        # 保存模型
        model_path = data_path.replace('.csv', '_model.pkl')
        classifier.save_model(model_path)
        
        print(f"✅ 模型训练完成并保存到: {model_path}")
        
    except Exception as e:
        print(f"❌ 训练失败: {e}")
        sys.exit(1)


def run_demo():
    """运行演示模式"""
    print("🌸 Digital Bloom 演示模式")
    print("=" * 50)
    print("\n系统组件检查:")
    
    # 检查依赖
    try:
        import cv2
        print("✅ OpenCV 已安装")
    except ImportError:
        print("❌ OpenCV 未安装: pip install opencv-python")
    
    try:
        import mediapipe
        print("✅ MediaPipe 已安装")
    except ImportError:
        print("❌ MediaPipe 未安装: pip install mediapipe")
    
    try:
        import deepface
        print("✅ DeepFace 已安装")
    except ImportError:
        print("❌ DeepFace 未安装: pip install deepface")
    
    try:
        import sklearn
        print("✅ scikit-learn 已安装")
    except ImportError:
        print("❌ scikit-learn 未安装: pip install scikit-learn")
    
    try:
        from pythonosc import udp_client
        print("✅ python-osc 已安装")
    except ImportError:
        print("❌ python-osc 未安装: pip install python-osc")
    
    print("\n" + "=" * 50)
    print("\n快速开始:")
    print("1. 连接ESP32花朵到电源")
    print("2. 用电脑连接到ESP32的WiFi热点")
    print("3. 运行: python main.py")
    print("\n详细文档请查看 docs/ 目录")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Digital Bloom - 具身AI花朵控制系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                          # 启动GUI控制面板
  %(prog)s --demo                   # 运行系统检查
  %(prog)s --train data.csv         # 训练ML模型
        """
    )
    
    parser.add_argument('--cli', action='store_true',
                       help='命令行模式')
    parser.add_argument('--train', metavar='DATA_FILE',
                       help='训练ML模型 (CSV文件路径)')
    parser.add_argument('--demo', action='store_true',
                       help='演示/检查模式')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    args = parser.parse_args()
    
    if args.demo:
        run_demo()
    elif args.train:
        train_model(args.train)
    elif args.cli:
        run_cli()
    else:
        run_gui()


if __name__ == '__main__':
    main()

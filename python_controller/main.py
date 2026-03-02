#!/usr/bin/env python3
"""
Digital Bloom — Main Application Entry Point
"""

import configparser
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('DigitalBloom')


def main():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)

    logger.info("=== Digital Bloom Control System ===")

    # Import modules
    from vision_tracker import VisionTracker
    from osc_client import FlowerNetwork
    from persona_engine import PersonaEngine
    from ml_trainer import MLTrainer

    # Initialise components
    vision = VisionTracker(config)
    network = FlowerNetwork(config)
    persona_engine = PersonaEngine(config, network.device_names())
    ml_trainer = MLTrainer(config)

    # Try to load existing ML model
    if ml_trainer.load_model():
        persona_engine.set_ml_model(ml_trainer.model, ml_trainer.label_encoder)
        logger.info("ML model loaded")
    else:
        logger.info("No ML model found, using heuristic persona mapping")

    # Launch control panel
    try:
        from control_panel import ControlPanel
        panel = ControlPanel(config, vision, network, persona_engine, ml_trainer)
        panel.run()
    except ImportError as e:
        logger.error(f"Could not launch control panel: {e}")
        logger.info("Running headless vision loop (Ctrl+C to stop)")
        import cv2, time
        cap = cv2.VideoCapture(config.getint('Vision', 'camera_id', fallback=0))
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                _, emotion_data = vision.process_frame(frame)
                persona_engine.update(emotion_data)
                persona_engine.apply_to_network(network)
                time.sleep(0.05)
        except KeyboardInterrupt:
            logger.info("Stopped")
        finally:
            cap.release()
            network.broadcast_stop()


if __name__ == '__main__':
    sys.exit(main() or 0)

#!/usr/bin/env python3
"""
Test script for Vision Tracker (requires camera)
Tests face and color tracking with live preview
"""

import sys
import cv2
sys.path.insert(0, '/home/runner/work/DATT3700/DATT3700/python_controller')

from vision_tracker import FaceTracker, ColorTracker


def test_face_tracker():
    """Test face tracking with live camera."""
    print("Testing Face Tracker...")
    print("Press 'q' to quit")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return False
    
    tracker = FaceTracker(640, 480)
    
    frame_count = 0
    detected_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            x_error, y_error, detected = tracker.get_tracking_error(frame)
            
            frame_count += 1
            if detected:
                detected_count += 1
            
            # Display info
            cv2.putText(frame, f"Detected: {detected}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Error: X={x_error:.0f} Y={y_error:.0f}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Face Tracker Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    detection_rate = (detected_count / frame_count * 100) if frame_count > 0 else 0
    print(f"\nFace detected in {detected_count}/{frame_count} frames ({detection_rate:.1f}%)")
    print("✓ Face tracker test completed")
    
    return True


def test_color_tracker():
    """Test color tracking with live camera."""
    print("\nTesting Color Tracker...")
    print("Hold a red object in front of the camera")
    print("Press 'q' to quit")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return False
    
    # Default: red color
    tracker = ColorTracker(640, 480, 
                          lower_hsv=(0, 120, 70),
                          upper_hsv=(10, 255, 255))
    
    frame_count = 0
    detected_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            x_error, y_error, detected = tracker.get_tracking_error(frame)
            
            frame_count += 1
            if detected:
                detected_count += 1
            
            # Display info
            cv2.putText(frame, f"Detected: {detected}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Error: X={x_error:.0f} Y={y_error:.0f}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Color Tracker Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    detection_rate = (detected_count / frame_count * 100) if frame_count > 0 else 0
    print(f"\nColor detected in {detected_count}/{frame_count} frames ({detection_rate:.1f}%)")
    print("✓ Color tracker test completed")
    
    return True


if __name__ == '__main__':
    print("=" * 50)
    print("Vision Tracker Test Suite")
    print("=" * 50)
    
    print("\n1. Face Tracker")
    print("2. Color Tracker")
    print("3. Both")
    choice = input("\nSelect test (1-3): ").strip()
    
    try:
        if choice == '1':
            test_face_tracker()
        elif choice == '2':
            test_color_tracker()
        elif choice == '3':
            test_face_tracker()
            test_color_tracker()
        else:
            print("Invalid choice")
            sys.exit(1)
        
        print("\n" + "=" * 50)
        print("✓ Vision tracker tests completed!")
        print("=" * 50)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)

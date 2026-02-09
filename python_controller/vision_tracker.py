"""
Vision Tracking Module
Implements face and color tracking using OpenCV.
"""

import cv2
import numpy as np


class VisionTracker:
    """Base class for vision tracking."""
    
    def __init__(self, frame_width=640, frame_height=480):
        """
        Initialize vision tracker.
        
        Args:
            frame_width: Width of camera frame
            frame_height: Height of camera frame
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        
    def get_tracking_error(self, frame):
        """
        Get tracking error from frame.
        
        Args:
            frame: Input image frame
            
        Returns:
            tuple: (x_error, y_error, detected) where errors are in pixels
                   from center, and detected is a boolean
        """
        raise NotImplementedError("Subclass must implement get_tracking_error")


class FaceTracker(VisionTracker):
    """Face tracking using Haar Cascade."""
    
    def __init__(self, frame_width=640, frame_height=480):
        """Initialize face tracker with Haar Cascade."""
        super().__init__(frame_width, frame_height)
        
        # Load pre-trained face detector
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load face cascade classifier")
    
    def get_tracking_error(self, frame):
        """
        Detect face and calculate tracking error.
        
        Args:
            frame: Input BGR image
            
        Returns:
            tuple: (x_error, y_error, detected)
        """
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) > 0:
            # Use the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            # Calculate center of face
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            # Calculate error from frame center
            x_error = face_center_x - self.center_x
            y_error = face_center_y - self.center_y
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 255, 0), -1)
            
            return (x_error, y_error, True)
        
        return (0, 0, False)


class ColorTracker(VisionTracker):
    """Color tracking using HSV color space."""
    
    def __init__(self, frame_width=640, frame_height=480,
                 lower_hsv=(0, 120, 70), upper_hsv=(10, 255, 255)):
        """
        Initialize color tracker.
        
        Args:
            frame_width: Width of camera frame
            frame_height: Height of camera frame
            lower_hsv: Lower bound for HSV color range (default: red)
            upper_hsv: Upper bound for HSV color range (default: red)
        """
        super().__init__(frame_width, frame_height)
        self.lower_hsv = np.array(lower_hsv)
        self.upper_hsv = np.array(upper_hsv)
        
    def set_color_range(self, lower_hsv, upper_hsv):
        """
        Update color tracking range.
        
        Args:
            lower_hsv: Lower bound for HSV color range
            upper_hsv: Upper bound for HSV color range
        """
        self.lower_hsv = np.array(lower_hsv)
        self.upper_hsv = np.array(upper_hsv)
    
    def get_tracking_error(self, frame):
        """
        Detect colored object and calculate tracking error.
        
        Args:
            frame: Input BGR image
            
        Returns:
            tuple: (x_error, y_error, detected)
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask for color
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)
        
        # Apply morphological operations to reduce noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Get minimum area that's significant
            if cv2.contourArea(largest_contour) > 500:
                # Calculate moments to find center
                M = cv2.moments(largest_contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Calculate error from frame center
                    x_error = cx - self.center_x
                    y_error = cy - self.center_y
                    
                    # Draw contour and center
                    cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                    
                    return (x_error, y_error, True)
        
        return (0, 0, False)

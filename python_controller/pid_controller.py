"""
PID Controller Implementation
Provides proportional-integral-derivative control for tracking errors.
"""

import time


class PIDController:
    """PID controller for error correction."""
    
    def __init__(self, kp=1.0, ki=0.0, kd=0.0, setpoint=0.0, 
                 output_limits=(-100, 100), sample_time=0.01):
        """
        Initialize PID controller.
        
        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
            setpoint: Target setpoint
            output_limits: Tuple of (min, max) output limits
            sample_time: Minimum time between updates (seconds)
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.sample_time = sample_time
        
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = None
        self._last_output = 0.0
        
    def update(self, current_value):
        """
        Calculate PID output based on current value.
        
        Args:
            current_value: Current measured value
            
        Returns:
            float: PID controller output
        """
        current_time = time.time()
        
        # Initialize on first call
        if self._last_time is None:
            self._last_time = current_time
            self._last_error = self.setpoint - current_value
            return 0.0
        
        # Calculate time delta
        dt = current_time - self._last_time
        
        # Check if enough time has passed
        if dt < self.sample_time:
            return self._last_output
        
        # Calculate error
        error = self.setpoint - current_value
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self._integral += error * dt
        i_term = self.ki * self._integral
        
        # Derivative term
        if dt > 0:
            derivative = (error - self._last_error) / dt
        else:
            derivative = 0.0
        d_term = self.kd * derivative
        
        # Calculate output
        output = p_term + i_term + d_term
        
        # Apply output limits
        if self.output_limits:
            output = max(self.output_limits[0], 
                        min(output, self.output_limits[1]))
            
            # Anti-windup: clamp integral if output is saturated
            if output != p_term + i_term + d_term:
                self._integral -= error * dt
        
        # Store values for next iteration
        self._last_error = error
        self._last_time = current_time
        self._last_output = output
        
        return output
    
    def reset(self):
        """Reset the PID controller state."""
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = None
        self._last_output = 0.0
    
    def set_tunings(self, kp=None, ki=None, kd=None):
        """Update PID tuning parameters."""
        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd

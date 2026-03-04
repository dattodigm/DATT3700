# PID Tuning Guide

## Understanding PID Control

A PID controller combines three control strategies:

### Proportional (Kp)
- Responds proportionally to the current error
- Higher Kp = faster response but can cause overshoot
- Formula: `P = Kp × error`

### Integral (Ki)
- Accumulates error over time
- Eliminates steady-state error
- Too high Ki can cause oscillations
- Formula: `I = Ki × ∫(error)dt`

### Derivative (Kd)
- Responds to rate of error change
- Dampens oscillations and overshoot
- Sensitive to noise
- Formula: `D = Kd × d(error)/dt`

### Total Output
```
output = Kp×error + Ki×∫(error)dt + Kd×d(error)/dt
```

## Tuning Process

### Step 1: Start with P-Only Control

1. Set Ki = 0, Kd = 0
2. Set Kp to a small value (e.g., 0.1)
3. Gradually increase Kp until system responds
4. Continue increasing until slight overshoot occurs
5. Reduce Kp by 20-30%

**Result**: System responds but may have steady-state error

### Step 2: Add Integral Control

1. Keep Kp from Step 1
2. Set Ki to a small value (e.g., 0.001)
3. Gradually increase Ki until steady-state error disappears
4. If oscillations occur, reduce Ki

**Result**: No steady-state error, but may oscillate

### Step 3: Add Derivative Control

1. Keep Kp and Ki from Steps 1-2
2. Set Kd to a small value (e.g., 0.01)
3. Gradually increase Kd to dampen oscillations
4. If system becomes sluggish, reduce Kd

**Result**: Fast response, no steady-state error, minimal oscillation

## Ziegler-Nichols Method

If the above doesn't work, try Ziegler-Nichols tuning:

1. Set Ki = 0, Kd = 0
2. Increase Kp until system oscillates continuously
3. Note the ultimate gain (Ku) and oscillation period (Tu)
4. Apply formulas:
   - Kp = 0.6 × Ku
   - Ki = 2 × Kp / Tu
   - Kd = Kp × Tu / 8

## Application-Specific Tuning

### For the Flower Tracker:

**Pan Control (Horizontal)**
- Start: Kp=0.1, Ki=0.005, Kd=0.03
- Goal: Smooth horizontal tracking without jerky movements

**Tilt Control (Vertical)**
- Start: Kp=0.1, Ki=0.005, Kd=0.03
- Goal: Stable vertical positioning with minimal bounce

### Tuning Tips for This Project:

1. **Kp (0.1-0.3)**:
   - Too low: Slow to respond, lags behind target
   - Too high: Jerky movements, overshoots target
   - Optimal: Smooth following with slight lag

2. **Ki (0.001-0.05)**:
   - Too low: Doesn't center on stationary target
   - Too high: Oscillates around target
   - Optimal: Slowly centers without oscillation

3. **Kd (0.01-0.1)**:
   - Too low: Overshoots and bounces
   - Too high: Sluggish, resistant to quick movements
   - Optimal: Smooth deceleration as it approaches target

## Testing Procedure

### Setup
```bash
python main.py --tracker face --ip YOUR_ESP32_IP
```

### Test 1: Step Response
1. Stand in front of camera at center
2. Press SPACE to enable tracking
3. Quickly move left/right by one body width
4. Observe servo response

**Good Response:**
- Smooth movement toward new position
- Slight overshoot (<10°)
- Settles within 1-2 seconds

**Bad Response:**
- Excessive overshoot (>20°)
- Oscillates back and forth
- Very slow to reach position

### Test 2: Continuous Tracking
1. Enable tracking
2. Slowly move left to right
3. Observe smoothness

**Good Response:**
- Smooth, continuous following
- No jerky movements
- Minimal lag

**Bad Response:**
- Choppy, stepwise movement
- Large lag behind movement
- Random oscillations

### Test 3: Stationary Target
1. Enable tracking
2. Remain still at offset position (not centered)
3. Wait 5 seconds

**Good Response:**
- Gradually moves to center on face
- Settles without oscillation
- Final error < 5 pixels

**Bad Response:**
- Doesn't center (needs more Ki)
- Oscillates around target (too much Ki)
- Overshoots repeatedly

## Configuration File Tuning

Edit `config.ini`:

```ini
[PID_Pan]
kp = 0.15    # Adjust this first
ki = 0.01    # Then this
kd = 0.05    # Finally this
output_limit = 30

[PID_Tilt]
kp = 0.15
ki = 0.01
kd = 0.05
output_limit = 30
```

## Common Issues and Solutions

### Issue: System oscillates
**Solution**: Reduce Kp, increase Kd

### Issue: Slow to respond
**Solution**: Increase Kp, reduce Kd

### Issue: Doesn't center on target
**Solution**: Increase Ki

### Issue: Overshoots target
**Solution**: Reduce Kp, increase Kd

### Issue: Jerky movements
**Solution**: Reduce Kp, reduce output_limit

### Issue: Drifts when stationary
**Solution**: Increase Ki (but watch for oscillation)

## Advanced: Dynamic Tuning

For different conditions, you may want different PID values:

```python
# In main.py, add mode switching:
if detected and distance_to_target < 50:
    # Close to target: gentle control
    self.pid_pan.set_tunings(kp=0.1, ki=0.005, kd=0.08)
else:
    # Far from target: aggressive control
    self.pid_pan.set_tunings(kp=0.2, ki=0.02, kd=0.03)
```

## Performance Metrics

Track these metrics during tuning:

1. **Rise Time**: Time to reach 90% of target
   - Target: < 1 second

2. **Overshoot**: Maximum deviation beyond target
   - Target: < 10% of error distance

3. **Settling Time**: Time to stay within 5% of target
   - Target: < 2 seconds

4. **Steady-State Error**: Final error when stationary
   - Target: < 5 pixels

## Logging for Analysis

Add this to `main.py` for detailed tuning analysis:

```python
import csv
import time

# In FlowerControlSystem.__init__:
self.log_file = open('pid_log.csv', 'w', newline='')
self.log_writer = csv.writer(self.log_file)
self.log_writer.writerow(['time', 'x_error', 'y_error', 
                          'pan_output', 'tilt_output',
                          'pan_angle', 'tilt_angle'])

# In run() loop:
if self.tracking_active and detected:
    self.log_writer.writerow([
        time.time(),
        x_error, y_error,
        pan_correction, tilt_correction,
        self.pan_angle, self.tilt_angle
    ])
```

Analyze with:
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('pid_log.csv')
plt.plot(df['time'], df['x_error'])
plt.plot(df['time'], df['pan_angle'])
plt.legend(['Error', 'Servo Angle'])
plt.show()
```

## Hardware Considerations

### Servo Response Time
- Cheap servos: slower response, increase Kd
- Quality servos: faster response, reduce Kd

### Power Supply
- Weak power: servos lag, reduce all gains
- Strong power: risk of damage, use output limits

### Mechanical Load
- Heavy flower: increase Kp, reduce Kd
- Light flower: decrease Kp, increase Kd

## Safety Limits

Always keep these limits in place:

```python
# In pid_controller.py
output_limits=(-30, 30)  # Max 30° change per update

# In main.py
self.pan_angle = max(0, min(180, self.pan_angle))
self.tilt_angle = max(0, min(180, self.tilt_angle))
```

This prevents:
- Violent servo movements
- Exceeding mechanical limits
- Damaging the flower mechanism

## Final Checklist

- [ ] Kp provides adequate response speed
- [ ] Ki eliminates steady-state error without oscillation
- [ ] Kd dampens overshoot without making system sluggish
- [ ] System tracks smoothly during slow movements
- [ ] System responds quickly to sudden changes
- [ ] No excessive oscillation or jitter
- [ ] Servos don't make unusual noises
- [ ] Power supply remains stable during operation
- [ ] Tracking works in various lighting conditions

## References

- [PID Control Theory](https://en.wikipedia.org/wiki/PID_controller)
- [Ziegler-Nichols Method](https://en.wikipedia.org/wiki/Ziegler%E2%80%93Nichols_method)
- [Control Systems Engineering](https://www.mathworks.com/help/control/)

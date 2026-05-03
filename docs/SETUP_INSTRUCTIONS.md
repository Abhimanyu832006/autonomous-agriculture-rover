# Setup Instructions — Autonomous Agriculture Rover

## Table of Contents
1. **Physical Assembly** (Mechanical)
2. **Hardware Bring-Up** (Electrical Testing)
3. **ESP32 Firmware Installation**
4. **Raspberry Pi 5 Configuration**
5. **YOLOv5 Model Setup**
6. **Flask Web App Deployment**
7. **System Integration & Testing**
8. **Field Deployment Checklist**

---

## 1. Physical Assembly

### Prerequisites
- 4WD chassis kit (soldered motors to wheels)
- All components from parts list
- Soldering iron (60W), solder (Sn/Pb or lead-free)
- Multimeter
- Zip ties, hot glue gun, electrical tape

### Step 1.1: Mount Main Components on Chassis

#### Motor Driver & Power Management
1. **L298N module:**
   - Mount on front-left chassis corner using double-sided foam tape or M2 screws
   - Ensure cooling vents face upward (passive airflow)
   - Position: accessible for testing, away from battery pack

2. **Battery pack 1 (5000 mAh, motor power):**
   - Mount on rear-left using Velcro strip or zip ties
   - Secure both positive and negative terminals
   - Ensure rocker switch is accessible (side of chassis)

3. **Battery pack 2 (3200 mAh, RPi power):**
   - Mount on rear-right using Velcro strip
   - Position LM2596 buck converter above battery pack
   - Adjust LM2596 potentiometer to 5.1V (see Section 1.2)

4. **ESP32 DevKit:**
   - Mount on central platform using double-sided tape or breadboard holder
   - Keep USB port accessible for firmware uploads
   - Surround with foam padding to prevent shorts on exposed solder joints

5. **RPi 5:**
   - Mount on top platform (if rover has second deck) or offset to side
   - Ensure heatsink has airflow; do NOT cover with plastic
   - USB-C connector faces rear for future modem access
   - CSI camera port faces upward (ribbon will route downward)

#### Sensors & Actuators
6. **HC-SR04 ultrasonic sensor:**
   - Hot-glue to SG90 servo horn (if rotating) or directly to front bumper
   - Orientation: IR transducers facing forward, ~1 cm above ground
   - Mounting height: ~20 mm (optimal detection zone for ground obstacles)

7. **SG90 servo:**
   - Mount on front-left side of chassis using servo bracket or M2 screws
   - Servo horn should rotate upward; servo body mounted horizontally
   - Attach HC-SR04 sensor to horn with zip tie or hot glue
   - Test rotation: should sweep 0–180° without mechanical binding

8. **TCRT5000 line sensor:**
   - Mount on chassis underside, ~5 mm above ground
   - Placement: center of chassis (between wheel axles)
   - Orientation: IR LED and phototransistor both facing downward
   - Protect from light: enclose in black heat-shrink sleeve (optional but recommended)

9. **KY-008 laser module:**
   - Mount on front bumper, angled downward at ~45°
   - Position: 5–10 cm ahead of front wheels
   - Ensure beam hits ground ~20–30 cm ahead of rover
   - Safety: enclose laser in 3D-printed housing with warning label

10. **Camera (OV5647):**
    - Hot-glue to rover chassis top, near front-center
    - Angle: 45° downward (captures weed/crop in typical field view)
    - Protect lens: clear transparent tape or small lens cap
    - Ribbon management: route inside frame through small slot to RPi

### Step 1.2: Prepare Power Distribution

#### Rocker Switches
1. Drill two holes in side of chassis for rocker switches
2. Mount switch 1 in-line with battery 1 + wire (motor power)
3. Mount switch 2 in-line with battery 2 + wire (RPi power)
4. Label with vinyl tape: "Motors" and "RPi"

#### LM2596 Adjustment (CRITICAL)
1. Connect 7.4V test supply to LM2596 input (via battery 2)
2. Power on with multimeter probes on output (+/−)
3. **Voltage should NOT exceed 5.2V** (RPi USB-C specs: 5.1V ±0.1V)
4. Use small flathead screwdriver to adjust potentiometer:
   - **Clockwise:** voltage increases (target 5.1V)
   - **Counter-clockwise:** voltage decreases (avoid < 5.0V)
5. Fine-tune to exactly 5.1V ±0.05V using multimeter precision
6. Once set, do NOT adjust again (mark position with tape)
7. Power down and proceed to hardware testing

#### GND Bus Assembly
1. Strip 5–10 mm of insulation from L298N GND wire
2. Prepare similar GND connections from ESP32, HC-SR04, TCRT5000, relay
3. Twist all stripped ends together in single point
4. Solder together using 60W iron and rosin-core solder (apply solder to joint, not iron)
5. Inspect solder joint: should be shiny, smooth
6. Wrap completed junction with electrical tape for insulation
7. Label junction with black tape marker: "GND BUS ◆"

### Step 1.3: Cable Management

1. **Route motor cables** under chassis, away from sensors
2. **Route signal cables** (22 AWG) along frame perimeter with zip ties (loose, not tight)
3. **Bundle power wires** (20 AWG) separately with 3M electrical tape
4. **Label all connections** with heat-shrink labels:
   - L298N IN/OUT pins
   - Motor left/right
   - Battery ± terminals
5. **Protect exposed solder joints** with heat-shrink sleeves
6. **Test for shorts:** use multimeter continuity mode on adjacent signal lines

---

## 2. Hardware Bring-Up (Testing Before Firmware)

### Prerequisite: Safety
- **Remove all wheels** (prevents unintended motion)
- **Disconnect motors** from L298N (if possible, or ensure no GPIO outputs HIGH)
- **Wear safety glasses** during testing (prevent solder splatter)

### Step 2.1: Power Supply Verification

1. **Battery 1 measurement:**
   ```
   Multimeter: Voltage DC mode
   Probe (+) → Battery 1 positive terminal
   Probe (−) → Battery 1 negative terminal
   Expected: 7.2–8.4V (new 18650s: ~8.0V)
   ```
   Record: ____________ V

2. **Battery 2 measurement:**
   ```
   Expected: 7.2–8.4V
   ```
   Record: ____________ V

3. **L298N 5V output (no load):**
   ```
   Battery 1 connected via switch 1
   Switch 1: ON
   Multimeter: DC voltage
   Probe (+) → L298N 5V pin
   Probe (−) → L298N GND
   Expected: 4.8–5.2V
   ```
   Record: ____________ V

4. **LM2596 5V output (no load):**
   ```
   Battery 2 connected via switch 2
   Switch 2: ON
   Probe (+) → LM2596 output (before RPi)
   Probe (−) → GND bus
   Expected: 5.05–5.15V (if adjusted correctly)
   ```
   Record: ____________ V

**PROCEED TO STEP 2.2 ONLY IF ALL VOLTAGES PASS**

### Step 2.2: ESP32 & L298N Testing (Motors Disconnected)

#### ESP32 USB Connection
1. Connect ESP32 to laptop via USB-C cable (data cable, not charge-only)
2. **Windows:** Device Manager → Ports (COM & LPT) → should see "Silicon Labs CP2102 USB to UART Bridge Controller" on COM3 (or similar)
   - If missing: Download driver from silabs.com, install, reboot
3. **Mac/Linux:** `ls /dev/tty.SLAB_*` should list device
4. Do NOT power ESP32 from external 5V yet; USB is sufficient for firmware upload

#### Test LED Blink
1. Open Arduino IDE (must have ESP32 board installed)
2. File → Examples → 01.Basics → Blink
3. Board: **Tools → Board → ESP32 → ESP32 Dev Module**
4. COM Port: **Tools → Port → COM3** (your COM port)
5. Upload speed: 921600
6. Press and hold **BOOT button** on ESP32, then click **Upload**, release BOOT when "Writing..." appears
7. Verify: **Blue LED on ESP32 should blink at 1 Hz**
8. Success: proceed to Step 2.3

#### Troubleshooting Upload Errors
- **"Failed to connect"**: Check BOOT button timing, try alternate USB port
- **"File not found"**: Arduino IDE may need restart
- **"Baud rate error"**: Change to 115200 or 460800, retry

### Step 2.3: GPIO Signal Test (Multimeter / Oscilloscope)

1. Create simple test sketch:
   ```cpp
   void setup() {
     pinMode(27, OUTPUT);  // IN1
     pinMode(26, OUTPUT);  // IN2
     pinMode(25, OUTPUT);  // IN3
     pinMode(33, OUTPUT);  // IN4
   }
   
   void loop() {
     digitalWrite(27, HIGH);   // IN1 HIGH
     delay(500);
     digitalWrite(27, LOW);    // IN1 LOW
     delay(500);
   }
   ```
2. Upload to ESP32
3. **Multimeter (DC voltage mode):**
   - Probe (+) → ESP32 GPIO 27
   - Probe (−) → GND
   - Should alternate between 3.3V and 0V every 0.5 s
4. Repeat for GPIO 26, 25, 33 (all should toggle)
5. If not, restart ESP32 (press RESET button) and retry

### Step 2.4: L298N Logic Input Test

1. With GPIO 27 toggling (from above test):
   ```
   Multimeter (DC voltage)
   Probe (+) → L298N IN1 pin
   Probe (−) → GND
   Expected: should toggle 3.3V ↔ 0V (follows ESP32 GPIO 27)
   ```
2. If voltage stuck: check wire continuity with continuity mode
3. If wire OK but voltage not toggling: L298N logic pin may be damaged; replace module

### Step 2.5: Motor Power Path Test (Still Motors Disconnected)

1. Disable GPIO outputs (comment out digitalWrite calls):
   ```cpp
   // digitalWrite(27, HIGH);  // Commented out
   // digitalWrite(26, HIGH);  // Commented out
   ```
2. Upload blank code (all outputs LOW)
3. Switch on battery 1
4. **Multimeter on L298N OUT1 pin:**
   - Probe (+) → OUT1
   - Probe (−) → GND
   - Expected: voltage should be LOW (within 1V of GND) since inputs are LOW
5. Repeat for OUT2, OUT3, OUT4 (all should read similar baseline)
6. **Now toggle GPIO 27 HIGH in sketch:**
   - L298N OUT1 and OUT2 should jump to ~12V (motor voltage)
   - Verify this; if not, IN1 or driver itself may be faulty

---

## 3. ESP32 Firmware Installation

### Step 3.1: Arduino IDE Setup (First Time Only)

1. Download Arduino IDE 2.x from arduino.cc
2. Open Arduino IDE → File → Preferences
3. **Paste in "Additional Boards Manager URLs":**
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Close Preferences (OK button)
5. Tools → Board Manager → Search "esp32" → **Install "esp32" by Espressif Systems** (wait ~2 min)
6. Tools → Manage Libraries → Search "Servo" → **Install "ESP32Servo" by Kevin Harrington**
7. Tools → Manage Libraries → Search "Ultrasonic" → **Install "HC-SR04" by Rui Santos** (optional; we use pulseIn)

### Step 3.2: Configure Board Settings

1. Tools → Board → **ESP32 → ESP32 Dev Module**
2. Tools → Flash Mode → **DIO**
3. Tools → Upload Speed → **921600** (fast; fall back to 115200 if errors)
4. Tools → Core Debug Level → **None** (optimize speed)
5. Tools → Port → **COM3** (or your detected port)

### Step 3.3: Enter Final Firmware Code

Create new sketch: **File → New → Sketch**

```cpp
#include <ESP32Servo.h>

// Motor pins (L298N)
const int IN1 = 27;   // Left forward
const int IN2 = 26;   // Left backward
const int IN3 = 25;   // Right forward
const int IN4 = 33;   // Right backward
const int ENA = 14;   // Left speed (PWM)
const int ENB = 12;   // Right speed (PWM)

// Sensor pins
const int TRIG = 5;   // Ultrasonic trigger
const int ECHO = 18;  // Ultrasonic echo
const int SERVO_PIN = 32;  // Servo control
const int LINE_SENSOR = 35; // TCRT5000 (ADC)

// Motion parameters
const int PWM_SPEED = 120;    // Base speed (0-255)
const int OBSTACLE_DIST = 15; // cm
const int TURN_DELAY = 1200;  // ms for 90° turn
const int MOVE_TIME = 900;    // ms for straight motion

// Servo object
Servo servo;
int servo_angle = 90; // Center position

// State variables
bool bypassing = false;

void setup() {
  Serial.begin(115200);
  
  // Motor pins as outputs
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  
  // Sensor pins
  pinMode(TRIG, OUTPUT);
  digitalWrite(TRIG, LOW);
  
  // Servo setup (must be before PWM ledcAttach)
  servo.attach(SERVO_PIN);
  servo.write(90); // Center position
  
  // PWM setup for motors (16 kHz frequency)
  ledcAttach(ENA, 16000, 8);
  ledcAttach(ENB, 16000, 8);
  
  // Flush sensor
  for(int i = 0; i < 5; i++) {
    getDistance();
    delay(10);
  }
  
  Serial.println("Rover ready!");
}

void loop() {
  // Read line sensor
  int lineValue = analogRead(LINE_SENSOR);
  
  // Read distance
  int distance = getDistance();
  
  // Main logic
  if (!bypassing && distance < OBSTACLE_DIST) {
    // Obstacle detected
    stopMotors();
    delay(200);
    
    // Servo scan L/R
    int left_dist = scanServoDist(60);   // Left position
    int right_dist = scanServoDist(120); // Right position
    servo.write(90); // Center
    
    // Decide bypass direction
    if (left_dist > right_dist) {
      bypassObstacle(true); // Bypass left
    } else {
      bypassObstacle(false); // Bypass right
    }
    
    bypassing = false;
    
    // Flush sensor after bypass
    for(int i = 0; i < 5; i++) {
      getDistance();
      delay(10);
    }
  }
  else if (lineValue > 2500) {
    // White surface (on line) - move forward
    moveForward(PWM_SPEED);
  }
  else {
    // Black surface (off line) - stop
    stopMotors();
    delay(100);
  }
  
  delay(10);
}

// ============= DISTANCE SENSOR =============
int getDistance() {
  // Trigger pulse
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  
  // Measure echo pulse (timeout 25ms = 4.25m max)
  long duration = pulseIn(ECHO, HIGH, 25000);
  
  if (duration == 0) return 999; // No valid reading
  
  // Convert to cm: speed of sound = 34300 cm/s, divide by 2 (round trip)
  int distance = duration * 0.034 / 2;
  
  return (distance > 400) ? 999 : distance; // Clamp to 4m max
}

// 5-reading median filter
int getDistanceFiltered() {
  int readings[5];
  for(int i = 0; i < 5; i++) {
    readings[i] = getDistance();
    delay(10);
  }
  
  // Sort and return median
  for(int i = 0; i < 4; i++) {
    for(int j = i + 1; j < 5; j++) {
      if(readings[i] > readings[j]) {
        int temp = readings[i];
        readings[i] = readings[j];
        readings[j] = temp;
      }
    }
  }
  
  return readings[2]; // Middle value
}

// ============= SERVO SCANNING =============
int scanServoDist(int angle) {
  servo.write(angle);
  delay(500); // Wait for servo to settle
  return getDistanceFiltered();
}

// ============= MOTOR CONTROL =============
void moveForward(int speed) {
  digitalWrite(IN1, HIGH);  // Left forward
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);  // Right forward
  digitalWrite(IN4, LOW);
  ledcWrite(ENA, speed);
  ledcWrite(ENB, speed);
}

void moveBackward(int speed) {
  digitalWrite(IN1, LOW);   // Left backward
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);   // Right backward
  digitalWrite(IN4, HIGH);
  ledcWrite(ENA, speed);
  ledcWrite(ENB, speed);
}

void turnLeft(int speed) {
  digitalWrite(IN1, LOW);   // Left backward
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);  // Right forward
  digitalWrite(IN4, LOW);
  ledcWrite(ENA, speed);
  ledcWrite(ENB, speed);
}

void turnRight(int speed) {
  digitalWrite(IN1, HIGH);  // Left forward
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);   // Right backward
  digitalWrite(IN4, HIGH);
  ledcWrite(ENA, speed);
  ledcWrite(ENB, speed);
}

void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  ledcWrite(ENA, 0);
  ledcWrite(ENB, 0);
}

// ============= OBSTACLE BYPASS =============
void bypassObstacle(bool go_left) {
  bypassing = true;
  
  if (go_left) {
    // Bypass left: R90 → forward → L90 → forward → L90 → forward → R90
    turnRight(220);
    delay(TURN_DELAY);
    moveForward(220);
    delay(MOVE_TIME);
    turnLeft(220);
    delay(TURN_DELAY);
    moveForward(220);
    delay(1400); // Extra distance
    turnLeft(220);
    delay(TURN_DELAY);
    moveForward(220);
    delay(MOVE_TIME);
    turnRight(220);
    delay(TURN_DELAY);
  } else {
    // Bypass right: L90 → forward → R90 → forward → R90 → forward → L90
    turnLeft(220);
    delay(TURN_DELAY);
    moveForward(220);
    delay(MOVE_TIME);
    turnRight(220);
    delay(TURN_DELAY);
    moveForward(220);
    delay(1400); // Extra distance
    turnRight(220);
    delay(TURN_DELAY);
    moveForward(220);
    delay(MOVE_TIME);
    turnLeft(220);
    delay(TURN_DELAY);
  }
  
  stopMotors();
}
```

### Step 3.4: Upload Firmware

1. Connect ESP32 via USB (should power on, blue LED visible)
2. Click **Upload** button (→ icon, top toolbar)
3. **HOLD BOOT button** on ESP32 board when "Connecting..." appears
4. **RELEASE BOOT** when "Writing..." appears
5. Wait for upload to complete (~30 seconds)
6. Observe Serial Monitor (Ctrl+Shift+M) — should see "Rover ready!" at 115200 baud
7. If upload fails: restart IDE, check COM port, try 115200 upload speed

### Step 3.5: Test Individual Sensors

#### Test Distance Sensor
1. Place hand 30 cm in front of rover
2. Open Serial Monitor (Ctrl+Shift+M, 115200 baud)
3. Should print distance readings: "Distance: 30"
4. Move hand closer/farther; values should change
5. If not working: check TRIG/ECHO wiring (Section 2.3)

#### Test Line Sensor
1. Add to `loop()` temporarily:
   ```cpp
   Serial.println(analogRead(LINE_SENSOR));
   ```
2. Open Serial Monitor
3. Place rover on white surface; value should be ~4000+
4. Place rover on black tape; value should be ~100
5. If values inverted: sensor is backward; flip 180°

#### Test Servo
1. Add to `loop()`:
   ```cpp
   servo.write(45);
   delay(1000);
   servo.write(135);
   delay(1000);
   ```
2. Upload; servo should sweep back/forth smoothly
3. If servo jumps randomly: GPIO 32 conflict (check `ledcAttach` order)

---

## 4. Raspberry Pi 5 Configuration

### Step 4.1: OS Installation

1. **Download Raspberry Pi OS Imager** from raspberrypi.com
2. Insert microSD card into card reader (128 GB recommended)
3. Open Imager:
   - Choose Device: **Raspberry Pi 5**
   - Choose OS: **Raspberry Pi OS (64-bit)**
   - Choose Storage: **microSD card**
   - Advanced Options (gear icon):
     - Hostname: `rover`
     - Enable SSH: Yes (password auth)
     - Username: `pi`
     - Password: (set your password)
     - Enable WiFi: Yes (if available)
   - **Write** (takes ~3 min)
4. Eject microSD, insert into RPi 5

### Step 4.2: Initial Boot & SSH Connection

1. Power on RPi via USB-C (use external 5A power supply, not laptop USB)
2. Wait ~30 seconds for first boot
3. **SSH from laptop:**
   ```bash
   ssh pi@rover.local
   # (or IP if .local doesn't work: ssh pi@192.168.x.x)
   ```
4. Password: (your set password)
5. You should see: `pi@rover:~ $`

### Step 4.3: Enable Interfaces

1. Run raspi-config:
   ```bash
   sudo raspi-config
   ```
2. Navigate to:
   - **Interface Options**
   - **I2C**: Enable
   - **Serial Port**: Enable (Interfacing, not Console)
   - **Camera**: Enable (CSI-1 = Camera 0)
   - Reboot when prompted

### Step 4.4: System Update

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv
sudo apt install -y python3-dev libatlas-base-dev libjasper-dev libtiff5 libjasper1
```

Note: `libatlas-base-dev` may not be available on RPi 5 64-bit; skip if error (not critical).

### Step 4.5: Python Virtual Environment

```bash
python3 -m venv ~/rover_env
source ~/rover_env/bin/activate
pip install --upgrade pip
```

---

## 5. YOLOv5 Model Setup

### Step 5.1: Install Dependencies

```bash
source ~/rover_env/bin/activate
pip install flask picamera2 opencv-python pyserial RPi.GPIO
pip install ultralytics --break-system-packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**Note:** On RPi 5, PyTorch CPU is adequate for inference (no GPU needed for inference-only, though training should be done on external GPU)

### Step 5.2: Prepare Model

The trained YOLOv5 model (`best.pt`) should be downloaded from your training environment:

```bash
cd ~/
mkdir weed_detector
# Copy best.pt from Google Colab or external source
scp path/to/best.pt pi@rover.local:~/weed_detector/
# (Or manually download & transfer)
```

### Step 5.3: Test Model Locally

```bash
source ~/rover_env/bin/activate
cd ~/weed_detector

python3 << 'EOF'
from ultralytics import YOLO
model = YOLO('best.pt')
print("Model loaded successfully")
# (If using YOLOv5: from yolov5 import YOLOv5)
EOF
```

If model loads without errors, proceed to Step 6.

---

## 6. Flask Web App Deployment

### Step 6.1: Create Flask Application

Create `~/app.py`:

```python
from flask import Flask, render_template, Response, jsonify, request
from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import numpy as np
import RPi.GPIO as GPIO
import serial
import time
import threading

app = Flask(__name__)

# Model setup
model = YOLO('/home/pi/weed_detector/best.pt')

# Camera setup
try:
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"format": 'XRGB8888', "size": (640, 480)}
    )
    picam2.configure(config)
    picam2.start()
    print("Camera initialized")
except Exception as e:
    print(f"Camera error: {e}")
    picam2 = None

# GPIO setup (laser relay)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.LOW)

# Detection stats
stats = {
    'weeds_detected': 0,
    'crops_detected': 0,
    'distance': 999,
    'line_value': 0,
    'laser_fired': 0
}
stats_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            if picam2 is None:
                continue
            
            # Capture frame
            frame = picam2.capture_array()
            # RGBA -> BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            
            # Run inference
            results = model(frame, conf=0.3)
            
            # Count detections
            weeds = sum(1 for r in results[0].boxes.cls if int(r) == 0)  # Class 0 = weed
            crops = sum(1 for r in results[0].boxes.cls if int(r) == 1)  # Class 1 = crop
            
            # Update stats
            with stats_lock:
                stats['weeds_detected'] = weeds
                stats['crops_detected'] = crops
                
                # Fire laser if high-confidence weeds
                high_conf_weeds = sum(1 for r in results[0].boxes if int(r.cls) == 0 and r.conf > 0.5)
                if high_conf_weeds > 0:
                    fire_laser()
            
            # Draw boxes
            frame_with_boxes = results[0].plot()
            
            # Encode frame
            _, buffer = cv2.imencode('.jpg', frame_with_boxes)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.05)  # ~20 FPS
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def get_stats():
    with stats_lock:
        return jsonify(stats)

@app.route('/laser/fire', methods=['POST'])
def laser_fire():
    fire_laser()
    return jsonify({'status': 'fired'})

def fire_laser():
    GPIO.output(17, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(17, GPIO.LOW)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        if picam2:
            picam2.stop()
        GPIO.cleanup()
```

### Step 6.2: Create Web Template

Create directory & `~/templates/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Agriculture Rover Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .video-container {
            text-align: center;
            margin: 20px 0;
        }
        video, img {
            max-width: 100%;
            border-radius: 8px;
            border: 2px solid #ddd;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-label {
            font-size: 12px;
            opacity: 0.8;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }
        .controls {
            text-align: center;
            margin-top: 20px;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            background: #e74c3c;
            color: white;
            transition: background 0.3s;
        }
        button:hover {
            background: #c0392b;
        }
        .stream {
            width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌾 Autonomous Agriculture Rover</h1>
        
        <div class="video-container">
            <h2>Live Video Feed</h2>
            <img id="video-stream" src="/video_feed" class="stream" />
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Weeds Detected</div>
                <div class="stat-value" id="weeds">0</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="stat-label">Crops Detected</div>
                <div class="stat-value" id="crops">0</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="stat-label">Distance (cm)</div>
                <div class="stat-value" id="distance">--</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <div class="stat-label">Laser Fires</div>
                <div class="stat-value" id="laser">0</div>
            </div>
        </div>
        
        <div class="controls">
            <button onclick="fireLaser()">🔴 Fire Laser</button>
        </div>
    </div>

    <script>
        function updateStats() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('weeds').textContent = data.weeds_detected;
                    document.getElementById('crops').textContent = data.crops_detected;
                    document.getElementById('distance').textContent = data.distance;
                    document.getElementById('laser').textContent = data.laser_fired;
                });
        }

        function fireLaser() {
            fetch('/laser/fire', { method: 'POST' })
                .then(response => response.json())
                .then(data => console.log('Laser fired:', data));
        }

        // Update stats every 1 second
        setInterval(updateStats, 1000);
        updateStats(); // Initial call
    </script>
</body>
</html>
```

### Step 6.3: Run Flask App

```bash
source ~/rover_env/bin/activate
python3 ~/app.py
```

Expected output:
```
 * Running on http://0.0.0.0:5000
```

Open browser: `http://rover.local:5000` (or IP address)

---

## 7. System Integration & Testing

### Step 7.1: Field Test Protocol

1. **Indoor Test (Safe Environment):**
   - Place rover on open floor (no obstacles)
   - Activate motors via ESP32 (run `moveForward(100)` in setup)
   - Verify all four wheels rotate
   - Test line sensor with black tape path (1 inch wide)
   - Verify rover follows line for 2 meters

2. **Obstacle Avoidance Test:**
   - Place obstacle (box) 20 cm in front of rover
   - Activate obstacle bypass routine
   - Verify: robot detects, scans, bypasses, resumes motion
   - Repeat 5 times; verify ~4/5 success rate

3. **Detection Test:**
   - Place weed sample 30 cm in front of camera
   - Monitor Flask dashboard; confirm detection
   - Verify laser fires (if high confidence)

4. **Endurance Test:**
   - Run rover for 30 minutes continuously
   - Monitor battery voltage (should not drop below 6.5V)
   - Verify no thermal issues (touch L298N; should be warm but not hot)

### Step 7.2: Troubleshooting

| Issue | Solution |
|-------|----------|
| Rover moves in circle | Adjust motor PWM difference (PWM_SPEED ± 10) |
| Line sensor doesn't detect | Check calibration threshold (2500) |
| Camera feed black | Check CSI ribbon; reboot RPi |
| Servo doesn't scan | Verify GPIO 32 PWM output; test servo directly |
| Flask not accessible | Check firewall; verify port 5000 not in use |

---

## 8. Field Deployment Checklist

- [ ] Battery 1 charged (8.0V ±0.2V)
- [ ] Battery 2 charged (8.0V ±0.2V)
- [ ] LM2596 outputs 5.1V
- [ ] All wheels rotate freely
- [ ] Servo scans 0–180° smoothly
- [ ] Camera captures clear video
- [ ] HC-SR04 reads distance (test with hand)
- [ ] Line sensor reads black/white correctly
- [ ] Laser fires on button press
- [ ] Flask dashboard accessible via WiFi
- [ ] All cables secured with zip ties
- [ ] Rocker switches in OFF position

**Deployment Protocol:**
1. Enable all rocker switches
2. Open Flask dashboard (`http://rover.local:5000`)
3. Verify live video feed
4. Deploy rover to field
5. Monitor stats in real-time
6. Test obstacle avoidance manually (place objects in path)
7. Retrieve rover after field test
8. Charge batteries immediately

---

## Post-Deployment Maintenance

- **After each use:** Wipe chassis with damp cloth (remove dirt/moisture)
- **Weekly:** Check all connectors for corrosion
- **Monthly:** Re-tension servo horn (may loosen over time)
- **Every 50 hours:** Inspect motor brushes (replace if worn)

---

**Document Version:** 1.0  
**Last Updated:** May 1, 2026  
**Author:** Abhi (Indus University ME0636)

from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
from flask import Flask, render_template, Response, jsonify
import threading
import serial
import RPi.GPIO as GPIO
import time
import json
from datetime import datetime

app = Flask(__name__)

# === CONFIGURATION ===
LASER_PIN = 17
STOP_PIN = 15  # GPIO 15 to ESP32 GPIO 15
MOTOR_SPEED = 120
LASER_FIRE_COUNT = 5
LASER_FIRE_DURATION = 0.3
CONFIDENCE_THRESHOLD = 0.5

# === YOLO MODEL ===
model = YOLO('/home/pi/weed_detector/best.pt')

# === CAMERA SETUP ===
camera = Picamera2()
camera.configure(camera.create_preview_configuration())
camera.start()

# === SERIAL ESP32 ===
try:
    ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
except:
    ser = None
    print("[WARNING] ESP32 not connected via UART")

# === GPIO LASER RELAY + STOP SIGNAL ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(LASER_PIN, GPIO.OUT)
GPIO.output(LASER_PIN, GPIO.LOW)
GPIO.setup(STOP_PIN, GPIO.OUT)
GPIO.output(STOP_PIN, GPIO.LOW)

# === GLOBAL STATS ===
stats = {
    'weeds_detected': 0,
    'crops_detected': 0,
    'laser_fired_count': 0,
    'total_laser_shots': 0,
    'fps': 0,
    'distance': 0,
    'line_value': 0,
    'rover_moving': True,
    'last_detection': None,
    'last_detection_class': None
}

detection_log = []
frame_lock = threading.Lock()
current_frame = None

# === FIRE LASER 5 TIMES ===
def fire_laser_sequence():
    """Stop rover via GPIO 15, fire laser 5 times, resume movement"""
    global stats
    
    # Signal ESP32 to stop via GPIO 15
    GPIO.output(STOP_PIN, GPIO.HIGH)
    
    stats['rover_moving'] = False
    time.sleep(0.5)  # Let rover stop
    
    print("[LASER] Firing sequence starting...")
    
    for shot in range(LASER_FIRE_COUNT):
        # Fire laser via relay
        GPIO.output(LASER_PIN, GPIO.HIGH)
        time.sleep(LASER_FIRE_DURATION)
        GPIO.output(LASER_PIN, GPIO.LOW)
        
        stats['total_laser_shots'] += 1
        stats['laser_fired_count'] += 1
        
        print(f"[LASER] Shot {shot + 1}/{LASER_FIRE_COUNT} fired")
        
        if shot < LASER_FIRE_COUNT - 1:
            time.sleep(0.2)  # Delay between shots
    
    print("[LASER] Sequence complete. Resuming movement...")
    GPIO.output(STOP_PIN, GPIO.LOW)  # Release STOP signal
    stats['rover_moving'] = True
    time.sleep(0.5)

# === READ ESP32 DATA ===
def read_esp32_data():
    """Parse UART data from ESP32: dist:XX,line:YYYY"""
    try:
        if ser and ser.in_waiting:
            data = ser.readline().decode().strip()
            if data:
                parts = data.split(',')
                for part in parts:
                    try:
                        key, val = part.split(':')
                        if key == 'dist':
                            stats['distance'] = int(val)
                        elif key == 'line':
                            stats['line_value'] = int(val)
                    except:
                        pass
    except Exception as e:
        print(f"[ERROR] Reading ESP32: {e}")

# === VIDEO GENERATOR (YOLOv5 DETECTION) ===
def generate_frames():
    global current_frame, stats
    frame_count = 0
    start_time = time.time()
    
    while True:
        try:
            # Capture frame
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            
            # YOLOv5 detection
            results = model(frame, conf=0.3)
            annotated = results[0].plot()
            
            weed_in_frame = False
            
            # Check detections
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = results[0].names[class_id]
                
                if class_name == 'weed' and conf > CONFIDENCE_THRESHOLD:
                    weed_in_frame = True
                    stats['weeds_detected'] += 1
                    stats['last_detection'] = datetime.now().strftime("%H:%M:%S")
                    stats['last_detection_class'] = 'weed'
                    
                    print(f"[DETECTION] WEED detected (conf: {conf:.2f})")
                    
                    # Log detection
                    detection_log.insert(0, {
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'class': 'weed',
                        'confidence': round(conf, 2),
                        'action': 'LASER FIRED (5x)'
                    })
                    
                    # Keep log to last 20
                    if len(detection_log) > 20:
                        detection_log.pop()
                    
                    # Fire laser sequence (blocks briefly)
                    fire_laser_sequence()
                
                elif class_name == 'crop':
                    stats['crops_detected'] += 1
                    stats['last_detection'] = datetime.now().strftime("%H:%M:%S")
                    stats['last_detection_class'] = 'crop'
                    
                    print(f"[DETECTION] Crop detected (conf: {conf:.2f})")
                    
                    detection_log.insert(0, {
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'class': 'crop',
                        'confidence': round(conf, 2),
                        'action': 'NO ACTION'
                    })
                    
                    if len(detection_log) > 20:
                        detection_log.pop()
            
            # FPS counter
            frame_count += 1
            elapsed = time.time() - start_time
            if elapsed > 1:
                stats['fps'] = round(frame_count / elapsed)
                frame_count = 0
                start_time = time.time()
            
            # Add FPS to frame
            cv2.putText(annotated, f"FPS: {stats['fps']}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Encode for streaming
            ret, buffer = cv2.imencode('.jpg', annotated)
            frame_bytes = buffer.tobytes()
            
            with frame_lock:
                current_frame = frame_bytes
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   frame_bytes + b'\r\n')
        
        except Exception as e:
            print(f"[ERROR] Frame generation: {e}")
            time.sleep(0.1)

# === FLASK ROUTES ===

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def get_stats():
    read_esp32_data()
    return jsonify(stats)

@app.route('/detection_log')
def get_detection_log():
    return jsonify(detection_log)

@app.route('/laser/fire', methods=['POST'])
def manual_laser():
    """Manual fire button (demo only)"""
    threading.Thread(target=fire_laser_sequence, daemon=True).start()
    return jsonify({'status': 'firing', 'shots': LASER_FIRE_COUNT})

@app.route('/rover/speed/<int:speed>', methods=['POST'])
def set_speed(speed):
    """Adjust motor speed (80-200)"""
    global MOTOR_SPEED
    MOTOR_SPEED = max(80, min(200, speed))
    return jsonify({'speed': MOTOR_SPEED})

@app.route('/health')
def health():
    return jsonify({
        'esp32_connected': ser is not None,
        'camera_active': camera is not None,
        'gpio_ready': True,
        'model_loaded': model is not None
    })

if __name__ == '__main__':
    try:
        print("[START] Weed Rover Dashboard initialized")
        print(f"[CONFIG] Laser pin: GPIO {LASER_PIN}")
        print(f"[CONFIG] STOP pin: GPIO {STOP_PIN}")
        print(f"[CONFIG] Laser fire count: {LASER_FIRE_COUNT}")
        print(f"[CONFIG] Motor speed: {MOTOR_SPEED}")
        print(f"[CONFIG] Confidence threshold: {CONFIDENCE_THRESHOLD}")
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Cleaning up...")
        GPIO.cleanup()
        if ser:
            ser.close()
        camera.close()
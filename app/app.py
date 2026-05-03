"""
AgriRover Weed Detection Backend - Laptop Camera Edition
Serves the same API as the rover, but uses your laptop's camera + best.pt model
"""

import cv2
import numpy as np
from flask import Flask, jsonify, Response, render_template
from flask_cors import CORS
from ultralytics import YOLO
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

# ──────── Config ────────
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = str((BASE_DIR.parent / "models" / "best.pt").resolve())
CONF_THRESHOLD = 0.5
VIDEO_FPS = 30
INFERENCE_BUFFER = 60  # Keep last N detections

# ──────── Global State ────────
model = None
camera = None
frame_lock = threading.Lock()
current_frame = None
detection_log = deque(maxlen=INFERENCE_BUFFER)

fps_counter = deque(maxlen=30)
inference_times = deque(maxlen=30)

# ──────── Detection Counters ────────
stats = {
    'weed_count': 0,
    'crop_count': 0,
    'laser_count': 0,
    'last_weed_conf': None,
    'last_crop_conf': None,
    'fps': 0,
    'inference_ms': 0,
}

rover_status = {
    'state': 'IDLE',
    'speed': 0.0,
    'obstacle_distance': 150.0,
    'line_status': 'ON_TRACK',
    'battery_voltage': 12.0,
    'grid_x': 5.0,
    'grid_y': 5.0,
}


def normalize_detection_label(raw_name, cls_id):
    """Map model class names/ids to dashboard labels."""
    name = str(raw_name).strip().lower()

    # Common weed aliases
    if name in {'weed', 'weeds', '0'} or 'weed' in name:
        return 'weed'

    # Common crop aliases
    if name in {'crop', 'crops', 'plant', 'plants', '1'} or 'crop' in name or 'plant' in name:
        return 'crop'

    # Fallback for two-class models where id order is weed/crop
    if cls_id == 0:
        return 'weed'
    if cls_id == 1:
        return 'crop'

    return name

# ──────── Initialize ────────
def init_model():
    global model
    try:
        print(f"[MODEL] Loading {MODEL_PATH}...")
        model = YOLO(MODEL_PATH)
        print("[MODEL] Loaded successfully")
        return True
    except Exception as e:
        print(f"[MODEL] Failed to load: {e}")
        return False

def init_camera():
    global camera
    try:
        print("[CAMERA] Initializing...")
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, VIDEO_FPS)
        print("[CAMERA] Ready")
        return True
    except Exception as e:
        print(f"[CAMERA] Failed: {e}")
        return False

# ──────── Camera Capture Loop ────────
def capture_frames():
    """Continuously capture and process frames"""
    global current_frame, stats, detection_log
    
    while True:
        if not camera or not camera.isOpened():
            time.sleep(0.1)
            continue
        
        ret, frame = camera.read()
        if not ret:
            continue
        
        # Inference
        start_inf = time.time()
        try:
            results = model(frame, conf=CONF_THRESHOLD, verbose=False)
            inference_ms = (time.time() - start_inf) * 1000
            inference_times.append(inference_ms)
        except Exception as e:
            print(f"[INFERENCE] Error: {e}")
            continue
        
        # Parse detections
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                conf = float(box.conf[0])

                label = normalize_detection_label(cls_name, cls_id)

                if label == 'weed':
                    stats['last_weed_conf'] = conf
                    stats['weed_count'] += 1
                    # Simulate auto-fire when weed is detected.
                    stats['laser_count'] += 1
                elif label == 'crop':
                    stats['last_crop_conf'] = conf
                    stats['crop_count'] += 1
                
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                det = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'class': label,
                    'confidence': conf,
                    'bbox': [x1, y1, x2, y2],
                    'action': 'laser_fired' if label == 'weed' else 'skipped'
                }
                detections.append(det)
                detection_log.append(det)
        
        # Draw boxes on frame
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            color = (0, 0, 255) if det['class'] == 'weed' else (0, 255, 0)  # Red for weed, green for crop
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label_text = f"{det['class'].upper()} {det['confidence']:.2f}"
            cv2.putText(annotated, label_text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # FPS
        now = time.time()
        fps_counter.append(now)
        if len(fps_counter) > 1:
            stats['fps'] = len(fps_counter) / (fps_counter[-1] - fps_counter[0])
        
        stats['inference_ms'] = np.mean(list(inference_times)) if inference_times else 0
        
        # Store frame
        with frame_lock:
            current_frame = annotated

# ──────── Routes ────────

@app.route('/')
def index():
    """Render dashboard template."""
    return render_template('index.html')

@app.route('/stats')
def get_stats():
    """Return detection stats (mimics rover backend)"""
    return jsonify({
        'weed_count': stats['weed_count'],
        'crop_count': stats['crop_count'],
        'laser_count': stats['laser_count'],
        'last_weed_conf': stats['last_weed_conf'],
        'last_crop_conf': stats['last_crop_conf'],
        'fps': stats['fps'],
        'inference_ms': stats['inference_ms'],
    })

@app.route('/rover_status')
def get_rover_status():
    """Return rover status (mimics rover backend)"""
    return jsonify(rover_status)

@app.route('/detection_log')
def get_detection_log():
    """Return recent detections"""
    return jsonify({
        'detections': list(detection_log)[::-1]  # Most recent first
    })

@app.route('/video_feed')
def video_feed():
    """Stream video with detections"""
    def generate():
        while True:
            with frame_lock:
                if current_frame is None:
                    continue
                frame = current_frame.copy()
            
            # Encode frame
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(1 / VIDEO_FPS)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/laser/fire', methods=['POST'])
def fire_laser():
    """Simulate laser fire"""
    stats['laser_count'] += 1
    print("[LASER] Manual fire")
    return jsonify({'status': 'fired'})

@app.route('/laser/auto', methods=['POST'])
def toggle_auto():
    """Simulate auto mode toggle"""
    return jsonify({'status': 'toggled'})

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

# ──────── Main ────────
if __name__ == '__main__':
    print("[START] AgriRover Backend (Laptop Camera)")
    
    if not init_model():
        exit(1)
    
    if not init_camera():
        exit(1)
    
    # Start capture thread
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()
    
    print("[SERVER] Starting Flask on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
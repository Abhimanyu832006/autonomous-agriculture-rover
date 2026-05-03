# Autonomous Agriculture Rover

An autonomous 4WD rover for crop-row navigation and weed detection using ESP32 + Raspberry Pi 5 + YOLOv5.

## Tech Stack
- ESP32 DevKit V1 (motion control and sensor logic)
- Raspberry Pi 5 (ML inference + dashboard backend)
- YOLOv5 (weed/crop object detection)
- Flask (live dashboard and control APIs)
- OpenCV + Ultralytics (video pipeline and inference)

## Key Achievements
- Weed detection precision: 71.9%
- Weed detection recall: 66.7%
- Obstacle avoidance success rate: ~80%
- End-to-end rover system with full wiring and deployment documentation

## Repository Structure
```text
autonomous-agriculture-rover/
├── README.md
├── assets/
│   ├── poster/
│   ├── ppt/
│   ├── images/
│   ├── video/
│   └── Weed_detection_dataset/
├── docs/
│   ├── HARDWARE_SPECIFICATIONS.md
│   ├── WIRING_GUIDE.md
│   └── SETUP_INSTRUCTIONS.md
├── firmware/
│   └── rover.ino
├── app/
│   ├── app.py
│   ├── rpi_app.py
│   └── templates/
│       └── index.html
├── models/
│   └── best.pt
├── COMPLETE_PROJECT_DOCUMENTATION.md
├── requirements.txt
├── setup.bat
├── setup.ps1
└── LICENSE
```

## Quick Start
1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Ensure your model is available at `models/best.pt`.
4. Start Flask backend:
   - `python app/app.py`
5. Open dashboard:
   - `http://localhost:5000`

## Runtime Variants
- `app/app.py`: Laptop demo backend (local webcam + dashboard template). Use this for portfolio demos and local testing.
- `app/rpi_app.py`: Raspberry Pi deployment backend (Picamera2, GPIO, relay, ESP32 UART). Kept for production rover records and on-device runs.

## Media And Dataset
- `assets/poster/`: Project poster files.
- `assets/ppt/`: Presentation slides.
- `assets/images/`: Demo and documentation images.
- `assets/video/`: Demo videos.
- `assets/Weed_detection_dataset/`: Weed detection dataset used for training and validation.

## Documentation
- [Hardware Specifications](docs/HARDWARE_SPECIFICATIONS.md)
- [Wiring Guide](docs/WIRING_GUIDE.md)
- [Setup Instructions](docs/SETUP_INSTRUCTIONS.md)
- [Complete Project Documentation](COMPLETE_PROJECT_DOCUMENTATION.md)

## LinkedIn Project Summary
Built an autonomous agriculture rover for weed detection using ESP32, Raspberry Pi 5, and YOLOv5. The project includes obstacle avoidance, crop-row line following, real-time dashboard monitoring, and complete documentation for hardware and software setup.

## License
MIT License. See [LICENSE](LICENSE).

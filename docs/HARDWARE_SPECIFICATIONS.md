# Hardware Specifications — Autonomous Agriculture Rover

## Overview
ESP32-based 4WD rover with autonomous weed detection, obstacle avoidance, and line-following capabilities. Designed for crop-row navigation and in-field weed management.

---

## 1. Core Compute Modules

### ESP32 DevKit V1 (WROOM)
- **Microcontroller:** Tensilica Xtensa 32-bit LX6 dual-core
- **Clock Speed:** 240 MHz
- **RAM:** 520 KB SRAM
- **Flash:** 4 MB (built-in)
- **GPIO Pins:** 34 total (25 usable)
- **ADC:** 12-bit, 18 channels
- **PWM:** 16 channels (all GPIO except ADC-only pins)
- **UART:** 3 channels (UART0 on pins 1/3, UART1 configurable, UART2 on pins 16/17)
- **SPI:** 4 channels
- **I2C:** 2 channels
- **Operating Voltage:** 3.3V (internal), 5V tolerant on inputs
- **Power Consumption:** ~80 mA active, ~10 μA deep sleep
- **Board Dimensions:** 48.26 × 25.4 mm

**USB-Serial Bridge:** CP2102 (required driver for flashing)

---

### Raspberry Pi 5 (8GB RAM)
- **SoC:** Broadcom BCM2712 (Quad-core ARM Cortex-A76, 2.4 GHz)
- **RAM:** 8 GB LPDDR5
- **Storage:** microSD card (128 GB recommended for ML models)
- **GPIO:** 40-pin header (28 usable)
- **Interfaces:** 2× USB 3.0, 2× USB 2.0, Gigabit Ethernet, WiFi 6E, Bluetooth 5.3
- **Camera:** Dual CSI (Camera Serial Interface) connectors
  - Camera 0 (primary): 22-pin
  - Camera 1 (secondary): 15-pin
- **Power:** USB-C PD (5.1V, min 5A recommended for ML workloads)
- **Dimensions:** 85.6 × 56.5 mm

**Notes:**
- Old OV5647 camera requires Wonrabai 22-pin → 15-pin CSI adapter
- Must use `picamera2` library (OpenCV VideoCapture does NOT work)

---

## 2. Motors & Drive System

### TT Motor (DC 3–6V)
- **Count:** 4 (2 per side)
- **Rated Voltage:** 3–6V DC
- **Rated Speed:** ~200 RPM @ 3V, ~300 RPM @ 5V (no load)
- **Gearbox Ratio:** 1:48 internal reduction
- **Torque:** ~0.5 kg·cm (rated), ~1.5 kg·cm (stall)
- **Operating Current:** ~100 mA (no load), ~500 mA (stall)
- **Efficiency:** ~50–60%

**Mounting:**
- Chassis: 4WD robot car kit (standard)
- Mechanical connection: Spur gears on motor shaft → wheel axle

### Motor Driver: L298N
- **Type:** Dual H-Bridge (2 motors per module, 2 modules for 4 motors)
- **Logic Voltage:** 5V
- **Motor Voltage:** Up to 46V (we use 12V from battery)
- **Max Current (per motor):** 2 A (continuous), 3 A (peak)
- **Thermal Shutdown:** ~125°C
- **Pinout:**
  ```
  IN1, IN2  → Motor A direction control (GPIO 27, 26)
  IN3, IN4  → Motor B direction control (GPIO 25, 33)
  ENA, ENB  → PWM speed control (GPIO 14, 12)
  OUT1–OUT4 → Motor terminals (left/right pairs)
  12V, GND  → Motor power from battery
  5V, GND   → Logic power
  ```
- **Logic Voltage Safe:** 3.3V inputs on IN pins are acceptable (with 10kΩ pull-down to GND recommended for glitch immunity)

**Heat Management:**
- Operates at 2 A continuous without heatsink
- Our typical load: ~1 A per motor (PWM 120–220)
- Passive cooling adequate; no active cooling required

---

## 3. Sensors

### HC-SR04 Ultrasonic Distance Sensor
- **Measurement Range:** 2 cm–4 m
- **Frequency:** 40 kHz
- **Trigger Pulse:** 10 μs HIGH
- **Echo Duration:** Proportional to distance
- **Accuracy:** ±3 mm (typical)
- **Response Time:** ~60 ms (per measurement)
- **Operating Voltage:** 5V (Vcc), 3.3V signal safe (needs pull-up)
- **Pinout:**
  ```
  VCC   → L298N 5V output
  GND   → Common GND bus
  TRIG  → ESP32 GPIO 5
  ECHO  → ESP32 GPIO 18 (direct, no level shifter)
  ```
- **Placement:** Mounted on front, ~1 cm above ground, facing forward

**Distance Calculation:**
```
distance (cm) = pulseIn(ECHO) × 0.034 / 2
```

**Our Implementation:**
- 5-reading median filter to eliminate outliers
- `pulseIn()` timeout: 25000 μs (prevents hang)
- Returns 999 if distance invalid (= clear path)
- Flush sequence: 5 dummy readings after bypass maneuver

---

### TCRT5000 Dual-Channel IR Line Sensor
- **Type:** Dual reflective IR sensor (2 channels independent)
- **Operating Voltage:** 3.3–5V
- **Analog Output:** 0–5V (0 = dark, 5 = bright)
- **Detection Range:** 1–8 mm (optimal ~3 mm)
- **Frequency:** 38 kHz modulation
- **Hysteresis:** ~50 mV
- **Pinout:**
  ```
  VCC     → L298N 5V output
  GND     → Common GND bus
  OUT A   → ESP32 GPIO 35 (ADC0)
  OUT B   → (not used in Phase 3)
  ```
- **Placement:** Mounted on underside, ~5 mm above ground, centered on chassis

**Calibration (Our Rover):**
- Black tape/line: ~100 (reflectance low)
- White floor: ~4095 (reflectance high)
- Detection threshold: 2500 (midpoint)
- Logic: `if (lineValue > 2500) → moveForward` else `→ stop`

**Note:** TCRT values inverted compared to typical sensors (higher value = brighter = white surface)

---

### SG90 Micro Servo
- **Type:** Standard 3-wire servo (180° rotation)
- **Operating Voltage:** 3.3–6V (we use 5V from LM2596)
- **Operating Speed:** 0.1 s/60° @ 5V
- **Torque:** 1.8 kg·cm @ 5V
- **Dimensions:** 32 × 11 × 24 mm
- **Pinout:**
  ```
  Brown (GND)    → Common GND bus
  Red (VCC)      → LM2596 5V output
  Orange (PWM)   → ESP32 GPIO 32
  ```
- **Pulse Width:** 1 ms (0°) to 2 ms (180°)
- **Frequency:** 50 Hz (PWM period 20 ms)

**Placement:** Mounted on front left side, rotates HC-SR04 sensor ±90° for obstacle scanning

---

### KY-008 Laser Module (650 nm)
- **Type:** 650 nm red laser diode
- **Operating Voltage:** 5V DC
- **Current:** ~20–30 mA
- **Laser Class:** IIIa (< 5 mW)
- **Wavelength:** 650 nm ±10 nm
- **Beam Divergence:** ~15°
- **Pinout:**
  ```
  (+) Red    → Relay NO (normally open)
  (−) Black  → L298N 5V GND
  ```
- **Safety:** Direct eye exposure at < 30 cm can cause discomfort; wear eye protection during testing

**Activation:** Relay-controlled via RPi GPIO 17; fires for 0.5 s per dashboard button press

---

## 4. Power Management

### Battery Pack 1 (Motor + Main Logic Power)
- **Specification:** 2× 18650 Lithium-Ion (5000 mAh, 3.7V each in series)
- **Configuration:** 2S (series) = 7.4V nominal (7.2–8.4V range)
- **Capacity:** 5000 mAh
- **Max Discharge:** 20 A (continuous), 40 A (burst)
- **Charging:** TP4056 USB-C TP charger module (not shown in wiring; external component)
- **Protection:** Integrated BMS (battery management system) or discrete low-voltage cutoff

**Load Distribution:**
- **Motor Power (L298N 12V in):** ~2 A (peak, both sides under load)
- **Logic Power (L298N 5V out):** ~365 mA total (ESP32, HC-SR04, Relay, KY-008 standby)

---

### Battery Pack 2 (RPi 5 + Servo Power)
- **Specification:** 2× 18650 Lithium-Ion (3200 mAh, 3.7V each in series)
- **Configuration:** 2S (series) = 7.4V nominal
- **Capacity:** 3200 mAh
- **Max Discharge:** 15 A (continuous)
- **Charging:** External USB-C TP charger (not integrated)

**Load Distribution:**
- **RPi 5 (LM2596 → 5.1V out):** ~2.5 A typical (YOLOv5 inference heavy load, ~8W)
- **SG90 Servo:** ~100–300 mA (peak during sweep)

**Advantages of separate battery:**
- Isolates noisy motor current from RPi power rail
- Prevents brownout during servo pulse
- Allows independent charging/monitoring

---

### DC-DC Converter: LM2596
- **Type:** Synchronous buck converter (step-down)
- **Input Voltage Range:** 5–36V
- **Output Voltage:** 1.25–35V (adjustable via feedback divider)
- **Output Current:** 3 A (continuous)
- **Switching Frequency:** 150 kHz
- **Efficiency:** 92% @ 12V → 5V, 2 A
- **Dimensions:** 40 × 20 × 13 mm (DIP module with potentiometer)

**Configuration (Our Rover):**
- **Input:** Battery Pack 2 (+7.4V, −GND)
- **Output:** Adjusted to 5.1V (via onboard potentiometer)
- **Load:** RPi 5 USB-C PD input (requires clean 5.1V)

**Adjustment Procedure:**
- Measure output voltage using multimeter
- Rotate potentiometer clockwise to increase voltage
- Target: 5.1V ±0.1V (safe for USB-C PD)
- Scope verification recommended to confirm ripple < 100 mV

---

### Rocker Switches
- **Switch 1 (Motors):** 12V battery → L298N input
- **Switch 2 (RPi):** 7.4V battery → LM2596 input
- **Type:** SPST (single-pole single-throw), rated 10 A @ 250V AC
- **Mounting:** Chassis side panel, accessible during operation

---

## 5. Additional Components

### Relay Module (Single-Channel, 5V Coil)
- **Type:** Electromagnetic relay (normally open)
- **Coil Voltage:** 5V DC
- **Coil Current:** ~70 mA
- **Contact Rating:** 10 A @ 30V DC (typical)
- **Pinout:**
  ```
  IN   → RPi GPIO 17
  COM  → L298N 5V output
  NO   → KY-008 laser anode
  GND  → Common GND
  ```
- **Function:** Switch laser ON/OFF from RPi GPIO (isolated signal)

---

### CSI Camera Adapter (Wonrabai 22-pin → 15-pin)
- **Compatibility:** RPi Camera Module v1 (OV5647, 22-pin) → RPi 5 Camera 1 port (15-pin)
- **Cable Type:** FPC (Flexible Printed Circuit) ribbon
- **Pin Mapping:** D0–D7 (data), MIPI CLK, synchronization signals
- **Integrity Check:** Ribbon must lie flat in connector; inspect for creasing

---

### Camera: OV5647 Rev 1.3
- **Sensor:** 1/4" CMOS
- **Resolution:** 2592 × 1944 pixels (5 MP still), 640 × 480 @ 90 FPS video
- **Focal Length:** Fixed focus (~∞)
- **Field of View (FOV):** ~54° horizontal
- **Operating Voltage:** 2.6–3.1V (via adapter power pins)
- **Interface:** MIPI CSI (Camera Serial Interface)
- **Library Support:** `picamera2` (Python), OpenCV (with limitations on RPi 5)

**Mounting:** Hot-glued to rover chassis, facing forward at ~45° downward angle for crop/weed detection

---

## 6. Summary Table

| Component | Qty | Voltage | Current | Power | Notes |
|-----------|-----|---------|---------|-------|-------|
| ESP32 DevKit V1 | 1 | 5V | 80 mA | 0.4 W | Via L298N 5V |
| RPi 5 | 1 | 5.1V | 2.5 A | 12.75 W | Via LM2596, heavy during inference |
| TT Motor | 4 | 12V | 1 A (ea.) | 12 W | Via L298N output |
| L298N | 1 | 12V in, 5V logic | 2 A (motors) | 24 W | Heat dissipation passive |
| HC-SR04 | 1 | 5V | 15 mA | 0.075 W | Peak during echo |
| TCRT5000 | 1 | 5V | 10 mA | 0.05 W | Constant draw |
| SG90 Servo | 1 | 5V | 0.3 A (peak) | 1.5 W | From separate LM2596 |
| KY-008 Laser | 1 | 5V | 25 mA | 0.125 W | Via relay, intermittent |
| Relay Module | 1 | 5V coil | 70 mA | 0.35 W | Coil only |
| **Total System** | — | — | **~4 A peak** | **~50 W** | Motors + RPi simultaneous |

---

## 7. Environmental Specifications

- **Operating Temperature:** 0–40°C (recommended), −10–60°C (absolute)
- **Humidity:** 10–90% RH (non-condensing)
- **Terrain:** Flat to gently sloped crop rows (< 15° gradient)
- **Ground Clearance:** ~40 mm (chassis height)
- **Wheelbase:** 85 mm (front to rear)
- **Track Width:** 65 mm (left to right wheel center)
- **Total Weight (estimated):** ~1.2 kg (frame + batteries + electronics)
- **Motor Efficiency Degradation:** ~10% per 10°C below 25°C

---

## 8. Design Rationale

**ESP32 vs Arduino:**
- WiFi capability for future telemetry
- More GPIO (needed for servo + line sensor simultaneously)
- Dual-core allows background tasks
- Cost-effective (~$5–8 vs Arduino ~$20)

**RPi 5 for ML:**
- Sufficient GPU acceleration for YOLOv5 (Broadcom VideoCore VII)
- 8GB RAM handles model + live video buffer
- Gigabit Ethernet for stable data logging
- Native Python/TensorFlow/PyTorch support

**Separate Batteries:**
- Motor battery: high-current spikes (motors) not affecting RPi logic
- RPi battery: isolated power rail → stable inference
- Parallel charging possible; independent replacement

**LM2596 over AMS1117:**
- AMS1117 produces excessive heat @ 2.5 A (7.4V→5V drop = 6 W dissipation)
- LM2596 switching design: 92% efficient, minimal thermal output
- Enables sustained RPi operation during 30+ minute field trials

---

## Appendix: Electrical Margins

**Voltage Safety:**
- ESP32 GPIO inputs: rated 3.3V max, but 5V tolerant with pull-downs
- L298N logic: strictly 5V, 3.3V acceptable but may cause marginal switching
- All signal lines use 22 AWG silicone (< 0.1Ω/m) to minimize voltage drop

**Current Budget (Worst Case):**
- Motors: 2 A (both sides, max PWM 220)
- RPi: 2.5 A (YOLOv5 + WiFi active)
- Sensors: 0.5 A combined (HC, TCRT, relay, laser)
- **Total:** ~5 A sustained (within 18650 20 A rating)

**Thermal Design:**
- L298N: 24 W dissipation @ 2 A per side; 30°C rise above ambient without heatsink (acceptable)
- LM2596: 0.6 W dissipation @ 2.5 A; negligible temperature rise
- Chassis: passive convection sufficient (no fans required)

---

## Future Upgrades

1. **Solar trickle-charger** on rover back panel (small 0.5 W panel)
2. **IMU (MPU6050)** for autonomous row-following refinement
3. **Dual servo scanning** (left + right HC-SR04) for better mapping
4. **4G/LTE modem** for remote operation
5. **Improved line sensor** → dual TCRT with analog calibration per row

---

**Document Version:** 1.0  
**Last Updated:** May 1, 2026  
**Author:** Abhi (Indus University ME0636)

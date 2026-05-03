# Wiring Guide — Autonomous Agriculture Rover

## Quick Reference: Pin Mapping

### ESP32 DevKit V1
```
GPIO 2    (D2)   — Reserved (boot mode select, SPI)
GPIO 4    (D4)   — UART2 RX (attempted RPi comms, not used)
GPIO 5    (D5)   — HC-SR04 TRIG
GPIO 12   (D12)  — L298N ENB (PWM, right motor speed)
GPIO 14   (D14)  — L298N ENA (PWM, left motor speed)
GPIO 15   (D15)  — Reserved (boot strapping)
GPIO 16   (D16)  — UART2 TX
GPIO 18   (D18)  — HC-SR04 ECHO (direct input, no level shifter)
GPIO 25   (D25)  — L298N IN3 (right motor fwd)
GPIO 26   (D26)  — L298N IN2 (left motor rev)
GPIO 27   (D27)  — L298N IN1 (left motor fwd)
GPIO 32   (D32)  — SG90 servo PWM (moved from GPIO 13 due to boot conflict)
GPIO 33   (D33)  — L298N IN4 (right motor rev)
GPIO 35   (D35)  — TCRT5000 analog line sensor (ADC0, input-only)

GND       (GND)  — Common ground bus (shared with all components)
VIN       (VIN)  — 5V input from L298N logic supply
3V3       (3V3)  — 3.3V rail (internal, not used for external loads)
```

### Raspberry Pi 5 (40-pin header, viewed from above)
```
Pin  1 → 3.3V        Pin  2 → 5V
Pin  3 → GPIO 2      Pin  4 → 5V
Pin  5 → GPIO 3      Pin  6 → GND
Pin  7 → GPIO 4      Pin  8 → GPIO 14 (UART TX, attempted)
Pin  9 → GND         Pin 10 → GPIO 15 (UART RX, attempted)
Pin 11 → GPIO 17 ⭐   Pin 12 → GPIO 18
Pin 13 → GPIO 27     Pin 14 → GND
Pin 15 → GPIO 22     Pin 16 → GPIO 23
Pin 17 → 3.3V        Pin 18 → GPIO 24
Pin 19 → GPIO 10     Pin 20 → GND
Pin 21 → GPIO 9      Pin 22 → GPIO 25
Pin 23 → GPIO 11     Pin 24 → GPIO 8
Pin 25 → GND         Pin 26 → GPIO 7
Pin 27 → GPIO 0      Pin 28 → GPIO 1
Pin 29 → GPIO 5      Pin 30 → GND
Pin 31 → GPIO 6      Pin 32 → GPIO 12
Pin 33 → GPIO 13     Pin 34 → GND
Pin 35 → GPIO 19     Pin 36 → GPIO 16
Pin 37 → GPIO 26     Pin 38 → GPIO 20
Pin 39 → GND         Pin 40 → GPIO 21

⭐ GPIO 17 (Pin 11) = Relay control (laser firing)
```

---

## Main Power Distribution

```
┌─────────────────────────────────────────────────────────┐
│                      BATTERY PACK 1                     │
│              2× 18650 5000mAh (7.4V series)            │
│                                                         │
│  [+] ←─── Rocker Switch 1 (disconnect point)           │
│   │                                                     │
│   └─→ L298N 12V input (motor power)                     │
│       L298N GND ←─ [−] battery                         │
│                                                         │
│  L298N outputs:                                         │
│  ├─ 5V logic supply (to ESP32 VIN)                     │
│  ├─ GND (main common ground)                            │
│  ├─ OUT1/OUT2 → Left motors (TT)                       │
│  └─ OUT3/OUT4 → Right motors (TT)                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                      BATTERY PACK 2                     │
│              2× 18650 3200mAh (7.4V series)            │
│                                                         │
│  [+] ←─── Rocker Switch 2 (disconnect point)           │
│   │                                                     │
│   └─→ LM2596 input (buck converter)                     │
│       LM2596 GND ←─ [−] battery                        │
│                                                         │
│  LM2596 output: 5.1V ±0.1V                             │
│  ├─→ RPi 5 USB-C PD input                              │
│  ├─→ SG90 servo red (VCC)                              │
│  └─→ Common GND bus (shared)                            │
└─────────────────────────────────────────────────────────┘

COMMON GND BUS (single point soldered connection):
  • L298N GND wire (main trunk)
  • ESP32 GND (soldered to L298N trunk)
  • HC-SR04 GND (soldered to trunk)
  • SG90 servo brown (GND)
  • TCRT5000 GND (soldered to trunk)
  • Relay GND (soldered to trunk)
  • RPi 5 Pin 6 / Pin 9 / Pin 14 / Pin 20 / Pin 25 / Pin 30 / Pin 39 (all same node)
  • LM2596 OUT− (soldered to trunk)

[Electrical tape wrapped around GND joint to prevent shorts]
```

---

## Signal Wiring: ESP32 ↔ Peripherals

### Motor Control (ESP32 → L298N)
```
ESP32 Pin 27 (GPIO 27) ──22AWG──→ L298N IN1  (left motor forward)
ESP32 Pin 26 (GPIO 26) ──22AWG──→ L298N IN2  (left motor reverse)
ESP32 Pin 25 (GPIO 25) ──22AWG──→ L298N IN3  (right motor forward)
ESP32 Pin 33 (GPIO 33) ──22AWG──→ L298N IN4  (right motor reverse)

ESP32 Pin 14 (GPIO 14) ──22AWG──→ L298N ENA  (left motor PWM speed)
ESP32 Pin 12 (GPIO 12) ──22AWG──→ L298N ENB  (right motor PWM speed)

[Cross-chassis wiring: routed along bottom frame edge, secured with zip ties]
```

### Motor Power Output (L298N → Motors)
```
L298N OUT1 ──20AWG (twisted)──→ Left front motor (red → +12V, black → GND)
L298N OUT2 ──20AWG (twisted)──→ Left rear motor  (red → +12V, black → GND)
L298N OUT3 ──20AWG (twisted)──→ Right front motor (red → +12V, black → GND)
L298N OUT4 ──20AWG (twisted)──→ Right rear motor (red → +12V, black → GND)

[Twisted pair for noise immunity; crimped connectors to motor terminals]
```

### Ultrasonic Sensor (HC-SR04)
```
HC-SR04 VCC   ──22AWG──→ L298N 5V output
HC-SR04 GND   ──22AWG──→ Common GND bus
HC-SR04 TRIG  ──22AWG──→ ESP32 Pin 5 (GPIO 5)
HC-SR04 ECHO  ──22AWG──→ ESP32 Pin 18 (GPIO 18) [direct, no level shifter]

[Notes]
• ECHO signal is 5V output from HC-SR04
• ESP32 GPIO 18 is 5V tolerant (safe without level shifter)
• Mount sensor on front chassis, ~1 cm above ground
• Ensure IR cone faces unobstructed forward direction
```

### Line Sensor (TCRT5000)
```
TCRT5000 VCC  ──22AWG──→ L298N 5V output
TCRT5000 GND  ──22AWG──→ Common GND bus
TCRT5000 OUT  ──22AWG──→ ESP32 Pin 35 (GPIO 35 / ADC0)

[Notes]
• GPIO 35 is input-only (cannot drive outputs)
• Mount on chassis underside, ~5 mm above ground
• Ensure both IR LED and phototransistor face downward
• Sensor placement: center of chassis (equidistant between wheels)
• Typical readings: black tape ~100, white floor ~4095
```

### Servo Motor (SG90)
```
SG90 Brown (GND)   ──22AWG──→ Common GND bus
SG90 Red (VCC)     ──22AWG──→ LM2596 5V output
SG90 Orange (PWM)  ──22AWG──→ ESP32 Pin 32 (GPIO 32)

[Critical!]
• Original GPIO 13 causes boot mode conflict (servo stuck at random angle)
• MUST use GPIO 32 (or 25, 26, 27 if available)
• Servo attach() MUST be called BEFORE ledcAttach() to avoid PWM conflicts
• Mount on chassis front-left, horn pointing upward
• Attach HC-SR04 to servo horn via hot glue or zip tie
• Test rotation range: should sweep 0–180° smoothly
```

### Laser Module (KY-008)
```
KY-008 Red (+5V)   ──22AWG──→ Relay NO (normally open contact)
KY-008 Black (GND) ──22AWG──→ L298N 5V GND

Relay Wiring:
  Relay IN    ──22AWG──→ RPi GPIO 17 (Pin 11)
  Relay COM   ──22AWG──→ L298N 5V output
  Relay NO    ──22AWG──→ KY-008 red wire
  Relay GND   ──22AWG──→ Common GND bus

[Safety Notes]
• Laser is 650 nm, ~5 mW (IIIa class)
• Do NOT stare into beam; wear safety glasses during testing
• Mount on chassis front, angled to intersect detection area (~20 cm ahead)
• Relay adds isolation: RPi GPIO cannot directly source 25 mA
```

---

## RPi 5 to ESP32 Communication (ATTEMPTED, NOT USED)

### UART Connection (Debugging Only)
```
[This connection was attempted but failed due to voltage/timing issues]

RPi Pin 8 (GPIO 14 TX)  ──22AWG──→ ESP32 GPIO 4 (RX)
RPi Pin 10 (GPIO 15 RX) ──22AWG──→ ESP32 GPIO 2 (TX)
RPi Pin 6 (GND)         ──22AWG──→ ESP32 GND

Tested configurations:
  • /dev/ttyAMA0 @ 115200 baud (primary UART)
  • /dev/ttyAMA1 @ 115200 baud (attempted alternate)
  • Swapped RX/TX pins (no effect)
  • Continuity verified with multimeter (OK)
  • Oscilloscope: no visible UART clock/data signals

[Troubleshooting Steps Performed]
1. Enabled serial port via raspi-config (Port & Console enabled)
2. Disabled Bluetooth (frees ttyAMA0)
3. Verified ESP32 UART code: Serial2.begin(115200, SERIAL_8N1, 4, 2) ✗
4. Checked /boot/config.txt for conflicts (none found)
5. Tested with loopback cable (fails — suggests hardware issue on RPi)
6. Alternative: RPi → USB serial → ESP32 (not explored)

[Conclusion] UART communication abandoned in favor of motion strategy:
  • Rovers operate at low fixed speed (PWM 80)
  • Laser fires manually via web dashboard button
  • No autonomous motor stop on detection needed
```

### GPIO Signal Control (ATTEMPTED, NOT USED)
```
[Attempted to pulse ESP32 GPIO from RPi for motor control]

RPi GPIO 17 (Pin 11) ──22AWG──→ ESP32 GPIO 13 (RX-only during boot)
                                 or GPIO 15, 19 (attempted alternatives)

[Issue] Voltage measured: -0.11V (floating); no switching observed
[Reason] RPi GPIO outputs 3.3V, but ESP32 on different power domain
         No common reference voltage without UART GND connection working first

[Resolution] Not pursued further; low-speed strategy used instead
```

---

## RPi 5 to External Peripherals

### Camera (CSI/Camera Serial Interface)
```
RPi Camera Port 1 (15-pin CSI, labeled "CAM0" on silkscreen)
  ├─ Data lines: D0–D7 (MIPI CSI format)
  ├─ Clock: MIPI CLK
  ├─ Sync: HS, VS
  └─ Power: +1.8V, +3.3V (integrated, no external supply needed)

[Connection]
  OV5647 Camera (v1.3, 22-pin) ──Wonrabai Adapter──→ RPi CSI-1 (15-pin)
  
  Adapter Details:
    • 22-pin ribbon (from camera) crimped to 15-pin ribbon (to RPi)
    • Pin mapping: D0–D7 (data), CLK, HS, VS preserved
    • Power pins: adapter supplies regulated 3.3V to camera VCC
    • GND: common reference

[Mounting]
  • Camera board: hot-glued to rover chassis top panel
  • Ribbon: runs down inside frame to CSI-1 port
  • Orientation: 45° downward (captures crop/weed in field of view)
  • Ensure ribbon is flat in CSI-1 connector (no creases)
  • Test with: raspistill -o test.jpg (verify image captures)
```

### Relay Module (GPIO Control for Laser)
```
Relay IN  ──22AWG──→ RPi Pin 11 (GPIO 17)
Relay GND ──22AWG──→ RPi Pin 6 (GND)
Relay COM ──22AWG──→ L298N 5V (closes circuit to KY-008 when activated)
Relay NO  ──22AWG──→ KY-008 red wire

[Control Code (Python)]
  import RPi.GPIO as GPIO
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(17, GPIO.OUT)
  GPIO.output(17, GPIO.HIGH)   # Activate relay (turn on laser)
  time.sleep(0.5)              # Hold for 500ms
  GPIO.output(17, GPIO.LOW)    # Deactivate relay (turn off laser)
```

### Power Input (USB-C PD)
```
LM2596 5V output (USB-C power module, not integrated into rover)
  ├─ 5V+ (red wire) ──20AWG──→ RPi USB-C connector pin 1 (or via external USB-C power board)
  └─ GND (black wire) ──20AWG──→ RPi USB-C connector pin 5

[Notes]
• RPi 5 requires 5.1V ±0.1V at 5A minimum (for ML inference load)
• LM2596 adjustable; set output to 5.1V via onboard potentiometer screw
• Use external USB-C power adapter board (not direct soldering to RPi port)
• Verify voltage with multimeter BEFORE powering RPi
• Ripple: should be < 100 mV (scope check optional but recommended)
```

---

## Summary Wiring Table

| From | To | Wire Gauge | Length | Purpose |
|------|-----|-----------|--------|---------|
| Battery 1 (+) | Switch 1 | 20 AWG | 150 mm | Main power enable |
| Battery 1 (−) | L298N GND | 20 AWG | 150 mm | Motor return |
| L298N 5V | ESP32 VIN | 22 AWG | 100 mm | Logic supply |
| L298N GND | GND bus | 20 AWG (trunk) | — | Common ground |
| L298N OUT1/2 | Left motors | 20 AWG (twisted) | 120 mm | Motor drive |
| L298N OUT3/4 | Right motors | 20 AWG (twisted) | 120 mm | Motor drive |
| ESP32 GPIO 27 | L298N IN1 | 22 AWG | 80 mm | Left fwd control |
| ESP32 GPIO 26 | L298N IN2 | 22 AWG | 80 mm | Left rev control |
| ESP32 GPIO 25 | L298N IN3 | 22 AWG | 80 mm | Right fwd control |
| ESP32 GPIO 33 | L298N IN4 | 22 AWG | 80 mm | Right rev control |
| ESP32 GPIO 14 | L298N ENA | 22 AWG | 80 mm | Left PWM speed |
| ESP32 GPIO 12 | L298N ENB | 22 AWG | 80 mm | Right PWM speed |
| HC-SR04 VCC | L298N 5V | 22 AWG | 80 mm | Sensor supply |
| HC-SR04 TRIG | ESP32 GPIO 5 | 22 AWG | 80 mm | Distance trigger |
| HC-SR04 ECHO | ESP32 GPIO 18 | 22 AWG | 80 mm | Distance readback |
| HC-SR04 GND | GND bus | 22 AWG | — | Sensor return |
| TCRT5000 VCC | L298N 5V | 22 AWG | 80 mm | Sensor supply |
| TCRT5000 OUT | ESP32 GPIO 35 | 22 AWG | 80 mm | Line detection |
| TCRT5000 GND | GND bus | 22 AWG | — | Sensor return |
| SG90 Red | LM2596 5V | 22 AWG | 150 mm | Servo power |
| SG90 Orange | ESP32 GPIO 32 | 22 AWG | 100 mm | Servo control |
| SG90 Brown | GND bus | 22 AWG | — | Servo return |
| Relay IN | RPi GPIO 17 | 22 AWG | 200 mm | Laser switch |
| Relay COM | L298N 5V | 22 AWG | 150 mm | Laser power (when active) |
| Relay NO | KY-008 red | 22 AWG | 80 mm | Laser anode |
| KY-008 black | GND bus | 22 AWG | 80 mm | Laser return |
| Battery 2 (+) | Switch 2 | 20 AWG | 150 mm | RPi power enable |
| Battery 2 (−) | LM2596 GND | 20 AWG | 150 mm | Converter return |
| LM2596 5V out | RPi USB-C | 20 AWG | 300 mm | Main supply |
| RPi CSI-1 | Camera | FPC ribbon | Wonrabai adapter | Video input |

---

## Chassis Layout (Top View)

```
                  [SG90 servo + HC-SR04]
                           ▲
                           │
         [Camera OV5647]
              │
    ┌─────────┼────────────┐
    │         │            │
[L] │ ╔═════╩════════╗    │ [R]
    │ ║  FRAME BODY  ║    │
  [L]│ ║              ║    │[R]
    │ ║   [GND BUS]  ║    │
    │ ║  junction◆   ║    │
    │ ╚═══╤═════╤════╝    │
    │     │ [ESP32] │     │
    │     │ [L298N] │     │
    └─────┼─────────┼──────┘
         [Bat 1]  [Bat 2 + LM2596]
```

---

## Troubleshooting Checklist

### Symptom: Motors don't spin
- [ ] Check battery voltage (should be 7.2–8.4V for battery 1)
- [ ] Verify rocker switch 1 is ON
- [ ] Confirm L298N receives 12V on pin 5
- [ ] Test motor directly to battery (+ to red, − to black) — if motor spins, driver issue
- [ ] Check ESP32 GPIO 27–33 are outputting HIGH/LOW (use oscilloscope or LED test)
- [ ] Verify ESP32 VIN receives 5V from L298N logic supply

### Symptom: Distance sensor reads constantly 999 or 0
- [ ] Verify HC-SR04 receives 5V (L298N supply, not 3.3V)
- [ ] Check TRIG line goes HIGH for 10 μs only
- [ ] Oscilloscope: verify ECHO pulse present on GPIO 18
- [ ] Test sensor directly (external 5V supply) — if works, ESP32 supply issue
- [ ] Increase `pulseIn()` timeout from 25000 to 30000 μs if marginal
- [ ] Ensure sensor is < 4 m from obstacles (outside range = 0)

### Symptom: Servo doesn't move
- [ ] Verify servo receives 5V from LM2596 output (check potentiometer adjustment)
- [ ] Confirm GPIO 32 outputs PWM (1–2 ms pulses at 50 Hz)
- [ ] Test servo directly with external PWM source (e.g., hobby servo tester)
- [ ] Check servo attach() is called BEFORE ledcAttach() in setup()
- [ ] Remove servo and check if it's mechanically stuck (try manual rotation)

### Symptom: ESP32 won't upload code
- [ ] Verify CP2102 driver installed (Device Manager → Silicon Labs)
- [ ] Confirm board selected: ESP32 DevKit V1, COM port correct
- [ ] Press and hold BOOT button during upload, release when "Writing..." appears
- [ ] Check USB cable is data cable (not charge-only)
- [ ] Try different USB port on computer

### Symptom: RPi camera shows black/blank image
- [ ] Verify CSI ribbon is fully inserted (should seat with firm click)
- [ ] Check adapter pinout matches camera (22 pins in, 15 pins out)
- [ ] Run `libcamera-hello` to test camera hardware
- [ ] Confirm camera is enabled in raspi-config
- [ ] Inspect ribbon for creases or damage

### Symptom: Laser doesn't fire (no light)
- [ ] Verify RPi GPIO 17 outputs HIGH (use multimeter or LED test)
- [ ] Test relay coil directly with 5V supply
- [ ] Check relay contacts continuity with multimeter (should be <1Ω when activated)
- [ ] Verify KY-008 laser receives 5V (measured at anode/cathode)
- [ ] Test laser directly with external 5V (if lights, relay issue; if not, laser failed)

### Symptom: RPi 5 shuts down during YOLOv5 inference
- [ ] Verify LM2596 output is 5.1V ±0.1V (adjust potentiometer if needed)
- [ ] Check power draw: 2.5 A @ 5.1V should not trigger USB PD cutoff
- [ ] Use external USB-C power supply instead of onboard USB port
- [ ] Disable WiFi during inference (`nmcli radio wifi off`) to reduce load

---

## Cable Labeling Recommendations

Use heat-shrink labels or solder bridges marked with tape:

- **RED → 5V power rail**
- **BLACK → GND**
- **YELLOW → Motor control signals**
- **ORANGE → Sensor signals**
- **BLUE → PWM speed control**
- **GREEN → Servo/special functions**

---

## Crimping & Soldering Standards

**All signal lines (22 AWG):**
- Solder directly to component pins (if not using header connectors)
- No crimp connectors (too unreliable for 22 AWG)
- Use solder sucker / desoldering braid for rework

**All power lines (20 AWG):**
- Crimp connectors (spade or ring terminal) or solder
- If soldering, use 60W+ iron (heat mass required for 20 AWG)
- Ensure solder joint is shiny, smooth (not dull or blobby)

**GND bus (main junction):**
- Single point soldered connection (reduces loop inductance)
- Use 20 AWG wire as trunk; smaller wires soldered to trunk
- Wrap with electrical tape for insulation

---

**Document Version:** 1.0  
**Last Updated:** May 1, 2026  
**Author:** Abhi (Indus University ME0636)

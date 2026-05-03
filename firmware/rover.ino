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
const int TURN_DELAY = 1200;  // ms for 90-degree turn
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
  for (int i = 0; i < 5; i++) {
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
    for (int i = 0; i < 5; i++) {
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

// Distance sensor
int getDistance() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  // Timeout 25 ms = 4.25 m max
  long duration = pulseIn(ECHO, HIGH, 25000);

  if (duration == 0) return 999; // No valid reading

  int distance = duration * 0.034 / 2;
  return (distance > 400) ? 999 : distance;
}

// 5-reading median filter
int getDistanceFiltered() {
  int readings[5];
  for (int i = 0; i < 5; i++) {
    readings[i] = getDistance();
    delay(10);
  }

  for (int i = 0; i < 4; i++) {
    for (int j = i + 1; j < 5; j++) {
      if (readings[i] > readings[j]) {
        int temp = readings[i];
        readings[i] = readings[j];
        readings[j] = temp;
      }
    }
  }

  return readings[2];
}

// Servo scanning
int scanServoDist(int angle) {
  servo.write(angle);
  delay(500);
  return getDistanceFiltered();
}

// Motor control
void moveForward(int speed) {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  ledcWrite(ENA, speed);
  ledcWrite(ENB, speed);
}

void moveBackward(int speed) {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  ledcWrite(ENA, speed);
  ledcWrite(ENB, speed);
}

void turnLeft(int speed) {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  ledcWrite(ENA, speed);
  ledcWrite(ENB, speed);
}

void turnRight(int speed) {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
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

// Obstacle bypass
void bypassObstacle(bool go_left) {
  bypassing = true;

  if (go_left) {
    // Bypass left: R90 -> forward -> L90 -> forward -> L90 -> forward -> R90
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
    // Bypass right: L90 -> forward -> R90 -> forward -> R90 -> forward -> L90
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

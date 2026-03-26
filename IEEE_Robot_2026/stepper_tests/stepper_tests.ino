#include <Wire.h>
#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>

// PI - Arduino Communication
#define SHOVEL 13    // Orange 11
#define ACTUATORS 5  // Brown-White 23
#define ARMS A2      // Green 25
#define BUSY 6       // Brown, PI 24
bool busy = false;
#define START 10  // Orange-white 8

// Actuators
#define RELAY_PIN_UP 9
#define RELAY_PIN_DOWN 8
bool actuatorsUp;

//Stepper Motors
#define ENA_1 7
#define DIR_1 3
#define STEP_1 4

#define LIMIT_SWITCH 2
bool limitTrigger = false;

int shovelPosition = 0;

// Servos
Adafruit_PWMServoDriver servos = Adafruit_PWMServoDriver();
#define SERVOMIN 110  // about 0 degrees
#define SERVOMAX 500  // about 180 degrees
#define SERVO_FREQ 50
#define LEFT_SERVO 3
#define RIGHT_SERVO 2
bool servosIn;

// Start Light Sensor
#define PHOTOCELL_F A0
#define PHOTOCELL_B A1
#define TELL_PI 12
int frontReading;
int backReading;
bool start = false;

void setup() {
  Serial.begin(115200);

  // Setup Pi - Arduino Communication
  pinMode(SHOVEL, INPUT);
  pinMode(ACTUATORS, INPUT);
  pinMode(ARMS, INPUT);
  pinMode(BUSY, OUTPUT);
  digitalWrite(BUSY, HIGH);
  pinMode(START, INPUT);

  // Setup Start LED
  pinMode(PHOTOCELL_F, INPUT);
  pinMode(PHOTOCELL_B, INPUT);
  pinMode(TELL_PI, OUTPUT);
  digitalWrite(TELL_PI, LOW);

  // Setup Actuators
  pinMode(RELAY_PIN_UP, OUTPUT);
  digitalWrite(RELAY_PIN_UP, LOW);
  pinMode(RELAY_PIN_DOWN, OUTPUT);
  digitalWrite(RELAY_PIN_DOWN, LOW);  // actuators off

  // Setup Stepper Motor
  pinMode(ENA_1, OUTPUT);
  pinMode(DIR_1, OUTPUT);
  pinMode(STEP_1, OUTPUT);
  digitalWrite(ENA_1, LOW);
  pinMode(LIMIT_SWITCH, INPUT_PULLUP);

  // Setup Servos
  servos.begin();
  servos.setPWMFreq(SERVO_FREQ);
  servos.setPWM(RIGHT_SERVO, 0, SERVOMIN);
  servos.setPWM(LEFT_SERVO, 0, SERVOMAX);

  // TESTING
  //turnServos(0);
  //actuators(0);
  //returnShovel();
}

void loop() {
  // TESTING
  // Serial.print(digitalRead(SHOVEL));
  // Serial.print(" , ");
  // Serial.print(digitalRead(ACTUATORS));
  // Serial.print(" , ");
  // Serial.print(digitalRead(ARMS));
  // Serial.print(" , ");
  // Serial.println(digitalRead(START));

  // if (!start) {
  //   start = startLED();
  // }

  if (!digitalRead(SHOVEL)) {
    if (!busy && !servosIn) {
      shovel(1);  // UP
    }
  } else {
    if (!busy && !servosIn) {
      shovel(0);  // DOWN
    }
  }

  if (digitalRead(ACTUATORS)) {
    if (!busy && servosIn) {
      actuators(0);  // DOWN
    }
  } else {
    if (!busy) {
      actuators(1);  // UP
    }
  }

  if (digitalRead(ARMS)) {
    if (!busy) {
      turnServos(0);
    }
  } else {
    if (!busy) {
      turnServos(1);
    }
  }
}

void shovel(int direction) {
  digitalWrite(BUSY, HIGH);
  busy = true;
  if (direction == 0) {  // move down
    digitalWrite(DIR_1, LOW);
    Serial.println("going down");
    while (digitalRead(LIMIT_SWITCH)) {
      digitalWrite(STEP_1, HIGH);
      delay(1);
      digitalWrite(STEP_1, LOW);
      delay(1);
    }
    shovelPosition = 0;
  } else if (direction == 1) {  // move up
    digitalWrite(DIR_1, HIGH);
    Serial.println("going up");
    for (int i = 0; i < 3300; i++) {
      if (shovelPosition > 3300) {
        break;
      }
      digitalWrite(STEP_1, HIGH);
      delay(1);
      digitalWrite(STEP_1, LOW);
      delay(1);
      shovelPosition++;
    }
  }
  digitalWrite(BUSY, LOW);
  busy = false;
}

void actuators(int setting) {
  digitalWrite(BUSY, HIGH);
  busy = true;
  if (setting == 0x00) {  // DOWN
    actuatorsUp = false;
    digitalWrite(RELAY_PIN_UP, HIGH);
    digitalWrite(RELAY_PIN_DOWN, LOW);
    delay(10000);
    digitalWrite(RELAY_PIN_UP, LOW);
    digitalWrite(RELAY_PIN_DOWN, LOW);
  } else if (setting == 0x01) {  // UP
    actuatorsUp = true;
    digitalWrite(RELAY_PIN_UP, LOW);
    digitalWrite(RELAY_PIN_DOWN, HIGH);
    delay(10000);
    digitalWrite(RELAY_PIN_UP, LOW);
    digitalWrite(RELAY_PIN_DOWN, LOW);
  }
  digitalWrite(BUSY, LOW);
  busy = false;
}

void turnServos(int direction) {
  digitalWrite(BUSY, HIGH);
  busy = true;
  if (direction == 0) {  // IN
    servosIn = true;
    servos.setPWM(RIGHT_SERVO, 0, SERVOMIN);
    servos.setPWM(LEFT_SERVO, 0, SERVOMAX);
  } else if (direction == 1) {  // OUT
    servosIn = false;
    servos.setPWM(RIGHT_SERVO, 0, (SERVOMAX - 200));
    servos.setPWM(LEFT_SERVO, 0, (SERVOMIN + 200));
  }
  digitalWrite(BUSY, LOW);
  busy = false;
}

bool startLED() {
  bool trigger = false;
  frontReading = analogRead(PHOTOCELL_F);
  backReading = analogRead(PHOTOCELL_B);
  if (backReading - frontReading >= 200) {
    trigger = true;
    digitalWrite(TELL_PI, HIGH);
  }
  return trigger;
}
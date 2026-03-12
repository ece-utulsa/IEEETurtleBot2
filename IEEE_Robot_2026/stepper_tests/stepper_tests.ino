// =============================
// Actuator motor control pins
// =============================

// Actuator 1 pins
#define A1_IN1 7
#define A1_IN2 8

// Actuator 2 pins
#define A2_IN1 9
#define A2_IN2 10

// =============================
// Limit switch pins
// =============================
// Using INPUT_PULLUP:
// NOT pressed = HIGH
// Pressed     = LOW

#define A1_UP_LIMIT 2
#define A1_DOWN_LIMIT 3
#define A2_UP_LIMIT 4
#define A2_DOWN_LIMIT 5

// Direction tracking
int currentDirection = -1;
//  1 = up
//  0 = down
// -1 = stopped

void setup() {
  pinMode(A1_IN1, OUTPUT);
  pinMode(A1_IN2, OUTPUT);
  pinMode(A2_IN1, OUTPUT);
  pinMode(A2_IN2, OUTPUT);

  pinMode(A1_UP_LIMIT, INPUT_PULLUP);
  pinMode(A1_DOWN_LIMIT, INPUT_PULLUP);
  pinMode(A2_UP_LIMIT, INPUT_PULLUP);
  pinMode(A2_DOWN_LIMIT, INPUT_PULLUP);

  stopActuators();

  Serial.begin(9600);
  Serial.println("Type 1 = UP, 0 = DOWN, s = STOP");
}

void loop() {
  checkLimitsWhileRunning();

  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == '1') {
      moveActuators(1);
    } else if (cmd == '0') {
      moveActuators(0);
    } else if (cmd == 's' || cmd == 'S') {
      stopActuators();
      Serial.println("Manual STOP");
    }
  }
}

void moveActuators(int direction) {
  if (direction == 1) {
    if (digitalRead(A1_UP_LIMIT) == LOW || digitalRead(A2_UP_LIMIT) == LOW) {
      stopActuators();
      Serial.println("Upper limit reached - cannot move UP");
      return;
    }

    digitalWrite(A1_IN1, HIGH);
    digitalWrite(A1_IN2, LOW);

    digitalWrite(A2_IN1, HIGH);
    digitalWrite(A2_IN2, LOW);

    currentDirection = 1;
    Serial.println("Moving UP");
  } else if (direction == 0) {
    if (digitalRead(A1_DOWN_LIMIT) == LOW || digitalRead(A2_DOWN_LIMIT) == LOW) {
      stopActuators();
      Serial.println("Lower limit reached - cannot move DOWN");
      return;
    }

    digitalWrite(A1_IN1, LOW);
    digitalWrite(A1_IN2, HIGH);

    digitalWrite(A2_IN1, LOW);
    digitalWrite(A2_IN2, HIGH);

    currentDirection = 0;
    Serial.println("Moving DOWN");
  }
}

void checkLimitsWhileRunning() {
  if (currentDirection == 1 && (digitalRead(A1_UP_LIMIT) == LOW || digitalRead(A2_UP_LIMIT) == LOW)) {
    stopActuators();
    Serial.println("Stopped: upper limit switch triggered");
  }

  if (currentDirection == 0 && (digitalRead(A1_DOWN_LIMIT) == LOW || digitalRead(A2_DOWN_LIMIT) == LOW)) {
    stopActuators();
    Serial.println("Stopped: lower limit switch triggered");
  }
}

void stopActuators() {
  digitalWrite(A1_IN1, LOW);
  digitalWrite(A1_IN2, LOW);

  digitalWrite(A2_IN1, LOW);
  digitalWrite(A2_IN2, LOW);

  currentDirection = -1;
}
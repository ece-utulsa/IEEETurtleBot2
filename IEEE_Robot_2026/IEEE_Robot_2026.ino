#include <Wire.h>
#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>
#include <SPI.h>

// SPI Communication
#define MESSAGE_LENGTH 3

const byte BUF_SIZE = 16;           // max message size you expect
volatile byte rx_buffer[BUF_SIZE];  // incoming from Pi
volatile byte tx_buffer[BUF_SIZE];  // what we'll send back
volatile byte command_buffer[BUF_SIZE];
volatile byte rx_index = 0;
volatile bool message_complete = false;

// Actuators
#define RELAY_PIN_UP 9
#define RELAY_PIN_DOWN 8

//Stepper Motors
#define ENA_1 7
#define DIR_1 3
#define STEP_1 4

#define LIMIT_SWITCH 2
bool limitTrigger = false;

// Servos
Adafruit_PWMServoDriver servos = Adafruit_PWMServoDriver();
#define SERVOMIN 110  // about 0 degrees
#define SERVOMAX 500  // about 180 degrees
#define SERVO_FREQ 50

// Start Light Sensor
#define PHOTOCELL_F A0
#define PHOTOCELL_B A1
#define LED 12
int frontReading;
int backReading;
bool start = false;

// Debouncing
#define DEBOUNCE_DELAY 100
unsigned long lastDebounceTime = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("starting");
  pinMode(MISO, OUTPUT);
  SPCR |= _BV(SPE);       // enable SPI slave
  SPI.attachInterrupt();  // use interrupt

  pinMode(13, INPUT_PULLUP);
  // Setup Start LED
  pinMode(PHOTOCELL_F, INPUT);
  pinMode(PHOTOCELL_B, INPUT);
  pinMode(LED, OUTPUT);
  digitalWrite(LED, HIGH);

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
  attachInterrupt(digitalPinToInterrupt(LIMIT_SWITCH), switchInterrupt, FALLING);

  // Setup Servos
  servos.begin();
  servos.setPWMFreq(SERVO_FREQ);
  servos.setPWM(0, 0, SERVOMIN);
  servos.setPWM(1, 0, SERVOMAX);

  // TESTING
  //turnServos(0x00);
  //motorStep(0x01);
  //actuators(0x00);
  delay(1000);
  //motorStep(0x00);
  actuators(0x00);
  //turnServos(0x01);
}

void loop() {
  if (!start) {
    start = startLED();
  }
  // if (!limitTrigger) {
  //   Serial.println("Frog");
  // }
  load_response();

  // check if something needs to be done:
  if (command_buffer[0] != 0xAA) {
    return;
  }

  switch (command_buffer[1]) {
    case 0x01:                       // Shovel Stepper
      motorStep(command_buffer[2]);  // 0 = down, 1 = up
      Serial.println("Motor Moved");
      break;
    case 0x02:                        // Servos
      turnServos(command_buffer[2]);  // 0 = in, 1 = out
      Serial.println("Servos Turned");
      break;
    case 0x03:  // Actuators
      actuators(command_buffer[2]);
      Serial.println("Actuators worked");
      break;
  }

  //empty the command buffer because its done!
  for (byte i = 0; i < BUF_SIZE; i++) {
    command_buffer[i] = 0x00;
  }
}

void motorStep(int direction) {
  if (direction == 0) {  // move down
    digitalWrite(DIR_1, LOW);
    while (!limitTrigger) {
      digitalWrite(STEP_1, HIGH);
      delay(1);
      digitalWrite(STEP_1, LOW);
      delay(1);
    }
  } else if (direction == 1) {  // move up
    digitalWrite(DIR_1, HIGH);
    for (int i = 0; i < 3300; i++) {
      digitalWrite(STEP_1, HIGH);
      delay(1);
      digitalWrite(STEP_1, LOW);
      delay(1);
    }
  }
}

void actuators(int setting) {
  if (setting == 0x00) {  // DOWN
    digitalWrite(RELAY_PIN_UP, HIGH);
    digitalWrite(RELAY_PIN_DOWN, LOW);
    delay(10000);
    digitalWrite(RELAY_PIN_UP, LOW);
    digitalWrite(RELAY_PIN_DOWN, LOW);
  } else if (setting == 0x01) {  // UP
    digitalWrite(RELAY_PIN_UP, LOW);
    digitalWrite(RELAY_PIN_DOWN, HIGH);
    delay(10000);
    digitalWrite(RELAY_PIN_UP, LOW);
    digitalWrite(RELAY_PIN_DOWN, LOW);
  } else if (setting == 0x02) {  // OFF
    digitalWrite(RELAY_PIN_UP, LOW);
    digitalWrite(RELAY_PIN_DOWN, LOW);
  }
}

void turnServos(int direction) {
  if (direction == 0) {
    servos.setPWM(0, 0, SERVOMIN);
    servos.setPWM(1, 0, SERVOMAX);
  } else if (direction == 1) {
    servos.setPWM(0, 0, (SERVOMAX - 200));
    servos.setPWM(1, 0, (SERVOMIN + 200));
  }
}

void switchInterrupt() {
  if (millis() - lastDebounceTime > DEBOUNCE_DELAY) {
    limitTrigger = true;
    lastDebounceTime = millis();
  }
}

bool startLED() {
  bool trigger = false;
  frontReading = analogRead(PHOTOCELL_F);
  backReading = analogRead(PHOTOCELL_B);
  if (backReading - frontReading >= 200) {
    trigger = true;
    digitalWrite(LED, LOW);
  }
  return trigger;
}

ISR(SPI_STC_vect) {      // called after every byte transfer
  byte received = SPDR;  // read what Pi just sent

  if (rx_index < BUF_SIZE) {
    rx_buffer[rx_index] = received;
    SPDR = tx_buffer[rx_index];  // load what we want to send next
    rx_index++;
  } else {
    // Buffer overflow protection – ignore or handle error
    SPDR = 0xFF;
  }
  // Assume Pi always sends exactly MESSAGE_LENGTH bytes
  if (rx_index == MESSAGE_LENGTH && !message_complete) {
    message_complete = true;
    rx_index = 0;  // ready for next message
  }
}

void load_response() {
  if (message_complete) {
    noInterrupts();             // briefly disable ISR to copy safely
    byte len = MESSAGE_LENGTH;  // or whatever length you used
    byte copy_rx[MESSAGE_LENGTH];
    for (byte i = 0; i < len; i++) {
      copy_rx[i] = rx_buffer[i];
      //OR do this with the global thing I made
      command_buffer[i] = rx_buffer[i];
    }
    interrupts();

    // All this does is print the recived bytes to serial
    Serial.print("Pi sent: ");
    for (byte i = 0; i < len; i++) {
      Serial.print(copy_rx[i]);
      Serial.print(" ");
    }
    Serial.println();

    // Optional: update tx_buffer for next time (e.g. echo back + offset)
    for (byte i = 0; i < len; i++) {
      tx_buffer[i] = copy_rx[i];
    }
    message_complete = false;
  }
}
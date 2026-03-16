//SLAVE CODE

#include <SPI.h>

//Received byte from Master
volatile byte recv_byte;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200); // for debugging.

  // Turn ON SPI in slave mode.
  SPCR |= bit(SPE);
  // Have to send on MASTER IN, SLAVE OUT
  pinMode(MISO,OUTPUT);
} // end of setup

void loop() {
  
  //Byte Received!
  if ((SPSR & (1 << SPIF)) != 0)
  {
    recv_byte = SPDR;
  }  
    Serial.println(recv_byte);

}


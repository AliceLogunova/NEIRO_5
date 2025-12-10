#include <TimerOne.h>

int valA0 = 0;
int valA1 = 0;

void sendData() {

  // Чтение с первого датчика (A0)
  valA0 = analogRead(A0);
  Serial.write("A0");
  Serial.write(map(valA0, 0, 1023, 0, 255));

  // Чтение со второго датчика (A1)
  valA1 = analogRead(A1);
  Serial.write("A1");  
  Serial.write(map(valA1, 0, 1023, 0, 255));
}

void setup() {
  Serial.begin(115200);      
  Timer1.initialize(3000);  
  Timer1.attachInterrupt(sendData); 
}

void loop() {
}
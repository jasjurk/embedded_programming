struct motor {
  uint8_t hall1_pin;
  uint8_t hall2_pin;
  int16_t hall1_offset;
  int16_t hall2_offset;
  float hall1_max;

  float theta;
  float sintheta;
  float costheta;

  float torque;

  float inta;
  float intb;

  uint8_t i1_pin;
  uint8_t i2_pin;
  uint8_t pwm1_pin;
  uint8_t pwm2_pin;
  uint8_t pwm3_pin;

  };

void update_motor_position(struct motor& m) {
  int16_t hall1 = analogRead(m.hall1_pin) - m.hall1_offset;
  if(hall1 < 0) {
    int16_t hall2 = analogRead(m.hall2_pin) - m.hall2_offset;
    if(hall2 < 0) {
      m.theta = 6.28318530 - asin(-hall1 / m.hall1_max);
      m.sintheta = sin(m.theta);
      m.costheta = sqrt(1 - m.sintheta * m.sintheta);
    }
    else {
      m.theta = 3.14159265 + asin(-hall1 / m.hall1_max);
      m.sintheta = sin(m.theta);
      m.costheta = -sqrt(1 - m.sintheta * m.sintheta);
    }
  }
  else {
    int16_t hall2 = analogRead(m.hall2_pin);
    if(hall2 < 0) {
      m.theta = 3.14159265 - asin(hall1 / m.hall1_max);
      m.sintheta = sin(m.theta);
      m.costheta = -sqrt(1 - m.sintheta * m.sintheta);
    }
    else {
      m.theta = asin(hall1 / m.hall1_max);
      m.sintheta = sin(m.theta);  
      m.costheta = sqrt(1 - m.sintheta * m.sintheta);
    }
  }
}

void update_pis(struct motor& m) {
  float iaf = analogRead(m.i1_pin);
  float ibf = analogRead(m.i2_pin);
  ibf = (iaf + 2 * ibf) / 1.73205081;
  float id = iaf * m.costheta + ibf * m.sintheta;
  float iq = ibf * m.costheta - iaf * m.sintheta;
  iq -= m.torque;
  iaf = id * m.costheta - iq * m.sintheta;
  ibf = id * m.sintheta + iq * m.costheta;
  m.inta += iaf;
  m.intb += ibf;
}

void update_pwms(struct motor& m) {
  int16_t p1 = m.inta;
  int16_t p2 = (m.intb * 1.73205081 - m.inta) / 2;
  int16_t p3 = (m.intb * -1.73205081 - m.inta) / 2;
  analogWrite(m.pwm1_pin, p1);
  analogWrite(m.pwm2_pin, p2);
  analogWrite(m.pwm3_pin, p3);
}

struct motor setup_motor(uint8_t hall1_pin, uint8_t hall2_pin, int16_t hall1_offset, int16_t hall2_offset, 
              float hall1_max, uint8_t i1_pin, uint8_t i2_pin, uint8_t pwm1_pin, uint8_t pwm2_pin, uint8_t pwm3_pin) {
                return (struct motor){hall1_pin, hall2_pin, hall1_offset, hall2_offset, hall1_max, 0, 0, 1, 0, 0, 0, i1_pin, i2_pin, pwm1_pin, pwm2_pin, pwm3_pin};
}

struct motor m1;

void setup() {
  m1 = setup_motor(A1, A2, 1500, 1500, 3000, A3, A4, 42, 43, 44);
  update_motor_position(m1);
  m1.torque = 1;
  update_pis(m1);
  update_pwms(m1);    
}

int counter = 0;

void loop() {
  update_pis(m1);
  update_pwms(m1);
  counter++;
  if(counter == 100) {
    counter = 0;
    update_motor_position(m1);
  }
}

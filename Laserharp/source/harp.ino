
#include <I2S.h>
#include <I2S_reg.h>

const int strings_num = 12 * 3;

const uint32_t max_time = 0xffffffff;

uint8_t cheating_counter = 0;
uint16_t cheating_millis = 0;

const uint8_t notes[] = {20, 27, 27, 24, 25, 27, 25, 24, 25, 27, 25, 24, 22,
                         20, 22, 18, 20, 24, 27, 25, 24, 25, 24, 20, 22, 18,
                         20, 24, 22, 25, 27, 24, 20, 20, 20, 17, 15};

uint32_t cur_time = 0;

uint32_t plucked[strings_num] = {0};
uint32_t sample_time[strings_num] = 
{13605, 13061, 12094, 11610, 10884, 10204, 9675, 9070, 8707, 8163, 7740, 7256, 
6803, 6531, 6047, 5805, 5442, 5102, 4837, 4535, 4354, 4082, 3870, 3628, 
3401, 3265, 3023, 2902, 2721, 2551, 2419, 2268, 2177, 2041, 1935, 1814};

/*{85, 82, 76, 73, 68, 64, 60, 57, 54, 51, 48, 45, 
43, 41, 38, 36, 34, 32, 30, 28, 27, 26, 24, 23, 
21, 20, 19, 18, 17, 16, 15, 14, 14, 13, 12, 11};*/

int16_t MixStrings();

const int oversample32 = 1;
typedef int32_t fixed24p8_t;
enum {fixedPosValue=0x007fff00};
fixed24p8_t lastSamp;
fixed24p8_t cumErr;   
uint8_t gainF2P6 = (uint8_t)(1.0*(1<<6));

void InitAudio() {
  lastSamp = 0;
  cumErr = 0;
  for(int i = 0; i < strings_num; i++)
    plucked[i] = max_time;
  uint32_t orig_bck = READ_PERI_REG(PERIPHS_IO_MUX_MTDO_U);
  uint32_t orig_ws = READ_PERI_REG(PERIPHS_IO_MUX_GPIO2_U);
  pinMode(3, OUTPUT); // Override default Serial initiation
  digitalWrite(3,0); // Set pin low
  //i2s_rxtxdrive_begin(false, true, false, true);
  i2s_begin();
  i2s_set_rate(44100 * oversample32);
  WRITE_PERI_REG(PERIPHS_IO_MUX_MTDO_U, orig_bck);
  WRITE_PERI_REG(PERIPHS_IO_MUX_GPIO2_U, orig_ws);
}

inline int16_t Amplify(int16_t s) {
  return s;
  int32_t v = (s * gainF2P6)>>6;
  if (v < -32767) return -32767;
  else if (v > 32767) return 32767;
  else return (int16_t)(v&0xffff);
}

void DeltaSigma(int16_t sample, uint32_t dsBuff[8])
{
  // Not shift 8 because addition takes care of one mult x 2
  int32_t sum = Amplify(sample);
  fixed24p8_t newSamp = sum<< 8;
  // How much the comparison signal changes each oversample step
  fixed24p8_t diffPerStep = (newSamp - lastSamp) >> (4 + oversample32);

  // Don't need lastSamp anymore, store this one for next round
  lastSamp = newSamp;

  for (int j = 0; j < oversample32; j++) {
    uint32_t bits = 0; // The bits we convert the sample into, MSB to go on the wire first
    
    for (int i = 32; i > 0; i--) {
      bits = bits << 1;
      if (cumErr < 0) {
        bits |= 1;
        cumErr += fixedPosValue - newSamp;
      } else {
        // Bits[0] = 0 handled already by left shift
        cumErr -= fixedPosValue + newSamp;
      }
      newSamp += diffPerStep; // Move the reference signal towards destination
    }
    dsBuff[j] = bits;
  }
}

bool ConsumeSample(int16_t sample)
{
  // Make delta-sigma filled buffer
  uint32_t dsBuff[8];
  DeltaSigma(sample, dsBuff);
  //dsBuff[0] = 0b01010101010101010101010101010101;
  i2s_write_sample( dsBuff[0]);
  cur_time += sample_time[23];
  //if (!i2s_write_sample_nb(dsBuff[0])) return false; // No room at the inn
  // At this point we've sent in first of possibly 8 32-bits, need to send
  // remaining ones even if they block.
  for (int i = 1; i < oversample32; i++)
    i2s_write_sample( dsBuff[i]);
  return true;
}

const uint8_t multiplex_out[] = {14, 16, 15, 1};
const uint8_t multiplex_in[] = {4, 13, 5, 12};

bool buttons[16] = {0};
uint8_t mul_index = 0;

void setupOTA();

void setup() { 
  pinMode(multiplex_out[3], OUTPUT);
  digitalWrite(multiplex_out[3], true);
  pinMode(multiplex_in[0], INPUT_PULLUP);  
  delay(1000); 
  if(digitalRead(multiplex_in[0])) {
    setupOTA();
  }  
  InitAudio();
  pinMode(D4, OUTPUT);
  digitalWrite(D4, 0);
  pinMode(D5, INPUT_PULLUP); // Override default Serial initiation
  for(int i = 0; i < sizeof(multiplex_out); i++) {
    pinMode(multiplex_out[i], OUTPUT);
    digitalWrite(multiplex_out[i], false);
  }
  for(int i = 0; i < 16; i++) {
    buttons[i] = true;
  }
  for(int i = 0; i < sizeof(multiplex_in); i++) {
    pinMode(multiplex_in[i], INPUT_PULLUP);
  }
}

bool button;
int8_t shift_sound = 12; 
bool cheating = false;
uint32_t multi_millis = millis();


void loop() {

  ConsumeSample(MixStrings());

  if(multi_millis + 1 < millis()) {
    button = digitalRead(multiplex_in[mul_index & 0b11]);
    if(button && !buttons[mul_index]) {
      if((mul_index >> 2) != 3) {
        if(!cheating)
          plucked[mul_index + shift_sound] = cur_time;
        else {
          if(millis() - cheating_millis > 200) {
            plucked[notes[cheating_counter++]] = cur_time;
            if(cheating_counter == sizeof(notes))
              cheating_counter = 0;
            cheating_millis = millis();
          }
        }
      }
      else {
          if((mul_index & 0b11) == 0) {
            shift_sound -= 12;        
          }
          if((mul_index & 0b11) == 1) {
            cheating = true;
          }
      }
    }
    if(!button && buttons[mul_index]) {
      if((mul_index >> 2) == 3) {
        if((mul_index & 0b11) == 0) {
          shift_sound += 12;        
        }
        if((mul_index & 0b11) == 1) {
          cheating = false;
        }
      }
      else {
        if(!cheating)
          plucked[mul_index + shift_sound] = max_time;
      }
    }
    buttons[mul_index] = button;
    if((mul_index & 0b11) == 0b11) {
      digitalWrite(multiplex_out[mul_index >> 2], false);
      mul_index++;
      mul_index &= 0b1111;
      digitalWrite(multiplex_out[mul_index >> 2], true);
      multi_millis = millis();
    }
    else {
      mul_index++;
      mul_index &= 0b1111;
    }
    
  }
}

#include "lib6.h"

int16_t MixStrings() {
    int32_t v = 0;
    
    for(uint8_t i = 0; i < strings_num; i++) {
        if(cur_time > plucked[i]) {
        uint32_t ind = (cur_time - plucked[i]) / (sample_time[i]);
          if(ind < max_wav_ind) {
            v += (int16_t)pgm_read_word(wav + ind);
          }
          else {
            plucked[i] = max_time;
          }
        }
    }
      


    if (v < -32767) return -32767;
    else if (v > 32767) return 32767;
    else return (int16_t)(v&0xffff);
}

#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>

const char* ssid = "bullshitweb";
const char* password = "abacaba123";

void setupOTA() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    delay(100);
  }

  ArduinoOTA.onStart([]() {
  });
  ArduinoOTA.onEnd([]() {
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
  });
  ArduinoOTA.onError([](ota_error_t error) {
  });
  ArduinoOTA.begin();
  while(true) {
      ArduinoOTA.handle();
      yield();
  }
}


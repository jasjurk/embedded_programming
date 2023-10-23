#include <Arduino.h>
#include <ESP8266SAM.h>
#include <AudioOutputI2SNoDAC.h>
#include <AudioFileSourceSPIFFS.h>
#include <AudioGeneratorMP3.h>

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoOTA.h>

#include <ESPAsyncTCP.h>

const int sensor_num = 5;

const uint8_t characters_len = 15;

const uint8_t my_ind = 10;

const String characters[characters_len] = {
  "Batman",
  "Nightwing",
  "Red_X",
  "Kid_Flash",
  "Cyborg",
  "Beast_Boy",
  "John_Constantine",
  "Wonder_Woman",
  "Wonder_Girl",
  "Starfire",
  "Raven",
  "Zatanna",
  "Artemis",
  "Miss_Martian",
  "Environment"
};

const uint8_t actions_len = 3;

const String actions[actions_len] = {
  "Attack",
  "Mind Control",
  "Protect"
};

AudioOutputI2SNoDAC *out = NULL;

AudioGeneratorMP3 *mp3;
AudioFileSourceSPIFFS *file;

const int cap_pins[sensor_num] = {13, 12, 14, 5, 4};

int detection_threshold[sensor_num] = {0};

uint32_t measure(int pin) {
  pinMode(pin, INPUT);
  uint32_t start = ESP.getCycleCount();
  //digitalWrite(control_pin, HIGH);
  while(!digitalRead(pin));
  uint32_t end = ESP.getCycleCount();
  pinMode(pin, OUTPUT);
  digitalWrite(pin, false);
  return end - start;
}

void calibrate_sensors() {
  for(int i = 0; i < sensor_num; i++) {
    pinMode(cap_pins[i], OUTPUT);
    digitalWrite(cap_pins[i], false);
  }
  for(int j = 0; j < 100; j++) {
    for(int i = 0; i < sensor_num; i++) {
      int measured = measure(cap_pins[i]);
      if(j > 0 && measured > detection_threshold[i]) {
        detection_threshold[i] = measured;
      }
    }
  }
}

const char *ssid = "bullshitweb";      // wifi router name
const char *pass = "abacaba123";    // wifi router password
const int port = 8000;            // server port
int flag = 1;      // flag to check for connection existance

bool ota = false;

String q[256];
uint8_t cons = 0;
uint8_t prod = 0;

void add_to_queue(String s) {
  q[prod++] = s;
}

String get_from_queue() {
  uint8_t con = cons;
  uint8_t pro = prod;
  if(con == pro) {
    return "";
  }
  else {
    String res = q[cons++];
    q[cons] = "";
    return res;
  }
}

static void handleData(void* arg, AsyncClient* client, void *data, size_t len) {
  char temp[len + 1];
  memcpy(&temp, data, len);
  temp[len] = 0;
  add_to_queue(String(temp));
}

void onDisconnected(void* arg, AsyncClient* client) {
	flag = 1;
  add_to_queue("Disconnected");
  client->connect(IPAddress(192,168,137,1), port);
}

void onConnect(void* arg, AsyncClient* client) {
	flag = 0;
  add_to_queue("Connected");
}

AsyncClient* client;

ESP8266SAM* sam = new ESP8266SAM;

void say(String s) {
  if(!file->open(("/" + s + ".mp3").c_str())) {
    sam->Say(out, s.c_str());
  }
  else {
    mp3->begin(file, out);
  }
}

void setup() {

  pinMode(14, INPUT_PULLUP);

  Serial.begin(115200);            // initialize serial communication
  Serial.print("Connecting to ");  
  Serial.println(ssid);  
  WiFi.mode(WIFI_STA);             // set mode to wifi station
  WiFi.begin(ssid, pass);          // connect to wifi router
  while (WiFi.status() != WL_CONNECTED){ // check status of connection
    delay(500);    
    Serial.print(".");
  }  
  Serial.println("WiFi connected");  
  Serial.println("IP address: ");  
  Serial.println(WiFi.localIP());  // print the Ip alocated by router
  delay(500);

  ArduinoOTA.begin();

  ota = !digitalRead(14);
  if(ota) {
    return;
  }
  Serial.end();

  SPIFFS.begin();
  file = new AudioFileSourceSPIFFS();
  mp3 = new AudioGeneratorMP3();
  
  /*if(!isRunning)
  mp3->stop();*/

  out = new AudioOutputI2SNoDAC();
  out->begin();
  client = new AsyncClient;
  client->onData(&handleData, client);
  client->onDisconnect(&onDisconnected, client);
	client->onConnect(&onConnect, client);
	client->connect(IPAddress(192,168,137,1), port);

  
  calibrate_sensors();

  say(characters[my_ind]);
}

int32_t lastmillis[sensor_num] = {0};
bool locked[sensor_num] = {0};

bool detected_push(int ind) {
  if(measure(cap_pins[ind]) <= detection_threshold[ind]) {
    lastmillis[ind] = 0;
    locked[ind] = false;
  }
  else {
    if(lastmillis[ind] == 0)
      lastmillis[ind] = millis();
  }
  if(!locked[ind] && lastmillis[ind] > 0 && ((int32_t)millis()) - lastmillis[ind] > 100) {
    locked[ind] = true;
    return true;
  }
  else {
    return false;
  }
}

bool send_to_server(String s) {
  if (flag == 0 && client->space() > s.length() && client->canSend()) {
		client->add(s.c_str(), strlen(s.c_str()));
		client->send();
    return true;
	}
  return false;
}


uint8_t menu_depth = 0;
uint8_t choice = 0;
uint8_t max_choices = characters_len;

uint8_t choices[2];

void loop() {
  ArduinoOTA.handle();
  if(ota) {
    return;
  }
  if (mp3->isRunning()) {
    if (!mp3->loop()) mp3->stop(); 
  }
  String s = get_from_queue();
  if(!s.isEmpty()) {
    say(s);
  }
  if(detected_push(0)) {
      if(menu_depth == 0) {
        say("select action");
        choices[0] = choice;
        max_choices = actions_len;
        choice = 0;
        say(actions[choice]);
        menu_depth++;
      } else if(menu_depth == 1) {
        say("applying now");
        max_choices = characters_len;
        choices[1] = choice;
        choice = 0;
        menu_depth = 0;
        send_to_server(String(my_ind) + " " + String(choices[0]) + " " + String(choices[1]));
      }
  }
  bool pushed = false;
  if(detected_push(1) && max_choices > 0) {
      choice = (choice + 1) % max_choices;
      pushed = true;
  }
  if(detected_push(2)) {
      if(choice >= 1) {
        choice--;
      }
      else {
        choice = max_choices - 1;
      }
      pushed = true;
  }
  if(detected_push(3)) {
      choice = (choice + 5) % max_choices;
      pushed = true;
  }
  if(detected_push(4)) {
      if(choice >= 5) {
        choice -= 5;
      }
      else {
        if(max_choices > 5)
          choice = max_choices - 5;
        else 
          choice = 0;
      }
      pushed = true;
  }
  if(pushed) {
    if(menu_depth == 0) {
      say(characters[choice]);
    }
    if(menu_depth == 1) {
      say(actions[choice]);
    }
  }
  /*for(int i = 0; i < sensor_num; i++) {
    if(detected_push(i)) {

    }
  }*/
}
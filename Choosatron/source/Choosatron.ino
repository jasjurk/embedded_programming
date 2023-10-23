#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoOTA.h>
#include <LittleFS.h>
#include <map>

const int control_pin = 13;

const int sensor_num = 4;

const int cap_pins[sensor_num] = {12, 14, 5, 4};

int detection_threshold[sensor_num] = {0};
uint32_t debouncing_start[sensor_num] = {0};

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

String last_passage = "";
int char_in_line = 0;
char last_char = '\n';

void write_to_serial_and_tabularize(char c) {
  if(c == '\n') {
    char_in_line = 0;
  }
  else if(++char_in_line == 32) {
    if(((last_char >= 'a' && last_char <= 'z') || (last_char >= 'A' && last_char <= 'Z')) && 
        ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'))) {
      Serial.write('-');
    }
    Serial.write('\n');
    char_in_line = 1;
  }
  Serial.write(c);
}

std::vector<String> process_passage(size_t address, File file, bool serial) {
  std::vector<String> result;
  file.seek(address);
  last_char = '\0';
  char current_char = '\0';
  bool way = false;
  bool visible = true;
  String way_id = "";
  last_passage = "";
  while(file.available() && file.read() != '\n'); //skipping header
  while(file.available()) {
    last_char = current_char;
    current_char = file.read();
    if(current_char == ':' && last_char == ':')
      return result;
    if(current_char != '<' && current_char != '>' && current_char != '[' && current_char != ']' && current_char != ':') {
      if(way) {
        if(current_char == '|') {
        way_id.clear();
        visible = false;
        }
        else {
          way_id += current_char;
        }
      }
      if(visible && (current_char != '\n' || last_char != '\n'))
      {
        if(serial) {
          write_to_serial_and_tabularize(current_char);
        }
        else
          last_passage += current_char;
      }
    }
    if(current_char == '[' && last_char == '[') {
      way = true;
    }
    if(current_char == '<' && last_char == '<')
      visible = false;
    if(current_char == '>' && last_char == '>')
      visible = true;
    if(current_char == ']' && last_char == ']') {
      way = false;
      visible = true;
      result.push_back(way_id);
      if(serial) {
        String s(result.size());
        write_to_serial_and_tabularize('-');
        for(size_t i = 0; i < s.length(); i++)
          write_to_serial_and_tabularize(s[i]);
        write_to_serial_and_tabularize('\n');
      }
      else {
        last_passage += '-';
        last_passage += String(result.size());
      }
      way_id.clear();
    }
  }
  return result;
}



std::map<String, uint32> cache; 

size_t lookup_passage(String target, File file) {
  if(cache.find(target) != cache.end())
    return cache[target];
  file.seek(0);
  String current_passage = "";
  char last_char = '\0';
  char current_char = '\0';
  size_t passage_begining = (~0);
  int seeker = -1;
  while(file.available() && seeker != 0) {
    last_char = current_char;
    current_char = file.read();
    if(current_char == ':' && last_char == ':') {
      current_passage = "";
      file.read();
      passage_begining = file.position();
    }
    else {
      if(passage_begining != (~0)) {
        if(current_char == '\n' || current_char == '[' || current_char == '{') {
          current_passage.trim();
          cache[current_passage] = passage_begining;
          seeker--;
          if(current_passage == target) 
            seeker = 100;
          current_passage.clear();
          passage_begining = (~0);
        }
        else
          current_passage += current_char;
      }
    }
  }
  if(cache.find(target) != cache.end())
    return cache[target];
  else
    return (~0);
}

void calibrate_sensors() {
  pinMode(control_pin, OUTPUT);
  digitalWrite(control_pin, true);
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

ESP8266WebServer server(80);    // Create a webserver object that listens for HTTP request on port 80

bool handleFileRead(String path);       // send the right file to the client (if it exists)
void handleFileUpload();                // upload a new file to the SPIFFS

int writeFilelist(bool serial) {
  Dir dir = SPIFFS.openDir("/");
  int i = 0;
  last_passage = "";
  while (dir.next()) {
    String name = "<" + String(i + 1) + "> " + dir.fileName();
    if(serial) {
      if(name.length() > 32) {
        Serial.print(name.substring(0,29));
        Serial.println("...");
      }
      else
        Serial.println(name);
    }
    else
      last_passage += name + '\n';
    i++;
  }
  if(serial) {
    Serial.write('\n');
    Serial.write('\n');
  }
  return i;
}

File chooseFilenum(int i) {
  Dir dir = SPIFFS.openDir("/");
  while (dir.next()) {
    if(i-- == 0)
      return SPIFFS.open(dir.fileName(), "r");
  }
  return File();
}

int skips = 0;
int choicenum = 0;

int chosen(int i) {
  if(skips * 4 + i >= choicenum)
    return -1;
  else
    return skips * 4 + i;
}

void skip(bool serial) {
  skips++;
  if(4 * skips > choicenum)
    skips = 0;
  if(serial) {
    Serial.print(F("Now choosing "));
    Serial.print(4 * skips + 1);
    Serial.print(F(" - "));
    Serial.println(4 * skips + 4);
    Serial.write('\n');
    Serial.write('\n');
  }
}

void setup_passagechoice(std::vector<String> &passages) {
  choicenum = passages.size();
  skips = 0;
}

void setup_filechoice(bool serial) {
  choicenum = writeFilelist(serial);
  skips = 0;
}

bool serial = false;

void setup() {
  pinMode(16, INPUT_PULLUP);

  Serial.begin(9600);

  SPIFFS.begin();                           // Start the SPI Flash Files System

  serial = digitalRead(16);

  if(!serial) {
    WiFi.softAP(F("Choosatron"), F("choosatron"));
    ArduinoOTA.begin();
    server.on("/", HTTP_GET, []() {    
      cache.clear();
      String str = F("<html><body>");
      Dir dir = SPIFFS.openDir("/");
      while (dir.next()) {
          str += F("<a href='") + dir.fileName() + F("'>") + dir.fileName() + F("</a>");
          str += " / ";
          str += dir.fileSize();  
          str += F("bytes <form method='post' action='");
          str += dir.fileName();
          str += F("' > <input class='button' type='submit' value='delete'></form><br>");
      }
      struct FSInfo info;
      SPIFFS.info(info);
      str += info.usedBytes;
      str += F("b out of ");
      str += info.totalBytes;
      str += F("b currently used.<br>");
      str += F("<form method='post' enctype='multipart/form-data'> \
      <input type='file' name='name'> \
      <input class='button' type='submit' value='Upload'></form></body></html>");  
        server.send(200, "text/html", str); 
    });

    server.on("/story", HTTP_GET, []() {    
      server.send(200, "text/plain", last_passage); 
    });

    server.on("/", HTTP_POST,                       // if the client posts to the upload page
      [](){ cache.clear(); server.send(200); },                          // Send status 200 (OK) to tell the client we are ready to receive
      handleFileUpload                                    // Receive and save the file
    );

    server.onNotFound([]() {                              // If the client requests any URI
      cache.clear();
      if(server.method() == HTTP_POST) {
        String filename = server.uri();
        if(!filename.startsWith("/")) filename = "/"+filename;
        if(SPIFFS.remove(filename)) {             // Delete the file
          server.sendHeader(F("Location"),"/");      // Redirect the client to the success page
          server.send(303);
        } else {
          server.send(500, F("text/plain"), F("500: couldn't delete file"));
        }
      }
      else {
      if (!handleFileRead(server.uri()))                  // send it if it exists
        server.send(404, F("text/plain"), F("404: Not Found")); // otherwise, respond with a 404 (Not Found) error
      }
    });

    server.begin();                           // Actually start the server

  }
  else
    delay(300);

  calibrate_sensors();
  setup_filechoice(serial);
}

bool menu = true;

int32_t lastmillis[sensor_num] = {0};

bool locked[sensor_num] = {0};

bool detected_push(int ind) {
  if(measure(cap_pins[ind]) <= detection_threshold[ind] + 70) {
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

File f;
std::vector<String> choices;

bool prev_16_read = false;

void loop() {
  if (!serial) 
  {
    server.handleClient();
    ArduinoOTA.handle();
  }
  if(digitalRead(16) && !prev_16_read)
    skip(serial);
  prev_16_read = digitalRead(16);
  if(menu) {
    for(int i = 0; i < sensor_num; i++) 
      if(detected_push(i)) {
        if(chosen(i) != -1) {
          f = chooseFilenum(chosen(i));
          menu = false;
          choices = process_passage(lookup_passage(F("Start"), f), f, serial);
          setup_passagechoice(choices);
        }
      }
  }
  else {
    for(int i = 0; i < sensor_num; i++) 
      if(detected_push(i)) {
        int ch = chosen(i);
        if(serial && ch != -1) {
          Serial.println(F("You chose ") + String(ch + 1));
          write_to_serial_and_tabularize('\n');
          write_to_serial_and_tabularize('\n');
        }
        if(!choices.empty() && ch != -1) {
          choices = process_passage(lookup_passage(choices[ch], f), f, serial);
          if(choices.empty()) {
            if(serial) {
              Serial.println(F("Return to Start - 1"));
              Serial.println(F("Return to Menu - 2"));
              Serial.print('\n');
              Serial.print('\n');
            }
            else {
              last_passage += F("\nReturn to Start - 1\nReturn to Menu - 2\n");
            }
            choicenum = 2;
          }
          else
            setup_passagechoice(choices);
        }
        else if(choices.empty() && ch != -1) {
          if(ch == 0) {
            choices = process_passage(lookup_passage(F("Start"), f), f, serial);
            setup_passagechoice(choices);
          }
          if(ch == 1) {
            f.close();
            cache.clear();
            menu = true;
            setup_filechoice(serial);
          }
        }
      }
  }
}


File fsUploadFile;              // a File object to temporarily store the received file

bool handleFileRead(String path) { // send the right file to the client (if it exists)
  if (SPIFFS.exists(path)) { // If the file exists, either as a compressed archive, or normal                                     // Use the compressed verion
    File file = SPIFFS.open(path, "r");                    // Open the file
    server.sendHeader(F("Content-Type"), F("text/text"));
    path.remove(0, 1);
    server.sendHeader(F("Content-Disposition"), F("attachment; filename=")+path);
    server.sendHeader(F("Connection"), F("close"));
    server.streamFile(file, F("application/octet-stream"));
    file.close();
    return true;
  }
  return false;
}

void handleFileUpload(){ // upload a new file to the SPIFFS
  HTTPUpload& upload = server.upload();
  if(upload.status == UPLOAD_FILE_START){
    String filename = upload.filename;
    filename.replace(" ", "_");
    filename.replace("/", "_");
    for(int i = 0; i < filename.length(); i++)
      if(filename[i] > 127)
        filename[i] = '*';
    if(!filename.startsWith("/")) filename = "/"+filename;
    fsUploadFile = SPIFFS.open(filename, "w");            // Open the file for writing in SPIFFS (create if it doesn't exist)
    filename = String();
  } else if(upload.status == UPLOAD_FILE_WRITE){
    if(fsUploadFile)
      fsUploadFile.write(upload.buf, upload.currentSize); // Write the received bytes to the file
  } else if(upload.status == UPLOAD_FILE_END){
    if(fsUploadFile) {                                    // If the file was successfully created
      fsUploadFile.close();                               // Close the file again
      server.send(200, F("text/html"), F("Success! Redirecting to starting page...<script>setInterval(call_back, 1000);\
function call_back() {\
   document.location.href = \"\";\
}</script>"));
    } else {
      server.send(500, F("text/plain"), F("500: couldn't create file. Probably name too long. Names of files should be shorter than 31 characters!"));
    }
  }
}
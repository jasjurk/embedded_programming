#include <ESP8266WiFi.h>

// Replace with your network credentials
const char* ssid     = "bullshitweb";
const char* password = "abacaba123";

// Set web server port number to 80
WiFiServer server(80);

// Variable to store the HTTP request
String header;

// Assign output variables to GPIO pins


void setup() {
  Serial.begin(115200);


  // Connect to Wi-Fi network with SSID and password
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Print local IP address and start web server
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
}

uint16_t data[1000];

void loop(){
  WiFiClient client = server.available();   // Listen for incoming clients

  if (client) {                             // If a new client connects,
    Serial.println("New Client.");          // print a message out in the serial port
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) { // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        header += c;
        if (c == '\n') {                    // if the byte is a newline character
          // if the current line is blank, you got two newline characters in a row.
          // that's the end of the client HTTP request, so send a response:
          if (currentLine.length() == 0) {
            //wifi_set_opmode(NULL_MODE);
            //ets_intr_lock( ); //close interrupt
            /*uint16 adc_addr[10];*/
            uint16 adc_num = 1000;
            uint8 adc_clk_div = 8;
            system_adc_read_fast(data, adc_num, adc_clk_div);
            //ets_intr_unlock();
            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println("Connection: close");
            client.println();

            // Display the HTML web page
            client.println("<!DOCTYPE html><html>");
            client.println("<head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
            client.println("<link rel=\"icon\" href=\"data:,\">");
            // CSS to style the on/off buttons 
            // Feel free to change the background-color and font-size attributes to fit your preferences
            client.println("</head>");
            
            // Web Page Heading
            client.println("<body>");
            client.println("<script>");
            client.println("var canvas = document.createElement(\"canvas\")");
            client.println("canvas.setAttribute(\"width\", window.innerWidth - 100)");
            client.println("canvas.setAttribute(\"height\", window.innerHeight - 100)");
            client.println("canvas.setAttribute(\"style\", \"position: absolute; x:0; y:0;\")");
            client.println("document.body.appendChild(canvas)");
            client.println("var ctx = canvas.getContext(\"2d\")");
            client.println("const data = [");
            for(int i = 0; i < 1000; i++) {
              client.print(data[i]);
              client.print(",");
            }
            client.println("];");
            client.println("ctx.lineTo(1000, window.innerHeight - 200);");
            client.println("ctx.lineTo(0, window.innerHeight - 200);");
            client.println("for (let i = 0; i < data.length; i++)");
            client.println("ctx.lineTo(i, window.innerHeight - data[i] / 2 - 200);");
            client.println("ctx.stroke();");
            client.println("setTimeout(function(){\
   window.location.reload();\
}, 1000);");


            client.println("</script></body></html>");
            
            // The HTTP response ends with another blank line
            client.println();
            // Break out of the while loop
            break;
          } else { // if you got a newline, then clear currentLine
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    // Clear the header variable
    header = "";
    // Close the connection
    client.stop();
    Serial.println("Client disconnected.");
    Serial.println("");
  }
}
#include <WiFi.h>

// --- WIFI SETTINGS ---
const char* ssid = "Net";
const char* password = "take1234";
WiFiServer server(8080);
WiFiClient client;             
String currentLine = "";       

// --- MOTOR PINS (Your exact working pins) ---
// Left L298N (#1)
int IN1 = 18;   // Front Left IN1
int IN2 = 14;   // Front Left IN2
int IN5 = 25;   // Rear Left IN1
int IN6 = 26;   // Rear Left IN2

// Right L298N (#2)
int IN3 = 13;   // Front Right IN1
int IN4 = 27;   // Front Right IN2
int IN7 = 19;   // Rear Right IN1
int IN8 = 21;   // Rear Right IN2

// --- MOTOR INVERSION SETTINGS ---
bool invert_FL = true;  
bool invert_FR = false; 
bool invert_RL = false; 
bool invert_RR = true;  

// --- MOTOR CALIBRATION (DELTA PWM TRIM) ---
// Boost a specific motor if it physically lags behind the others.
// 1.0 = normal speed. 1.15 = 15% boost, 1.20 = 20% boost, etc.
float trim_FL = 1.0;
float trim_FR = 1.25; // 15% power boost to compensate for Front Right lag
float trim_RL = 1.0;
float trim_RR = 1.25;

// --- STATE VARIABLES ---
// Target inputs from Wi-Fi (-255 to 255)
int targetVx = 0; // Forward/Backward
int targetVy = 0; // Strafe Left/Right
int targetWz = 0; // Turn Left/Right

// Smoothed values to prevent battery spikes
float currentVx = 0;
float currentVy = 0;
float currentWz = 0;

// Helper: set motor direction and speed using PWM on the IN pins
void setMotor(int INa, int INb, int speed, bool inverted) {
  if (inverted) {
    speed = -speed;
  }

  // analogWrite() directly controls the speed and direction!
  if (speed > 0) {
    analogWrite(INa, speed); 
    analogWrite(INb, 0);
  } else if (speed < 0) {
    analogWrite(INa, 0);
    analogWrite(INb, abs(speed)); 
  } else {
    analogWrite(INa, 0);
    analogWrite(INb, 0);
  }
}

// The Mecanum Math Engine (Proportional Vector Control)
void mecanumDrive(int Vx, int Vy, int Wz) {
  // Using floats to prevent integer overflow during math
  // Apply the trim multipliers directly to the base vector calculations
  float FL = (Vx + Vy + Wz) * trim_FL; 
  float FR = (Vx - Vy - Wz) * trim_FR; 
  float RL = (Vx - Vy + Wz) * trim_RL; 
  float RR = (Vx + Vy - Wz) * trim_RR; 

  // Find the maximum value requested among all 4 wheels
  float max_val = max(abs(FL), max(abs(FR), max(abs(RL), abs(RR))));

  // Vector Normalization:
  // If the mixed math pushes any wheel above 255, we proportionally scale ALL wheels down.
  // This keeps the robot moving in the exact correct diagonal angle, just capped at max speed.
  if (max_val > 255.0) {
    FL = (FL / max_val) * 255.0;
    FR = (FR / max_val) * 255.0;
    RL = (RL / max_val) * 255.0;
    RR = (RR / max_val) * 255.0;
  }

  // Send calculated speeds directly to the wheels
  setMotor(IN1, IN2, (int)FL, invert_FL);
  setMotor(IN3, IN4, (int)FR, invert_FR);
  setMotor(IN5, IN6, (int)RL, invert_RL);
  setMotor(IN7, IN8, (int)RR, invert_RR);
}

void setup() {
  // Logic Pins
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  pinMode(IN5, OUTPUT); pinMode(IN6, OUTPUT);
  pinMode(IN7, OUTPUT); pinMode(IN8, OUTPUT);
  
  mecanumDrive(0, 0, 0); // Stop all

  Serial.begin(115200);   
  
  // Connect to WiFi
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi Connected!");
  Serial.print("ROBOT IP ADDRESS: ");
  Serial.println(WiFi.localIP());
  
  server.begin();
}

void loop() {
  // 1. Handle incoming WiFi commands (Non-Blocking)
  if (!client || !client.connected()) {
    client = server.available();
  }

  if (client && client.available()) {
    while (client.available()) {
      char c = client.read();
      
      if (c == '\n') {
        currentLine.trim();
        
        if (currentLine.length() > 0) {
          // Parse the incoming string "Vx Vy Wz" into integers (-255 to 255)
          int parsed = sscanf(currentLine.c_str(), "%d %d %d", &targetVx, &targetVy, &targetWz);
        }
        currentLine = "";
      } 
      else if (c != '\r') {
        currentLine += c;
      }
    }
  }

  // 2. Analog Smoothing Filter (The new "Soft-Start")
  // This forces the motors to smoothly glide to the target speed instead of jerking,
  // preventing battery voltage spikes even if you slam the joystick forward instantly.
  currentVx += (targetVx - currentVx) * 0.1;
  currentVy += (targetVy - currentVy) * 0.1;
  currentWz += (targetWz - currentWz) * 0.1;

  // 3. Constantly Apply the Speed to the Motors
  mecanumDrive((int)currentVx, (int)currentVy, (int)currentWz);
  
  delay(5); // Small 5ms delay stabilizes the smoothing math
}
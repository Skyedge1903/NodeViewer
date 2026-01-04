#include <Adafruit_GFX.h>
#include <Adafruit_TFTLCD.h>
#include <TouchScreen.h>

#define DEG2RAD 0.0174532925

#define LCD_CS A3
#define LCD_CD A2
#define LCD_WR A1
#define LCD_RD A0
#define LCD_RESET A4

#define LCD_RESET A4
#define BLACK 0x0000
#define BLUE 0x001F
#define RED 0xF800
#define GREEN 0x07E0
#define CYAN 0x07FF
#define MAGENTA 0xF81F
#define YELLOW 0xFFE0
#define WHITE 0xFFFF
#define ORANGE 0xFD20
#define GREENYELLOW 0xAFE5
#define NAVY 0x000F
#define DARKGREEN 0x03E0
#define DARKCYAN 0x03EF
#define MAROON 0x7800
#define PURPLE 0x780F
#define OLIVE 0x7BE0
#define LIGHTGREY 0xF7BE
#define DARKGREY 0xC618

#define YP A2  // must be an analog pin, use "An" notation!
#define XM A3  // must be an analog pin, use "An" notation!
#define YM 8   // can be a digital pin
#define XP 9   // can be a digital pin

Adafruit_TFTLCD tft(LCD_CS, LCD_CD, LCD_WR, LCD_RD, LCD_RESET);
String inputString = "";      // a String to hold incoming data

unsigned int n = 0;
String names[] = {"", "", "", "", "", ""};
unsigned int pourcent[] = {0, 0, 0, 0, 0, 0};
String totalvalue = "          0.00 USDC";

String validatorname = "Validator XXXXXX";
String ch1 = "Rank  0 %        Balance";
String ch2 = "0                0.00000";
String ch3 = "Status     Effectiveness";
String ch4 = "?                      ?";
bool active = false;

String ch11 = "         +0.00000 ETH";
String ch12 = "            +0.00 USDC";
String ch13 = "       +0.00000 ETH";
String ch14 = "            +0.00 USDC  ";
unsigned int graph[] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

bool p[] = {false, false, false};
bool first = true;

void setup() {
  tft.reset();
  uint16_t identifier = tft.readID();
  tft.begin(identifier);
  tft.setRotation(1);
  unsigned int back = WHITE;
  tft.fillScreen(BLACK);
  tft.fillTriangle(160, 0, 160, 170, 232, 124, RED);
  tft.fillTriangle(172, 150, 172, 40, 218, 120, back);
  tft.fillTriangle(160, 0, 160, 170, 89, 124, YELLOW);
  tft.fillTriangle(150, 39, 150, 150, 103, 119, back);

  tft.fillTriangle(89, 136, 160, 240, 160, 182, CYAN);
  tft.fillTriangle(150, 206, 150, 186, 127, 172, back);
  tft.fillTriangle(231, 136, 160, 240, 160, 182, BLUE);
  tft.fillTriangle(171, 206, 171, 186, 193, 172, back);

  tft.fillTriangle(218, 120, 212, 124, 214, 113, MAGENTA);
  tft.fillTriangle(172, 101, 212, 124, 214, 113, MAGENTA);
  tft.fillTriangle(172, 89, 172, 101, 214, 113, MAGENTA);

  tft.fillTriangle(110, 123, 107, 114, 103, 119, GREEN);
  tft.fillTriangle(110, 123, 107, 114, 150, 101, GREEN);
  tft.fillTriangle(150, 89, 107, 114, 150, 101, GREEN);

  tft.setTextColor(WHITE);
  tft.setCursor(235, 230);
  tft.setTextSize(1);
  tft.println("by Skyedge1903");

  Serial.begin(9600);
  Serial.println(F("TFT LCD NODE VIWER by Skyedge1903"));
  Serial.print("TFT size is ");
  Serial.print(tft.width());
  Serial.print("x");
  Serial.println(tft.height()); 

  while((char)Serial.read() != 'O');
  while((char)Serial.read() != 'K');
  Serial.println("OK");
  wait_validation();

  // Load the mode
  String p_bool = "";
  for (int i = 0; i < 3; i++) {
    char w = ' ';
    do {
      w = (char)Serial.read();
    } while (!(w == '0' || w == '1'));
    p[i] = w == '1';
    p_bool += w;
  }

  unsigned int n_count = p[0] + p[1] + p[2];
  Serial.println(p_bool);
  wait_validation();

  // Loads the startup information
  while (n_count > 0) {
    if (serial()) {
      // decode
      if (decode()) n_count -= 1;
      inputString = "";
    }
  }

}
void loop() {

  if (p[0]) {
    first = true;
    do {
      total();
    } while (!next(1, false));
  }

  if (p[1]) {
    first = true;
    do {
      validator();
    } while (!next(2, active));
  }

  if (p[2]) {
    first = true;
    do {
      income();
    } while (!next(3, false));
  }
}


int fillSegment(int x, int y, int start_angle, int sub_angle, int r, unsigned int colour)
{
  tft.setRotation(1);
  // Calculate first pair of coordinates for segment start
  float sx = cos((start_angle - 90) * DEG2RAD);
  float sy = sin((start_angle - 90) * DEG2RAD);
  uint16_t x1 = sx * r + x;
  uint16_t y1 = sy * r + y;

  // Draw colour blocks every inc degrees
  for (int i = start_angle; i < start_angle + sub_angle; i += 1) {

    // Calculate pair of coordinates for segment end
    for (int j = r; j > 53; j --){
      int x2 = cos((i + 1 - 90) * DEG2RAD) * j + x;
      int y2 = sin((i + 1 - 90) * DEG2RAD) * j + y;
      tft.drawLine(x1, y1, x2, y2, colour);
    }
    //tft.drawTriangle(x1, y1, x2, y2, x, y, colour);
    //tft.fillCircle(220, 110, 50, BLACK);

    int x2 = cos((i + 1 - 90) * DEG2RAD) * r + x;
    int y2 = sin((i + 1 - 90) * DEG2RAD) * r + y;

    // Copy segment end to sgement start for next segment
    x1 = x2;
    y1 = y2;

  }
}

int fillDonnut(int r, int x, int y, int l, String names[], unsigned int pourcent[])
{
  tft.setTextSize(2);
  unsigned int colors[] = {CYAN, ORANGE, MAGENTA, BLUE, RED};
  unsigned int total = 0;
  for (int i = 0; i < l; i ++) 
  {
    fillSegment(x + 200, y, total, pourcent[i], r, colors[i]);
    tft.setTextColor(colors[i]);
    tft.setCursor(x, y - r + ((r*2)/l)*i);
    tft.println(names[i]);
    total += pourcent[i];
  }
}

int total()
{
  unsigned int border = 20;
  tft.fillScreen(BLACK);
  tft.setTextColor(WHITE);
  tft.setCursor(border + 50, 0);
  tft.setTextSize(2);
  tft.println("  Total Value");
  tft.setTextColor(LIGHTGREY);
  tft.setCursor(border, 200);
  tft.print("Total");
  tft.setTextColor(GREEN);
  tft.print(totalvalue);
  fillDonnut(60, border, 110, n, names, pourcent);
}

int validator() 
{

  unsigned int border = 20;
  tft.fillScreen(BLACK);
  tft.setTextColor(WHITE);
  tft.setCursor(border + 50, 0);
  tft.setTextSize(2);
  tft.println(validatorname);
  tft.setTextSize(1);
  tft.setTextColor(CYAN);
  tft.setCursor(border - 6, 40);
  tft.println("Deposited     Pending       Active       Exited");
  unsigned int h = 80;
  for (int i = border + 20; i < 210; i += 80) {
    tft.fillCircle(i, h, 20, GREEN);
    tft.fillCircle(i, h, 15, BLACK);
    if ((i + 40) >= 210) break;
    tft.drawLine(i + 30, h - 1, i + 50, h - 1, WHITE);
    tft.drawLine(i + 30, h, i + 50, h, WHITE);
    tft.drawLine(i + 30, h + 1, i + 50, h + 1, WHITE);
  }
  if (active) {
    tft.fillCircle(200, h, 20, GREEN);
    tft.fillCircle(200, h, 15, GREEN);
  }
  else {
    tft.fillCircle(200, h, 20, DARKGREY);
    tft.fillCircle(200, h, 15, RED);
  }

  tft.fillCircle(280, h, 20, DARKGREY);
  tft.fillCircle(280, h, 15, BLACK);
  tft.drawLine(200 + 30, h - 1, 200 + 50, h - 1, DARKGREY);
  tft.drawLine(200 + 30, h, 200 + 50, h, DARKGREY);
  tft.drawLine(200 + 30, h + 1, 200 + 50, h + 1, DARKGREY);

  tft.setTextSize(2);
  tft.setTextColor(LIGHTGREY);
  tft.setCursor(border, 120);
  tft.println(ch1);
  tft.setCursor(border, 150);
  tft.setTextColor(BLUE);
  tft.println(ch2);
  tft.setTextColor(LIGHTGREY);
  tft.setCursor(border, 190);
  tft.println(ch3);
  tft.setTextColor(GREEN);
  tft.setCursor(border, 220);
  tft.println(ch4);
}

int income() 
{
  unsigned int border = 20;
  tft.fillScreen(BLACK);
  tft.setTextColor(WHITE);
  tft.setCursor(border + 50, 0);
  tft.setTextSize(2);
  tft.println("Passive Income");
  tft.setTextSize(2);
  tft.setTextColor(LIGHTGREY);
  tft.setCursor(border, 50);
  tft.print("Day");
  tft.setTextColor(GREEN);
  tft.print(ch11);
  tft.setCursor(border, 80);
  tft.setTextColor(BLUE);
  tft.print(ch12);
  tft.setTextColor(LIGHTGREY);
  tft.setCursor(border, 110);
  tft.print("Month");
  tft.setTextColor(GREEN);
  tft.print(ch13);
  tft.setTextColor(BLUE);
  tft.setCursor(border, 140);
  tft.print(ch14);
  unsigned int l = 170;
  for (int i = 0; i < 28; i++) {
    tft.fillRect(border + i*10, l + (70 - graph[i]), 10, 70, CYAN);
    tft.drawLine(border + i*10, l + (70 - graph[i]), border + i*10, l + 70, DARKGREY);
  }
}

int next(unsigned int p, bool active)
{
  unsigned long cpt = 0;
  unsigned long refresh = 0;
  unsigned int h = 80;
  TouchScreen ts = TouchScreen(XP, YP, XM, YM, 300);
  while (1) {
    ts = TouchScreen(XP, YP, XM, YM, 300);
    if (ts.getPoint().x < 1000) {
      Adafruit_TFTLCD tft(LCD_CS, LCD_CD, LCD_WR, LCD_RD, LCD_RESET);
      tft.setRotation(1);
      return true;
    }
    if (serial()) {
      // decode
      unsigned int n_count = 1;
      bool b = true;
      while (n_count > 0) {
        // decode
        if (b && decode()) n_count -= 1;
        else {
          inputString = "";
          b = serial();
        }
        
      }
      Adafruit_TFTLCD tft(LCD_CS, LCD_CD, LCD_WR, LCD_RD, LCD_RESET);
      tft.setRotation(1);
      inputString = "";
      return false;
    }
    delay(10);
    if (p == 2) 
    {
      Adafruit_TFTLCD tft(LCD_CS, LCD_CD, LCD_WR, LCD_RD, LCD_RESET);
      tft.setRotation(1);
      if (cpt == 100) {
        tft.fillCircle(200, h, 15, BLACK);
      }
      if (cpt == 200) {
        if (active) {
          tft.fillCircle(200, h, 20, GREEN);
          tft.fillCircle(200, h, 15, GREEN);
        }
        else {
          tft.fillCircle(200, h, 20, DARKGREY);
          tft.fillCircle(200, h, 15, RED);
        }
        cpt = 0;
      }
    }
    cpt ++;

    if (first && refresh == 500) {
      if (p == 1) Serial.println("Page 1");
      if (p == 2) Serial.println("Page 2");
      if (p == 3) Serial.println("Page 3");
      first = false;
    }

    if (refresh == 120000) {
      if (p == 1) Serial.println("Page 1");
      if (p == 2) Serial.println("Page 2");
      if (p == 3) Serial.println("Page 3");
      refresh = 0;
    }
    refresh ++;
  }
}


int serial() {
  if (Serial.available()) {
    while (1) {
      if (Serial.available()) {
        // get the new byte:
        char inChar = (char)Serial.read();
        // if the incoming character is a newline, set a flag so the main loop can
        // do something about it:
        if (inChar == '#') {
          return true;
        }

        inputString += inChar;
      }
    }
  }
  return false;
}

int decode()
{
  Serial.println(inputString);

  char w = ' ';
  do {
    w = (char)Serial.read();
  } while (!(w == '0' || w == '1'));
  if (w != '1') return 0;

  if (inputString.charAt(0) == '1') {
    unsigned int cpt = 0;
    String curent = "";
    n = 0;
    for (int i = 1; i < inputString.length(); i++) {
      if (inputString.charAt(i) == '_') {
        cpt ++;
        if (cpt == 1) totalvalue = curent;
        if (cpt == 2) n = curent.toInt();
        if (cpt > 2 && cpt <= 2 + n) names[cpt -3] = curent;
        if (cpt > 2 + n && cpt <= 2 + 2*n) pourcent[cpt -3 -n] = curent.toInt();
        curent = "";
      } else {
        curent += inputString.charAt(i);
      }
    }
  }
  if (inputString.length() == 120 && inputString.charAt(0) == '2') {
    unsigned int cpt = 0;
    String curent = "";
    for (int i = 1; i < 120; i++) {
      if (inputString.charAt(i) == '_') {
        cpt ++;
        if (cpt == 1) validatorname = curent;
        if (cpt == 2) ch1 = curent;
        if (cpt == 3) ch2 = curent;
        if (cpt == 4) ch3 = curent;
        if (cpt == 5) ch4 = curent;
        if (cpt == 6) {
          if (curent.charAt(0) == '0') active = false;
          else active = true;
        }
        curent = "";
      } else {
        curent += inputString.charAt(i);
      }
    }
  }
  if (inputString.charAt(0) == '3') {
    unsigned int cpt = 0;
    String curent = "";
    for (int i = 1; i < inputString.length(); i++) {
      if (inputString.charAt(i) == '_') {
        cpt ++;
        if (cpt == 1) ch11 = curent;
        if (cpt == 2) ch12 = curent;
        if (cpt == 3) ch13 = curent;
        if (cpt == 4) ch14 = curent;
        if (cpt > 4 && cpt <= 4 + 28) graph[cpt - 5] = curent.toInt();
        curent = "";
      } else {
        curent += inputString.charAt(i);
      }
    }
  }
  return 1;
}

int wait_validation() {
  char w = ' ';
  do {
    w = (char)Serial.read();
  } while (w != '1');
}
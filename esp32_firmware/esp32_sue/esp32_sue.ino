#include <Arduino_GFX_Library.h>
#include <ESP32Servo.h>

// DISPLAY
#define TFT_MOSI 23
#define TFT_SCLK 18
#define TFT_CS   19
#define TFT_DC   21
#define TFT_RST  22

Arduino_DataBus *bus  = new Arduino_ESP32SPI(TFT_DC, TFT_CS, TFT_SCLK, TFT_MOSI, -1);
Arduino_GFX    *panel = new Arduino_GC9A01(bus, TFT_RST, 0);

// Local canvas covering only the pupil + iris region
// Iris radius = 30, pupil radius = 13, pupil travels x = 110~130
// Bounding box with margin: x=90~150 (w=60), y=84~156 (h=72)
#define CANVAS_X  90
#define CANVAS_Y  84
#define CANVAS_W  60
#define CANVAS_H  72

Arduino_GFX *sprite = new Arduino_Canvas(CANVAS_W, CANVAS_H, panel, CANVAS_X, CANVAS_Y);

// Local-space center (offset from canvas origin)
#define LCX  (120 - CANVAS_X)   // 30
#define LCY  (120 - CANVAS_Y)   // 36

// SERVO
Servo servo1;
#define SERVO1_PIN 4

// COLORS
#define BLACK      0x0000
#define WHITE      0xFFFF
#define SCLERA     0xEF7D
#define IRIS_DARK  0x0015
#define IRIS_MID   0x027F
#define IRIS_LIGHT 0x3DFF
#define SHADOW     0x4208

#define CX 120
#define CY 120


// Draw full static eye directly to panel — called ONCE in setup()
void drawStaticEye()
{
  panel->fillScreen(BLACK);
  // eyeball
  panel->fillCircle(CX, CY, 65, SCLERA);
  // iris
  panel->fillCircle(CX, CY, 30, IRIS_DARK);
  panel->fillCircle(CX, CY, 24, IRIS_MID);
  panel->fillCircle(CX, CY, 16, IRIS_LIGHT);
  
  panel->fillRoundRect(35, 40, 170, 20, 10, SHADOW);
}


// Redraw pupil region into sprite buffer, flush patch to screen
void drawPupil(int pupilX)
{
  int lx = pupilX - CANVAS_X;   // pupil x in local canvas space

  // clear sprite and redraw iris layers that fall inside this region
  sprite->fillScreen(BLACK);
  sprite->fillCircle(LCX, LCY, 65, SCLERA);
  sprite->fillCircle(LCX, LCY, 30, IRIS_DARK);
  sprite->fillCircle(LCX, LCY, 24, IRIS_MID);
  sprite->fillCircle(LCX, LCY, 16, IRIS_LIGHT);

  // pupil + highlight in local coords
  sprite->fillCircle(lx,     LCY,     13, BLACK);
  sprite->fillCircle(lx - 4, LCY - 6,  4, WHITE);

  // push sprite patch to screen — only 60×72 = 4320 pixels over SPI
  ((Arduino_Canvas *)sprite)->flush();
}


void setup()
{
  Serial.begin(115200);
  Serial.print("MaxAllocHeap: "); Serial.println(ESP.getMaxAllocHeap());

  panel->begin();
  panel->setRotation(2);

  Serial.println("panel ok");

  sprite->begin();

  Serial.println("sprite ok");

  servo1.setPeriodHertz(50);
  servo1.attach(SERVO1_PIN, 500, 2400);

  drawStaticEye();   // full background drawn once to panel GRAM
  drawPupil(CX);     // initial pupil
}


void loop()
{
  // sweep 0 → 180
  for (int pos = 0; pos <= 120; pos++)
  {
    servo1.write(pos);
    int pupilX = map(pos, 0, 180, 110, 130);
    drawPupil(pupilX);
    delay(2);
  }

  delay(500);

  // sweep 180 → 0
  for (int pos = 100; pos >= 0; pos--)
  {
    servo1.write(pos);
    int pupilX = map(pos, 0, 180, 110, 130);
    drawPupil(pupilX);
    delay(2);
  }

  delay(500);
}
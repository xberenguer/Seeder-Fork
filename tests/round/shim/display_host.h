#pragma once
#include <Arduino_GFX.h>
#include <canvas/Arduino_Canvas.h>
using SeederDisplay = Arduino_Canvas;
extern SeederDisplay tft;
namespace roundBoard {
  bool begin();
  void present();
}

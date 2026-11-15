#pragma once
#include "boards/board.h"

#if defined(SEEDER_BOARD_WAVESHARE175C)
  #include <Arduino_GFX_Library.h>
  using SeederDisplay = Arduino_Canvas;
  extern SeederDisplay tft;
  namespace roundBoard {
    bool begin();
    void present();
  }
#elif defined(SEEDER_BOARD_STICKS3)
  #include <M5Unified.h>
  using SeederDisplay = M5GFX;
  // One panel instance: the UI paints directly on M5Unified's display.
  extern SeederDisplay &tft;
#else
  #include <TFT_eSPI.h>
  using SeederDisplay = TFT_eSPI;
  extern SeederDisplay tft;
#endif

#include "../boards/board.h"
#if defined(SEEDER_BOARD_WAVESHARE175C)
#include <TFT_eSPI.h>
#include "bitmaker_reference.h"

namespace {
// Never initialize or write this hardware parent. All original drawing goes
// into TFT_eSprite, using the exact vendored TFT_eSPI fonts and rasterizer.
TFT_eSPI unusedPanel;
}
TFT_eSprite bitmakerCanvas(&unusedPanel);
namespace { TFT_eSprite captionCanvas(&unusedPanel); }

void bitmakerDelay(unsigned long ms) {
  bitmaker::showSplashFrame();
  ::delay(ms);
}

namespace bitmaker {
bool begin() {
  bitmakerCanvas.setColorDepth(16);
  if(!bitmakerCanvas.createSprite(240, 135)) return false;
  bitmakerCanvas.setSwapBytes(true);
  bitmakerCanvas.fillSprite(0);
  captionCanvas.setColorDepth(16);
  if(!captionCanvas.createSprite(240, 8)) return false;
  captionCanvas.setSwapBytes(true);
  captionCanvas.fillSprite(0);
  return true;
}
void prepareHold(){bitmakerCanvas.drawFastVLine(183,0,135,0x2945);}
uint16_t pixel(int x, int y) { return bitmakerCanvas.readPixel(x, y); }
void renderCaption(const char *text, uint16_t color) {
  captionCanvas.fillSprite(0);
  captionCanvas.setTextFont(1);
  captionCanvas.setTextSize(1);
  captionCanvas.setTextColor(color, 0);
  for(int i=0; text[i] && i<40; ++i)
    captionCanvas.drawChar(text[i], i*6, 0, 1);
}
uint16_t captionPixel(int x, int y) { return captionCanvas.readPixel(x, y); }
}

// These are symbol adapters only. The included upstream source, assets,
// theme, font selections, pixel sizes and primitive drawing are unmodified.
#undef UI_W
#undef UI_H
#undef UI_REF_W
#undef UI_REF_H
#undef SX
#undef SY
#undef PIN_MOVE
#undef PIN_SELECT
#define ui bitmakerUi
#define tft bitmakerCanvas
#define TFT_eSPI TFT_eSprite
#define delay bitmakerDelay
#include "bitmaker/src/ui/ui.cpp.inc"
#undef delay
#undef TFT_eSPI
#undef tft
#undef ui
#endif

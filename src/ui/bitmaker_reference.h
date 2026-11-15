#pragma once
#include <Arduino.h>

// The upstream declarations get their own namespace; the original file is
// retained byte-for-byte under bitmaker/, together with its provenance hashes.
#define ui bitmakerUi
#include "bitmaker/src/ui/ui.h"
#undef ui

namespace bitmaker {
bool begin();
uint16_t pixel(int x, int y);
void prepareHold();
void renderCaption(const char *text, uint16_t color);
uint16_t captionPixel(int x, int y);
void showSplashFrame(); // Placement-only compositor implemented by round_ui.cpp.
}

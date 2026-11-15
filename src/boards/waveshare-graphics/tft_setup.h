#pragma once
// TFT_eSPI is a software sprite renderer here. Its panel is never initialized;
// Arduino_GFX alone owns the Waveshare's actual QSPI panel. Use the original
// bitmap/GFX fonts without adding filesystem-backed smooth-font dependencies.
#define USER_SETUP_LOADED
#define ST7789_DRIVER
#define TFT_WIDTH 240
#define TFT_HEIGHT 135
#define LOAD_GLCD
#define LOAD_FONT2
#define LOAD_FONT4
#define LOAD_FONT6
#define LOAD_FONT7
#define LOAD_FONT8
#define LOAD_GFXFF

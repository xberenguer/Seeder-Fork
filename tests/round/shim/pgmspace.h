#pragma once
#include "Arduino.h"
#define pgm_read_byte(p) (*(const uint8_t *)(p))
#define pgm_read_word(p) (*(const uint16_t *)(p))
// Preserve host-sized font pointers; scalar uint32_t reads remain uint32_t.
#define pgm_read_dword(p) (*(p))
#define memcpy_P memcpy
#define strlen_P strlen
#define strcpy_P strcpy
#define PGM_P const char *

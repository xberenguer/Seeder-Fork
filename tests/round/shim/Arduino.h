#pragma once
#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <cstdarg>
#include "pgmspace.h"
using std::min;
using std::max;
using byte = uint8_t;
class __FlashStringHelper;
#define PROGMEM
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define F(s) (s)
#define bitSet(value, bit) ((value) |= (1UL << (bit)))
#define bitClear(value, bit) ((value) &= ~(1UL << (bit)))
#define bitRead(value, bit) (((value) >> (bit)) & 1U)
#define constrain(v, a, b) min(max((v), (a)), (b))

// Host only: display rendering uses the production Arduino_GFX canvas/font.
class String : public std::string {
 public:
  using std::string::string;
  using std::string::operator=;
  String(const std::string &s) : std::string(s) {}
  int indexOf(char c, int start = 0) const {
    auto p = find(c, start); return p == npos ? -1 : int(p);
  }
  String substring(int start) const { return substr(start); }
  String substring(int start, int end) const { return substr(start, end - start); }
  void toUpperCase() {
    std::transform(begin(), end(), begin(), [](unsigned char c) { return std::toupper(c); });
  }
  void toCharArray(char *out, size_t size) const {
    if(size) { std::strncpy(out, c_str(), size); out[size-1] = 0; }
  }
};
void delay(unsigned long);
unsigned long millis();
void pinMode(uint8_t, uint8_t);
int digitalRead(uint8_t);
void digitalWrite(uint8_t, uint8_t);
inline uint16_t word(uint8_t hi, uint8_t lo) { return (uint16_t(hi) << 8) | lo; }
inline unsigned long micros() { return millis() * 1000; }
inline void delayMicroseconds(unsigned) {}
inline long random(long n) { return n ? ::random() % n : 0; }
inline char *ltoa(long value, char *out, int) { std::sprintf(out, "%ld", value); return out; }
inline char *dtostrf(double value, int width, unsigned precision, char *out) {
  std::sprintf(out, "%*.*f", width, int(precision), value); return out;
}

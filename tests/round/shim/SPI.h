#pragma once
#include <cstdint>
#include <cstdlib>
#define MSBFIRST 1
#define SPI_MODE0 0
#define SPI_MODE3 3
struct SPISettings { SPISettings(uint32_t, int, int) {} };
// Sprite rendering must never use a physical SPI bus, even indirectly.
struct SPIClass {
  void begin() { std::abort(); }
  void end() { std::abort(); }
  void beginTransaction(const SPISettings &) { std::abort(); }
  void endTransaction() { std::abort(); }
  void setFrequency(uint32_t) { std::abort(); }
  uint8_t transfer(uint8_t) { std::abort(); }
  uint16_t transfer16(uint16_t) { std::abort(); }
};
extern SPIClass SPI;

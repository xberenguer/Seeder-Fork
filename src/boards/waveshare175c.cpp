#include "board.h"
#if defined(SEEDER_BOARD_WAVESHARE175C)
#include "../display.h"
#include <Wire.h>
#include <esp_log.h>

namespace {
Arduino_ESP32QSPI bus(12, 38, 4, 5, 6, 7);

// Keep the panel dark until the first complete frame has been transferred.
class SeederPanel : public Arduino_CO5300 {
 public:
  // Arduino_GFX 1.5.9 includes the IPS argument before width/height.
  SeederPanel() : Arduino_CO5300(&bus, 1, 0, false, UI_W, UI_H, 6, 0, 0, 0) {}
 protected:
  void tftInit() override {
    pinMode(_rst, OUTPUT);
    digitalWrite(_rst, HIGH); delay(10);
    digitalWrite(_rst, LOW); delay(CO5300_RST_DELAY);
    digitalWrite(_rst, HIGH); delay(CO5300_RST_DELAY);
    static const uint8_t init[] = {
      BEGIN_WRITE, WRITE_COMMAND_8, CO5300_C_SLPOUT,
      END_WRITE, DELAY, CO5300_SLPOUT_DELAY,
      BEGIN_WRITE, WRITE_C8_D8, 0xFE, 0x00,
      WRITE_C8_D8, CO5300_W_SPIMODECTL, 0x80,
      WRITE_C8_D8, CO5300_W_PIXFMT, 0x55,
      WRITE_C8_D8, CO5300_W_WCTRLD1, 0x20,
      WRITE_C8_D8, CO5300_W_WDBRIGHTNESSVALHBM, 0xFF,
      WRITE_C8_D8, CO5300_W_WDBRIGHTNESSVALNOR, 0x00,
      WRITE_C8_D8, CO5300_W_WCE, 0x00,
      WRITE_COMMAND_8, CO5300_C_DISPOFF, END_WRITE, DELAY, 10
    };
    _bus->batchOperation(init, sizeof(init));
    invertDisplay(false);
  }
} panel;

int readRegister(uint8_t address, uint8_t reg) {
  Wire.beginTransmission(address); Wire.write(reg);
  if(Wire.endTransmission() || Wire.requestFrom(address, size_t(1)) != 1) return -1;
  return Wire.read();
}
void writeRegister(uint8_t address, uint8_t reg, uint8_t value) {
  Wire.beginTransmission(address); Wire.write(reg); Wire.write(value);
  Wire.endTransmission();
}

void quietUnusedDevices() {
  // Power down the QMI8658 without starting any sensor sampling.
  if(readRegister(0x6b, 0x00) == 0x05) {
    const int c7 = readRegister(0x6b, 0x08), c1 = readRegister(0x6b, 0x02);
    if(c7 >= 0 && c1 >= 0) {
      writeRegister(0x6b, 0x08, uint8_t(c7 & ~3));
      writeRegister(0x6b, 0x02, uint8_t(c1 | 2));
    }
  }
  // Stop all ES7210 microphone channels/clocks left by another application.
  if(readRegister(0x40, 0x01) >= 0) {
    for(uint8_t reg = 0x47; reg <= 0x4c; ++reg) writeRegister(0x40, reg, 0xff);
    writeRegister(0x40, 0x01, 0x7f);
    writeRegister(0x40, 0x06, 0x07);
  }
}
} // namespace

SeederDisplay tft(UI_W, UI_H, &panel);

namespace roundBoard {
bool begin() {
  esp_log_level_set("*", ESP_LOG_NONE);
  pinMode(0, INPUT_PULLUP);
  pinMode(3, INPUT);
  pinMode(46, OUTPUT); digitalWrite(46, LOW); // Amplifier disabled.
  pinMode(2, OUTPUT); digitalWrite(2, LOW);   // Touch held in reset.
  Wire.begin(15, 14); Wire.setClock(400000); Wire.setTimeOut(20);
  // Preserve AXP2101 power rails, charging configuration and factory NVS.
  quietUnusedDevices();
  if(!psramFound() || !tft.begin(40000000)) return false;
  if(panel.width() != UI_W || panel.height() != UI_H) return false;
  tft.setRotation(SEEDER_CANVAS_ROTATION);
  tft.setTextWrap(false);
  tft.fillScreen(0);
  tft.flush();
  panel.displayOn();
  panel.setBrightness(128);
  return true;
}
void present() { tft.flush(); }
} // namespace roundBoard
#endif

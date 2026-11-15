#include "display_host.h"
#include "ui/ui.h"
#include "GlobalVARS.h"
#include "gpio.h"
#include "workflow.h"
#include "ui/bitmaker_reference.h"
#include "SPI.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>

SeederDisplay tft(UI_W, UI_H, nullptr);
sWallet myWallet;
sButton btnMove(PIN_MOVE);
sButton btnSelect(PIN_SELECT, true);
static unsigned long now = 100;
static int levels[64] = {HIGH, 0, 0, LOW};
void delay(unsigned long);
unsigned long millis() { return now; }
void pinMode(uint8_t, uint8_t) {}
int digitalRead(uint8_t pin) { return levels[pin]; }
void digitalWrite(uint8_t, uint8_t) { std::abort(); }
SPIClass SPI;
namespace roundBoard {
bool begin() { return true; }
void present() {} // Frames are captured explicitly below.
}

struct Placement {int sx, sy, w, h, dx, dy, dw, dh, rotation;};
static std::vector<Placement> placements;
struct QrPlacement {int version, modules, scale, x, y, quiet;};
static QrPlacement qrPlacement;
static bool hasQr = false;
static const char *qrKind = "seed";
struct HeaderBand {int y, h; uint16_t color;};
static HeaderBand headerBand;
static bool hasHeaderBand = false;
struct AssetPlacement {int id, x, y;};
static std::vector<AssetPlacement> assets;
struct AddressGlyph {int index, sx, sy, dx, dy; uint16_t color;};
static std::vector<AddressGlyph> addressGlyphs;
struct Caption {std::string text;int x,y,w,h;uint16_t color;};
static std::vector<Caption> captions;
static int exitProgress=-1;
static bool exitHolding=false;
static bool splashCapture = false;
void roundVerifyBegin() {
  placements.clear(); assets.clear(); addressGlyphs.clear(); captions.clear(); hasQr = false; hasHeaderBand = false;
  qrKind = "seed";
  exitProgress=-1;exitHolding=false;
}
void roundVerifyCopy(int sx, int sy, int w, int h, int dx, int dy, int dw, int dh) {
  assert(sx >= 0 && sy >= 0 && sx + w <= 240 && sy + h <= 135);
  assert(w > 0 && h > 0 && dw > 0 && dh > 0);
  assert(dx >= 0 && dy >= 0 && dx + dw <= 466 && dy + dh <= 466);
  placements.push_back({sx,sy,w,h,dx,dy,dw,dh,0});
}
void roundVerifyRotatedCopy(int sx, int sy, int w, int h, int dx, int dy, int dw, int dh, int rotation) {
  assert(rotation == 3); // The original Exit triangle turns CCW90 toward OK.
  roundVerifyCopy(sx,sy,w,h,dx,dy,dw,dh);
  placements.back().rotation = rotation;
}
void roundVerifyQr(int version, int modules, int scale, int x, int y, int quiet) {
  assert(modules == version * 4 + 17 && scale > 0);
  const int side = (modules + 2*quiet) * scale;
  assert(x >= 0 && y >= 0 && x + side <= 466 && y + side <= 466);
  qrPlacement = {version,modules,scale,x,y,quiet}; hasQr = true;
  qrKind = "seed";
}
void roundVerifyAddressQr(int version, int modules, int scale, int x, int y, int quiet) {
  roundVerifyQr(version,modules,scale,x,y,quiet); qrKind = "address";
}
void roundVerifyHeaderBand(int y, int h, uint16_t color) {
  assert(y >= 0 && h > 0 && y + h <= 466 && color == 0x86f3);
  headerBand = {y,h,color}; hasHeaderBand = true;
}
void roundVerifyAsset(int id, int x, int y) {
  assert(id >= 0 && id < 5 && x >= 0 && y >= 0 && x < 466 && y < 466);
  assets.push_back({id,x,y});
}
void roundVerifyAddressGlyph(int index, int sx, int sy, int dx, int dy, uint16_t color) {
  assert(index >= 0 && index < 42);
  assert(sx >= 0 && sy >= 0 && sx + 12 <= 240 && sy + 16 <= 135);
  assert(dx >= 0 && dy >= 0 && dx + 18 <= 466 && dy + 24 <= 466);
  assert(color == 0x86f3 || color == 0xffff);
  addressGlyphs.push_back({index,sx,sy,dx,dy,color});
}
void roundVerifyCaption(const char *text,int x,int y,int w,int h,uint16_t color) {
  assert(x>=0 && y>=0 && w>0 && h==12 && x+w<=466 && y+h<=466);
  captions.push_back({text,x,y,w,h,color});
}
void roundVerifyExitProgress(int filled,bool holding) {
  assert(filled>=0 && filled<=216);exitProgress=filled;exitHolding=holding;
}
static void ppmPixel(std::ofstream &out, uint16_t p) {
  const char rgb[] = {char((p >> 11)*255/31), char(((p >> 5)&63)*255/63), char((p&31)*255/31)};
  out.write(rgb,3);
}
static void save(const std::string &name) {
  std::ofstream view(name + ".ppm", std::ios::binary), raw(name + "-panel.ppm", std::ios::binary);
  std::ofstream reference(name + "-original.ppm", std::ios::binary), map(name + ".json");
  view << "P6\n466 466\n255\n"; raw << "P6\n466 466\n255\n";
  reference << "P6\n240 135\n255\n";
  const uint16_t *frame = tft.getFramebuffer();
  // Production canvas rotates the output CW90 to compensate for the enclosure
  // being held with its former right-side buttons at the top.
  for(int y=0;y<466;++y) for(int x=0;x<466;++x) {
    ppmPixel(view,frame[x*466 + (465-y)]);
    ppmPixel(raw,frame[y*466+x]);
  }
  for(int y=0;y<135;++y) for(int x=0;x<240;++x) ppmPixel(reference,bitmaker::pixel(x,y));
  map << "{\"placements\":[";
  for(size_t i=0;i<placements.size();++i) {
    if(i) map << ",";
    const auto &p=placements[i];
    map << "["<<p.sx<<","<<p.sy<<","<<p.w<<","<<p.h<<","<<p.dx<<","<<p.dy<<","<<p.dw<<","<<p.dh;
    if(p.rotation) map << "," << p.rotation;
    map << "]";
  }
  map << "],\"qr\":";
  if(hasQr) {
    const auto &q=qrPlacement;
    map << "["<<q.version<<","<<q.modules<<","<<q.scale<<","<<q.x<<","<<q.y<<","<<q.quiet<<"]";
  } else map << "null";
  map << ",\"qr_kind\":\"" << qrKind << "\",\"header_band\":";
  if(hasHeaderBand) map << "[" << headerBand.y << "," << headerBand.h << "," << headerBand.color << "]";
  else map << "null";
  map << ",\"assets\":[";
  for(size_t i=0;i<assets.size();++i) {
    if(i) map << ",";
    map << "[" << assets[i].id << "," << assets[i].x << "," << assets[i].y << "]";
  }
  map << "],\"address_glyphs\":[";
  for(size_t i=0;i<addressGlyphs.size();++i) {
    if(i) map << ",";
    const auto &g=addressGlyphs[i];
    map << "[" << g.index << "," << g.sx << "," << g.sy << "," << g.dx << "," << g.dy << "," << g.color << "]";
  }
  map << "],\"captions\":[";
  for(size_t i=0;i<captions.size();++i) {
    if(i)map << ",";
    const auto &c=captions[i];
    map << "[\""<<c.text<<"\","<<c.x<<","<<c.y<<","<<c.w<<","<<c.h<<","<<c.color<<"]";
  }
  map << "],\"exit_progress\":";
  if(exitProgress<0)map << "null";
  else map << "["<<exitProgress<<","<<(exitHolding?1:0)<<"]";
  map << "}\n";
}
void delay(unsigned long) {
  if(splashCapture) {
    static int n=0;
    save(n++ ? "02-splash-credits" : "01-splash-brand");
  }
}
static void service() {
  btnMove.check(); btnSelect.check();
  switch(myWallet.State) {
    case STATE_INITMENU: doInitMenu(); break;
    case STATE_WORDS: doMenuWords(); break;
    case STATE_COINSEED: doCoinSeed(); break;
    case STATE_DICESEED: doDiceSeed(); break;
    case STATE_SEED: doShowSeed(); break;
  }
}
static void ticks(unsigned ms) {
  for(unsigned elapsed = 0; elapsed < ms; elapsed += 10) { now += 10; service(); }
}
static void press(int pin, unsigned duration = 80) {
  levels[pin] = pin == PIN_SELECT ? HIGH : LOW; ticks(duration);
  levels[pin] = pin == PIN_SELECT ? LOW : HIGH; ticks(80);
}
extern int menuSeed;
extern uint8_t entropy[32];
extern char diceRolls[];

static void workflowChecks() {
  // Exercise the real detector and real workflow, with the board's opposite
  // button polarities. No forceClick shortcuts for seed entry.
  std::ofstream counterReport("workflow-counters.json");
  counterReport << "[";
  bool firstCounter = true;
  auto recordCounter = [&](const char *expected) {
    if(!firstCounter) counterReport << ",";
    firstCounter = false;
    counterReport << "{\"expected\":\"" << expected << "\",\"source_pixels\":[";
    for(int y=0;y<8;++y) for(int x=0;x<18;++x) {
      if(x || y) counterReport << ",";
      counterReport << bitmaker::pixel(10+x,114+y);
    }
    counterReport << "],\"display_pixels\":[";
    const uint16_t *frame=tft.getFramebuffer();
    for(int y=0;y<16;++y) for(int x=0;x<36;++x) {
      if(x || y) counterReport << ",";
      counterReport << frame[(307+x)*466+(465-(36+y))];
    }
    counterReport << "]}";
  };
  myWallet.State = STATE_INITMENU; myWallet.entropySrc = coinEntropy;
  ticks(80); press(PIN_SELECT);
  assert(myWallet.State == STATE_WORDS && myWallet.nWords == 12);
  press(PIN_SELECT); assert(myWallet.State == STATE_COINSEED);
  press(PIN_MOVE); assert(myWallet.nBCoinEntropy == 1 && entropy[0] == 0x80);
  press(PIN_SELECT); assert(myWallet.nBCoinEntropy == 2 && entropy[0] == 0x80);
  press(PIN_SELECT, 1600); // Cancel an armed discard on release.
  assert(myWallet.State == STATE_COINSEED && myWallet.nBCoinEntropy == 2);
  press(PIN_SELECT, 3200); // Confirm discard; release must not enter a bit.
  assert(myWallet.State == STATE_INITMENU && myWallet.nBCoinEntropy == 0);
  for(int i = 0; i < 32; ++i) assert(entropy[i] == 0);
  press(PIN_SELECT); press(PIN_SELECT);
  for(int i = 0; i < 128; ++i) press(PIN_SELECT);
  assert(myWallet.State == STATE_SEED && menuSeed == SHOW_SEED1);
  assert(myWallet.mnemonic == "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about");
  assert(myWallet.firstAddress == "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu");
  // On generated-seed pages only: big OK advances and small MOVE reverses.
  // Both directions still wrap, while a held OK at Exit clears the seed.
  press(PIN_MOVE); assert(menuSeed == SHOW_EXIT);
  press(PIN_SELECT); assert(menuSeed == SHOW_SEED1);
  const int order12[] = {SHOW_DATA1, SHOW_ENTROPY, SHOW_EXPORTQR, SHOW_EXPORTZPUB, SHOW_EXIT};
  for(int page : order12) {
    press(PIN_SELECT); assert(menuSeed == page);
    if(page == SHOW_EXPORTQR) recordCounter("4/5");
    if(page == SHOW_EXPORTZPUB) recordCounter("5/5");
  }
  press(PIN_MOVE); assert(menuSeed == SHOW_EXPORTZPUB);
  press(PIN_SELECT);
  const uint16_t *exitFrame=tft.getFramebuffer();
  std::vector<uint16_t> exitIdle(exitFrame,exitFrame+466*466);
  press(PIN_SELECT, 1600);
  assert(myWallet.State==STATE_SEED && menuSeed==SHOW_EXIT && !myWallet.mnemonic.empty());
  assert(std::equal(exitIdle.begin(),exitIdle.end(),tft.getFramebuffer()));
  levels[PIN_SELECT]=HIGH;ticks(1400);
  press(PIN_MOVE);assert(menuSeed==SHOW_EXIT); // MOVE is ignored during armed reset.
  levels[PIN_SELECT]=LOW;ticks(80);
  assert(myWallet.State==STATE_SEED && menuSeed==SHOW_EXIT && !myWallet.mnemonic.empty());
  press(PIN_SELECT, 3200);
  assert(myWallet.State == STATE_INITMENU && myWallet.mnemonic.empty());
  press(PIN_MOVE); assert(myWallet.entropySrc == diceEntropy);
  press(PIN_SELECT); press(PIN_MOVE);
  assert(myWallet.nWords == 24);
  press(PIN_SELECT); assert(myWallet.State == STATE_DICESEED);
  press(PIN_MOVE); assert(myWallet.nRolls == 0);
  press(PIN_SELECT); assert(myWallet.nRolls == 1 && diceRolls[0] == '2');
  press(PIN_SELECT, 1600); assert(myWallet.nRolls == 1);
  for(int i = 1; i < 99; ++i) press(PIN_SELECT);
  assert(myWallet.State == STATE_SEED && menuSeed == SHOW_SEED1);
  press(PIN_SELECT); assert(menuSeed == SHOW_SEED2);
  press(PIN_SELECT); assert(menuSeed == SHOW_DATA1);
  press(PIN_MOVE); assert(menuSeed == SHOW_SEED2);
  press(PIN_SELECT); assert(menuSeed == SHOW_DATA1);
  press(PIN_SELECT); assert(menuSeed == SHOW_ENTROPY);
  press(PIN_SELECT); assert(menuSeed == SHOW_EXPORTQR); recordCounter("5/6");
  press(PIN_SELECT); assert(menuSeed == SHOW_EXPORTZPUB); recordCounter("6/6");
  press(PIN_MOVE); assert(menuSeed == SHOW_EXPORTQR);
  counterReport << "]\n";
  std::cout << "PASS: real active-low/high buttons, canceled/confirmed holds, 128-bit coin entry, 99 dice rolls, big-forward/small-back 12/24-word navigation and export order.\n";
}

int main() {
  assert(tft.begin()); tft.setRotation(SEEDER_CANVAS_ROTATION); tft.setTextWrap(false);
  splashCapture=true; ui::splash(); splashCapture=false;
  ui::menu(false); save("03-menu-coin"); ui::menu(true); save("04-menu-dice");
  ui::words(12); save("05-words-12"); ui::words(24); save("06-words-24");
  uint8_t data[32]={};
  ui::coinEnter(128); ui::coinUpdate(0,128,data); save("07-coin-start");
  data[0]=0xa5;data[1]=0xf0;
  ui::coinUpdate(16,256,data); save("08-coin-progress");
  uint8_t hist[3]={2,5,6};
  ui::diceEnter(99); ui::diceUpdate(7,99,6,hist); save("09-dice-progress");
  ui::holdEnter(); ui::holdUpdate(.5f); save("10-hold");
  ui::generating(); save("11-generating");
  const String widest="abstract acoustic broccoli daughter electric favorite identify language marriage midnight strategy umbrella";
  ui::mnemonic(widest,12,0,1,5); save("12-mnemonic-wide");
  ui::mnemonic(widest+" "+widest,24,12,2,6); save("13-mnemonic-24");
  ui::seedAddress("bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu",2,5); save("14-address");
  ui::seedEntropy("000102030405060708090A0B0C0D0E0F",3,5); save("15-entropy-16");
  ui::seedEntropy("000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F",4,6); save("16-entropy-32");
  const String mnemonic="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
  const String mnemonic24="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art";
  ui::seedQr(mnemonic,12,4,5); save("17-export-12");
  ui::seedQr(mnemonic24,24,5,6); save("18-export-24");
  ui::seedZpubQr("zpub6rFR7y4Q2AijBEqTUquhVz398htDFrtymD1mfWTWvUqWxL2umYHFKQFm7ikXtRmhAbAxbyxDSdL36mhkBTjm7Exz6mnNw63zgRwRB3j4L5s","73c5da0a",5,5);
  save("19-watch-only"); ui::seedExit(); save("20-exit");
  ui::seedZpubQr("zpub6rFR7y4Q2AijBEqTUquhVz398htDFrtymD1mfWTWvUqWxL2umYHFKQFm7ikXtRmhAbAxbyxDSdL36mhkBTjm7Exz6mnNw63zgRwRB3j4L5s","73c5da0a",6,6);
  save("21-watch-only-24");
  ui::seedQr("rule opera robot moon exhibit logic minute priority proof pigeon erase include voyage cable humor index club uncover ride furnace diagram age tape jeans",24,5,6);
  save("22-export-24-v7");
  ui::seedQr("abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract abstract banner",24,5,6);
  save("23-export-24-v9");
  ui::seedExit();ui::holdEnter();ui::holdUpdate(.5f);save("24-exit-hold-half");
  ui::holdUpdate(1.0f);save("25-exit-hold-full");
  workflowChecks();
}

#include "../boards/board.h"
#if defined(SEEDER_BOARD_WAVESHARE175C)
#include "../display.h"
#include "ui.h"
#include "bitmaker_reference.h"
#include "round_brand.h"
#include "../qrcoded.h"

// Original BitMaker artwork/font pixels, enlarged uniformly with nearest
// sampling. The native renderer stays unchanged; only composition/scale changes.
#if defined(SEEDER_UI_VERIFY)
void roundVerifyBegin();
void roundVerifyCopy(int,int,int,int,int,int,int,int);
void roundVerifyRotatedCopy(int,int,int,int,int,int,int,int,int);
void roundVerifyQr(int,int,int,int,int,int);
void roundVerifyAddressQr(int,int,int,int,int,int);
void roundVerifyHeaderBand(int,int,uint16_t);
void roundVerifyAsset(int,int,int);
void roundVerifyAddressGlyph(int,int,int,int,int,uint16_t);
void roundVerifyCaption(const char*,int,int,int,int,uint16_t);
void roundVerifyExitProgress(int,bool);
#endif
namespace {
constexpr int C=233;
constexpr int QR_QUIET=2;
int splashFrame=0;
void startFrame() {
  tft.fillScreen(0);
#if defined(SEEDER_UI_VERIFY)
  roundVerifyBegin();
#endif
}
void copy(int sx,int sy,int w,int h,int dx,int dy,int dw,int dh) {
#if defined(SEEDER_UI_VERIFY)
  roundVerifyCopy(sx,sy,w,h,dx,dy,dw,dh);
#endif
  for(int y=0;y<dh;++y) {
    const int sourceY=sy+y*h/dh;
    int lastX=-1; uint16_t color=0;
    for(int x=0;x<dw;++x) {
      const int sourceX=sx+x*w/dw;
      if(sourceX!=lastX) {
        color=bitmaker::pixel(sourceX,sourceY);lastX=sourceX;
      }
      // Every frame starts black. Empty padding need not be written again.
      if(color) tft.drawPixel(dx+x,dy+y,color);
    }
  }
}
void centerInk(int sx,int sy,int w,int h,int cx,int dy,int numerator=2,int denominator=1) {
  int first=w,last=-1;
  for(int y=0;y<h;++y) for(int x=0;x<w;++x)
    if(bitmaker::pixel(sx+x,sy+y)) {if(x<first)first=x;if(x>last)last=x;}
  if(last<first)return;
  const int sw=last-first+1;
  const int dw=(sw*numerator+denominator/2)/denominator;
  const int dh=(h*numerator+denominator/2)/denominator;
  copy(sx+first,sy,sw,h,cx-dw/2,dy,dw,dh);
}
void exitPointer() {
  // Reorient the original right-pointing triangle toward the big top-left
  // OK button. Only this small indicator rotates; all lettering stays upright.
#if defined(SEEDER_UI_VERIFY)
  roundVerifyRotatedCopy(233,100,7,30,126,39,60,14,3);
#endif
  for(int y=0;y<14;++y)for(int x=0;x<60;++x) {
    const uint16_t color=bitmaker::pixel(233+(13-y)/2,100+x/2);
    if(color)tft.drawPixel(126+x,39+y,color);
  }
}
void finish() {roundBoard::present();}
void asset(int id,int x,int y) {
#if defined(SEEDER_UI_VERIFY)
  roundVerifyAsset(id,x,y);
#endif
  const auto &a=roundBrand::assets[id];
  // Opaque: black lettering must replace the green banner background too.
  for(int row=0;row<a.h;++row)for(int col=0;col<a.w;++col)
    tft.drawPixel(x+col,y+row,a.pixels[row*a.w+col]);
}
void splashPlacement() {
  startFrame();
  if(splashFrame++==0) {
    copy(0,103,240,32,41,290,384,51);
    asset(roundBrand::Splash,73,149);
  } else {
    copy(0,100,240,35,41,285,384,56);
    asset(roundBrand::CreditsLogo,152,146);
    asset(roundBrand::CreditsPowered,137,247);
  }
  finish();
}
void header() {
  copy(0,0,140,20,43,66,280,40);
  copy(190,0,50,20,323,66,100,40);
  copy(0,20,240,2,33,109,400,3);
}
void menuPlacement() {
  startFrame();
  // Full-bleed color band: the circular panel clips it exactly at its edge.
#if defined(SEEDER_UI_VERIFY)
  roundVerifyHeaderBand(94,54,0x86f3);
#endif
  tft.fillRect(0,94,466,54,0x86f3);
  asset(roundBrand::MenuWordmark,68,101);
  asset(roundBrand::MenuLeaf,358,96);
  copy(0,36,214,52,53,172,360,87);
  copy(0,88,214,47,53,278,360,79);
  // Big left button = OK/check; small right button = MOVE/arrows.
  copy(215,99,25,24,130,27,50,48);
  copy(215,52,25,27,282,31,50,54);
  finish();
}
void captureControls() {
  copy(184,90,56,45,100,16,112,90);
  copy(184,8,56,36,254,16,112,72);
}
void coinPlacement() {
  startFrame();
  copy(0,0,183,20,50,95,366,40);
  copy(0,20,183,50,50,135,366,100);
  copy(0,70,183,18,50,251,366,36);
  copy(0,88,183,29,50,300,366,58);
  copy(0,117,183,18,50,381,366,36);
  captureControls();finish();
}
void dicePlacement() {
  startFrame();
  copy(0,0,104,20,46,95,208,40);
  copy(0,20,104,58,46,145,208,116);
  copy(104,0,79,81,252,125,158,162);
  copy(0,78,104,27,129,304,208,54);
  copy(0,105,183,30,50,357,366,60);
  captureControls();finish();
}
uint8_t originalQrVersion(size_t length) {
  if(length<=134)return 6;
  if(length<=154)return 7;
  if(length<=192)return 8;
  if(length<=230)return 9;
  return 11;
}
void caption(const char *text,int y,uint16_t color) {
  // Use the same TFT_eSPI GLCD rasterizer in a separate small sprite, so
  // longer sentences cannot overwrite the original QR source or counter.
  bitmaker::renderCaption(text,color);
  int first=240,last=-1;
  for(int row=0;row<8;++row)for(int col=0;col<240;++col)
    if(bitmaker::captionPixel(col,row)) {
      if(col<first)first=col;
      if(col>last)last=col;
    }
  if(last<first)return;
  const int width=last-first+1,dw=(width*3+1)/2,dx=C-dw/2;
#if defined(SEEDER_UI_VERIFY)
  roundVerifyCaption(text,dx,y,dw,12,color);
#endif
  for(int row=0;row<12;++row)for(int col=0;col<dw;++col) {
    const uint16_t ink=bitmaker::captionPixel(first+col*width/dw,row*8/12);
    if(ink)tft.drawPixel(dx+col,y+row,ink);
  }
}
void qrPlacement(const String &payload,uint8_t step,uint8_t total,
                 bool watchOnly,const char *fingerprint,uint8_t words) {
  startFrame();
  centerInk(0,10,103,8,C-24,34,2);
  // Upstream QR pages lack a counter. Reuse its actual font/rasterizer in
  // an otherwise unused source strip; frozen upstream files stay untouched.
  char counter[8];snprintf(counter,sizeof(counter),"%u/%u",step,total);
  bitmakerUi::tiny(counter,10,114,0x4a49,'L',0);
  copy(10,114,18,8,307,36,36,16);
  const int version=originalQrVersion(payload.length());
  const int modules=version*4+17;
  int oldScale=1;
  while((modules+4)*(oldScale+1)<=135&&oldScale<6)++oldScale;
  const int oldQuiet=min(4,(135-modules*oldScale)/(2*oldScale));
  const int oldX=240-modules*oldScale-oldQuiet*oldScale-2;
  const int oldY=(135-modules*oldScale)/2;
  // A two-module white margin keeps the original module pitch while the
  // entire panel fits above the captions, even for 24-word version-7 QRs.
  const int scale=294/(modules+2*QR_QUIET),side=(modules+2*QR_QUIET)*scale;
  const int x=(466-side)/2,y=214-side/2;
#if defined(SEEDER_UI_VERIFY)
  roundVerifyQr(version,modules,scale,x,y,QR_QUIET);
#endif
  tft.fillRect(x,y,side,side,0xffff);
  for(int row=0;row<modules;++row)for(int col=0;col<modules;++col)
    if(bitmaker::pixel(oldX+col*oldScale,oldY+row*oldScale)==0)
      tft.fillRect(x+(col+QR_QUIET)*scale,y+(row+QR_QUIET)*scale,scale,scale,0);
  if(watchOnly) {
    caption("ACCOUNT PUBLIC KEY",370,0xd6ba);
    caption("USE THIS KEY TO VIEW",384,0x86f3);
    caption("WALLET ACTIVITY.",398,0x86f3);
    caption("IT CANNOT SPEND BITCOIN.",412,0x86f3);
    caption("FINGERPRINT",428,0xd6ba);
    caption(fingerprint,442,0x86f3);
  } else {
    caption(words==12?"12 SEED WORDS":"24 SEED WORDS",370,0xd6ba);
    caption("KEEP THIS QR PRIVATE.",384,0x86f3);
    caption("SCAN ONLY WITH AN",402,0xd6ba);
    caption("OFFLINE SIGNING DEVICE.",418,0x86f3);
    caption("NEVER PHOTOGRAPH IT.",432,0x86f3);
  }
  finish();
}
void holdPlacement() {
  startFrame();copy(0,0,183,135,50,118,366,270);captureControls();finish();
}
void exitPlacement() {
  startFrame();
  copy(0,0,240,35,53,101,360,53);
  centerInk(0,35,240,27,C,158,2);
  centerInk(0,62,240,36,C,215,2);
  centerInk(0,110,126,14,C,303,3,2);
  copy(126,100,106,30,127,327,212,60);
  exitPointer();finish();
}
} // namespace
namespace bitmaker {void showSplashFrame(){splashPlacement();}}
namespace ui {
void splash(){if(!bitmaker::begin())while(true)delay(100);splashFrame=0;bitmakerUi::splash();}
void menu(bool selected){bitmakerUi::menu(selected);menuPlacement();}
void words(uint8_t count){bitmakerUi::words(count);menuPlacement();}
void coinEnter(uint16_t total){bitmakerUi::coinEnter(total);}
void coinUpdate(uint16_t done,uint16_t total,const uint8_t *entropy){bitmakerUi::coinUpdate(done,total,entropy);coinPlacement();}
void diceEnter(uint8_t total){bitmakerUi::diceEnter(total);}
void diceUpdate(uint8_t done,uint8_t total,uint8_t value,const uint8_t *history){bitmakerUi::diceUpdate(done,total,value,history);dicePlacement();}
void holdEnter(){bitmaker::prepareHold();bitmakerUi::holdEnter();holdPlacement();}
void holdUpdate(float frac){bitmakerUi::holdUpdate(frac);holdPlacement();}
void generating(){
  bitmakerUi::generating();startFrame();centerInk(0,59,240,18,C,211,5,2);finish();
}
void mnemonic(const String &words,uint8_t count,uint8_t from,uint8_t step,uint8_t total){
  bitmakerUi::mnemonic(words,count,from,step,total);startFrame();header();
  for(int row=0;row<6;++row){
    copy(0,30+row*17,122,17,44,135+row*42,183,26);
    copy(122,30+row*17,118,17,243,135+row*42,177,26);
  }
  finish();
}
void seedAddress(const String &address,uint8_t step,uint8_t total){
  bitmakerUi::seedAddress(address,step,total);startFrame();
  centerInk(0,10,190,8,C-23,34,2);
  copy(212,10,18,8,307,34,36,16);
  String qrAddress=address;qrAddress.toUpperCase();
  QRCode qr;uint8_t buffer[(25*25+7)/8];
  if(qrcode_initText(&qr,buffer,2,ECC_LOW,qrAddress.c_str())>=0) {
    constexpr int scale=10,x=88,y=58,side=(25+2*QR_QUIET)*scale;
#if defined(SEEDER_UI_VERIFY)
    roundVerifyAddressQr(2,25,scale,x,y,QR_QUIET);
#endif
    tft.fillRect(x,y,side,side,0xffff);
    for(int row=0;row<25;++row)for(int col=0;col<25;++col)
      if(qrcode_getModule(&qr,col,row))
        tft.fillRect(x+(col+QR_QUIET)*scale,y+(row+QR_QUIET)*scale,scale,scale,0);
  }
  // Five-character verification groups, kept intact when wrapping. The input
  // address and QR payload remain unchanged; only the original glyph ink tints.
  const int length=address.length();
  for(int i=0;i<length;++i) {
    const int row=i/15,col=i%15,count=min(15,length-row*15);
    const int rowWidth=count*18+((count+4)/5-1)*8;
    const int dx=C-rowWidth/2+col*18+(col/5)*8,dy=350+row*28;
    const int sx=10+(i%18)*12,sy=48+(i/18)*20;
    const uint16_t color=(i/5)%2?0xffff:0x86f3;
#if defined(SEEDER_UI_VERIFY)
    roundVerifyAddressGlyph(i,sx,sy,dx,dy,color);
#endif
    for(int y=0;y<24;++y)for(int x=0;x<18;++x)
      if(bitmaker::pixel(sx+x*2/3,sy+y*2/3))tft.drawPixel(dx+x,dy+y,color);
  }
  finish();
}
void seedEntropy(const String &hex,uint8_t step,uint8_t total){
  bitmakerUi::seedEntropy(hex,step,total);startFrame();header();
  const int rows=(hex.length()/2+7)/8;
  for(int row=0;row<rows;++row)
    copy(0,32+row*26,240,row==3?25:26,35,151+row*60,396,row==3?41:43);
  if(rows<=2)centerInk(0,84,240,51,C,300,2);
  finish();
}
void seedQr(const String &data,uint8_t count,uint8_t step,uint8_t total){bitmakerUi::seedQr(data,count);qrPlacement(data,step,total,false,"",count);}
void seedZpubQr(const String &data,const String &fingerprint,uint8_t step,uint8_t total){bitmakerUi::seedZpubQr(data,fingerprint);qrPlacement(data,step,total,true,fingerprint.c_str(),0);}
void seedExit(){bitmakerUi::seedExit();exitPlacement();}

} // namespace ui
#endif

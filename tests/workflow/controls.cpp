#include "Arduino.h"
#include "GlobalVARS.h"
#include "gpio.h"
#include "workflow.h"
#include "ui/ui.h"
#include <cassert>
#include <iostream>

#ifndef SELECT_ACTIVE_HIGH
#define SELECT_ACTIVE_HIGH 0
#endif
enum View { Menu, Words, Capture, Seed, Address, Entropy, Export, Watch, Exit, Hold };
static View view=Menu;
static int pageStep=0,pageTotal=0,holdEntries=0;
static float holdFraction=0;
static unsigned long now=100;
static int pins[64];
sWallet myWallet;
sButton btnMove(PIN_MOVE);
sButton btnSelect(PIN_SELECT,SELECT_ACTIVE_HIGH);
unsigned long millis(){return now;}
void delay(unsigned long ms){now+=ms;}
void pinMode(uint8_t,uint8_t){}
int digitalRead(uint8_t pin){return pins[pin];}
void digitalWrite(uint8_t,uint8_t){std::abort();}
namespace ui {
void menu(bool){view=Menu;} void words(uint8_t){view=Words;}
void coinEnter(uint16_t){view=Capture;}
void coinUpdate(uint16_t,uint16_t,const uint8_t*){view=Capture;}
void diceEnter(uint8_t){view=Capture;}
void diceUpdate(uint8_t,uint8_t,uint8_t,const uint8_t*){view=Capture;}
void holdEnter(){view=Hold;++holdEntries;holdFraction=0;}
void holdUpdate(float f){view=Hold;holdFraction=f;}
void generating(){}
void mnemonic(const String&,uint8_t,uint8_t,uint8_t s,uint8_t t){view=Seed;pageStep=s;pageTotal=t;}
void seedAddress(const String&,uint8_t s,uint8_t t){view=Address;pageStep=s;pageTotal=t;}
void seedEntropy(const String&,uint8_t s,uint8_t t){view=Entropy;pageStep=s;pageTotal=t;}
void seedQr(const String&,uint8_t,uint8_t s,uint8_t t){view=Export;pageStep=s;pageTotal=t;}
void seedZpubQr(const String&,const String&,uint8_t s,uint8_t t){view=Watch;pageStep=s;pageTotal=t;}
void seedExit(){view=Exit;}
}
extern int menuSeed;
extern uint8_t entropy[32];
static void tick(unsigned ms){
 for(unsigned i=0;i<ms;i+=10){now+=10;btnMove.check();btnSelect.check();
  switch(myWallet.State){case STATE_INITMENU:doInitMenu();break;case STATE_WORDS:doMenuWords();break;case STATE_COINSEED:doCoinSeed();break;case STATE_DICESEED:doDiceSeed();break;case STATE_SEED:doShowSeed();break;}
 }
}
static void level(int pin,bool pressed){pins[pin]=pin==PIN_SELECT?(pressed?SELECT_ACTIVE_HIGH:!SELECT_ACTIVE_HIGH):(pressed?LOW:HIGH);}
static void press(int pin,unsigned ms=80){level(pin,true);tick(ms);level(pin,false);tick(80);}
int main(){
 level(PIN_MOVE,false);level(PIN_SELECT,false);myWallet.State=STATE_INITMENU;myWallet.entropySrc=coinEntropy;tick(80);
 press(PIN_SELECT);press(PIN_SELECT);assert(myWallet.State==STATE_COINSEED);
 press(PIN_SELECT);const int entries=holdEntries;press(PIN_SELECT,1600);assert(holdEntries==entries+1&&myWallet.nBCoinEntropy==1&&view==Capture);
 press(PIN_SELECT,3200);assert(myWallet.State==STATE_INITMENU);
 press(PIN_SELECT);press(PIN_SELECT);for(int i=0;i<128;++i)press(PIN_SELECT);
 assert(myWallet.State==STATE_SEED&&menuSeed==SHOW_SEED1&&pageStep==1&&pageTotal==5);
 assert(myWallet.mnemonic=="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about");
 const int order[]={SHOW_DATA1,SHOW_ENTROPY,SHOW_EXPORTQR,SHOW_EXPORTZPUB,SHOW_EXIT};
 for(int next:order){press(PIN_SELECT);assert(menuSeed==next);if(next==SHOW_EXPORTQR)assert(view==Export&&pageStep==4&&pageTotal==5);if(next==SHOW_EXPORTZPUB)assert(view==Watch&&pageStep==5&&pageTotal==5);}
 press(PIN_MOVE);assert(menuSeed==SHOW_EXPORTZPUB);press(PIN_SELECT);assert(view==Exit);
 const String saved=myWallet.mnemonic;level(PIN_SELECT,true);tick(1700);assert(view==Hold&&holdFraction>0&&holdFraction<1&&myWallet.mnemonic==saved);
 press(PIN_MOVE);assert(menuSeed==SHOW_EXIT&&view==Hold);level(PIN_SELECT,false);tick(80);assert(view==Exit&&myWallet.mnemonic==saved);
 press(PIN_SELECT);assert(menuSeed==SHOW_SEED1);press(PIN_MOVE);assert(view==Exit);
 press(PIN_SELECT,3200);assert(myWallet.State==STATE_INITMENU&&myWallet.mnemonic.empty()&&myWallet.firstAddress.empty()&&myWallet.xpub.empty());
 for(auto b:entropy)assert(b==0);
 press(PIN_MOVE);press(PIN_SELECT);press(PIN_MOVE);press(PIN_SELECT);assert(myWallet.State==STATE_DICESEED&&myWallet.nWords==24);
 for(int i=0;i<99;++i)press(PIN_SELECT);
 assert(myWallet.State==STATE_SEED&&pageStep==1&&pageTotal==6);
 press(PIN_SELECT);assert(menuSeed==SHOW_SEED2);press(PIN_SELECT);assert(view==Address&&pageStep==3&&pageTotal==6);
 press(PIN_SELECT);press(PIN_SELECT);assert(view==Export&&pageStep==5&&pageTotal==6);press(PIN_SELECT);assert(view==Watch&&pageStep==6&&pageTotal==6);
 std::cout<<
#if defined(SEEDER_BOARD_WAVESHARE175C)
"Waveshare 1.75C"
#else
BOARD_NAME
#endif
<<": PASS matching page order/counters, big-forward/small-back, real button polarities, input/Exit hold overlays, cancel/confirm and clearing\n";
}

#pragma once
/**********************************
 🍃 SELECCIÓN DE PLACA

 La composición rectangular se diseñó sobre 240x135. Sus coordenadas pasan
 por SX()/SY(). La pantalla circular usa round_ui.cpp a resolución nativa.

 Los dos ejes escalan distinto (320/240 = 1,33 frente a 170/135 = 1,26),
 así que se escalan por separado y no con un único factor.
**********************************/

#if defined(SEEDER_BOARD_WAVESHARE175C)
  #include "waveshare175c.h"
#elif defined(SEEDER_BOARD_STICKS3)
  #include "sticks3.h"
#elif defined(SEEDER_BOARD_TDISPLAY_S3)
  #include "tdisplay_s3.h"
#else
  #include "tdisplay.h"
#endif

// SX/SY remain for the rectangular boards. round_ui.cpp uses native geometry
// inside the circular panel, rather than stretching the landscape layout.
#define UI_REF_W  240        // lienzo de referencia del diseño
#define UI_REF_H  135

#define SX(v)  ((int)(((long)(v) * UI_W) / UI_REF_W))
#define SY(v)  ((int)(((long)(v) * UI_H) / UI_REF_H))

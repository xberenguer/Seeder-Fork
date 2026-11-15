#pragma once

// ESP32-S3-Touch-AMOLED-1.75C only (32 MB flash, CO5300, 466 x 466).
// The non-C board has different wiring and is not this build target.
#define UI_W 466
#define UI_H 466
#define PIN_MOVE 0       // Small BOOT: MOVE, active LOW.
#define PIN_SELECT 3     // Big PWR: OK, active HIGH (inverted SYS_OUT).
#define SELECT_ACTIVE_HIGH 1
// Hold the enclosure 270 degrees clockwise from its old buttons-right pose.
// Counter-rotate the pixels 90 degrees clockwise so the UI stays upright:
// both buttons are above the dial, OK on the left and MOVE on the right.
#define SEEDER_DEVICE_ORIENTATION_DEGREES 270
#define SEEDER_CANVAS_ROTATION 1

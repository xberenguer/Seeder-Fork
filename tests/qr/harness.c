#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "qrcoded.h"

static int hex_nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int check_api_contract(void) {
    QRCode qr;
    uint8_t modules[qrcode_getBufferSize(2)];
    uint8_t payload[32] = {0};
    // Version 1-L cannot hold a 32-byte BYTE segment. Reject before writing.
    if (qrcode_initBinary(&qr, modules, 1, ECC_LOW, payload, 32) >= 0) return 10;
    if (qrcode_initBinary(&qr, modules, 0, ECC_LOW, payload, 16) >= 0) return 11;
    if (qrcode_initBinary(&qr, modules, 41, ECC_LOW, payload, 16) >= 0) return 12;
    if (qrcode_initBinary(&qr, modules, 1, 4, payload, 16) >= 0) return 13;
    if (qrcode_initBinary(&qr, modules, 1, ECC_LOW, NULL, 16) >= 0) return 14;

    // Keep the original text/byte APIs' automatic compression for other pages.
    const char *digits = "1234567890123456";
    uint8_t uppercase[] = "ABCDEFGHIJKLMNOP";
    if (qrcode_initText(&qr, modules, 1, ECC_LOW, digits) < 0 || qr.mode != MODE_NUMERIC) return 15;
    if (qrcode_initBytes(&qr, modules, 1, ECC_LOW, uppercase, 16) < 0 || qr.mode != MODE_ALPHANUMERIC) return 16;
    return 0;
}

static int write_image(QRCode *qr, const char *path) {
    printf("%u %u %u %u\n", qr->version, qr->size, qr->ecc, qr->mode);
    // Reference image for testing the encoder independently of the display.
    // The actual firmware panel layout is checked by the native UI renderer.
    const int quiet = 4, scale = 4;
    const int side = (qr->size + 2*quiet) * scale;
    FILE *image = fopen(path, "wb");
    if (!image) return 6;
    fprintf(image, "P5\n%d %d\n255\n", side, side);
    for (int y = 0; y < side; ++y) {
        for (int x = 0; x < side; ++x) {
            const int mx = x/scale - quiet, my = y/scale - quiet;
            const int dark = mx >= 0 && my >= 0 && mx < qr->size && my < qr->size
                && qrcode_getModule(qr, (uint8_t)mx, (uint8_t)my);
            if (fputc(dark ? 0 : 255, image) == EOF) return 7;
        }
    }
    if (fclose(image)) return 8;
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--contract") == 0) return check_api_contract();
    if (argc == 4 && strcmp(argv[1], "--address") == 0) {
        if (strlen(argv[2]) != 42) return 20;
        char address[43];
        // Match the display's BIP173 uppercasing step before passing the
        // address through the production text encoder in version 2-L.
        for (int i = 0; i < 42; ++i) address[i] = (char)toupper((unsigned char)argv[2][i]);
        address[42] = '\0';
        uint8_t modules[qrcode_getBufferSize(2)];
        QRCode qr;
        if (qrcode_initText(&qr, modules, 2, ECC_LOW, address) != 0) return 21;
        return write_image(&qr, argv[3]);
    }
    if (argc != 3) return 2;
    const size_t length = strlen(argv[1]) / 2;
    if ((length != 16 && length != 32) || strlen(argv[1]) != length * 2) return 3;
    uint8_t payload[32];
    for (size_t i = 0; i < length; ++i) {
        const int hi = hex_nibble(argv[1][2*i]);
        const int lo = hex_nibble(argv[1][2*i+1]);
        if (hi < 0 || lo < 0) return 4;
        payload[i] = (uint8_t)((hi << 4) | lo);
    }

    const uint8_t version = length == 16 ? 1 : 2;
    uint8_t modules[qrcode_getBufferSize(version)];
    QRCode qr;
    if (qrcode_initBinary(&qr, modules, version, ECC_LOW, payload, (uint16_t)length) != 0) return 5;
    return write_image(&qr, argv[2]);
}

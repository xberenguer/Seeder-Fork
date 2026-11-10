#include <iostream>
#include <string>
#include <Arduino.h>
#include "GlobalVARS.h"
#include "btc.h"
#include "Conversion.h"

sWallet myWallet;
int main(int argc, char** argv) {
  if (argc != 4) return 2;
  int words = std::stoi(argv[1]);
  uint8_t entropy[32] = {};
  std::string kind = argv[2], input = argv[3];
  if (kind == "dice") {
    entropyFromDice(input.c_str(), input.length(), entropy);
  } else if (kind == "coin") {
    const size_t needed = words * 4 / 3;
    if (input.length() != needed * 8) return 3;
    // Exact MSB-first bit assembly used by doCoinSeed in workflow.cpp.
    for (size_t i = 0; i < input.length(); ++i) {
      if (input[i] != '0' && input[i] != '1') return 4;
      entropy[i/8] |= ((input[i] - '0') << (7-i%8));
    }
  } else if (kind == "hex") {
    fromHex(input, entropy, sizeof(entropy));
  } else return 5;
  createSeed(words, entropy);
  std::cout << myWallet.entropyHex << '\n' << myWallet.mnemonic << '\n'
    << myWallet.fingerprint << '\n' << myWallet.xpub << '\n'
    << myWallet.firstAddress << '\n';
}

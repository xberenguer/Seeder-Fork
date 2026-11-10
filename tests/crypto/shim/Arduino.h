#pragma once
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <string>

// Host-only compatibility for compiling the unmodified application btc.cpp.
// uBitcoin itself is compiled in its supported USE_STDONLY mode.
class String : public std::string {
 public:
  using std::string::string;
  using std::string::operator=;
  String(const std::string& s) : std::string(s) {}
  void toUpperCase() {
    std::transform(begin(), end(), begin(), [](unsigned char c) { return std::toupper(c); });
  }
};
inline void delay(unsigned long) {}

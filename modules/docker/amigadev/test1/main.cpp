#include <proto/exec.h>
#include <proto/dos.h>
#include <string>

using uint16_t = unsigned short;
using reg16_t  = volatile uint16_t*;

int main(int argc, char** argv) {

  auto COLOR0 = reg16_t(0xDFF180);

  auto setcolor = [](uint16_t color, uint16_t val) {
    auto reg_addr = reg16_t(0xDFF180 + (color << 1));
    (*reg_addr)   = val;
  };

  auto SysBase = *((Library**)4UL);
  auto DOSBase = OpenLibrary("dos.library", 0);

  auto outputstr = Output();

  auto writestr = [DOSBase, outputstr](const std::string s) { Write(outputstr, (void*)s.c_str(), s.length()); };

  printf("DOSBase<%p>\n", (void*)DOSBase);

  if (DOSBase) {
    writestr("Hello World\n");

    while (true) {
      auto VHPOSR  = reg16_t(0xDFF006);
      uint16_t val = *VHPOSR;
      setcolor(0, val);
    }

    CloseLibrary(DOSBase);
  }

  return (0);
}

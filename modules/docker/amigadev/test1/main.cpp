#include <exec/exec.h>
#include <graphics/gfxbase.h>
#include <clib/exec_protos.h>
#include <clib/dos_protos.h>
#include <clib/graphics_protos.h>
#include <clib/intuition_protos.h>
#include <hardware/custom.h>
#include <string>
#include <memory>
#include <assert.h>

using uint16_t = unsigned short;
using reg16_t  = volatile uint16_t*;

////////////////////////////////////////////////////////////

struct LibraryRef {

  LibraryRef(const char* name, int version) {
    auto SysBase = *((Library**)4UL);
    _libref      = OpenLibrary(name, version);
    assert(_libref != nullptr);
    _libname = name;
  }
  virtual ~LibraryRef() {
    CloseLibrary(_libref);
  }
  operator bool() const {
    return _libref != nullptr;
  }
  Library* _libref = nullptr;
  std::string _libname;
};

/*
        //printf("buffer<%s> length<%d>\n", buffer, length);
        //LONG rval;
        //BPTR __Output(__reg("a6") struct DosLibrary *)="\tjsr\t-60(a6)";
        //LONG __Write(__reg("d1") BPTR file, __reg("d2") APTR buffer, __reg("d3") long length, __reg("a6") struct DosLibrary
   *)="\tjsr\t-48(a6)";
        //#define Write(file, buffer, length) __Write((file), (buffer), (length), DOSBase)
        /*asm (
            "# get output stream\n"
            "move.l %1, a6\n"
            "jsr -60(a6)\n"
            "# write to output stream (in d0)\n"
            "move.l d0, d1\n"
            "move.l %2, d1\n"
            "move.l %3, d3\n"
            "jsr -48(a6)\n"
            "move.l d0, %0\n"
            : "=g" (rval)// outputs
            : "g" (_libref), "g" (buffer), "d" (length) // inputs
            : "d0", "d1", "d2", "d3", "a6" // clobbers
        );
*/

////////////////////////////////////////////////////////////
// Dos http://amigadev.elowar.com/read/ADCD_2.1/Includes_and_Autodocs_2._guide/node0029.html
////////////////////////////////////////////////////////////
struct DosLib : public LibraryRef {
  DosLib()
    : LibraryRef("dos.library", 36) {
    _outputstream = Output();
  }
  ////////////////////////////////////////////
  void output(const std::string& s) {
    auto buffer = (APTR)s.c_str();
    auto length = (long)s.length();
    Write(_outputstream, buffer, length);
  }
  ////////////////////////////////////////////
  void output(const char* formatstring, ...) {
    char formatbuffer[512];
    va_list args;
    va_start(args, formatstring);
    vsnprintf(&formatbuffer[0], sizeof(formatbuffer), formatstring, args);
    va_end(args);
    auto length = (long)strlen(formatbuffer);
    Write(_outputstream, formatbuffer, length);
  }
  ////////////////////////////////////////////

  BPTR _outputstream = 0;
};
////////////////////////////////////////////////////////////
// Exec http://amigadev.elowar.com/read/ADCD_2.1/Includes_and_Autodocs_2._guide/node002B.html
////////////////////////////////////////////////////////////
struct ExecLib : public LibraryRef {
  ExecLib()
    : LibraryRef("exec.library", 36) {
  }
  void setMainThreadPriority(int pri) {
    SetTaskPri(FindTask(nullptr), pri);
  }
};

////////////////////////////////////////////////////////////
// gfx http://amigadev.elowar.com/read/ADCD_2.1/Includes_and_Autodocs_2._guide/node0031.html
////////////////////////////////////////////////////////////

#define COP_MOVE(addr, data) addr, data
#define COP_WAIT_END 0xffff, 0xfffe
#define TASK_PRIORITY (20)
#define COLOR00 (0x180)
#define BPLCON0 (0x100)
#define PRA_FIR0_BIT (1 << 6)
#define BPLCON0_COMPOSITE_COLOR (1 << 9)

////////////////////////////////////////////////////////////

struct GfxLib : public LibraryRef {
  GfxLib()
    : LibraryRef("graphics.library", 36) {
  }
  enum class VidStd {
    ntsc = 0,
    pal,
  };

  void initDisplay() {
    extern struct GfxBase* GfxBase;
    extern struct Custom custom;
    LoadView(NULL);
    WaitTOF();
    WaitTOF();
    _vidstd       = (GfxBase->DisplayFlags & PAL) ? VidStd::pal : VidStd::ntsc;

    // copper list

    static UWORD __attribute__((chip)) _the_copper_list[] = {
      COP_MOVE(BPLCON0, BPLCON0_COMPOSITE_COLOR),
      COP_MOVE(COLOR00, 0x000),
      0x6607,
      0xfffe,
      COP_MOVE(COLOR00, 0xf00),
      0xb607,
      0xfffe,
      COP_MOVE(COLOR00, 0xff0),
      COP_WAIT_END
    };

    // install copper list

    custom.cop1lc = (ULONG) _the_copper_list;
  }

  void resetDisplay() {
    extern struct GfxBase* GfxBase;
    extern struct Custom custom;
    LoadView(((struct GfxBase*)GfxBase)->ActiView);
    WaitTOF();
    WaitTOF();
    custom.cop1lc = (ULONG)((struct GfxBase*)GfxBase)->copinit;
    RethinkDisplay();
  }

  VidStd _vidstd;
};

////////////////////////////////////////////////////////////

int main(int argc, char** argv) {

  auto exec = std::make_shared<ExecLib>();
  auto dos  = std::make_shared<DosLib>();
  auto gfx  = std::make_shared<GfxLib>();

  exec->setMainThreadPriority(TASK_PRIORITY);
  dos->output("Hello World\n");
  dos->output("dos<%p>\n", dos.get());
  dos->output("exec<%p>\n", exec.get());
  dos->output("gfx<%p>\n", gfx.get());

  Delay(120);

  auto setcolor = [](uint16_t color, uint16_t val) {
    auto reg_addr = reg16_t(0xDFF180 + (color << 1));
    (*reg_addr)   = val;
  };

  gfx->initDisplay();

  while (false) {
    auto VHPOSR  = reg16_t(0xDFF006);
    uint16_t val = *VHPOSR;
    setcolor(0, val);
  }

  Delay(120);

  gfx->resetDisplay();

  return (0);
}

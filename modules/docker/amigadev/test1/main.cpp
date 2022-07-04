#include <proto/exec.h>
#include <proto/dos.h>
#include <string>

using uint16_t = unsigned short;
using reg16_t = volatile uint16_t*;

int main(int argc, char **argv )
{


    auto COLOR0 = reg16_t(0xDFF180);

    auto setcolor = [](uint16_t color, uint16_t val){
        auto reg_addr = reg16_t(0xDFF180+(color<<1));
        (*reg_addr) = val;
    };


    for( int i=0; i<32; i++ )
        setcolor(i,0);

    auto SysBase = *((Library **)4UL);
    auto DOSBase = OpenLibrary("dos.library", 0);

    auto outputstr = Output();
    
    auto writestr = [DOSBase,outputstr](const std::string s){
        Write(outputstr, (void*) s.c_str(), s.length());
    };

    if (DOSBase) {
        writestr("Hello World\n");
        writestr("wtf1\n");
        writestr("wtf2\n");
        writestr("wtf3\n");
        CloseLibrary(DOSBase);
    }

    return(0);
}

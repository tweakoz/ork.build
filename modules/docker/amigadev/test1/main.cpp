#include <proto/exec.h>
#include <proto/dos.h>
#include <string>



int main(int argc, char **argv )
{
    auto SysBase = *((Library **)4UL);
    auto DOSBase = OpenLibrary("dos.library", 0);

    auto writestr = [DOSBase](const std::string s){
        auto outputstr = Output();
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

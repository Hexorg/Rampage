#include <iostream>
#include "Tracer.h"

int main(int argc, char *argv[]) {
	System::Tracer t(32579);
	unsigned long data = t.getMemory(0x7ffcdd5baa58);
	std::cout <<std::hex <<  data << std::endl;
	return 0;
}

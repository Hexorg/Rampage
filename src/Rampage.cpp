#include <iostream>
#include "ProcMaps.h"

int main(int argc, char *argv[]) {
	System::ProcMaps fMap(3588);
	std::vector<System::ProcMapEntry> result = fMap.getNonLibraryEntries();
	std::vector<System::ProcMapEntry>::iterator it;

	for (it = result.begin(); it != result.end(); ++it) {
		std::cout << std::hex << it->start << '-' << it->end << ' ' << it->pathname << std::endl;
	}
	return 0;
}

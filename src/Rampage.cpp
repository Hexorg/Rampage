#include <iostream>
#include "ProcMaps.h"

int main(int argc, char *argv[]) {
	System::ProcMaps fMap(3588);
	std::vector<System::ProcMapEntry> result = fMap.getNonFileEntries();
	std::vector<System::ProcMapEntry>::iterator it;

	for (it = result.begin(); it != result.end(); ++it) {
		std::cout << std::hex << it->start << '-' << it->end << ' '
			<< std::dec << (unsigned int) it->perms << ' ' 
			<< std::hex << (unsigned int) it->dev_major << ':' << (unsigned int) it->dev_minor
			<< ' ' << std::dec << it->inode << '\t' << it->pathname << std::endl;
	}
	return 0;
}

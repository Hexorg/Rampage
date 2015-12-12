#include "ProcMaps.h"
#include <fstream>
#include <sstream>

namespace System {

	ProcMaps::ProcMaps(unsigned short pid) {
		std::stringstream ss;
		ss << "/proc/" << pid << "/maps";
		std::ifstream mapFile(ss.str().c_str());
		char buffer[1024];
		while (mapFile.getline(buffer, sizeof(buffer))) {
			ss.clear(); ss.str(buffer);
			struct ProcMapEntry entry;
			ss >> std::hex >> entry.start;
			ss.ignore(3, '-');
			ss >> std::hex >> entry.end >> std::skipws >>  entry.perms >> std::skipws  
				>> std::hex >> entry.offset >> std::skipws >> std::hex >> entry.dev_major;
			ss.ignore(1, ':');
			ss >> std::hex >> entry.dev_minor >> std::skipws >> std::dec >> entry.inode 
				>> std::skipws >> entry.pathname;
			//mapFile.ignore(100, '\n');
			entryList.push_back(entry);
			if (entry.pathname.rfind(".so") != std::string::npos)
				libraryList.push_back(entry);
			else
				nonLibraryList.push_back(entry);
		}

	}

	ProcMaps::~ProcMaps() {  }
	
	const struct ProcMapEntry * ProcMaps::getEntry(unsigned int id) const {
		return &entryList.at(id);
	}

	std::vector<struct ProcMapEntry> ProcMaps::getLibraryEntries() const {
		return libraryList;
	}

	std::vector<struct ProcMapEntry> ProcMaps::getNonLibraryEntries() const {
		return nonLibraryList;
	}

}

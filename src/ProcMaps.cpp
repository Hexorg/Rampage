#include "ProcMaps.h"
#include <fstream>
#include <sstream>

namespace System {

	ProcMaps::ProcMaps(unsigned short pid) {
		std::stringstream ss;
		ss << "/proc/" << pid << "/maps";
		std::ifstream mapFile(ss.str().c_str());
		char buffer[1024];
		char perms[4];
		unsigned short dev_tmp;
		while (mapFile.getline(buffer, sizeof(buffer))) {
			ss.clear(); ss.str(buffer);
			struct ProcMapEntry entry;
			ss >> std::hex >> entry.start;
			ss.ignore(3, '-');
			ss >> std::hex >> entry.end >> std::skipws >>  perms >> std::skipws  
				>> std::hex >> entry.offset >> std::skipws >> std::hex >> dev_tmp;
			ss.ignore(1, ':');
			entry.perms = 0;
			if (perms[3] == 'p') entry.perms |= PERM_PRIVATE;
			if (perms[2] == 'x') entry.perms |= PERM_EXECUTE;
			if (perms[1] == 'w') entry.perms |= PERM_WRITE;
			if (perms[0] == 'r') entry.perms |= PERM_READ;
			entry.dev_major = (unsigned char ) dev_tmp;
			ss >> std::hex >> dev_tmp >> std::skipws >> std::dec >> entry.inode 
				>> std::skipws >> entry.pathname;
			entry.dev_minor = dev_tmp;
			//mapFile.ignore(100, '\n');
			entryList.push_back(entry);
			if (entry.pathname.rfind(".so") != std::string::npos)
				libraryList.push_back(entry);
			else
				nonLibraryList.push_back(entry);
			if (entry.inode == 0)
				nonFileList.push_back(entry);
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

	std::vector<struct ProcMapEntry> ProcMaps::getNonFileEntries() const {
		return nonFileList;
	}
}

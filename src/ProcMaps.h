#ifndef __PROCMAPS_H__
#define __PROCMAPS_H__

#include <string>
#include <vector>
namespace System {

struct ProcMapEntry {
	unsigned long start;
	unsigned long end;
	char perms[4];
	unsigned long offset;
	unsigned short dev_major;
	unsigned short dev_minor;
	unsigned int inode;
	std::string pathname;
};

class ProcMaps {
	public:
		ProcMaps(unsigned short pid);
		~ProcMaps();
		
		const struct ProcMapEntry *getEntry(unsigned int id) const;
		std::vector<struct ProcMapEntry> getLibraryEntries() const;
		std::vector<struct ProcMapEntry> getNonLibraryEntries() const;
	private:
		std::vector<struct ProcMapEntry> entryList;
		std::vector<struct ProcMapEntry> libraryList;
		std::vector<struct ProcMapEntry> nonLibraryList;
};

}

#endif

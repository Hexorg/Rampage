#ifndef __PROCMAPS_H__
#define __PROCMAPS_H__

#include <string>
#include <vector>
namespace System {

#define PERM_PRIVATE 1
#define PERM_EXECUTE 2
#define PERM_WRITE 4
#define PERM_READ 8

struct ProcMapEntry {
	unsigned long start;
	unsigned long end;
	unsigned char perms;
	unsigned long offset;
	unsigned char dev_major;
	unsigned char dev_minor;
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
		std::vector<struct ProcMapEntry> getNonFileEntries() const;
	private:
		std::vector<struct ProcMapEntry> entryList;
		std::vector<struct ProcMapEntry> libraryList;
		std::vector<struct ProcMapEntry> nonLibraryList;
		std::vector<struct ProcMapEntry> nonFileList;
};

}

#endif

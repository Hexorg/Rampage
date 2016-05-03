#ifndef __TRACER_H__
#define __TRACER_H__

#include <exception>

namespace System {

class TracerException: public std::exception {
	const char* what() const throw() {
		return "Tracer Exception";
	}
};

class Tracer {
public:
	Tracer(unsigned int pid, bool pauseOnStart = false);
	~Tracer();

	unsigned long getMemory(unsigned long address);
private:
	unsigned int pid;
};


}
#endif
